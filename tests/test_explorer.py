"""Tests unitaires de la page Explorer du dashboard."""

import pandas as pd
import pytest

from dash import Patch, dcc, html, no_update

import config
from src.pages import explorer


# ---------------------------------------------------------
# 1. Données fictives pour les tests
# ---------------------------------------------------------


@pytest.fixture
def donnees_test(monkeypatch):
    """Prépare des données fictives pour quatre EPCI."""

    codes = [
        "200000001",
        "200000002",
        "200000003",
        "200000004",
    ]

    tableau = pd.DataFrame(
        {
            2021: [10.2, 10.8, 12.3, float("nan")],
            2022: [11.1, 11.7, 14.2, float("nan")],
        },
        index=codes,
    )

    noms = pd.Series(
        [
            "EPCI A",
            "EPCI B",
            "EPCI C",
            "EPCI D",
        ],
        index=codes,
    )

    monkeypatch.setattr(
        explorer,
        "valeurs_par_annee",
        lambda _indicateur: tableau.copy(),
    )

    monkeypatch.setattr(
        explorer,
        "annees_disponibles",
        lambda _indicateur: [2021, 2022],
    )

    monkeypatch.setattr(
        explorer,
        "noms_epci",
        lambda: noms.copy(),
    )

    return tableau


# ---------------------------------------------------------
# 2. Tests des titres et des textes
# ---------------------------------------------------------


def test_titre_carte():
    """Vérifie le titre de la carte."""

    indicateur = config.INDICATEURS["part_75_plus"]

    resultat = explorer.titre_carte(indicateur, 2022)

    assert indicateur.nom in resultat
    assert "2022" in resultat
    assert "intercommunalité" in resultat


def test_titre_histogramme():
    """Vérifie le titre de l'histogramme."""

    resultat = explorer.titre_histogramme(2022)

    assert resultat == "Répartition des intercommunalités en 2022"


def test_lecture_carte():
    """Vérifie la présence des explications de la carte."""

    indicateur = config.INDICATEURS["part_75_plus"]

    resultat = explorer.lecture_carte(indicateur)

    assert indicateur.lecture in resultat
    assert "sans donnée" in resultat


# ---------------------------------------------------------
# 3. Tests de annee_retenue()
# ---------------------------------------------------------


def test_annee_retenue_valide(donnees_test):
    """Vérifie qu'une année disponible est conservée."""

    resultat = explorer.annee_retenue("part_75_plus", 2021)

    assert resultat == 2021


def test_annee_retenue_invalide(donnees_test):
    """Vérifie que la dernière année est utilisée par défaut."""

    resultat = explorer.annee_retenue("part_75_plus", 2010)

    assert resultat == 2022


def test_annee_retenue_aucune(donnees_test):
    """Vérifie le comportement si aucune année n'est sélectionnée."""

    resultat = explorer.annee_retenue("part_75_plus", None)

    assert resultat == 2022


# ---------------------------------------------------------
# 4. Tests de valeurs_affichees()
# ---------------------------------------------------------


def test_valeurs_affichees_2021(donnees_test):
    """Vérifie la récupération des valeurs de 2021."""

    resultat = explorer.valeurs_affichees("part_75_plus", 2021)

    assert isinstance(resultat, pd.Series)

    assert resultat.loc["200000001"] == 10.2
    assert resultat.loc["200000002"] == 10.8
    assert resultat.loc["200000003"] == 12.3


def test_valeurs_affichees_2022(donnees_test):
    """Vérifie la récupération des valeurs de 2022."""

    resultat = explorer.valeurs_affichees("part_75_plus", 2022)

    assert resultat.loc["200000001"] == 11.1
    assert resultat.loc["200000002"] == 11.7
    assert resultat.loc["200000003"] == 14.2


def test_valeurs_affichees_manquantes(donnees_test):
    """Vérifie que les valeurs manquantes restent manquantes."""

    resultat = explorer.valeurs_affichees("part_75_plus", 2022)

    assert pd.isna(resultat.loc["200000004"])


# ---------------------------------------------------------
# 5. Tests de selectionner_tranche()
# ---------------------------------------------------------


def test_selectionner_tranche_meme_classe(donnees_test):
    """Vérifie la sélection des EPCI appartenant à la même tranche."""

    positions, description = explorer.selectionner_tranche(
        "part_75_plus",
        2021,
        0,
    )

    assert positions == [0, 1]
    assert "2 intercommunalités" in description


def test_selectionner_tranche_autre_classe(donnees_test):
    """Vérifie la sélection d'une tranche contenant un seul EPCI."""

    positions, description = explorer.selectionner_tranche(
        "part_75_plus",
        2021,
        2,
    )

    assert positions == [2]
    assert "1 intercommunalités" in description


def test_selectionner_tranche_autre_annee(donnees_test):
    """Vérifie que les tranches dépendent de l'année."""

    positions, description = explorer.selectionner_tranche(
        "part_75_plus",
        2022,
        0,
    )

    assert positions == [0, 1]
    assert "2 intercommunalités" in description


# ---------------------------------------------------------
# 6. Tests de interpreter_clic()
# ---------------------------------------------------------


def test_interpreter_clic_aucun(donnees_test):
    """Vérifie qu'une absence de clic ne sélectionne rien."""

    resultat = explorer.interpreter_clic(
        None,
        None,
        "part_75_plus",
        2021,
    )

    assert resultat is None


def test_interpreter_clic_histogramme(donnees_test):
    """Vérifie la sélection après un clic sur l'histogramme."""

    clic = {
        "points": [
            {
                "pointNumbers": [0, 1],
            }
        ]
    }

    resultat = explorer.interpreter_clic(
        clic,
        None,
        "part_75_plus",
        2021,
    )

    assert resultat is not None

    positions, texte = resultat

    assert positions == [0, 1]
    assert "Sélection" in texte
    assert "2 intercommunalités" in texte


def test_interpreter_clic_carte(donnees_test):
    """Vérifie la sélection après un clic sur un EPCI."""

    clic = {
        "points": [
            {
                "location": "200000001",
            }
        ]
    }

    resultat = explorer.interpreter_clic(
        None,
        clic,
        "part_75_plus",
        2021,
    )

    assert resultat is not None

    positions, texte = resultat

    assert positions == [0, 1]
    assert "EPCI A" in texte
    assert "10,2" in texte


def test_interpreter_clic_carte_sans_donnee(donnees_test):
    """Vérifie qu'un EPCI sans donnée ne peut pas être sélectionné."""

    clic = {
        "points": [
            {
                "location": "200000004",
            }
        ]
    }

    resultat = explorer.interpreter_clic(
        None,
        clic,
        "part_75_plus",
        2021,
    )

    assert resultat is None


# ---------------------------------------------------------
# 7. Tests de patch_selection()
# ---------------------------------------------------------


def test_patch_selection_type():
    """Vérifie que la fonction crée une mise à jour Dash."""

    resultat = explorer.patch_selection([0, 1])

    assert isinstance(resultat, Patch)


def test_patch_selection_aucune():
    """Vérifie qu'une sélection peut être annulée."""

    resultat = explorer.patch_selection(None)

    assert isinstance(resultat, Patch)


# ---------------------------------------------------------
# 8. Tests du curseur des années
# ---------------------------------------------------------


def test_regler_curseur_plusieurs_annees(donnees_test):
    """Vérifie la configuration d'un curseur avec deux années."""

    resultat = explorer.regler_curseur("part_75_plus")

    minimum, maximum, marques, valeur, style = resultat

    assert minimum == 2021
    assert maximum == 2022

    assert marques == {
        2021: "2021",
        2022: "2022",
    }

    assert valeur == 2022
    assert style == {}


def test_regler_curseur_annee_unique(monkeypatch):
    """Vérifie que le curseur est masqué si une seule année existe."""

    monkeypatch.setattr(
        explorer,
        "annees_disponibles",
        lambda _indicateur: [2022],
    )

    resultat = explorer.regler_curseur("part_75_plus")

    assert resultat[0] is no_update
    assert resultat[1] is no_update
    assert resultat[2] is no_update
    assert resultat[3] is no_update

    assert resultat[4] == {"display": "none"}


# ---------------------------------------------------------
# 9. Tests de basculer_lecture()
# ---------------------------------------------------------


def test_basculer_lecture_demarrer():
    """Vérifie le démarrage de l'animation."""

    annees = [2020, 2021, 2022]

    annee, pause = explorer.basculer_lecture(
        True,
        2020,
        annees,
    )

    assert annee is no_update
    assert pause is False


def test_basculer_lecture_pause():
    """Vérifie la mise en pause de l'animation."""

    annees = [2020, 2021, 2022]

    annee, pause = explorer.basculer_lecture(
        False,
        2021,
        annees,
    )

    assert annee is no_update
    assert pause is True


def test_basculer_lecture_recommencer():
    """Vérifie que l'animation recommence après la dernière année."""

    annees = [2020, 2021, 2022]

    annee, pause = explorer.basculer_lecture(
        True,
        2022,
        annees,
    )

    assert annee == 2020
    assert pause is False


# ---------------------------------------------------------
# 10. Tests de avancer_annee()
# ---------------------------------------------------------


def test_avancer_annee():
    """Vérifie le passage à l'année suivante."""

    annees = [2020, 2021, 2022]

    annee, pause = explorer.avancer_annee(
        2020,
        annees,
    )

    assert annee == 2021
    assert pause is False


def test_avancer_annee_derniere():
    """Vérifie la mise en pause à la dernière année."""

    annees = [2020, 2021, 2022]

    annee, pause = explorer.avancer_annee(
        2021,
        annees,
    )

    assert annee == 2022
    assert pause is True


def test_avancer_annee_invalide():
    """Vérifie le retour à la première année si l'année est invalide."""

    annees = [2020, 2021, 2022]

    annee, pause = explorer.avancer_annee(
        None,
        annees,
    )

    assert annee == 2020
    assert pause is False


# ---------------------------------------------------------
# 11. Tests de piloter_animation()
# ---------------------------------------------------------


def test_piloter_animation_changement_indicateur():
    """Vérifie l'arrêt de l'animation lors d'un changement d'indicateur."""

    resultat = explorer.piloter_animation(
        "choix-indicateur",
        False,
        2021,
        [2020, 2021, 2022],
    )

    assert resultat[0] is no_update
    assert resultat[1] is True


def test_piloter_animation_annee_unique():
    """Vérifie qu'une animation ne démarre pas avec une seule année."""

    resultat = explorer.piloter_animation(
        "bouton-lecture",
        True,
        2022,
        [2022],
    )

    assert resultat[0] is no_update
    assert resultat[1] is True


def test_piloter_animation_bouton_lecture():
    """Vérifie le lancement de l'animation."""

    resultat = explorer.piloter_animation(
        "bouton-lecture",
        True,
        2020,
        [2020, 2021, 2022],
    )

    assert resultat[0] is no_update
    assert resultat[1] is False


def test_piloter_animation_bouton_pause():
    """Vérifie l'arrêt de l'animation avec le bouton."""

    resultat = explorer.piloter_animation(
        "bouton-lecture",
        False,
        2021,
        [2020, 2021, 2022],
    )

    assert resultat[0] is no_update
    assert resultat[1] is True


def test_piloter_animation_minuteur():
    """Vérifie l'avancement automatique du curseur."""

    resultat = explorer.piloter_animation(
        "minuteur-annees",
        False,
        2020,
        [2020, 2021, 2022],
    )

    assert resultat == (2021, False)


def test_piloter_animation_fin():
    """Vérifie l'arrêt automatique à la dernière année."""

    resultat = explorer.piloter_animation(
        "minuteur-annees",
        False,
        2021,
        [2020, 2021, 2022],
    )

    assert resultat == (2022, True)


def test_piloter_animation_deja_en_pause():
    """Vérifie que le minuteur ne change rien pendant la pause."""

    resultat = explorer.piloter_animation(
        "minuteur-annees",
        True,
        2021,
        [2020, 2021, 2022],
    )

    assert resultat[0] is no_update
    assert resultat[1] is True


# ---------------------------------------------------------
# 12. Tests de creer_reglages()
# ---------------------------------------------------------


def test_creer_reglages_type(donnees_test):
    """Vérifie la création du bloc de réglages."""

    resultat = explorer.creer_reglages()

    assert isinstance(resultat, html.Div)

    assert len(resultat.children) == 2


def test_creer_reglages_indicateur_defaut(donnees_test):
    """Vérifie que le bon indicateur est sélectionné au démarrage."""

    resultat = explorer.creer_reglages()

    bloc_indicateur = resultat.children[0]

    menu = bloc_indicateur.children[1]

    assert isinstance(menu, dcc.Dropdown)

    assert menu.id == "choix-indicateur"

    assert menu.value == config.INDICATEUR_PAR_DEFAUT


def test_creer_reglages_curseur(donnees_test):
    """Vérifie les paramètres du curseur."""

    resultat = explorer.creer_reglages()

    bloc_annees = resultat.children[1]

    zone_curseur = bloc_annees.children[1]

    curseur = zone_curseur.children[1].children

    assert isinstance(curseur, dcc.Slider)

    assert curseur.min == 2021
    assert curseur.max == 2022

    assert curseur.value == 2022


def test_creer_reglages_minuteur(donnees_test):
    """Vérifie que le minuteur est désactivé au démarrage."""

    resultat = explorer.creer_reglages()

    bloc_annees = resultat.children[1]

    zone_curseur = bloc_annees.children[1]

    minuteur = zone_curseur.children[2]

    assert isinstance(minuteur, dcc.Interval)

    assert minuteur.disabled is True

    assert minuteur.interval == config.INTERVALLE_ANIMATION_MS


# ---------------------------------------------------------
# 13. Test de creer_mise_en_page()
# ---------------------------------------------------------


def test_creer_mise_en_page(donnees_test, monkeypatch):
    """Vérifie la création de la page Explorer."""

    monkeypatch.setattr(
        explorer,
        "creer_graphiques",
        lambda: html.Div(id="graphiques-test"),
    )

    resultat = explorer.creer_mise_en_page()

    assert isinstance(resultat, html.Div)

    assert resultat.id == "page-explorer"

    assert resultat.n_clicks == 0

    assert len(resultat.children) == 1

    contenu = resultat.children[0]

    assert contenu.className == "page"

    assert len(contenu.children) == 5


# ---------------------------------------------------------
# 14. Test de actualiser_graphiques()
# ---------------------------------------------------------


def test_actualiser_graphiques(donnees_test, monkeypatch):
    """Vérifie l'actualisation de la carte et de l'histogramme."""

    import plotly.graph_objects as go

    appels = {}

    def faux_histogramme(valeurs, indicateur, plage, titre):
        """Enregistre les paramètres reçus par l'histogramme."""

        appels["valeurs"] = valeurs
        appels["titre"] = titre

        return go.Figure()

    monkeypatch.setattr(
        explorer,
        "creer_histogramme",
        faux_histogramme,
    )

    resultat = explorer.actualiser_graphiques(
        "part_75_plus",
        2021,
    )

    carte, histogramme, mention, texte, lecture = resultat

    assert isinstance(carte, Patch)

    assert isinstance(histogramme, go.Figure)

    assert mention == "ANNÉE : 2021"

    assert texte == explorer.TEXTE_AIDE

    assert "Lecture" in lecture

    assert appels["titre"] == (
        "Répartition des intercommunalités en 2021"
    )

    assert appels["valeurs"].loc["200000001"] == 10.2