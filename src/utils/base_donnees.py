"""Accès à la base SQLite avec SQLAlchemy.

Chaque source de données a sa propre table brute (``raw_<code de la source>``) et
chaque indicateur sa propre table nettoyée (``cleaned_<nom de l'indicateur>``).
Toutes les lectures et écritures de la base passent par ce module.
"""

import pandas as pd
from sqlalchemy import Engine, create_engine, inspect

import config


def creer_moteur() -> Engine:
    """Crée le moteur SQLAlchemy relié à la base SQLite du projet.

    Le chemin est lu à chaque appel, ce qui permet aux tests d'utiliser une base temporaire.
    """
    return create_engine(f"sqlite:///{config.BASE_SQLITE}")


def nom_table_brute(code_source: str) -> str:
    """Renvoie le nom de la table brute d'une source (``raw_tx_pauv_60``, par exemple)."""
    return f"{config.PREFIXE_TABLE_BRUTE}{code_source}"


def nom_table_nettoyee(indicateur: str) -> str:
    """Renvoie le nom de la table nettoyée d'un indicateur (``cleaned_taux_pauvrete``...)."""
    return f"{config.PREFIXE_TABLE_NETTOYEE}{indicateur}"


def ecrire_table(table: pd.DataFrame, nom: str) -> None:
    """Enregistre un tableau dans la base, en remplaçant la table si elle existe déjà."""
    moteur = creer_moteur()
    # La transaction garantit qu'une table n'est jamais enregistrée à moitié.
    with moteur.begin() as connexion:
        table.to_sql(nom, connexion, if_exists="replace", index=False)
    moteur.dispose()


def lire_table(nom: str) -> pd.DataFrame:
    """Charge une table de la base dans un tableau pandas."""
    moteur = creer_moteur()
    with moteur.connect() as connexion:
        table = pd.read_sql_table(nom, connexion)
    moteur.dispose()
    return table


def lister_tables() -> list[str]:
    """Renvoie le nom des tables présentes dans la base, par ordre alphabétique."""
    moteur = creer_moteur()
    noms = sorted(inspect(moteur).get_table_names())
    moteur.dispose()
    return noms
