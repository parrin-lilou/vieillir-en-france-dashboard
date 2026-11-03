"""Page « Comparer » : relations entre deux indicateurs, et corrélations entre tous.

Un clic sur une case de la matrice des corrélations affiche la paire
d'indicateurs correspondante dans le nuage de points.
"""

from typing import Any

import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html, no_update

import config
from src.components.matrice import creer_matrice
from src.components.nuage import creer_nuage
from src.utils.common_functions import (
    derniere_annee,
    tableau_comparaison,
)

# Seuils usuels pour qualifier l'intensité d'une corrélation (valeur absolue).
SEUILS_INTENSITE = [
    (0.2, "très faible"),
    (0.4, "faible"),
    (0.6, "modérée"),
    (1.01, "forte"),
]

LECTURE_NUAGE = (
    "Lecture : chaque point est une intercommunalité. Survolez un point pour voir son nom "
    "et ses valeurs. Un nuage qui monte vers la droite indique que les deux indicateurs "
    "évoluent dans le même sens."
)
LECTURE_MATRICE = (
    "Lecture : chaque case donne la corrélation entre deux indicateurs, de -1 (sens "
    "opposés) à +1 (même sens), 0 signifiant l'absence de lien. Cliquez sur une case pour "
    "afficher cette paire dans le nuage de points."
)

# Correspondance nom court -> code de l'indicateur, pour interpréter un clic sur la matrice.
CODE_PAR_NOM_COURT = {
    indicateur.nom_court: nom for nom, indicateur in config.INDICATEURS.items()
}


def options_indicateurs() -> list[dict[str, str]]:
    """Renvoie les options d'un menu déroulant listant les quatre indicateurs."""
    return [
        {"label": indicateur.nom, "value": nom}
        for nom, indicateur in config.INDICATEURS.items()
    ]


def qualifier_correlation(coefficient: float) -> str:
    """Traduit un coefficient de corrélation en mots (« modérée et positive », etc.)."""
    intensite = next(mot for seuil, mot in SEUILS_INTENSITE if abs(coefficient) < seuil)
    sens = "positive" if coefficient >= 0 else "négative"
    return f"{intensite} et {sens}"


def texte_correlation(tableau: pd.DataFrame, nom_x: str, nom_y: str) -> str:
    """Rédige la phrase qui décrit la corrélation entre les deux indicateurs affichés."""
    if nom_x == nom_y:
        return "Choisissez deux indicateurs différents pour les comparer."
    paires = tableau[[nom_x, nom_y]].dropna()
    coefficient = float(paires[nom_x].corr(paires[nom_y]))
    coefficient_texte = f"{coefficient:.2f}".replace(".", ",")
    debut = (
        f"Corrélation {qualifier_correlation(coefficient)} ({coefficient_texte}) sur "
        f"{len(paires)} intercommunalités : "
    )
    x_en_phrase = config.INDICATEURS[nom_x].nom_en_phrase
    y_en_phrase = config.INDICATEURS[nom_y].nom_en_phrase
    # Sous le premier seuil, décrire une tendance serait trompeur : on parle d'absence de lien.
    if abs(coefficient) < SEUILS_INTENSITE[0][0]:
        return debut + "les deux indicateurs ne sont pratiquement pas liés."
    sens = "augmente" if coefficient >= 0 else "diminue"
    return (
        debut + f"en moyenne, {y_en_phrase} {sens} quand {x_en_phrase} augmente. "
        "Une corrélation ne prouve pas qu'un indicateur explique l'autre."
    )


def note_annees() -> str:
    """Indique l'année retenue pour chaque indicateur, puisqu'elles diffèrent."""
    annees = ", ".join(
        f"{indicateur.nom_court.lower()} : {derniere_annee(nom)}"
        for nom, indicateur in config.INDICATEURS.items()
    )
    return (
        f"Chaque indicateur est pris à sa dernière année disponible ({annees}). Sources : "
        "Insee (recensements de la population, Filosofi) et DREES, via l'Observatoire des "
        "territoires."
    )


def creer_menu(
    etiquette: str, identifiant: str, options: list[dict[str, str]], valeur: str
) -> html.Div:
    """Construit un menu déroulant précédé de son étiquette."""
    return html.Div(
        [
            html.Label(etiquette, htmlFor=identifiant, className="etiquette"),
            dcc.Dropdown(
                id=identifiant,
                options=options,
                value=valeur,
                clearable=False,
                searchable=False,
            ),
        ],
        className="reglage-comparer",
    )


def creer_reglages() -> html.Div:
    """Construit les trois menus : abscisse, ordonnée et couleur des points."""
    choix = config.COMPARAISON_PAR_DEFAUT
    options_couleur = [
        {"label": "Aucune", "value": config.SANS_COULEUR},
        *options_indicateurs(),
    ]
    return html.Div(
        [
            creer_menu("AXE HORIZONTAL", "axe-x", options_indicateurs(), choix["x"]),
            creer_menu("AXE VERTICAL", "axe-y", options_indicateurs(), choix["y"]),
            creer_menu(
                "COULEUR DES POINTS",
                "couleur-points",
                options_couleur,
                choix["couleur"],
            ),
        ],
        className="bloc reglages",
    )


def creer_mise_en_page() -> html.Div:
    """Construit la page : présentation, réglages, corrélation, graphiques et sources."""
    tableau = tableau_comparaison()
    return html.Div(
        [
            html.Div(
                [
                    html.H1("Comparer les indicateurs"),
                    html.P(
                        "Les territoires où vivent beaucoup de personnes âgées sont-ils aussi "
                        "les plus pauvres, les plus isolés ou les moins bien dotés en "
                        "médecins ? Choisissez deux indicateurs pour les confronter."
                    ),
                ],
                className="entete",
            ),
            creer_reglages(),
            html.P(id="texte-correlation", className="aide"),
            html.Div(
                [
                    html.Div(
                        [
                            dcc.Graph(
                                id="nuage",
                                config={
                                    "displaylogo": False,
                                    "showSendToCloud": False,
                                    "modeBarButtonsToRemove": ["select2d", "lasso2d"],
                                },
                            ),
                            html.P(LECTURE_NUAGE, className="note"),
                        ],
                        className="bloc",
                    ),
                    html.Div(
                        [
                            dcc.Graph(
                                id="matrice",
                                figure=creer_matrice(tableau),
                                config={
                                    "displaylogo": False,
                                    "showSendToCloud": False,
                                    "modeBarButtons": [["toImage"]],
                                },
                            ),
                            html.P(LECTURE_MATRICE, className="note"),
                        ],
                        className="bloc",
                    ),
                ],
                className="graphiques",
            ),
            html.P(note_annees(), className="pied"),
        ],
        className="page",
    )


@callback(
    Output("nuage", "figure"),
    Output("texte-correlation", "children"),
    Input("axe-x", "value"),
    Input("axe-y", "value"),
    Input("couleur-points", "value"),
)
def actualiser_nuage(nom_x: str, nom_y: str, nom_couleur: str) -> tuple[go.Figure, str]:
    """Redessine le nuage de points et la phrase de corrélation quand un menu change."""
    tableau = tableau_comparaison()
    couleur = None if nom_couleur == config.SANS_COULEUR else nom_couleur
    return creer_nuage(tableau, nom_x, nom_y, couleur), texte_correlation(
        tableau, nom_x, nom_y
    )


@callback(
    Output("axe-x", "value"),
    Output("axe-y", "value"),
    Input("matrice", "clickData"),
    prevent_initial_call=True,
)
def choisir_depuis_matrice(clic: dict[str, Any] | None) -> tuple[Any, Any]:
    """Reporte dans les menus la paire d'indicateurs de la case cliquée.

    Les cases de la diagonale (un indicateur avec lui-même) sont ignorées.
    """
    if not clic:
        return no_update, no_update
    point = clic["points"][0]
    nom_x = CODE_PAR_NOM_COURT[point["x"]]
    nom_y = CODE_PAR_NOM_COURT[point["y"]]
    if nom_x == nom_y:
        return no_update, no_update
    return nom_x, nom_y
