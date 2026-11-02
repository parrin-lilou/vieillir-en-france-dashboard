"""Récupération des données sur le web et stockage brut, une table ``raw_...`` par source.

Usage depuis la racine du projet :
    python -m src.utils.get_data

Si une source n'est plus téléchargeable, la copie d'origine conservée dans ``data/raw/``
est utilisée à sa place : les tables brutes peuvent toujours être reconstruites.
"""

import shutil
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd

import config
from src.utils.base_donnees import ecrire_table, nom_table_brute


def construire_url(indicateur: str, base: str) -> str:
    """Renvoie l'adresse de téléchargement d'un indicateur de l'Observatoire des territoires."""
    return config.API_OBSERVATOIRE.format(
        niveau=config.NIVEAU_GEOGRAPHIQUE, base=base, indicateur=indicateur
    )


def telecharger(url: str, destination: Path) -> None:
    """Télécharge ``url`` et enregistre le fichier tel quel dans ``destination``.

    Le fichier est d'abord écrit à côté, sous un nom temporaire : un téléchargement
    interrompu ne peut donc pas abîmer la copie déjà présente.
    """
    temporaire = destination.with_name(destination.name + ".partiel")
    requete = urllib.request.Request(url, headers=config.EN_TETES_HTTP)
    with (
        urllib.request.urlopen(requete, timeout=config.DELAI_MAX_SECONDES) as reponse,
        temporaire.open("wb") as sortie,
    ):
        # Copie par blocs : le fond de carte pèse plusieurs Mo.
        shutil.copyfileobj(reponse, sortie)
    temporaire.replace(destination)


def recuperer_source(url: str, destination: Path) -> bool:
    """Télécharge une source, ou garde sa copie locale si le téléchargement échoue.

    Renvoie ``True`` si le fichier a été téléchargé, ``False`` si la copie locale est
    utilisée. Lève ``FileNotFoundError`` s'il n'y a ni téléchargement ni copie.
    """
    try:
        telecharger(url, destination)
        return True
    except (urllib.error.URLError, TimeoutError) as erreur:
        if not destination.exists():
            raise FileNotFoundError(
                f"{destination.name} : téléchargement impossible ({erreur}) "
                "et aucune copie locale dans data/raw/."
            ) from erreur
        print(f"{destination.name} : téléchargement impossible ({erreur}).")
        print(
            f"  -> utilisation de la copie conservée dans {config.DOSSIER_BRUT.name}/."
        )
        return False


def telecharger_sources() -> int:
    """Récupère les classeurs des indicateurs et le fond de carte dans ``data/raw/``.

    Renvoie le nombre de sources remplacées par leur copie locale.
    """
    config.DOSSIER_BRUT.mkdir(parents=True, exist_ok=True)
    sources = {
        construire_url(indicateur, base): config.DOSSIER_BRUT / f"{indicateur}.xlsx"
        for indicateur, base in config.SOURCES_OBSERVATOIRE.items()
    }
    sources[config.URL_FOND_CARTE] = config.FOND_CARTE_BRUT
    telechargees = [recuperer_source(url, fichier) for url, fichier in sources.items()]
    return telechargees.count(False)


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
    # La colonne de valeurs porte le code de l'indicateur : on lui donne un nom commun,
    # pour que toutes les tables brutes aient la même structure.
    donnees = donnees.rename(columns={indicateur: "valeur"})
    donnees["indicateur"] = indicateur
    # Seuls certains indicateurs sont détaillés par sexe.
    if "sexe" not in donnees.columns:
        donnees["sexe"] = None
    return donnees[["indicateur", "codgeo", "libgeo", "an", "sexe", "valeur"]]


def enregistrer_tables_brutes() -> dict[str, int]:
    """Enregistre chaque classeur dans sa propre table brute.

    Renvoie le nombre de lignes de chaque table, indexé par le nom de la table.
    """
    nombres_lignes = {}
    for indicateur in config.SOURCES_OBSERVATOIRE:
        brut = lire_classeur(indicateur)
        nom = nom_table_brute(indicateur)
        ecrire_table(brut, nom)
        nombres_lignes[nom] = len(brut)
    return nombres_lignes


def main() -> None:
    """Récupère toutes les sources puis alimente une table brute par source."""
    copies_locales = telecharger_sources()
    if copies_locales:
        # Cas connu : depuis sa mise à jour du 9 octobre 2026, l'Observatoire ne diffuse
        # plus le découpage EPCI 2025 (voir la section Data du README).
        print(f"{copies_locales} source(s) reconstruite(s) depuis la copie d'origine.")
    # La base est recréée à chaque récupération : elle ne contient que les tables à jour.
    config.BASE_SQLITE.unlink(missing_ok=True)
    for nom, nombre_lignes in enregistrer_tables_brutes().items():
        print(f"Table {nom} : {nombre_lignes} lignes enregistrées.")


if __name__ == "__main__":
    main()
