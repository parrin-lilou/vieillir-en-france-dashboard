"""Composant : nuage de points comparant deux indicateurs, avec Plotly Express."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import config


def echelle_couleurs(nom_indicateur: str) -> str:
    """Renvoie l'échelle de couleurs d'un indicateur, retournée si une valeur basse est défavorable.

    Ainsi le foncé signale toujours la fragilité, comme sur la carte de la page « Explorer ».
    """
    if config.INDICATEURS[nom_indicateur].echelle_inversee:
        return f"{config.ECHELLE_COULEURS}_r"
    return config.ECHELLE_COULEURS


def ligne_survol(nom_indicateur: str, champ: str) -> str:
    """Renvoie une ligne d'infobulle « Indicateur : valeur unité » pour un champ Plotly.

    ``champ`` désigne la donnée du point à afficher (``x``, ``y`` ou ``marker.color``).
    Le format ``.1f`` utilise les séparateurs français définis dans la mise en page.
    """
    indicateur = config.INDICATEURS[nom_indicateur]
    return f"{indicateur.nom} : %{{{champ}:.1f}}{indicateur.unite}"


def texte_survol(nom_x: str, nom_y: str, nom_couleur: str | None) -> str:
    """Construit l'infobulle d'un point : le nom de l'intercommunalité, puis ses valeurs."""
    lignes = [ligne_survol(nom_x, "x"), ligne_survol(nom_y, "y")]
    if nom_couleur is not None:
        lignes.append(ligne_survol(nom_couleur, "marker.color"))
    # <extra></extra> retire le cadre secondaire que Plotly ajoute à droite de l'infobulle.
    return "<b>%{hovertext}</b><br>" + "<br>".join(lignes) + "<extra></extra>"


def creer_nuage(
    tableau: pd.DataFrame, nom_x: str, nom_y: str, nom_couleur: str | None
) -> go.Figure:
    """Crée le nuage de points : une intercommunalité par point.

    ``tableau`` est le tableau large de ``tableau_comparaison()``. ``nom_couleur`` désigne
    un troisième indicateur qui colorie les points, ou ``None`` pour une couleur unique.
    """
    colonnes_utiles = [nom_x, nom_y] + ([nom_couleur] if nom_couleur else [])
    # Un point n'a de sens que si l'EPCI a une valeur pour chaque indicateur affiché.
    donnees = tableau.dropna(subset=colonnes_utiles)
    figure = px.scatter(
        donnees,
        x=nom_x,
        y=nom_y,
        color=nom_couleur,
        hover_name="libgeo",
        # Les libellés avec unités remplacent les codes techniques sur les axes et au survol.
        labels={
            nom: indicateur.libelle for nom, indicateur in config.INDICATEURS.items()
        },
        color_continuous_scale=echelle_couleurs(nom_couleur) if nom_couleur else None,
        title=f"{config.INDICATEURS[nom_y].nom} selon {config.INDICATEURS[nom_x].nom_en_phrase}",
    )
    figure.update_traces(
        marker={"size": 7, "opacity": 0.8, "line": {"width": 0.4, "color": "#ffffff"}},
        # Infobulle « Indicateur : valeur », au lieu du format « libellé=valeur » de Plotly.
        hovertemplate=texte_survol(nom_x, nom_y, nom_couleur),
    )
    if nom_couleur is None:
        figure.update_traces(marker_color=config.COULEUR_HISTOGRAMME)
    figure.update_layout(
        font=config.POLICE_GRAPHIQUES,
        height=config.HAUTEUR_GRAPHIQUE,
        margin={"l": 60, "r": 20, "t": config.MARGE_HAUTE_GRAPHIQUE, "b": 60},
        separators=config.SEPARATEURS_NOMBRES,
        template="plotly_white",
        # Le titre de la légende de couleurs est placé sur le côté, pour rester lisible.
        coloraxis_colorbar={"title": {"side": "right"}, "thickness": 14},
    )
    return figure
