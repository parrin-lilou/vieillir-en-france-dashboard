"""Point d'entrée du dashboard : ``python main.py``."""

from collections.abc import Callable

from dash import Dash, Input, Output, callback, dcc, html

import config
from src.components.navbar import creer_bandeau
from src.pages import comparer, explorer

# Adresse de chaque page -> fonction qui construit son contenu.
PAGES: dict[str, Callable[[], html.Div]] = {
    "/explorer": explorer.creer_mise_en_page,
    "/comparer": comparer.creer_mise_en_page,
}


def creer_application() -> Dash:
    """Crée l'application Dash : un bandeau, et le contenu de la page demandée."""
    application = Dash(__name__, title=config.TITRE_DASHBOARD)
    application.layout = html.Div(
        [
            # Suit l'adresse affichée dans le navigateur, pour savoir quelle page montrer.
            dcc.Location(id="adresse"),
            html.Div(id="bandeau"),
            html.Div(id="contenu-page"),
        ]
    )
    # Les pages ne sont construites qu'à la demande. On présente à Dash l'ensemble de leurs
    # composants, pour qu'il valide les callbacks de chaque page sans erreur dans le navigateur.
    # Dash annote cet attribut comme vide par défaut, d'où l'exception de typage.
    application.validation_layout = html.Div(  # type: ignore[assignment]
        [application.layout, *(construire() for construire in PAGES.values())]
    )
    return application


def page_introuvable() -> html.Div:
    """Construit le message affiché pour une adresse qui ne correspond à aucune page."""
    return html.Div(
        [
            html.H1("Page introuvable"),
            dcc.Link("Revenir à la page Explorer", href=config.PAGE_PAR_DEFAUT),
        ],
        className="page entete",
    )


@callback(
    Output("bandeau", "children"),
    Output("contenu-page", "children"),
    Input("adresse", "pathname"),
)
def afficher_page(chemin: str | None) -> tuple[html.Div, html.Div]:
    """Affiche la page correspondant à l'adresse, et souligne son lien dans le bandeau."""
    chemin_page = config.PAGE_PAR_DEFAUT if chemin in (None, "/") else chemin
    construire = PAGES.get(chemin_page)
    contenu = construire() if construire else page_introuvable()
    return creer_bandeau(chemin_page), contenu


if __name__ == "__main__":
    creer_application().run(host=config.HOTE, port=config.PORT, debug=config.MODE_DEBUG)