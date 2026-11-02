"""Tests unitaires de la validation des données avec Pydantic."""

import pandas as pd
import pytest
from pydantic import ValidationError

from src.utils.validation import (
    LigneNettoyee,
    decrire_erreur,
    valider_table,
)

# 1. Données de test


def creer_ligne_valide():
    """Crée une ligne correcte pour les tests."""
    return {
        "codgeo": "200000001",
        "libgeo": "EPCI de test",
        "indicateur": "part_75_plus",
        "annee": 2022,
        "valeur": 25.5,
    }


# 2. Tests de LigneNettoyee


def test_ligne_valide():
    """Vérifie qu'une ligne correcte est acceptée."""
    donnees = creer_ligne_valide()

    resultat = LigneNettoyee(**donnees)

    assert resultat.codgeo == "200000001"
    assert resultat.libgeo == "EPCI de test"
    assert resultat.indicateur == "part_75_plus"
    assert resultat.annee == 2022
    assert resultat.valeur == pytest.approx(25.5)


def test_code_epci_trop_court():
    """Vérifie qu'un code EPCI trop court est refusé."""
    donnees = creer_ligne_valide()
    donnees["codgeo"] = "12345"

    with pytest.raises(ValidationError):
        LigneNettoyee(**donnees)


def test_code_epci_avec_lettres():
    """Vérifie qu'un code EPCI doit contenir uniquement des chiffres."""
    donnees = creer_ligne_valide()
    donnees["codgeo"] = "20000ABCD"

    with pytest.raises(ValidationError):
        LigneNettoyee(**donnees)


def test_nom_epci_vide():
    """Vérifie qu'un EPCI doit posséder un nom."""
    donnees = creer_ligne_valide()
    donnees["libgeo"] = ""

    with pytest.raises(ValidationError):
        LigneNettoyee(**donnees)


def test_indicateur_inconnu():
    """Vérifie qu'un indicateur inconnu est refusé."""
    donnees = creer_ligne_valide()
    donnees["indicateur"] = "indicateur_inexistant"

    with pytest.raises(ValidationError):
        LigneNettoyee(**donnees)


@pytest.mark.parametrize(
    "annee_invalide",
    [1900, 1967, 2101, 2200],
)
def test_annee_invalide(annee_invalide):
    """Vérifie le refus des années hors des bornes autorisées."""
    donnees = creer_ligne_valide()
    donnees["annee"] = annee_invalide

    with pytest.raises(ValidationError):
        LigneNettoyee(**donnees)


@pytest.mark.parametrize(
    "annee_valide",
    [1968, 2022, 2100],
)
def test_annee_valide(annee_valide):
    """Vérifie que les années autorisées sont acceptées."""
    donnees = creer_ligne_valide()
    donnees["annee"] = annee_valide

    resultat = LigneNettoyee(**donnees)

    assert resultat.annee == annee_valide


def test_valeur_negative():
    """Vérifie qu'une valeur négative est refusée."""
    donnees = creer_ligne_valide()
    donnees["valeur"] = -10

    with pytest.raises(ValidationError):
        LigneNettoyee(**donnees)


def test_valeur_nulle():
    """Vérifie que la valeur zéro est autorisée."""
    donnees = creer_ligne_valide()
    donnees["valeur"] = 0

    resultat = LigneNettoyee(**donnees)

    assert resultat.valeur == 0


def test_pourcentage_superieur_a_100():
    """Vérifie qu'un pourcentage supérieur à 100 est refusé."""
    donnees = creer_ligne_valide()
    donnees["valeur"] = 120

    with pytest.raises(
        ValidationError,
        match="pourcentage supérieur à 100",
    ):
        LigneNettoyee(**donnees)


def test_pourcentage_egal_a_100():
    """Vérifie que 100 % est une valeur autorisée."""
    donnees = creer_ligne_valide()
    donnees["valeur"] = 100

    resultat = LigneNettoyee(**donnees)

    assert resultat.valeur == 100


def test_indicateur_non_pourcentage():
    """Vérifie qu'un nombre de consultations peut dépasser 100."""
    donnees = creer_ligne_valide()
    donnees["indicateur"] = "apl_medecins"
    donnees["valeur"] = 150

    resultat = LigneNettoyee(**donnees)

    assert resultat.valeur == 150


# 3. Tests de decrire_erreur()


def test_decrire_erreur():
    """Vérifie la création d'un message d'erreur."""
    erreur = {
        "loc": (2, "annee"),
        "msg": "année invalide",
    }

    resultat = decrire_erreur(erreur)

    assert "ligne 2" in resultat
    assert "annee" in resultat
    assert "année invalide" in resultat


def test_decrire_erreur_sans_champ():
    """Vérifie le message d'une erreur sans champ précis."""
    erreur = {
        "loc": (3,),
        "msg": "donnée incorrecte",
    }

    resultat = decrire_erreur(erreur)

    assert resultat == "ligne 3 : donnée incorrecte"


# 4. Tests de valider_table


def test_valider_table_correcte():
    """Vérifie qu'une table contenant des lignes valides est acceptée."""
    ligne1 = creer_ligne_valide()

    ligne2 = creer_ligne_valide()
    ligne2["codgeo"] = "200000002"
    ligne2["libgeo"] = "Deuxième EPCI"
    ligne2["valeur"] = 30

    table = pd.DataFrame([ligne1, ligne2])

    resultat = valider_table(table)

    assert resultat is None


def test_valider_table_incorrecte():
    """Vérifie qu'une table contenant une valeur invalide est refusée."""
    ligne1 = creer_ligne_valide()

    ligne2 = creer_ligne_valide()
    ligne2["codgeo"] = "123"
    ligne2["valeur"] = -5

    table = pd.DataFrame([ligne1, ligne2])

    with pytest.raises(ValueError) as erreur:
        valider_table(table)

    message = str(erreur.value)

    assert "erreur(s) dans les données nettoyées" in message
    assert "ligne 1" in message


def test_valider_table_colonne_manquante():
    """Vérifie le refus d'une table sans colonne obligatoire."""
    table = pd.DataFrame(
        {
            "codgeo": ["200000001"],
            "libgeo": ["EPCI de test"],
            "annee": [2022],
            "valeur": [25],
        }
    )

    with pytest.raises(ValueError):
        valider_table(table)


def test_valider_table_plusieurs_erreurs():
    """Vérifie que le nombre d'erreurs est indiqué."""
    ligne1 = creer_ligne_valide()
    ligne1["codgeo"] = "123"

    ligne2 = creer_ligne_valide()
    ligne2["valeur"] = -20

    table = pd.DataFrame([ligne1, ligne2])

    with pytest.raises(ValueError) as erreur:
        valider_table(table)

    message = str(erreur.value)

    assert "2 erreur(s)" in message
    assert "ligne 0" in message
    assert "ligne 1" in message


def test_valider_table_vide():
    """Vérifie qu'une table vide est acceptée par le validateur."""
    table = pd.DataFrame(
        columns=[
            "codgeo",
            "libgeo",
            "indicateur",
            "annee",
            "valeur",
        ]
    )

    resultat = valider_table(table)

    assert resultat is None
