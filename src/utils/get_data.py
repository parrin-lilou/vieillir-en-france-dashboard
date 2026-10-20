"""Récupération des données sur le web et stockage brut dans la table ``raw``.

Usage depuis la racine du projet :
    python -m src.utils.get_data
"""

import shutil
import sqlite3
import urllib.request
from pathlib import Path

import pandas as pd

import config


def construire_url(indicateur: str, base: str) -> str:
    """Renvoie l'adresse de téléchargement d'un indicateur de l'Observatoire des territoires."""
    return config.API_OBSERVATOIRE.format(
        niveau=config.NIVEAU_GEOGRAPHIQUE, base=base, indicateur=indicateur
    )


def telecharger(url: str, destination: Path) -> None:
    """Télécharge ``url`` et enregistre le fichier tel quel dans ``destination``."""
    requete = urllib.request.Request(url, headers=config.EN_TETES_HTTP)
    with (
        urllib.request.urlopen(requete, timeout=config.DELAI_MAX_SECONDES) as reponse,
        destination.open("wb") as sortie,
    ):
        # Copie par blocs : le fond de carte pèse plusieurs Mo.
        shutil.copyfileobj(reponse, sortie)


def telecharger_sources() -> None:
    """Télécharge les classeurs des indicateurs et le fond de carte dans ``data/raw/``."""
    config.DOSSIER_BRUT.mkdir(parents=True, exist_ok=True)
    for indicateur, base in config.SOURCES_OBSERVATOIRE.items():
        telecharger(
            construire_url(indicateur, base), config.DOSSIER_BRUT / f"{indicateur}.xlsx"
        )
    telecharger(config.URL_FOND_CARTE, config.FOND_CARTE_BRUT)


def lire_classeur(indicateur: str) -> pd.DataFrame:
    """Lit le classeur brut d'un indicateur sans modifier ses valeurs.

    Tout est lu comme du texte pour conserver exactement le contenu de la source.
    Les colonnes renvoyées sont : indicateur, codgeo, libgeo, an, sexe, valeur.
    """
    donnees = pd.read_excel(
        config.DOSSIER_BRUT / f"{indicateur}.xlsx",
        sheet_name=config.FEUILLE_DONNEES,
        skiprows=config.LIGNES_AVANT_EN_TETE,
        dtype=str,
    )
    # La colonne de valeurs porte le code de l'indicateur : on lui donne un nom commun
    # pour pouvoir empiler tous les indicateurs dans une seule table.
    donnees = donnees.rename(columns={indicateur: "valeur"})
    donnees["indicateur"] = indicateur
    # Seuls certains indicateurs sont détaillés par sexe.
    if "sexe" not in donnees.columns:
        donnees["sexe"] = None
    return donnees[["indicateur", "codgeo", "libgeo", "an", "sexe", "valeur"]]


def enregistrer_table_brute() -> int:
    """Empile les classeurs bruts dans la table ``raw`` et renvoie le nombre de lignes."""
    brut = pd.concat(
        [lire_classeur(indicateur) for indicateur in config.SOURCES_OBSERVATOIRE],
        ignore_index=True,
    )
    with sqlite3.connect(config.BASE_SQLITE) as connexion:
        brut.to_sql(config.TABLE_BRUTE, connexion, if_exists="replace", index=False)
    return len(brut)


def main() -> None:
    """Télécharge toutes les sources puis alimente la table ``raw``."""
    telecharger_sources()
    nombre_lignes = enregistrer_table_brute()
    print(f"Table {config.TABLE_BRUTE} : {nombre_lignes} lignes enregistrées.")


if __name__ == "__main__":
    main()
