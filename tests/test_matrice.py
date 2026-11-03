"""Tests unitaires du composant matrice de corrélation."""

import pandas as pd
import plotly.graph_objects as go
import pytest

import config
from src.components.matrice import (
    calculer_correlations,
    creer_matrice,
)

# ---------------------------------------------------------
# 1. Données fictives pour les tests
# ---------------------------------------------------------


@pytest.fixture
def tableau_test():
    """Crée des indicateurs avec des corrélations connues."""
    return pd.DataFrame(
        {
            "part_75_plus": [10, 20, 30, 40, 50],
            "part_75_seuls": [5, 10, 15, 20, 25],
            "taux_pauvrete": [50, 40, 30, 20, 10],
            "apl_medecins": [2, 4, 1, 5, 3],
        }
    )


# ---------------------------------------------------------
# 2. Tests de calculer_correlations()
# ---------------------------------------------------------


def test_calculer_correlations_dimensions(tableau_test):
    """Vérifie que la matrice contient les quatre indicateurs."""
    resultat = calculer_correlations(tableau_test)

    assert isinstance(resultat, pd.DataFrame)
    assert resultat.shape == (4, 4)


def test_calculer_correlations_diagonale(tableau_test):
    """Vérifie qu'un indicateur est corrélé avec lui-même."""
    resultat = calculer_correlations(tableau_test)

    for nom in resultat.index:
        assert resultat.loc[nom, nom] == pytest.approx(1.0)


def test_calculer_correlations_positive(tableau_test):
    """Vérifie une corrélation parfaitement positive."""
    resultat = calculer_correlations(tableau_test)

    nom_x = config.INDICATEURS["part_75_plus"].nom_court
    nom_y = config.INDICATEURS["part_75_seuls"].nom_court

    assert resultat.loc[nom_x, nom_y] == pytest.approx(1.0)


def test_calculer_correlations_negative(tableau_test):
    """Vérifie une corrélation parfaitement négative."""
    resultat = calculer_correlations(tableau_test)

    nom_x = config.INDICATEURS["part_75_plus"].nom_court
    nom_y = config.INDICATEURS["taux_pauvrete"].nom_court

    assert resultat.loc[nom_x, nom_y] == pytest.approx(-1.0)


def test_calculer_correlations_symetrie(tableau_test):
    """Vérifie que la matrice est symétrique."""
    resultat = calculer_correlations(tableau_test)

    pd.testing.assert_frame_equal(
        resultat,
        resultat.T,
    )


def test_calculer_correlations_noms_courts(tableau_test):
    """Vérifie que la matrice utilise les noms courts du dashboard."""
    resultat = calculer_correlations(tableau_test)

    noms_attendus = [indicateur.nom_court for indicateur in config.INDICATEURS.values()]

    assert resultat.index.tolist() == noms_attendus
    assert resultat.columns.tolist() == noms_attendus


def test_calculer_correlations_valeurs_manquantes(tableau_test):
    """Vérifie que les valeurs manquantes sont ignorées."""
    tableau_test.loc[2, "part_75_seuls"] = float("nan")

    resultat = calculer_correlations(tableau_test)

    nom_x = config.INDICATEURS["part_75_plus"].nom_court
    nom_y = config.INDICATEURS["part_75_seuls"].nom_court

    assert resultat.loc[nom_x, nom_y] == pytest.approx(1.0)


def test_calculer_correlations_valeur_constante(tableau_test):
    """Vérifie qu'une variable constante donne une corrélation indéfinie."""
    tableau_test["apl_medecins"] = 3.0

    resultat = calculer_correlations(tableau_test)

    nom = config.INDICATEURS["apl_medecins"].nom_court

    assert pd.isna(resultat.loc[nom, nom])


# ---------------------------------------------------------
# 3. Tests de creer_matrice()
# ---------------------------------------------------------


def test_creer_matrice_type(tableau_test):
    """Vérifie que la fonction renvoie une figure Plotly."""
    resultat = creer_matrice(tableau_test)

    assert isinstance(resultat, go.Figure)


def test_creer_matrice_dimensions(tableau_test):
    """Vérifie que le graphique contient une matrice 4 x 4."""
    figure = creer_matrice(tableau_test)

    assert len(figure.data) == 1
    assert figure.data[0].type == "heatmap"
    assert len(figure.data[0].z) == 4
    assert len(figure.data[0].z[0]) == 4


def test_creer_matrice_valeurs(tableau_test):
    """Vérifie que les coefficients sont transmis au graphique."""
    figure = creer_matrice(tableau_test)

    matrice = calculer_correlations(tableau_test)

    for i in range(4):
        for j in range(4):
            assert figure.data[0].z[i][j] == pytest.approx(matrice.iloc[i, j])


def test_creer_matrice_titre(tableau_test):
    """Vérifie que le graphique possède le bon titre."""
    figure = creer_matrice(tableau_test)

    assert figure.layout.title.text == ("Corrélations entre les indicateurs")


def test_creer_matrice_noms_axes(tableau_test):
    """Vérifie les noms courts affichés sur les axes."""
    figure = creer_matrice(tableau_test)

    noms_attendus = [indicateur.nom_court for indicateur in config.INDICATEURS.values()]

    assert list(figure.data[0].x) == noms_attendus
    assert list(figure.data[0].y) == noms_attendus


def test_creer_matrice_infobulle(tableau_test):
    """Vérifie que l'infobulle affiche la corrélation."""
    figure = creer_matrice(tableau_test)

    assert "Corrélation" in figure.data[0].hovertemplate


def test_creer_matrice_hauteur(tableau_test):
    """Vérifie que la hauteur du graphique respecte la configuration."""
    figure = creer_matrice(tableau_test)

    assert figure.layout.height == config.HAUTEUR_GRAPHIQUE
