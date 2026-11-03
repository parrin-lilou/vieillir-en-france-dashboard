"""Tests unitaires de l'accès à la base SQLite avec SQLAlchemy."""

import pandas as pd
import pytest

import config
from src.utils import base_donnees


@pytest.fixture
def base_temporaire(tmp_path, monkeypatch):
    """Redirige la base vers un fichier temporaire, pour ne pas toucher la vraie."""
    chemin = tmp_path / "test.sqlite"
    monkeypatch.setattr(config, "BASE_SQLITE", chemin)
    return chemin


def test_nom_table_brute():
    """Vérifie le nom de la table brute d'une source."""
    assert base_donnees.nom_table_brute("tx_pauv_60") == "raw_tx_pauv_60"


def test_nom_table_nettoyee():
    """Vérifie le nom de la table nettoyée d'un indicateur."""
    assert base_donnees.nom_table_nettoyee("taux_pauvrete") == "cleaned_taux_pauvrete"


def test_moteur_utilise_la_base_du_projet(base_temporaire):
    """Vérifie que le moteur SQLAlchemy pointe vers la base configurée."""
    moteur = base_donnees.creer_moteur()

    assert moteur.url.database == str(base_temporaire)

    moteur.dispose()


def test_ecrire_puis_lire_table(base_temporaire):
    """Vérifie qu'une table écrite est relue à l'identique."""
    table = pd.DataFrame({"codgeo": ["200000001", "200000002"], "valeur": [1.5, 2.5]})

    base_donnees.ecrire_table(table, "essai")
    resultat = base_donnees.lire_table("essai")

    pd.testing.assert_frame_equal(resultat, table)


def test_ecrire_table_remplace(base_temporaire):
    """Vérifie qu'une nouvelle écriture remplace la table au lieu de l'allonger."""
    base_donnees.ecrire_table(pd.DataFrame({"valeur": [1, 2, 3]}), "essai")
    base_donnees.ecrire_table(pd.DataFrame({"valeur": [9]}), "essai")

    resultat = base_donnees.lire_table("essai")

    assert resultat["valeur"].tolist() == [9]


def test_lister_tables(base_temporaire):
    """Vérifie que les tables écrites apparaissent, triées par nom."""
    base_donnees.ecrire_table(pd.DataFrame({"a": [1]}), "raw_b")
    base_donnees.ecrire_table(pd.DataFrame({"a": [1]}), "cleaned_a")

    assert base_donnees.lister_tables() == ["cleaned_a", "raw_b"]


def test_lister_tables_base_vide(base_temporaire):
    """Vérifie qu'une base neuve ne contient aucune table."""
    assert base_donnees.lister_tables() == []
