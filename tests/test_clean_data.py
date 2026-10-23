"""Tests unitaires des fonctions de nettoyage des données."""

import pandas as pd
import pytest

from src.utils.clean_data import (
    calculer_part_seuls,
    construire_table_nettoyee,
    est_en_metropole,
    extraire_indicateur,
    premier_point,
)


# 1. Tests de premier_point()

def test_premier_point_polygone():
    """Vérifie l'extraction du premier point d'un polygone."""
    coordonnees = [
        [
            [2.35, 48.85],
            [2.36, 48.86],
        ]
    ]

    resultat = premier_point(coordonnees)

    assert resultat == (2.35, 48.85)


def test_premier_point_multipolygone():
    """Vérifie l'extraction du premier point d'un multipolygone."""
    coordonnees = [
        [
            [
                [1.50, 47.20],
                [1.60, 47.30],
            ]
        ]
    ]

    resultat = premier_point(coordonnees)

    assert resultat == (1.50, 47.20)


# 2. Tests de est_en_metropole()

def test_est_en_metropole_vrai():
    """Vérifie qu'un territoire métropolitain est accepté."""
    contour = {
        "geometry": {
            "coordinates": [[[2.35, 48.85]]]
        }
    }

    assert est_en_metropole(contour) is True


def test_est_en_metropole_faux():
    """Vérifie qu'un territoire hors métropole est exclu."""
    contour = {
        "geometry": {
            "coordinates": [[[55.5, -21.1]]]
        }
    }

    assert est_en_metropole(contour) is False


# 3. Tests de extraire_indicateur()

def test_extraire_indicateur():
    """Vérifie la sélection et la conversion des données."""
    donnees = pd.DataFrame(
        {
            "codgeo": ["A", "B", "C"],
            "libgeo": ["EPCI A", "EPCI B", "EPCI C"],
            "indicateur": [
                "part_pop75p",
                "part_pop75p",
                "tx_pauv_60",
            ],
            "sexe": [None, None, None],
            "an": ["2022", "2023", "2022"],
            "valeur": ["12.5", "15.0", "20.0"],
        }
    )

    resultat = extraire_indicateur(donnees, "part_pop75p")

    assert len(resultat) == 2
    assert resultat["valeur"].tolist() == [12.5, 15.0]
    assert resultat["annee"].tolist() == [2022, 2023]


def test_extraire_indicateur_valeur_invalide():
    """Vérifie qu'une valeur non numérique devient manquante."""
    donnees = pd.DataFrame(
        {
            "codgeo": ["A"],
            "libgeo": ["EPCI A"],
            "indicateur": ["part_pop75p"],
            "sexe": [None],
            "an": ["2022"],
            "valeur": ["inconnu"],
        }
    )

    resultat = extraire_indicateur(donnees, "part_pop75p")

    assert pd.isna(resultat["valeur"].iloc[0])


def test_extraire_indicateur_sexe():
    """Vérifie que seule la modalité ensemble est conservée."""
    donnees = pd.DataFrame(
        {
            "codgeo": ["A", "A"],
            "libgeo": ["EPCI A", "EPCI A"],
            "indicateur": ["part_pop75p", "part_pop75p"],
            "sexe": ["F", "T"],
            "an": ["2022", "2022"],
            "valeur": ["14", "12"],
        }
    )

    resultat = extraire_indicateur(donnees, "part_pop75p")

    assert len(resultat) == 1
    assert resultat["valeur"].iloc[0] == 12


# 4. Tests de calculer_part_seuls()

def test_calculer_part_seuls():
    """Vérifie le calcul de la part des personnes âgées seules."""
    donnees = pd.DataFrame(
        {
            "codgeo": ["A", "A"],
            "libgeo": ["EPCI A", "EPCI A"],
            "indicateur": ["nb_persseul75", "pop75p"],
            "sexe": [None, None],
            "an": ["2022", "2022"],
            "valeur": ["25", "100"],
        }
    )

    resultat = calculer_part_seuls(donnees)

    assert len(resultat) == 1
    assert resultat["valeur"].iloc[0] == pytest.approx(25.0)


def test_calculer_part_seuls_zero():
    """Vérifie le traitement d'un effectif nul."""
    donnees = pd.DataFrame(
        {
            "codgeo": ["A", "A"],
            "libgeo": ["EPCI A", "EPCI A"],
            "indicateur": ["nb_persseul75", "pop75p"],
            "sexe": [None, None],
            "an": ["2022", "2022"],
            "valeur": ["0", "100"],
        }
    )

    resultat = calculer_part_seuls(donnees)

    assert pd.isna(resultat["valeur"].iloc[0])


def test_calculer_part_seuls_annees_differentes():
    """Vérifie que seules les années communes sont associées."""
    donnees = pd.DataFrame(
        {
            "codgeo": ["A", "A"],
            "libgeo": ["EPCI A", "EPCI A"],
            "indicateur": ["nb_persseul75", "pop75p"],
            "sexe": [None, None],
            "an": ["2022", "2023"],
            "valeur": ["25", "100"],
        }
    )

    resultat = calculer_part_seuls(donnees)

    assert resultat.empty


# 5. Tests de construire_table_nettoyee()


def test_construire_table_nettoyee():
    """Vérifie la construction de la table finale."""
    donnees = pd.DataFrame(
        {
            "codgeo": ["A", "A", "A", "A", "A", "B"],
            "libgeo": [
                "EPCI A",
                "EPCI A",
                "EPCI A",
                "EPCI A",
                "EPCI A",
                "EPCI B",
            ],
            "indicateur": [
                "part_pop75p",
                "nb_persseul75",
                "pop75p",
                "tx_pauv_60",
                "apl_mg_hmep",
                "part_pop75p",
            ],
            "sexe": [None, None, None, None, None, None],
            "an": ["2022"] * 6,
            "valeur": ["12", "10", "100", "20", "3.5", "15"],
        }
    )

    codes_metropole = {"A"}

    resultat = construire_table_nettoyee(
        donnees,
        codes_metropole,
    )

    assert len(resultat) == 4

    assert list(resultat.columns) == [
        "codgeo",
        "libgeo",
        "indicateur",
        "annee",
        "valeur",
    ]

    assert set(resultat["codgeo"]) == {"A"}

    assert set(resultat["indicateur"]) == {
        "part_75_plus",
        "part_75_seuls",
        "taux_pauvrete",
        "apl_medecins",
    }

    assert resultat["annee"].iloc[0] == 2022


def test_construire_table_nettoyee_sans_donnees():
    """Vérifie qu'un territoire absent du périmètre est exclu."""
    donnees = pd.DataFrame(
        {
            "codgeo": ["B"],
            "libgeo": ["EPCI B"],
            "indicateur": ["part_pop75p"],
            "sexe": [None],
            "an": ["2022"],
            "valeur": ["15"],
        }
    )

    codes_metropole = {"A"}

    resultat = construire_table_nettoyee(
        donnees,
        codes_metropole,
    )

    assert resultat.empty