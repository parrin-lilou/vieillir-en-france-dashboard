"""Tests unitaires des fonctions communes du dashboard."""

import json
import sqlite3

import pandas as pd
import pytest

import config
from src.utils import common_functions as cf


# ---------------------------------------------------------
# 1. Création de données fictives pour les tests
# ---------------------------------------------------------


@pytest.fixture
def donnees_test(monkeypatch):
    """Prépare des données fictives sans utiliser la vraie base SQLite."""
    table = pd.DataFrame(
        {
            "codgeo": [
                "200000003",
                "200000001",
                "200000001",
                "200000002",
                "200000001",
                "200000002",
                "200000003",
            ],
            "libgeo": [
                "EPCI C",
                "EPCI A",
                "EPCI A",
                "EPCI B",
                "EPCI A",
                "EPCI B",
                "EPCI C",
            ],
            "indicateur": [
                "part_75_plus",
                "part_75_plus",
                "part_75_plus",
                "part_75_plus",
                "taux_pauvrete",
                "taux_pauvrete",
                "taux_pauvrete",
            ],
            "annee": [
                2021,
                2021,
                2022,
                2022,
                2023,
                2023,
                2023,
            ],
            "valeur": [
                18.0,
                12.0,
                15.0,
                20.0,
                10.0,
                25.0,
                30.0,
            ],
        }
    )

    # Remplace temporairement la lecture SQLite par nos données.
    monkeypatch.setattr(
        cf,
        "charger_table_nettoyee",
        lambda: table.copy(),
    )

    return table


# ---------------------------------------------------------
# 2. Tests de chargement des fichiers
# ---------------------------------------------------------


def test_charger_table_nettoyee(tmp_path, monkeypatch):
    """Vérifie la lecture d'une table SQLite temporaire."""
    chemin_base = tmp_path / "test.sqlite"

    table = pd.DataFrame(
        {
            "codgeo": ["200000001"],
            "libgeo": ["EPCI A"],
            "indicateur": ["part_75_plus"],
            "annee": [2022],
            "valeur": [15.0],
        }
    )

    with sqlite3.connect(chemin_base) as connexion:
        table.to_sql("cleaned", connexion, index=False)

    monkeypatch.setattr(config, "BASE_SQLITE", chemin_base)
    monkeypatch.setattr(config, "TABLE_NETTOYEE", "cleaned")

    cf.charger_table_nettoyee.cache_clear()

    try:
        resultat = cf.charger_table_nettoyee()

        assert len(resultat) == 1
        assert resultat["codgeo"].iloc[0] == "200000001"
        assert resultat["valeur"].iloc[0] == 15.0
    finally:
        cf.charger_table_nettoyee.cache_clear()


def test_charger_fond_carte(tmp_path, monkeypatch):
    """Vérifie la lecture d'un fichier GeoJSON temporaire."""
    chemin_geojson = tmp_path / "carte.geojson"

    contenu = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"nom": "EPCI A"},
                "geometry": {
                    "type": "Point",
                    "coordinates": [2.35, 48.85],
                },
            }
        ],
    }

    chemin_geojson.write_text(
        json.dumps(contenu),
        encoding="utf-8",
    )

    monkeypatch.setattr(config, "FOND_CARTE", chemin_geojson)

    cf.charger_fond_carte.cache_clear()

    try:
        resultat = cf.charger_fond_carte()

        assert resultat["type"] == "FeatureCollection"
        assert len(resultat["features"]) == 1
        assert (
            resultat["features"][0]["properties"]["nom"]
            == "EPCI A"
        )
    finally:
        cf.charger_fond_carte.cache_clear()


# ---------------------------------------------------------
# 3. Tests des noms et des années
# ---------------------------------------------------------


def test_noms_epci(donnees_test):
    """Vérifie que les EPCI sont uniques et triés par code."""
    resultat = cf.noms_epci()

    assert len(resultat) == 3

    assert resultat.index.tolist() == [
        "200000001",
        "200000002",
        "200000003",
    ]

    assert resultat.loc["200000001"] == "EPCI A"
    assert resultat.loc["200000002"] == "EPCI B"
    assert resultat.loc["200000003"] == "EPCI C"


def test_valeurs_par_annee(donnees_test):
    """Vérifie l'organisation des valeurs par EPCI et par année."""
    resultat = cf.valeurs_par_annee("part_75_plus")

    assert resultat.columns.tolist() == [2021, 2022]

    assert resultat.loc["200000001", 2021] == 12.0
    assert resultat.loc["200000001", 2022] == 15.0
    assert resultat.loc["200000002", 2022] == 20.0


def test_valeurs_par_annee_manquantes(donnees_test):
    """Vérifie qu'une année absente reste une valeur manquante."""
    resultat = cf.valeurs_par_annee("part_75_plus")

    assert pd.isna(resultat.loc["200000002", 2021])
    assert pd.isna(resultat.loc["200000003", 2022])


def test_annees_disponibles(donnees_test):
    """Vérifie que les années sont classées dans l'ordre croissant."""
    resultat = cf.annees_disponibles("part_75_plus")

    assert resultat == [2021, 2022]


def test_derniere_annee(donnees_test):
    """Vérifie que la dernière année disponible est sélectionnée."""
    resultat = cf.derniere_annee("part_75_plus")

    assert resultat == 2022


def test_derniere_annee_autre_indicateur(donnees_test):
    """Vérifie qu'un autre indicateur peut avoir une année différente."""
    resultat = cf.derniere_annee("taux_pauvrete")

    assert resultat == 2023


# ---------------------------------------------------------
# 4. Tests du tableau de comparaison
# ---------------------------------------------------------


def test_tableau_comparaison(donnees_test, monkeypatch):
    """Vérifie le regroupement des indicateurs par EPCI."""
    monkeypatch.setattr(
        config,
        "INDICATEURS",
        {
            "part_75_plus": None,
            "taux_pauvrete": None,
        },
    )

    resultat = cf.tableau_comparaison()

    assert len(resultat) == 3

    assert resultat.columns.tolist() == [
        "libgeo",
        "part_75_plus",
        "taux_pauvrete",
    ]

    assert resultat.loc["200000001", "libgeo"] == "EPCI A"

    assert resultat.loc[
        "200000001", "part_75_plus"
    ] == 15.0

    assert resultat.loc[
        "200000001", "taux_pauvrete"
    ] == 10.0


def test_tableau_comparaison_valeur_manquante(
    donnees_test,
    monkeypatch,
):
    """Vérifie que les valeurs absentes ne deviennent pas zéro."""
    monkeypatch.setattr(
        config,
        "INDICATEURS",
        {
            "part_75_plus": None,
            "taux_pauvrete": None,
        },
    )

    resultat = cf.tableau_comparaison()

    assert pd.isna(
        resultat.loc["200000003", "part_75_plus"]
    )


# ---------------------------------------------------------
# 5. Tests des bornes de l'histogramme
# ---------------------------------------------------------


def test_plage_valeurs():
    """Vérifie les bornes d'un histogramme."""
    tableau = pd.DataFrame(
        {
            2021: [12.0, 18.0],
            2022: [15.0, 23.0],
        }
    )

    resultat = cf.plage_valeurs(tableau, 5.0)

    assert resultat == (10.0, 25.0)


def test_plage_valeurs_negatives():
    """Vérifie le calcul des bornes avec des valeurs négatives."""
    tableau = pd.DataFrame(
        {
            2022: [-12.0, 7.0],
        }
    )

    resultat = cf.plage_valeurs(tableau, 5.0)

    assert resultat == (-15.0, 10.0)


def test_plage_valeurs_plusieurs_annees():
    """Vérifie que toutes les années sont prises en compte."""
    tableau = pd.DataFrame(
        {
            2021: [10.0, 20.0],
            2022: [5.0, 30.0],
            2023: [15.0, 25.0],
        }
    )

    resultat = cf.plage_valeurs(tableau, 10.0)

    assert resultat == (0.0, 30.0)


# ---------------------------------------------------------
# 6. Tests du calcul des tranches
# ---------------------------------------------------------


@pytest.mark.parametrize(
    "valeur, borne_basse, largeur, attendu",
    [
        (5.0, 0.0, 10.0, 0),
        (10.0, 0.0, 10.0, 1),
        (25.0, 0.0, 10.0, 2),
        (39.9, 0.0, 10.0, 3),
        (50.0, 0.0, 10.0, 5),
        (-5.0, 0.0, 10.0, -1),
    ],
)
def test_numero_tranche(
    valeur,
    borne_basse,
    largeur,
    attendu,
):
    """Vérifie le classement d'une valeur dans sa tranche."""
    resultat = cf.numero_tranche(
        valeur,
        borne_basse,
        largeur,
    )

    assert resultat == attendu


def test_numero_tranche_borne_decalee():
    """Vérifie le classement lorsque la première borne n'est pas zéro."""
    resultat = cf.numero_tranche(25.0, 10.0, 5.0)

    assert resultat == 3


# ---------------------------------------------------------
# 7. Tests des valeurs manquantes
# ---------------------------------------------------------


def test_valeurs_ou_vide():
    """Vérifie la transformation d'une série en liste de nombres."""
    valeurs = pd.Series([10, 20, 30])

    resultat = cf.valeurs_ou_vide(valeurs)

    assert resultat == [10.0, 20.0, 30.0]


def test_valeurs_ou_vide_avec_nan():
    """Vérifie que les données manquantes deviennent None."""
    valeurs = pd.Series([10.0, float("nan"), 25.5])

    resultat = cf.valeurs_ou_vide(valeurs)

    assert resultat == [10.0, None, 25.5]


def test_valeurs_ou_vide_serie_vide():
    """Vérifie le traitement d'une série vide."""
    valeurs = pd.Series([], dtype=float)

    resultat = cf.valeurs_ou_vide(valeurs)

    assert resultat == []


# ---------------------------------------------------------
# 8. Tests du formatage des valeurs
# ---------------------------------------------------------


def test_formater_valeur_pourcentage():
    """Vérifie l'affichage français d'un pourcentage."""
    resultat = cf.formater_valeur(12.5, " %")

    assert resultat == "12,5 %"


def test_formater_valeur_decimale():
    """Vérifie l'affichage avec une décimale."""
    resultat = cf.formater_valeur(15.0, " %")

    assert resultat == "15,0 %"


def test_formater_valeur_autre_unite():
    """Vérifie le formatage avec une autre unité."""
    resultat = cf.formater_valeur(3.25, " consultations")

    assert resultat == "3,2 consultations"


# ---------------------------------------------------------
# 9. Tests du formatage des bornes
# ---------------------------------------------------------


def test_formater_borne_entier():
    """Vérifie qu'un entier s'affiche sans décimale."""
    resultat = cf.formater_borne(10.0)

    assert resultat == "10"


def test_formater_borne_decimal():
    """Vérifie l'utilisation de la virgule décimale."""
    resultat = cf.formater_borne(3.25)

    assert resultat == "3,25"


def test_formater_borne_negative():
    """Vérifie le formatage d'une borne négative."""
    resultat = cf.formater_borne(-5.5)

    assert resultat == "-5,5"