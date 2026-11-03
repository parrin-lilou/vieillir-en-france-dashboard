"""Nettoyage des données brutes et stockage, une table ``cleaned_...`` par indicateur.

Usage depuis la racine du projet (après get_data) :
    python -m src.utils.clean_data
"""

import json
from typing import Any

import pandas as pd

import config
from src.utils.base_donnees import (
    ecrire_table,
    lire_table,
    nom_table_brute,
    nom_table_nettoyee,
)
from src.utils.validation import valider_table

COLONNES_NETTOYEES = ["codgeo", "libgeo", "indicateur", "annee", "valeur"]


def lire_tables_brutes() -> pd.DataFrame:
    """Charge et rassemble les tables brutes de toutes les sources.

    Les tables ont la même structure : leur réunion permet d'extraire chaque indicateur,
    et de croiser deux sources pour calculer la part des personnes âgées seules.
    """
    return pd.concat(
        [lire_table(nom_table_brute(code)) for code in config.SOURCES_OBSERVATOIRE],
        ignore_index=True,
    )


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
    config.DOSSIER_NETTOYE.mkdir(parents=True, exist_ok=True)
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


def enregistrer_tables_nettoyees(table: pd.DataFrame) -> dict[str, int]:
    """Enregistre chaque indicateur de la table nettoyée dans sa propre table.

    Renvoie le nombre de lignes de chaque table, indexé par le nom de la table.
    """
    nombres_lignes = {}
    for indicateur in config.INDICATEURS:
        lignes = table[table["indicateur"] == indicateur]
        nom = nom_table_nettoyee(indicateur)
        ecrire_table(lignes, nom)
        nombres_lignes[nom] = len(lignes)
    return nombres_lignes


def main() -> None:
    """Nettoie le fond de carte et les indicateurs, puis alimente les tables nettoyées."""
    codes_metropole = nettoyer_fond_carte()
    table = construire_table_nettoyee(lire_tables_brutes(), codes_metropole)
    # Contrôle avant écriture : rien n'est enregistré si une ligne est incorrecte.
    valider_table(table)
    for nom, nombre_lignes in enregistrer_tables_nettoyees(table).items():
        print(f"Table {nom} : {nombre_lignes} lignes.")
    print(f"{len(table)} lignes au total, {len(codes_metropole)} EPCI.")


if __name__ == "__main__":
    main()
