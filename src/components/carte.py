"""Composant : carte choroplèthe des EPCI."""

import pandas as pd
import plotly.graph_objects as go

import config
from src.utils.common_functions import charger_fond_carte, valeurs_ou_vide


def texte_survol(libelle: str) -> str:
    """Renvoie le modèle d'infobulle de la carte : nom de l'EPCI, puis valeur avec son libellé."""
    return f"<b>%{{text}}</b><br>{libelle} : %{{z:.1f}}<extra></extra>"


def creer_carte(
    valeurs: pd.Series,
    noms: pd.Series,
    indicateur: config.Indicateur,
    plage: tuple[float, float],
    titre: str,
) -> go.Figure:
    """Crée la carte d'un indicateur.

    ``valeurs`` et ``noms`` sont indexés par code EPCI, dans le même ordre.
    ``plage`` fixe les bornes de l'échelle de couleurs.
    """
    carte = go.Figure(
        go.Choroplethmap(
            geojson=charger_fond_carte(),
            featureidkey="properties.code",
            locations=list(valeurs.index),
            z=valeurs_ou_vide(valeurs),
            zmin=plage[0],
            zmax=plage[1],
            colorscale=config.ECHELLE_COULEURS,
            reversescale=indicateur.echelle_inversee,
            marker={"line": {"width": 0.2, "color": "#ffffff"}},
            text=list(noms),
            hovertemplate=texte_survol(indicateur.libelle),
            colorbar={
                "title": {"text": indicateur.libelle, "side": "right"},
                "thickness": 14,
            },
            # Quand une sélection est active, les EPCI non concernés sont estompés.
            selected={"marker": {"opacity": 1}},
            unselected={"marker": {"opacity": config.OPACITE_EPCI_ESTOMPE}},
        )
    )
    carte.update_layout(
        title={"text": titre},
        font=config.POLICE_GRAPHIQUES,
        map={
            "style": config.STYLE_CARTE,
            "center": config.CENTRE_CARTE,
            "zoom": config.ZOOM_CARTE,
        },
        height=config.HAUTEUR_GRAPHIQUE,
        margin={"l": 0, "r": 0, "t": config.MARGE_HAUTE_GRAPHIQUE, "b": 0},
        separators=config.SEPARATEURS_NOMBRES,
        # Conserve le zoom choisi par l'utilisateur quand les données changent.
        uirevision="carte",
    )
    return carte
