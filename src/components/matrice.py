"""Composant : matrice des corrélations entre tous les indicateurs, avec Plotly Express."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import config


def calculer_correlations(tableau: pd.DataFrame) -> pd.DataFrame:
    """Calcule les corrélations entre indicateurs, avec leurs noms courts en lignes et colonnes.

    pandas ignore, pour chaque paire, les EPCI qui n'ont pas les deux valeurs.
    """
    noms = list(config.INDICATEURS)
    correlations = tableau[noms].corr()
    noms_courts = [config.INDICATEURS[nom].nom_court for nom in noms]
    correlations.index = pd.Index(noms_courts)
    correlations.columns = pd.Index(noms_courts)
    return correlations


def creer_matrice(tableau: pd.DataFrame) -> go.Figure:
    """Crée la matrice des corrélations, chaque case affichant son coefficient."""
    figure = px.imshow(
        calculer_correlations(tableau),
        text_auto=".2f",
        # Bornes fixes de -1 à 1 : le blanc correspond à l'absence de lien.
        zmin=-1,
        zmax=1,
        color_continuous_scale=config.ECHELLE_CORRELATION,
        aspect="auto",
        title="Corrélations entre les indicateurs",
    )
    figure.update_traces(
        hovertemplate="%{y} et %{x}<br>Corrélation : %{z:.2f}<extra></extra>"
    )
    figure.update_layout(
        font=config.POLICE_GRAPHIQUES,
        height=config.HAUTEUR_GRAPHIQUE,
        margin={"l": 20, "r": 20, "t": config.MARGE_HAUTE_GRAPHIQUE, "b": 20},
        separators=config.SEPARATEURS_NOMBRES,
        coloraxis_colorbar={
            "title": {"text": "Corrélation", "side": "right"},
            "thickness": 14,
        },
        xaxis={"side": "bottom", "title": None},
        yaxis={"title": None},
    )
    return figure
