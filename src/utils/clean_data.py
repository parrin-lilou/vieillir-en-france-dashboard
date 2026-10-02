"""Nettoyage des données brutes et stockage dans la table ``cleaned``.

Usage depuis la racine du projet (après get_data) :
    python -m src.utils.clean_data
"""

import json
import sqlite3
from typing import Any

import pandas as pd

import config

COLONNES_NETTOYEES = ["codgeo", "libgeo", "indicateur", "annee", "valeur"]


def lire_table_brute() -> pd.DataFrame:
    """Charge la table ``raw`` depuis la base SQLite."""
    with sqlite3.connect(config.BASE_SQLITE) as connexion:
        return pd.read_sql(f"SELECT * FROM {config.TABLE_BRUTE}", connexion)


def premier_point(coordonnees: list[Any]) -> tuple[float, float]:
    """Renvoie la (longitude, latitude) du premier point d'une géométrie GeoJSON.

    Les coordonnées sont des listes imbriquées, plus ou moins profondes selon que
    le contour est un polygone ou un ensemble de polygones : on descend jusqu'au point.
    """
    while isinstance(coordonnees[0], list):
        coordonnees = coordonnees[0]
    return coordonnees[0], coordonnees[1]


def est_en_metropole(contour: dict[str, Any]) -> bool:
    """Indique si un contour du fond de carte se trouve en France métropolitaine."""
    longitude, latitude = premier_point(contour["geometry"]["coordinates"])
    longitude_min, latitude_min, longitude_max, latitude_max = config.EMPRISE_METROPOLE
    return (
        longitude_min <= longitude <= longitude_max
        and latitude_min <= latitude <= latitude_max
    )


def nettoyer_fond_carte() -> set[str]:
    """Réduit le fond de carte à la métropole et renvoie les codes des EPCI conservés."""
    fond = json.loads(config.FOND_CARTE_BRUT.read_text(encoding="utf-8"))
    fond["features"] = [
        contour for contour in fond["features"] if est_en_metropole(contour)
    ]
    # Écriture compacte (sans espaces) pour alléger le fichier chargé par le dashboard.
    config.FOND_CARTE.write_text(
        json.dumps(fond, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    return {contour["properties"]["code"] for contour in fond["features"]}


def extraire_indicateur(brut: pd.DataFrame, code_source: str) -> pd.DataFrame:
    """Extrait un indicateur de la table brute, avec année et valeur numériques.

    Pour les indicateurs détaillés par sexe, seule la ligne « ensemble » est gardée.
    """
    lignes = brut[brut["indicateur"] == code_source]
    lignes = lignes[lignes["sexe"].isna() | (lignes["sexe"] == config.CODE_SEXE_TOTAL)]
    resultat = lignes[["codgeo", "libgeo"]].copy()
    # Les valeurs sont stockées comme du texte dans la source.
    resultat["annee"] = pd.to_numeric(lignes["an"], errors="coerce")
    resultat["valeur"] = pd.to_numeric(lignes["valeur"], errors="coerce")
    return resultat


def calculer_part_seuls(brut: pd.DataFrame) -> pd.DataFrame:
    """Calcule la part des 75 ans et plus vivant seuls (%).

    La source ne fournit pas cette part par EPCI : elle est obtenue en divisant le
    nombre de 75 ans et plus vivant seuls par le nombre total de 75 ans et plus.
    """
    seuls = extraire_indicateur(brut, "nb_persseul75")
    population = extraire_indicateur(brut, "pop75p")
    # Jointure sur le territoire et l'année : seules les années communes sont gardées.
    fusion = seuls.merge(
        population[["codgeo", "annee", "valeur"]],
        on=["codgeo", "annee"],
        suffixes=("_seuls", "_population"),
    )
    # Un effectif nul signale un territoire sans donnée, pas une absence de personnes seules.
    effectif_seuls = fusion["valeur_seuls"].where(fusion["valeur_seuls"] > 0)
    fusion["valeur"] = (effectif_seuls / fusion["valeur_population"] * 100).round(1)
    return fusion[["codgeo", "libgeo", "annee", "valeur"]]


def construire_table_nettoyee(
    brut: pd.DataFrame, codes_metropole: set[str]
) -> pd.DataFrame:
    """Assemble les quatre indicateurs du dashboard au format long (une ligne par valeur)."""
    indicateurs = {
        "part_75_plus": extraire_indicateur(brut, "part_pop75p"),
        "part_75_seuls": calculer_part_seuls(brut),
        "taux_pauvrete": extraire_indicateur(brut, "tx_pauv_60"),
        "apl_medecins": extraire_indicateur(brut, "apl_mg_hmep"),
    }
    table = pd.concat(
        [donnees.assign(indicateur=nom) for nom, donnees in indicateurs.items()],
        ignore_index=True,
    )
    # Les lignes sans valeur (secret statistique, territoire non couvert) sont inutilisables.
    table = table.dropna(subset=["annee", "valeur"])
    table = table[table["codgeo"].isin(codes_metropole)]
    table["annee"] = table["annee"].astype(int)
    return table[COLONNES_NETTOYEES].sort_values(["indicateur", "annee", "codgeo"])


def main() -> None:
    """Nettoie le fond de carte et les indicateurs, puis alimente la table ``cleaned``."""
    codes_metropole = nettoyer_fond_carte()
    table = construire_table_nettoyee(lire_table_brute(), codes_metropole)
    with sqlite3.connect(config.BASE_SQLITE) as connexion:
        table.to_sql(config.TABLE_NETTOYEE, connexion, if_exists="replace", index=False)
    print(
        f"Table {config.TABLE_NETTOYEE} : {len(table)} lignes, {len(codes_metropole)} EPCI."
    )


if __name__ == "__main__":
    main()
