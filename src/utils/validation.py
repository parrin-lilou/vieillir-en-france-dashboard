"""Validation des données nettoyées avec pydantic, avant leur écriture dans la base.

Si une source change de format (colonne renommée, valeur aberrante, code mal formé),
le nettoyage s'arrête avec un message clair au lieu d'enregistrer des données fausses
que le dashboard afficherait sans prévenir.
"""

from typing import Any, Self

import pandas as pd
from pydantic import (
    BaseModel,
    Field,
    TypeAdapter,
    ValidationError,
    field_validator,
    model_validator,
)

import config

# Un code d'EPCI est un numéro SIREN : exactement 9 chiffres.
MOTIF_CODE_EPCI = r"^\d{9}$"
# Bornes larges pour les années : le plus ancien recensement utilisé date de 1968.
ANNEE_MINIMALE = 1968
ANNEE_MAXIMALE = 2100
NOMBRE_ERREURS_AFFICHEES = 5


class LigneNettoyee(BaseModel):
    """Une ligne de la table ``cleaned`` : la valeur d'un indicateur pour un EPCI et une année."""

    codgeo: str = Field(pattern=MOTIF_CODE_EPCI)
    libgeo: str = Field(min_length=1)
    indicateur: str
    annee: int = Field(ge=ANNEE_MINIMALE, le=ANNEE_MAXIMALE)
    # Toutes les valeurs du projet sont des parts, des taux ou des nombres de consultations.
    valeur: float = Field(ge=0)

    @field_validator("indicateur")
    @classmethod
    def verifier_indicateur(cls, nom: str) -> str:
        """Refuse un indicateur que le dashboard ne sait pas afficher."""
        if nom not in config.INDICATEURS:
            raise ValueError(f"indicateur inconnu : {nom}")
        return nom

    @model_validator(mode="after")
    def verifier_pourcentage(self) -> Self:
        """Refuse une part ou un taux supérieur à 100 %."""
        if config.INDICATEURS[self.indicateur].unite == " %" and self.valeur > 100:
            raise ValueError(f"pourcentage supérieur à 100 : {self.valeur}")
        return self


def decrire_erreur(erreur: Any) -> str:
    """Rédige une erreur de validation : numéro de ligne, champ concerné et message."""
    numero_ligne, *champs = erreur["loc"]
    emplacement = f"ligne {numero_ligne}"
    if champs:
        emplacement += ", " + "/".join(map(str, champs))
    return f"{emplacement} : {erreur['msg']}"


def valider_table(table: pd.DataFrame) -> None:
    """Vérifie chaque ligne de la table nettoyée.

    Lève ``ValueError`` en citant les premières lignes fautives.
    """
    # Un TypeAdapter valide toute la liste en une fois, bien plus vite qu'une boucle Python.
    validateur = TypeAdapter(list[LigneNettoyee])
    try:
        validateur.validate_python(table.to_dict(orient="records"))
    except ValidationError as erreurs:
        premieres = erreurs.errors()[:NOMBRE_ERREURS_AFFICHEES]
        details = "\n".join(decrire_erreur(erreur) for erreur in premieres)
        raise ValueError(
            f"{erreurs.error_count()} erreur(s) dans les données nettoyées :\n{details}"
        ) from erreurs
