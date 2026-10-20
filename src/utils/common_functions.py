"""Fonctions communes d'accès aux données nettoyées du dashboard."""

import json
import math
import sqlite3
from functools import lru_cache
from typing import Any

import pandas as pd

import config


@lru_cache(maxsize=1)
def charger_table_nettoyee() -> pd.DataFrame:
    """Charge la table ``cleaned`` (lue une seule fois, puis gardée en mémoire)."""
    with sqlite3.connect(config.BASE_SQLITE) as connexion:
        return pd.read_sql(f"SELECT * FROM {config.TABLE_NETTOYEE}", connexion)


@lru_cache(maxsize=1)
def charger_fond_carte() -> dict[str, Any]:
    """Charge les contours des EPCI de métropole au format GeoJSON."""
    contenu: dict[str, Any] = json.loads(config.FOND_CARTE.read_text(encoding="utf-8"))
    return contenu


def noms_epci() -> pd.Series:
    """Renvoie le nom de chaque EPCI, indexé et trié par code."""
    table = charger_table_nettoyee()
    return table.drop_duplicates("codgeo").set_index("codgeo")["libgeo"].sort_index()


def valeurs_par_annee(indicateur: str) -> pd.DataFrame:
    """Renvoie un indicateur sous forme de tableau : une ligne par EPCI, une colonne par année.

    Tous les EPCI sont présents sur toutes les années, dans le même ordre que
    ``noms_epci()`` : une valeur absente de la source apparaît comme manquante.
    """
    table = charger_table_nettoyee()
    lignes = table[table["indicateur"] == indicateur]
    tableau = lignes.pivot(index="codgeo", columns="annee", values="valeur")
    return tableau.reindex(noms_epci().index)


def annees_disponibles(indicateur: str) -> list[int]:
    """Renvoie les années pour lesquelles un indicateur est disponible, en ordre croissant."""
    return [int(annee) for annee in valeurs_par_annee(indicateur).columns]


def plage_valeurs(tableau: pd.DataFrame, largeur_classe: float) -> tuple[float, float]:
    """Renvoie les bornes encadrant toutes les valeurs, alignées sur les tranches.

    La même plage sert à toutes les années d'un indicateur, pour que les couleurs
    de la carte et les tranches de l'histogramme restent comparables dans le temps.
    """
    minimum = float(tableau.min().min())
    maximum = float(tableau.max().max())
    borne_basse = math.floor(minimum / largeur_classe) * largeur_classe
    borne_haute = math.ceil(maximum / largeur_classe) * largeur_classe
    return borne_basse, borne_haute


def formater_valeur(valeur: float, unite: str) -> str:
    """Écrit une valeur à la française, avec une décimale et son unité (« 11,1 % »)."""
    return f"{valeur:.1f}".replace(".", ",") + unite


def valeurs_ou_vide(valeurs: pd.Series) -> list[float | None]:
    """Convertit une série en liste, les valeurs manquantes devenant ``None``.

    Les graphiques ignorent alors ces EPCI au lieu de les confondre avec zéro,
    tout en gardant la même position pour chaque EPCI d'un graphique à l'autre.
    """
    return [None if pd.isna(valeur) else float(valeur) for valeur in valeurs]


def formater_borne(valeur: float) -> str:
    """Écrit une borne de tranche à la française, sans décimale inutile (« 10 », « 3,25 »)."""
    return f"{valeur:g}".replace(".", ",")


def numero_tranche(valeur: float, borne_basse: float, largeur_classe: float) -> int:
    """Renvoie le numéro de la tranche de l'histogramme qui contient une valeur.

    La tranche 0 commence à ``borne_basse`` ; chaque tranche inclut sa borne basse
    et exclut sa borne haute, comme dans l'histogramme.
    """
    return math.floor((valeur - borne_basse) / largeur_classe)
