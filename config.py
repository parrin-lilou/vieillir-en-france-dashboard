"""Paramètres de configuration du projet : sources de données, chemins et libellés."""

from dataclasses import dataclass
from pathlib import Path

# --- Chemins -----------------------------------------------------------------
RACINE = Path(__file__).resolve().parent
DOSSIER_DONNEES = RACINE / "data"
DOSSIER_BRUT = DOSSIER_DONNEES / "raw"
BASE_SQLITE = DOSSIER_DONNEES / "db.sqlite"
FOND_CARTE_BRUT = DOSSIER_BRUT / "epci.geojson"
DOSSIER_NETTOYE = DOSSIER_DONNEES / "cleaned"
FOND_CARTE = DOSSIER_NETTOYE / "epci_metropole.geojson"

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
@dataclass(frozen=True)
class Indicateur:
    """Description d'un indicateur affiché dans le dashboard."""

    nom: str  # nom complet, utilisé dans les titres et les menus
    nom_court: str  # nom abrégé, utilisé là où la place manque (matrice de corrélation)
    nom_en_phrase: str  # nom précédé de son article, pour les phrases générées
    libelle: str  # nom avec unité, utilisé sur les axes et la légende
    unite: str  # texte ajouté après une valeur (" %", " consultations")
    largeur_classe: float  # largeur des tranches de l'histogramme
    echelle_inversee: bool = False  # True si une valeur basse est défavorable

    @property
    def lecture(self) -> str:
        """Renvoie la phrase qui explique comment lire les couleurs de la carte."""
        sens = "basses" if self.echelle_inversee else "élevées"
        phrase = (
            f"le foncé signale les valeurs les plus {sens} pour {self.nom_en_phrase}"
        )
        if self.echelle_inversee:
            phrase += " (échelle inversée par rapport aux autres indicateurs)"
        return phrase + "."


# Nom de l'indicateur dans la table nettoyée -> sa description.
INDICATEURS: dict[str, Indicateur] = {
    "part_75_plus": Indicateur(
        nom="Part des 75 ans et plus",
        nom_court="75 ans et plus",
        nom_en_phrase="la part des 75 ans et plus",
        libelle="Part des 75 ans et plus (%)",
        unite=" %",
        largeur_classe=1.0,
    ),
    "part_75_seuls": Indicateur(
        nom="Part des 75 ans et plus vivant seuls",
        nom_court="75 ans et plus seuls",
        nom_en_phrase="la part des 75 ans et plus vivant seuls",
        libelle="Part des 75 ans et plus vivant seuls (%)",
        unite=" %",
        largeur_classe=1.0,
    ),
    "taux_pauvrete": Indicateur(
        nom="Taux de pauvreté",
        nom_court="Pauvreté",
        nom_en_phrase="le taux de pauvreté",
        libelle="Taux de pauvreté (%)",
        unite=" %",
        largeur_classe=1.0,
    ),
    "apl_medecins": Indicateur(
        nom="Accessibilité aux médecins généralistes",
        nom_court="Accès aux médecins",
        nom_en_phrase="l'accessibilité aux médecins généralistes",
        libelle="Consultations accessibles par an et par habitant",
        unite=" consultations",
        largeur_classe=0.25,
        # Peu de consultations accessibles = territoire plus fragile : le foncé doit
        # toujours signaler la fragilité, donc l'échelle de couleurs est retournée.
        echelle_inversee=True,
    ),
}
INDICATEUR_PAR_DEFAUT = "part_75_plus"

# Choix affichés à l'ouverture de la page « Comparer » : l'âge face à la pauvreté,
# les points étant coloriés selon l'isolement.
COMPARAISON_PAR_DEFAUT = {
    "x": "part_75_plus",
    "y": "taux_pauvrete",
    "couleur": "part_75_seuls",
}
SANS_COULEUR = "aucune"  # valeur du menu « couleur » qui désactive le coloriage

# --- Dashboard ---------------------------------------------------------------
NOM_DASHBOARD = "Vieillir en France"
# Pages du dashboard : adresse -> texte du lien dans la barre de navigation.
NAVIGATION = {"/explorer": "Explorer", "/comparer": "Comparer"}
PAGE_PAR_DEFAUT = "/explorer"  # page affichée à l'adresse racine « / »
TITRE_DASHBOARD = "Vieillir en France : où sont les territoires fragiles ?"
HOTE = "127.0.0.1"
PORT = 8050
MODE_DEBUG = False

# Fond de carte sans tuiles : la carte s'affiche même sans connexion internet.
STYLE_CARTE = "white-bg"
# Cadrage de la carte : la France entière tient dans la hauteur des graphiques.
# Un zoom plus grand rapproche la carte (ajuster par pas de 0,1).
CENTRE_CARTE = {"lat": 46.45, "lon": 2.4}
ZOOM_CARTE = 4.3
HAUTEUR_GRAPHIQUE = 470
# Durée d'affichage de chaque année pendant l'animation, en millisecondes.
INTERVALLE_ANIMATION_MS = 1500
# Même marge haute pour tous les graphiques, afin que leurs titres soient alignés.
MARGE_HAUTE_GRAPHIQUE = 50
# Écriture française des nombres : virgule décimale, espace pour les milliers.
SEPARATEURS_NOMBRES = ", "
ECHELLE_COULEURS = "YlOrRd"
# Couleur d'accent, reprise dans assets/style.css pour le curseur et le menu.
COULEUR_HISTOGRAMME = "#b23a0a"
# Texte des graphiques, accordé à celui de la page.
POLICE_GRAPHIQUES = {
    "family": 'system-ui, -apple-system, "Segoe UI", sans-serif',
    "color": "#1f2933",
}
# Aspect des éléments non concernés quand une tranche est sélectionnée par un clic.
COULEUR_BARRE_ESTOMPEE = "#d5d5d5"
OPACITE_EPCI_ESTOMPE = 0.12
# Échelle divergente pour les corrélations : bleu si négative, rouge si positive.
ECHELLE_CORRELATION = "RdBu_r"
