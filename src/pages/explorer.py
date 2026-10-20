"""Page « Explorer » : carte et histogramme d'un indicateur, pour une année au choix.

Les deux graphiques sont liés : un clic sur une barre de l'histogramme ou sur un
EPCI de la carte met en évidence, dans les deux, les EPCI de la même tranche.
"""

from typing import Any

import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, Patch, State, callback, ctx, dcc, html, no_update

import config
from src.components.carte import creer_carte, texte_survol
from src.components.histogramme import creer_histogramme
from src.utils.common_functions import (
    annees_disponibles,
    formater_borne,
    formater_valeur,
    noms_epci,
    numero_tranche,
    plage_valeurs,
    valeurs_ou_vide,
    valeurs_par_annee,
)

TEXTE_AIDE = (
    "Astuce : cliquez sur une barre de l'histogramme ou sur une intercommunalité de la "
    "carte pour ne garder en couleur que celles de la même tranche."
)
TEXTE_RETOUR = " Cliquez ailleurs sur la page pour tout réafficher."
LECTURE_HISTOGRAMME = (
    "Lecture : chaque barre indique combien d'intercommunalités ont une valeur comprise "
    "dans la tranche. Le trait pointillé marque la médiane : la moitié des "
    "intercommunalités sont en dessous, l'autre moitié au-dessus."
)
SOURCES = (
    "Sources : Insee (recensements de la population, Filosofi) et DREES, via "
    "l'Observatoire des territoires. Contours des intercommunalités : data.gouv.fr."
)


def lecture_carte(indicateur: config.Indicateur) -> str:
    """Renvoie la phrase qui explique comment lire les couleurs de la carte."""
    return (
        f"Lecture : {indicateur.lecture} Les intercommunalités sans donnée pour "
        "l'année choisie ne sont pas coloriées."
    )


def titre_carte(indicateur: config.Indicateur, annee: int) -> str:
    """Renvoie le titre de la carte pour un indicateur et une année."""
    return f"{indicateur.nom} par intercommunalité en {annee}"


def titre_histogramme(annee: int) -> str:
    """Renvoie le titre de l'histogramme pour une année."""
    return f"Répartition des intercommunalités en {annee}"


def annee_retenue(nom_indicateur: str, annee_curseur: int | None) -> int:
    """Renvoie l'année à afficher : celle du curseur si l'indicateur l'a, sinon la plus récente."""
    annees = annees_disponibles(nom_indicateur)
    return annee_curseur if annee_curseur in annees else annees[-1]


def valeurs_affichees(nom_indicateur: str, annee_curseur: int | None) -> pd.Series:
    """Renvoie les valeurs actuellement affichées, indexées par code EPCI."""
    tableau = valeurs_par_annee(nom_indicateur)
    return tableau[annee_retenue(nom_indicateur, annee_curseur)]


def selectionner_tranche(
    nom_indicateur: str, annee_curseur: int | None, position: int
) -> tuple[list[int], str]:
    """Sélectionne tous les EPCI de la même tranche que celui situé à ``position``.

    Renvoie leurs positions (communes à la carte et à l'histogramme) et une
    phrase décrivant la tranche.
    """
    indicateur = config.INDICATEURS[nom_indicateur]
    largeur = indicateur.largeur_classe
    borne_basse = plage_valeurs(valeurs_par_annee(nom_indicateur), largeur)[0]
    valeurs = valeurs_affichees(nom_indicateur, annee_curseur)
    tranches = valeurs.dropna().map(
        lambda valeur: numero_tranche(valeur, borne_basse, largeur)
    )
    tranche = tranches[valeurs.index[position]]
    codes = tranches[tranches == tranche].index
    positions = [int(valeurs.index.get_loc(code)) for code in codes]
    debut = borne_basse + tranche * largeur
    description = (
        f"{len(positions)} intercommunalités entre {formater_borne(debut)} et "
        f"{formater_borne(debut + largeur)}{indicateur.unite}"
    )
    return positions, description


def interpreter_clic(
    clic_histogramme: dict[str, Any] | None,
    clic_carte: dict[str, Any] | None,
    nom_indicateur: str,
    annee_curseur: int | None,
) -> tuple[list[int], str] | None:
    """Traduit un clic en sélection : positions des EPCI concernés et phrase d'explication.

    Renvoie ``None`` quand le clic ne désigne ni une barre ni un EPCI avec une valeur.
    """
    if clic_histogramme:
        # Pour un histogramme, plotly fournit la position des valeurs regroupées dans la barre.
        position = clic_histogramme["points"][0]["pointNumbers"][0]
        positions, description = selectionner_tranche(
            nom_indicateur, annee_curseur, position
        )
        return positions, f"Sélection : {description}."
    if clic_carte:
        valeurs = valeurs_affichees(nom_indicateur, annee_curseur)
        code = clic_carte["points"][0]["location"]
        if pd.isna(valeurs[code]):
            return None
        position = int(valeurs.index.get_loc(code))
        positions, description = selectionner_tranche(
            nom_indicateur, annee_curseur, position
        )
        valeur = formater_valeur(
            valeurs[code], config.INDICATEURS[nom_indicateur].unite
        )
        return (
            positions,
            f"{noms_epci()[code]} : {valeur}. Elle fait partie des {description}.",
        )
    return None


def patch_selection(positions: list[int] | None) -> Patch:
    """Prépare la mise à jour d'un graphique : seules ``positions`` restent en couleur."""
    patch = Patch()
    patch["data"][0]["selectedpoints"] = positions
    return patch


def creer_reglages() -> html.Div:
    """Construit le bloc des réglages : menu des indicateurs et curseur d'années."""
    annees = annees_disponibles(config.INDICATEUR_PAR_DEFAUT)
    return html.Div(
        [
            html.Div(
                [
                    html.Label(
                        "INDICATEUR", htmlFor="choix-indicateur", className="etiquette"
                    ),
                    dcc.Dropdown(
                        id="choix-indicateur",
                        options=[
                            {"label": indicateur.nom, "value": nom}
                            for nom, indicateur in config.INDICATEURS.items()
                        ],
                        value=config.INDICATEUR_PAR_DEFAUT,
                        clearable=False,
                        searchable=False,
                    ),
                ],
                className="reglage-indicateur",
            ),
            html.Div(
                [
                    html.Div(id="mention-annee", className="etiquette"),
                    html.Div(
                        dcc.Slider(
                            id="curseur-annee",
                            min=annees[0],
                            max=annees[-1],
                            # step=None limite le curseur aux années disponibles.
                            step=None,
                            marks={annee: str(annee) for annee in annees},
                            value=annees[-1],
                            allow_direct_input=False,
                        ),
                        id="zone-curseur",
                    ),
                ],
                className="reglage-annee",
            ),
        ],
        className="bloc reglages",
    )


def creer_graphiques() -> html.Div:
    """Construit la carte et l'histogramme côte à côte, chacun avec sa note de lecture."""
    nom_indicateur = config.INDICATEUR_PAR_DEFAUT
    indicateur = config.INDICATEURS[nom_indicateur]
    tableau = valeurs_par_annee(nom_indicateur)
    annee = annees_disponibles(nom_indicateur)[-1]
    carte = creer_carte(
        tableau[annee],
        noms_epci(),
        indicateur,
        plage_valeurs(tableau, indicateur.largeur_classe),
        titre_carte(indicateur, annee),
    )
    return html.Div(
        [
            html.Div(
                [
                    # La molette ne zoome pas la carte : elle fait défiler la page, et le
                    # cadrage ne change pas par accident. La barre d'outils ne garde que
                    # l'export en image, le zoom et le retour à la vue de départ : la sélection
                    # au lasso ferait doublon avec la sélection au clic, et le bouton de
                    # partage envoie le graphique en ligne.
                    dcc.Graph(
                        id="carte",
                        figure=carte,
                        config={
                            "scrollZoom": False,
                            "displaylogo": False,
                            "showSendToCloud": False,
                            "modeBarButtonsToRemove": ["pan2d", "select2d", "lasso2d"],
                        },
                    ),
                    html.P(
                        lecture_carte(indicateur), id="lecture-carte", className="note"
                    ),
                ],
                className="bloc",
            ),
            html.Div(
                [
                    # La barre d'outils ne garde que l'export en image : le zoom est désactivé
                    # sur l'histogramme, donc les autres boutons n'auraient aucun effet.
                    dcc.Graph(
                        id="histogramme",
                        config={
                            "displaylogo": False,
                            "showSendToCloud": False,
                            "modeBarButtons": [["toImage"]],
                        },
                    ),
                    html.P(LECTURE_HISTOGRAMME, className="note"),
                ],
                className="bloc",
            ),
        ],
        className="graphiques",
    )


def creer_mise_en_page() -> html.Div:
    """Construit la page : bandeau, présentation, réglages, aide, graphiques et sources."""
    nombre_epci = f"{len(noms_epci()):,}".replace(",", " ")
    return html.Div(
        [
            html.Div(
                html.Div(
                    html.Div(config.NOM_DASHBOARD, className="marque"),
                    className="bandeau-contenu",
                ),
                className="bandeau",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.H1("Explorer un indicateur"),
                            html.P(
                                "Choisissez un indicateur, puis une année quand plusieurs sont "
                                "disponibles. La carte et l'histogramme portent sur les "
                                f"{nombre_epci} intercommunalités (EPCI) de France métropolitaine."
                            ),
                        ],
                        className="entete",
                    ),
                    creer_reglages(),
                    html.P(TEXTE_AIDE, id="texte-selection", className="aide"),
                    creer_graphiques(),
                    html.P(SOURCES, className="pied"),
                ],
                className="page",
            ),
        ],
        # Chaque clic dans la page est compté : c'est ce qui permet d'annuler une
        # sélection en cliquant ailleurs que sur une barre ou un EPCI.
        id="page-explorer",
        n_clicks=0,
    )


@callback(
    Output("curseur-annee", "min"),
    Output("curseur-annee", "max"),
    Output("curseur-annee", "marks"),
    Output("curseur-annee", "value"),
    Output("zone-curseur", "style"),
    Input("choix-indicateur", "value"),
)
def regler_curseur(nom_indicateur: str) -> tuple[Any, Any, Any, Any, dict[str, str]]:
    """Adapte le curseur aux années de l'indicateur choisi, ou le masque s'il n'y en a qu'une."""
    annees = annees_disponibles(nom_indicateur)
    if len(annees) == 1:
        return no_update, no_update, no_update, no_update, {"display": "none"}
    marques = {annee: str(annee) for annee in annees}
    return annees[0], annees[-1], marques, annees[-1], {"display": "block"}


@callback(
    Output("carte", "figure"),
    Output("histogramme", "figure"),
    Output("mention-annee", "children"),
    Output("texte-selection", "children"),
    Output("lecture-carte", "children"),
    Input("choix-indicateur", "value"),
    Input("curseur-annee", "value"),
)
def actualiser_graphiques(
    nom_indicateur: str, annee_curseur: int | None
) -> tuple[Patch, go.Figure, str, str, str]:
    """Met à jour la carte et l'histogramme quand l'indicateur ou l'année change.

    La sélection en cours est annulée, puisqu'elle portait sur d'autres valeurs.
    """
    indicateur = config.INDICATEURS[nom_indicateur]
    tableau = valeurs_par_annee(nom_indicateur)
    plage = plage_valeurs(tableau, indicateur.largeur_classe)
    annee = annee_retenue(nom_indicateur, annee_curseur)
    valeurs = tableau[annee]
    # Mise à jour partielle : seules les valeurs et les textes sont renvoyés au navigateur,
    # pas le fond de carte de plusieurs Mo, ce qui garde la page fluide.
    carte = patch_selection(None)
    donnees_carte = carte["data"][0]
    donnees_carte["z"] = valeurs_ou_vide(valeurs)
    donnees_carte["zmin"] = plage[0]
    donnees_carte["zmax"] = plage[1]
    donnees_carte["reversescale"] = indicateur.echelle_inversee
    donnees_carte["hovertemplate"] = texte_survol(indicateur.libelle)
    donnees_carte["colorbar"]["title"]["text"] = indicateur.libelle
    carte["layout"]["title"]["text"] = titre_carte(indicateur, annee)
    histogramme = creer_histogramme(
        valeurs, indicateur, plage, titre_histogramme(annee)
    )
    mention = f"ANNÉE : {annee}"
    if len(annees_disponibles(nom_indicateur)) == 1:
        mention += " (seule année disponible pour cet indicateur)"
    return carte, histogramme, mention, TEXTE_AIDE, lecture_carte(indicateur)


@callback(
    Output("carte", "figure", allow_duplicate=True),
    Output("histogramme", "figure", allow_duplicate=True),
    Output("texte-selection", "children", allow_duplicate=True),
    Output("histogramme", "clickData"),
    Output("carte", "clickData"),
    Input("page-explorer", "n_clicks"),
    Input("carte", "clickData"),
    State("histogramme", "clickData"),
    State("choix-indicateur", "value"),
    State("curseur-annee", "value"),
    prevent_initial_call=True,
)
def gerer_clic(
    _nombre_clics: int,
    clic_carte: dict[str, Any] | None,
    clic_histogramme: dict[str, Any] | None,
    nom_indicateur: str,
    annee_curseur: int | None,
) -> tuple[Any, Any, Any, Any, Any]:
    """Traite les clics : sélection d'une tranche, ou retour à l'affichage complet.

    Un clic sur un EPCI est signalé par la carte elle-même, car plotly l'empêche
    d'atteindre le reste de la page. Tous les autres clics sont comptés par la page :
    sur une barre, l'histogramme a enregistré le clic juste avant ; ailleurs, aucun
    graphique n'a rien enregistré et la sélection est annulée.
    """
    clic_sur_epci = "carte.clickData" in ctx.triggered_prop_ids
    if clic_sur_epci and not clic_carte:
        # Le clic de la carte vient d'être effacé par cette fonction : rien à faire.
        return no_update, no_update, no_update, no_update, no_update
    if clic_sur_epci:
        selection = interpreter_clic(None, clic_carte, nom_indicateur, annee_curseur)
    else:
        selection = interpreter_clic(
            clic_histogramme, None, nom_indicateur, annee_curseur
        )
    if selection is None:
        return patch_selection(None), patch_selection(None), TEXTE_AIDE, None, None
    positions, texte = selection
    # Le clic de la carte est effacé après un clic ailleurs ou sur une barre, pour qu'un
    # nouveau clic sur le même EPCI soit de nouveau signalé. Il est conservé après un clic
    # sur un EPCI : l'effacer aussitôt pourrait annuler la sélection qui vient d'être faite.
    clic_carte_apres = no_update if clic_sur_epci else None
    selection_carte = patch_selection(positions)
    selection_histogramme = patch_selection(positions)
    return (
        selection_carte,
        selection_histogramme,
        texte + TEXTE_RETOUR,
        None,
        clic_carte_apres,
    )
