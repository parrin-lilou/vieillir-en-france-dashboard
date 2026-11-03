"""Tests unitaires de la récupération des données, sans connexion internet."""

import urllib.error

import pytest

import config
from src.utils import get_data


def erreur_serveur(url, destination):
    """Simule le serveur de l'Observatoire qui répond par une erreur 500."""
    raise urllib.error.HTTPError(url, 500, "internal server error", None, None)


def test_construire_url():
    """Vérifie que l'adresse contient le niveau, la base et l'indicateur."""
    resultat = get_data.construire_url("tx_pauv_60", "filosofi")

    assert "nivgeo=" + config.NIVEAU_GEOGRAPHIQUE in resultat
    assert "dataset=filosofi" in resultat
    assert "indic=tx_pauv_60" in resultat


def test_recuperer_source_telechargee(tmp_path, monkeypatch):
    """Vérifie qu'un téléchargement réussi est signalé comme tel."""
    destination = tmp_path / "source.xlsx"
    monkeypatch.setattr(
        get_data, "telecharger", lambda url, chemin: chemin.write_text("neuf")
    )

    assert get_data.recuperer_source("https://exemple", destination) is True
    assert destination.read_text() == "neuf"


def test_recuperer_source_copie_locale(tmp_path, monkeypatch):
    """Vérifie que la copie locale est gardée, intacte, si le serveur échoue."""
    destination = tmp_path / "source.xlsx"
    destination.write_text("copie d'origine")
    monkeypatch.setattr(get_data, "telecharger", erreur_serveur)

    assert get_data.recuperer_source("https://exemple", destination) is False
    assert destination.read_text() == "copie d'origine"


def test_recuperer_source_sans_copie(tmp_path, monkeypatch):
    """Vérifie l'erreur claire quand il n'y a ni téléchargement ni copie."""
    monkeypatch.setattr(get_data, "telecharger", erreur_serveur)

    with pytest.raises(FileNotFoundError, match="aucune copie locale"):
        get_data.recuperer_source("https://exemple", tmp_path / "absente.xlsx")


def test_telecharger_sources_compte_les_copies(tmp_path, monkeypatch):
    """Vérifie le nombre de sources reconstruites depuis leur copie locale."""
    monkeypatch.setattr(config, "DOSSIER_BRUT", tmp_path)
    monkeypatch.setattr(config, "FOND_CARTE_BRUT", tmp_path / "epci.geojson")
    for indicateur in config.SOURCES_OBSERVATOIRE:
        (tmp_path / f"{indicateur}.xlsx").write_text("copie")
    (tmp_path / "epci.geojson").write_text("copie")
    monkeypatch.setattr(get_data, "telecharger", erreur_serveur)

    resultat = get_data.telecharger_sources()

    assert resultat == len(config.SOURCES_OBSERVATOIRE) + 1
