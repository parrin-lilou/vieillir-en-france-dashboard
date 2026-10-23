"""Composant : bandeau du haut, avec le nom du dashboard et les liens vers les pages."""

from dash import dcc, html

import config


def creer_bandeau(chemin_actif: str) -> html.Div:
    """Construit le bandeau, en soulignant le lien de la page affichée."""
    liens = [
        dcc.Link(
            texte,
            href=chemin,
            className="lien-nav actif" if chemin == chemin_actif else "lien-nav",
        )
        for chemin, texte in config.NAVIGATION.items()
    ]
    return html.Div(
        html.Div(
            [
                html.Div(config.NOM_DASHBOARD, className="marque"),
                html.Nav(liens, className="navigation"),
            ],
            className="bandeau-contenu",
        ),
        className="bandeau",
    )
