"""Composant : histogramme de la distribution d'un indicateur."""

import pandas as pd
import plotly.graph_objects as go

import config
from src.utils.common_functions import formater_valeur, numero_tranche, valeurs_ou_vide


def creer_histogramme(
    valeurs: pd.Series,
    indicateur: config.Indicateur,
    plage: tuple[float, float],
    titre: str,
) -> go.Figure:
    """Crée l'histogramme des valeurs d'un indicateur sur l'ensemble des EPCI.

    Chaque barre compte les EPCI dont la valeur tombe dans une tranche de largeur
    ``indicateur.largeur_classe``. ``plage`` fixe les bornes de l'axe horizontal.
    """
    largeur = indicateur.largeur_classe
    # Les tranches démarrent à la première tranche occupée, sur la même grille que la
    # plage commune. Sans cela, plotly retire les tranches vides du début et met alors
    # en évidence une barre décalée lors d'une sélection.
    debut = plage[0] + numero_tranche(float(valeurs.min()), plage[0], largeur) * largeur
    histogramme = go.Figure(
        go.Histogram(
            # Les valeurs gardent l'ordre des EPCI de la carte (les manquantes sont
            # ignorées) : une barre cliquée désigne ainsi les mêmes positions sur la carte.
            x=valeurs_ou_vide(valeurs),
            xbins={"start": debut, "end": plage[1], "size": largeur},
            marker={
                "color": config.COULEUR_HISTOGRAMME,
                "line": {"width": 1, "color": "#ffffff"},
            },
            hovertemplate=(
                "<b>%{y} intercommunalités</b><br>"
                f"{indicateur.libelle} : %{{x}}<extra></extra>"
            ),
            # Quand une tranche est sélectionnée, les autres barres sont grisées.
            selected={"marker": {"color": config.COULEUR_HISTOGRAMME}},
            unselected={
                "marker": {"color": config.COULEUR_BARRE_ESTOMPEE, "opacity": 1}
            },
        )
    )
    mediane = float(valeurs.median())
    histogramme.add_vline(
        x=mediane,
        line={"color": "#1f2933", "width": 2, "dash": "dash"},
        annotation={
            "text": f"Médiane : {formater_valeur(mediane, indicateur.unite)}",
            "font": {"color": "#1f2933"},
        },
        annotation_position="top",
    )
    histogramme.update_layout(
        title={"text": titre},
        font=config.POLICE_GRAPHIQUES,
        xaxis={"title": {"text": indicateur.libelle}, "range": list(plage)},
        yaxis={"title": {"text": "Nombre d'intercommunalités"}},
        height=config.HAUTEUR_GRAPHIQUE,
        margin={"l": 60, "r": 20, "t": config.MARGE_HAUTE_GRAPHIQUE, "b": 60},
        separators=config.SEPARATEURS_NOMBRES,
        bargap=0.05,
        # Pas de zoom à la souris : un clic sert uniquement à sélectionner une tranche.
        dragmode=False,
        template="plotly_white",
    )
    return histogramme
