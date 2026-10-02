"""Paramètres de configuration du projet : sources de données, chemins et libellés."""

from pathlib import Path

# --- Chemins -----------------------------------------------------------------
RACINE = Path(__file__).resolve().parent
DOSSIER_DONNEES = RACINE / "data"
DOSSIER_BRUT = DOSSIER_DONNEES / "raw"
BASE_SQLITE = DOSSIER_DONNEES / "db.sqlite"
FOND_CARTE_BRUT = DOSSIER_BRUT / "epci.geojson"
FOND_CARTE = DOSSIER_DONNEES / "epci_metropole.geojson"

TABLE_BRUTE = "raw"
TABLE_NETTOYEE = "cleaned"

# --- Sources -----------------------------------------------------------------
# Tous les indicateurs de l'Observatoire des territoires suivent le même modèle d'adresse.
API_OBSERVATOIRE = (
    "https://www.observatoire-des-territoires.gouv.fr/outils/cartographie-interactive/"
    "api/v1/functions/GC_API_download.php"
    "?type=stat&nivgeo={niveau}&dataset={base}&indic={indicateur}"
)
NIVEAU_GEOGRAPHIQUE = "epci2025"

# Code de l'indicateur -> base de données d'origine dans l'API de l'Observatoire.
SOURCES_OBSERVATOIRE: dict[str, str] = {
    "part_pop75p": "insee_rp_hist_1968",  # part des 75 ans et plus (Insee, recensement)
    "pop75p": "insee_rp_hist_1968",  # nombre de 75 ans et plus (Insee, recensement)
    "nb_persseul75": "indic_sex_rp",  # 75 ans et plus vivant seuls (Insee, recensement)
    "tx_pauv_60": "filosofi",  # taux de pauvreté au seuil de 60 % (Insee, Filosofi)
    "apl_mg_hmep": "apl",  # accessibilité aux médecins généralistes (DREES)
}

# Contours des EPCI 2025, simplifiés à 100 m (data.gouv.fr, Contours administratifs).
URL_FOND_CARTE = (
    "https://object.data.gouv.fr/contours-administratifs/2025/geojson/epci-100m.geojson"
)

# Certains serveurs refusent les requêtes qui ne s'identifient pas.
EN_TETES_HTTP = {"User-Agent": "Mozilla/5.0 (projet etudiant ESIEE)"}
DELAI_MAX_SECONDES = 120

# --- Lecture des classeurs de l'Observatoire ---------------------------------
FEUILLE_DONNEES = "Data"
LIGNES_AVANT_EN_TETE = 4  # les titres de colonnes sont sur la cinquième ligne
CODE_SEXE_TOTAL = "T"  # modalité « ensemble » des indicateurs détaillés par sexe

# --- Périmètre de l'étude ----------------------------------------------------
# Rectangle (longitude min, latitude min, longitude max, latitude max) englobant la
# France métropolitaine, Corse comprise. L'outre-mer est exclu : ses données sont incomplètes.
EMPRISE_METROPOLE = (-5.5, 41.0, 10.0, 51.5)

# --- Indicateurs du dashboard ------------------------------------------------
# Nom de l'indicateur dans la table nettoyée -> libellé affiché dans les graphiques.
INDICATEURS: dict[str, str] = {
    "part_75_plus": "Part des 75 ans et plus (%)",
    "part_75_seuls": "Part des 75 ans et plus vivant seuls (%)",
    "taux_pauvrete": "Taux de pauvreté (%)",
    "apl_medecins": "Accessibilité aux médecins généralistes (consultations/an/habitant)",
}
