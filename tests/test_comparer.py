"""Tests unitaires de la page Comparer du dashboard."""

import pandas as pd
import plotly.graph_objects as go
import pytest
from dash import dcc, html, no_update

import config
from src.pages import comparer

# ---------------------------------------------------------
# 1. Données fictives pour les tests
# ---------------------------------------------------------


@pytest.fixture
def tableau_test():
    """Crée un tableau avec des corrélations connues."""
    return pd.DataFrame(
        {
            "libgeo": ["EPCI A", "EPCI B", "EPCI C", "EPCI D"],
            "part_75_plus": [10, 20, 30, 40],
            "part_75_seuls": [5, 10, 15, 20],
            "taux_pauvrete": [40, 30, 20, 10],
            "apl_medecins": [2, 4, 1, 3],
        }
    )


# ---------------------------------------------------------
# 2. Tests de options_indicateurs()
# ---------------------------------------------------------


def test_options_indicateurs_nombre():
    """Vérifie que tous les indicateurs sont proposés."""
    resultat = comparer.options_indicateurs()

    assert len(resultat) == len(config.INDICATEURS)


def test_options_indicateurs_contenu():
    """Vérifie les noms et codes des indicateurs."""
    resultat = comparer.options_indicateurs()

    attendu = [
        {"label": indicateur.nom, "value": code}
        for code, indicateur in config.INDICATEURS.items()
    ]

    assert resultat == attendu


# ---------------------------------------------------------
# 3. Tests de qualifier_correlation()
# ---------------------------------------------------------


@pytest.mark.parametrize(
    "coefficient, attendu",
    [
        (0.10, "très faible et positive"),
        (0.30, "faible et positive"),
        (0.50, "modérée et positive"),
        (0.80, "forte et positive"),
        (-0.10, "très faible et négative"),
        (-0.30, "faible et négative"),
        (-0.50, "modérée et négative"),
        (-0.80, "forte et négative"),
        (0.0, "très faible et positive"),
        (1.0, "forte et positive"),
        (-1.0, "forte et négative"),
    ],
)
def test_qualifier_correlation(coefficient, attendu):
    """Vérifie la qualification des coefficients."""
    resultat = comparer.qualifier_correlation(coefficient)

    assert resultat == attendu


# ---------------------------------------------------------
# 4. Tests de texte_correlation()
# ---------------------------------------------------------


def test_texte_correlation_memes_indicateurs(tableau_test):
    """Vérifie le message lorsque les indicateurs sont identiques."""
    resultat = comparer.texte_correlation(
        tableau_test,
        "part_75_plus",
        "part_75_plus",
    )

    assert resultat == ("Choisissez deux indicateurs différents pour les comparer.")


def test_texte_correlation_positive(tableau_test):
    """Vérifie l'explication d'une corrélation positive."""
    resultat = comparer.texte_correlation(
        tableau_test,
        "part_75_plus",
        "part_75_seuls",
    )

    assert "forte et positive" in resultat
    assert "(1,00)" in resultat
    assert "4 intercommunalités" in resultat
    assert "augmente" in resultat


def test_texte_correlation_negative(tableau_test):
    """Vérifie l'explication d'une corrélation négative."""
    resultat = comparer.texte_correlation(
        tableau_test,
        "part_75_plus",
        "taux_pauvrete",
    )

    assert "forte et négative" in resultat
    assert "(-1,00)" in resultat
    assert "diminue" in resultat


def test_texte_correlation_valeurs_manquantes(tableau_test):
    """Vérifie que les valeurs manquantes sont exclues du calcul."""
    tableau_test.loc[0, "part_75_seuls"] = float("nan")

    resultat = comparer.texte_correlation(
        tableau_test,
        "part_75_plus",
        "part_75_seuls",
    )

    assert "3 intercommunalités" in resultat
    assert "forte et positive" in resultat


def test_texte_correlation_absence_lien(tableau_test):
    """Vérifie le texte lorsque la corrélation est nulle."""
    tableau_test["part_75_seuls"] = [1, -1, -1, 1]

    resultat = comparer.texte_correlation(
        tableau_test,
        "part_75_plus",
        "part_75_seuls",
    )

    assert "ne sont pratiquement pas liés" in resultat


def test_texte_correlation_avertissement(tableau_test):
    """Vérifie que la corrélation n'est pas présentée comme une causalité."""
    resultat = comparer.texte_correlation(
        tableau_test,
        "part_75_plus",
        "taux_pauvrete",
    )

    assert "ne prouve pas" in resultat


# ---------------------------------------------------------
# 5. Tests de note_annees()
# ---------------------------------------------------------


def test_note_annees(monkeypatch):
    """Vérifie que la note utilise les années disponibles."""
    annees = {
        "part_75_plus": 2022,
        "part_75_seuls": 2021,
        "taux_pauvrete": 2023,
        "apl_medecins": 2024,
    }

    monkeypatch.setattr(
        comparer,
        "derniere_annee",
        lambda code: annees[code],
    )

    resultat = comparer.note_annees()

    assert "2022" in resultat
    assert "2021" in resultat
    assert "2023" in resultat
    assert "2024" in resultat
    assert "Insee" in resultat
    assert "DREES" in resultat


# ---------------------------------------------------------
# 6. Tests de creer_menu()
# ---------------------------------------------------------


def test_creer_menu_type():
    """Vérifie que le menu est un composant Dash."""
    options = [
        {"label": "Option A", "value": "a"},
        {"label": "Option B", "value": "b"},
    ]

    resultat = comparer.creer_menu(
        "INDICATEUR",
        "menu-test",
        options,
        "a",
    )

    assert isinstance(resultat, html.Div)


def test_creer_menu_contenu():
    """Vérifie les paramètres du menu déroulant."""
    options = [
        {"label": "Option A", "value": "a"},
        {"label": "Option B", "value": "b"},
    ]

    resultat = comparer.creer_menu(
        "INDICATEUR",
        "menu-test",
        options,
        "a",
    )

    etiquette, menu = resultat.children

    assert isinstance(etiquette, html.Label)
    assert isinstance(menu, dcc.Dropdown)

    assert etiquette.children == "INDICATEUR"
    assert menu.id == "menu-test"
    assert menu.value == "a"
    assert menu.options == options
    assert menu.clearable is False


# ---------------------------------------------------------
# 7. Tests de creer_reglages()
# ---------------------------------------------------------


def test_creer_reglages_nombre():
    """Vérifie que la page possède trois menus."""
    resultat = comparer.creer_reglages()

    assert isinstance(resultat, html.Div)
    assert len(resultat.children) == 3


def test_creer_reglages_identifiants():
    """Vérifie les identifiants des trois menus."""
    resultat = comparer.creer_reglages()

    identifiants = [bloc.children[1].id for bloc in resultat.children]

    assert identifiants == [
        "axe-x",
        "axe-y",
        "couleur-points",
    ]


def test_creer_reglages_valeurs_defaut():
    """Vérifie les indicateurs sélectionnés au démarrage."""
    resultat = comparer.creer_reglages()

    menus = [bloc.children[1] for bloc in resultat.children]

    assert menus[0].value == config.COMPARAISON_PAR_DEFAUT["x"]
    assert menus[1].value == config.COMPARAISON_PAR_DEFAUT["y"]
    assert menus[2].value == config.COMPARAISON_PAR_DEFAUT["couleur"]


def test_creer_reglages_sans_couleur():
    """Vérifie qu'on peut désactiver la couleur des points."""
    resultat = comparer.creer_reglages()

    menu_couleur = resultat.children[2].children[1]

    valeurs = [option["value"] for option in menu_couleur.options]

    assert config.SANS_COULEUR in valeurs


# ---------------------------------------------------------
# 8. Test de creer_mise_en_page()
# ---------------------------------------------------------


def test_creer_mise_en_page(tableau_test, monkeypatch):
    """Vérifie que la page Comparer est construite."""
    monkeypatch.setattr(
        comparer,
        "tableau_comparaison",
        lambda: tableau_test.copy(),
    )

    monkeypatch.setattr(
        comparer,
        "creer_matrice",
        lambda _tableau: go.Figure(),
    )

    monkeypatch.setattr(
        comparer,
        "note_annees",
        lambda: "Années de test",
    )

    resultat = comparer.creer_mise_en_page()

    assert isinstance(resultat, html.Div)
    assert resultat.className == "page"
    assert len(resultat.children) == 5

    assert isinstance(resultat.children[0], html.Div)
    assert isinstance(resultat.children[1], html.Div)
    assert resultat.children[2].id == "texte-correlation"
    assert resultat.children[4].children == "Années de test"


# ---------------------------------------------------------
# 9. Tests de actualiser_nuage()
# ---------------------------------------------------------


def test_actualiser_nuage_sans_couleur(tableau_test, monkeypatch):
    """Vérifie que l'absence de couleur est transmise au graphique."""
    appels = {}

    monkeypatch.setattr(
        comparer,
        "tableau_comparaison",
        lambda: tableau_test.copy(),
    )

    def faux_nuage(tableau, nom_x, nom_y, nom_couleur):
        """Enregistre les arguments reçus par le graphique."""
        appels["x"] = nom_x
        appels["y"] = nom_y
        appels["couleur"] = nom_couleur
        return go.Figure()

    monkeypatch.setattr(comparer, "creer_nuage", faux_nuage)

    figure, texte = comparer.actualiser_nuage(
        "part_75_plus",
        "taux_pauvrete",
        config.SANS_COULEUR,
    )

    assert isinstance(figure, go.Figure)
    assert appels["x"] == "part_75_plus"
    assert appels["y"] == "taux_pauvrete"
    assert appels["couleur"] is None
    assert "corrélation" in texte.lower()


def test_actualiser_nuage_avec_couleur(tableau_test, monkeypatch):
    """Vérifie la transmission de l'indicateur de couleur."""
    appels = {}

    monkeypatch.setattr(
        comparer,
        "tableau_comparaison",
        lambda: tableau_test.copy(),
    )

    def faux_nuage(tableau, nom_x, nom_y, nom_couleur):
        """Enregistre les paramètres du nuage de points."""
        appels["couleur"] = nom_couleur
        return go.Figure()

    monkeypatch.setattr(comparer, "creer_nuage", faux_nuage)

    figure, texte = comparer.actualiser_nuage(
        "part_75_plus",
        "taux_pauvrete",
        "part_75_seuls",
    )

    assert isinstance(figure, go.Figure)
    assert appels["couleur"] == "part_75_seuls"
    assert isinstance(texte, str)


# ---------------------------------------------------------
# 10. Tests de choisir_depuis_matrice()
# ---------------------------------------------------------


def test_choisir_depuis_matrice_aucun_clic():
    """Vérifie qu'aucun clic ne modifie les menus."""
    resultat = comparer.choisir_depuis_matrice(None)

    assert resultat[0] is no_update
    assert resultat[1] is no_update


def test_choisir_depuis_matrice_clic_vide():
    """Vérifie le traitement d'un événement vide."""
    resultat = comparer.choisir_depuis_matrice({})

    assert resultat[0] is no_update
    assert resultat[1] is no_update


def test_choisir_depuis_matrice_clic_valide():
    """Vérifie la sélection de deux indicateurs différents."""
    clic = {
        "points": [
            {
                "x": config.INDICATEURS["part_75_plus"].nom_court,
                "y": config.INDICATEURS["taux_pauvrete"].nom_court,
            }
        ]
    }

    resultat = comparer.choisir_depuis_matrice(clic)

    assert resultat == (
        "part_75_plus",
        "taux_pauvrete",
    )


def test_choisir_depuis_matrice_diagonale():
    """Vérifie qu'un clic sur la diagonale est ignoré."""
    nom = config.INDICATEURS["part_75_plus"].nom_court

    clic = {
        "points": [
            {
                "x": nom,
                "y": nom,
            }
        ]
    }

    resultat = comparer.choisir_depuis_matrice(clic)

    assert resultat[0] is no_update
    assert resultat[1] is no_update


def test_choisir_depuis_matrice_autre_paire():
    """Vérifie qu'une autre paire est correctement sélectionnée."""
    clic = {
        "points": [
            {
                "x": config.INDICATEURS["apl_medecins"].nom_court,
                "y": config.INDICATEURS["part_75_seuls"].nom_court,
            }
        ]
    }

    resultat = comparer.choisir_depuis_matrice(clic)

    assert resultat == (
        "apl_medecins",
        "part_75_seuls",
    )
