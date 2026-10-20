"""Point d'entrée du dashboard : ``python main.py``."""

from dash import Dash

import config
from src.pages import explorer


def creer_application() -> Dash:
    """Crée l'application Dash et lui associe sa mise en page."""
    application = Dash(__name__, title=config.TITRE_DASHBOARD)
    application.layout = explorer.creer_mise_en_page()
    return application


if __name__ == "__main__":
    creer_application().run(host=config.HOTE, port=config.PORT, debug=config.MODE_DEBUG)
