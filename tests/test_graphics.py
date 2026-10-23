"""Tests unitaires des composants graphiques du dashboard."""

import pandas as pd
import pytest
import plotly.graph_objects as go

import config
from src.components import carte
from src.components import histogramme
from src.components import nuage


# ---------------------------------------------------------
# 1. Données fictives utilisées dans les tests
# ---------------------------------------------------------


@pytest.fixture
def donnees_carte(monkeypatch):
    """Prépare des données fictives et un petit fond de carte."""

    codes = [
        "200000001",
        "200000002",
        "200000003",
    ]

    valeurs = pd.Series(
        [10.0, 15.0, 20.0],
        index=codes,
    )

    noms = pd.Series(
        ["EPCI A", "EPCI B", "EPCI C"],
        index=codes,
    )

    fond_carte = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"code": "200000001"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [2.0, 48.0],
                            [2.1, 48.0],
                            [2.1, 48.1],
                            [2.0, 48.0],
                        ]
                    ],
                },
            }
        ],
    }

    monkeypatch.setattr(
        carte,
        "charger_fond_carte",
        lambda: fond_carte,
    )

    return valeurs, noms


@pytest.fixture
def donnees_nuage():
    """Prépare un tableau fictif pour le nuage de points."""

    return pd.DataFrame(
        {
            "libgeo": [
                "EPCI A",
                "EPCI B",
                "EPCI C",
                "EPCI D",
            ],
            "part_75_plus": [
                10.0,
                15.0,
                20.0,
                25.0,
            ],
            "part_75_seuls": [
                5.0,
                10.0,
                15.0,
                20.0,
            ],
            "taux_pauvrete": [
                12.0,
                18.0,
                22.0,
                30.0,
            ],
            "apl_medecins": [
                2.0,
                3.0,
                4.0,
                5.0,
            ],
        }
    )


# ---------------------------------------------------------
# 2. Tests de texte_survol()
# ---------------------------------------------------------


def test_texte_survol():
    """Vérifie le contenu de l'infobulle de la carte."""

    resultat = carte.texte_survol("Population âgée")

    assert "%{text}" in resultat
    assert "Population âgée" in resultat
    assert "%{z:.1f}" in resultat


def test_texte_survol_format():
    """Vérifie le format HTML de l'infobulle."""

    resultat = carte.texte_survol("Taux de pauvreté")

    assert resultat.startswith("<b>")
    assert "<br>" in resultat
    assert "<extra></extra>" in resultat


# ---------------------------------------------------------
# 3. Tests de creer_carte()
# ---------------------------------------------------------


def test_creer_carte_type(donnees_carte):
    """Vérifie que la carte est une figure Plotly."""

    valeurs, noms = donnees_carte

    figure = carte.creer_carte(
        valeurs,
        noms,
        config.INDICATEURS["part_75_plus"],
        (0.0, 30.0),
        "Carte de test",
    )

    assert isinstance(figure, go.Figure)
    assert len(figure.data) == 1
    assert figure.data[0].type == "choroplethmap"


def test_creer_carte_codes_epci(donnees_carte):
    """Vérifie que les codes des EPCI sont transmis à la carte."""

    valeurs, noms = donnees_carte

    figure = carte.creer_carte(
        valeurs,
        noms,
        config.INDICATEURS["part_75_plus"],
        (0.0, 30.0),
        "Carte de test",
    )

    assert list(figure.data[0].locations) == [
        "200000001",
        "200000002",
        "200000003",
    ]


def test_creer_carte_valeurs(donnees_carte):
    """Vérifie les valeurs associées aux territoires."""

    valeurs, noms = donnees_carte

    figure = carte.creer_carte(
        valeurs,
        noms,
        config.INDICATEURS["part_75_plus"],
        (0.0, 30.0),
        "Carte de test",
    )

    assert list(figure.data[0].z) == [
        10.0,
        15.0,
        20.0,
    ]


def test_creer_carte_noms(donnees_carte):
    """Vérifie les noms affichés au survol de la carte."""

    valeurs, noms = donnees_carte

    figure = carte.creer_carte(
        valeurs,
        noms,
        config.INDICATEURS["part_75_plus"],
        (0.0, 30.0),
        "Carte de test",
    )

    assert list(figure.data[0].text) == [
        "EPCI A",
        "EPCI B",
        "EPCI C",
    ]


def test_creer_carte_bornes(donnees_carte):
    """Vérifie les limites de l'échelle de couleurs."""

    valeurs, noms = donnees_carte

    figure = carte.creer_carte(
        valeurs,
        noms,
        config.INDICATEURS["part_75_plus"],
        (5.0, 25.0),
        "Carte de test",
    )

    assert figure.data[0].zmin == 5.0
    assert figure.data[0].zmax == 25.0


def test_creer_carte_titre(donnees_carte):
    """Vérifie le titre et la hauteur de la carte."""

    valeurs, noms = donnees_carte

    figure = carte.creer_carte(
        valeurs,
        noms,
        config.INDICATEURS["part_75_plus"],
        (0.0, 30.0),
        "Ma carte",
    )

    assert figure.layout.title.text == "Ma carte"
    assert figure.layout.height == config.HAUTEUR_GRAPHIQUE


def test_creer_carte_valeur_manquante(donnees_carte):
    """Vérifie le traitement d'une valeur manquante."""

    valeurs, noms = donnees_carte

    valeurs.iloc[1] = float("nan")

    figure = carte.creer_carte(
        valeurs,
        noms,
        config.INDICATEURS["part_75_plus"],
        (0.0, 30.0),
        "Carte de test",
    )

    assert list(figure.data[0].z) == [
        10.0,
        None,
        20.0,
    ]


def test_creer_carte_configuration(donnees_carte):
    """Vérifie les paramètres de navigation sur la carte."""

    valeurs, noms = donnees_carte

    figure = carte.creer_carte(
        valeurs,
        noms,
        config.INDICATEURS["part_75_plus"],
        (0.0, 30.0),
        "Carte de test",
    )

    assert figure.layout.map.style == config.STYLE_CARTE
    assert figure.layout.map.zoom == config.ZOOM_CARTE
    assert figure.layout.uirevision == "carte"


# ---------------------------------------------------------
# 4. Tests de creer_histogramme()
# ---------------------------------------------------------


def test_creer_histogramme_type():
    """Vérifie que l'histogramme est une figure Plotly."""

    valeurs = pd.Series([10.0, 15.0, 20.0])

    figure = histogramme.creer_histogramme(
        valeurs,
        config.INDICATEURS["part_75_plus"],
        (0.0, 30.0),
        "Histogramme de test",
    )

    assert isinstance(figure, go.Figure)
    assert len(figure.data) == 1
    assert figure.data[0].type == "histogram"


def test_creer_histogramme_valeurs():
    """Vérifie les données utilisées pour les barres."""

    valeurs = pd.Series([10.0, 15.0, 20.0])

    figure = histogramme.creer_histogramme(
        valeurs,
        config.INDICATEURS["part_75_plus"],
        (0.0, 30.0),
        "Histogramme de test",
    )

    assert list(figure.data[0].x) == [
        10.0,
        15.0,
        20.0,
    ]


def test_creer_histogramme_largeur_classes():
    """Vérifie la largeur des tranches de l'histogramme."""

    valeurs = pd.Series([10.0, 15.0, 20.0])

    indicateur = config.INDICATEURS["part_75_plus"]

    figure = histogramme.creer_histogramme(
        valeurs,
        indicateur,
        (0.0, 30.0),
        "Histogramme de test",
    )

    assert figure.data[0].xbins.size == indicateur.largeur_classe


def test_creer_histogramme_bornes():
    """Vérifie les limites de l'axe horizontal."""

    valeurs = pd.Series([10.0, 15.0, 20.0])

    figure = histogramme.creer_histogramme(
        valeurs,
        config.INDICATEURS["part_75_plus"],
        (0.0, 30.0),
        "Histogramme de test",
    )

    assert list(figure.layout.xaxis.range) == [
        0.0,
        30.0,
    ]

    assert figure.data[0].xbins.end == 30.0


def test_creer_histogramme_titre():
    """Vérifie le titre du graphique."""

    valeurs = pd.Series([10.0, 15.0, 20.0])

    figure = histogramme.creer_histogramme(
        valeurs,
        config.INDICATEURS["part_75_plus"],
        (0.0, 30.0),
        "Répartition des EPCI",
    )

    assert figure.layout.title.text == "Répartition des EPCI"


def test_creer_histogramme_valeur_manquante():
    """Vérifie que les valeurs manquantes sont conservées comme None."""

    valeurs = pd.Series([
        10.0,
        float("nan"),
        20.0,
    ])

    figure = histogramme.creer_histogramme(
        valeurs,
        config.INDICATEURS["part_75_plus"],
        (0.0, 30.0),
        "Histogramme de test",
    )

    assert list(figure.data[0].x) == [
        10.0,
        None,
        20.0,
    ]


def test_creer_histogramme_mediane():
    """Vérifie la présence de la ligne verticale de médiane."""

    valeurs = pd.Series([10.0, 15.0, 20.0])

    figure = histogramme.creer_histogramme(
        valeurs,
        config.INDICATEURS["part_75_plus"],
        (0.0, 30.0),
        "Histogramme de test",
    )

    assert len(figure.layout.shapes) >= 1

    ligne = figure.layout.shapes[0]

    assert ligne.x0 == pytest.approx(15.0)
    assert ligne.x1 == pytest.approx(15.0)


def test_creer_histogramme_infobulle():
    """Vérifie les informations affichées au survol."""

    valeurs = pd.Series([10.0, 15.0, 20.0])

    figure = histogramme.creer_histogramme(
        valeurs,
        config.INDICATEURS["part_75_plus"],
        (0.0, 30.0),
        "Histogramme de test",
    )

    assert "intercommunalités" in figure.data[0].hovertemplate


def test_creer_histogramme_interactions():
    """Vérifie la configuration des interactions du graphique."""

    valeurs = pd.Series([10.0, 15.0, 20.0])

    figure = histogramme.creer_histogramme(
        valeurs,
        config.INDICATEURS["part_75_plus"],
        (0.0, 30.0),
        "Histogramme de test",
    )

    assert figure.layout.dragmode is False
    assert figure.layout.height == config.HAUTEUR_GRAPHIQUE


# ---------------------------------------------------------
# 5. Tests de echelle_couleurs()
# ---------------------------------------------------------


def test_echelle_couleurs_normale():
    """Vérifie l'échelle lorsque les couleurs ne sont pas inversées."""

    code = next(
        nom
        for nom, indicateur in config.INDICATEURS.items()
        if not indicateur.echelle_inversee
    )

    resultat = nuage.echelle_couleurs(code)

    assert resultat == config.ECHELLE_COULEURS


def test_echelle_couleurs_inversee():
    """Vérifie l'inversion des couleurs pour un indicateur concerné."""

    code = next(
        nom
        for nom, indicateur in config.INDICATEURS.items()
        if indicateur.echelle_inversee
    )

    resultat = nuage.echelle_couleurs(code)

    assert resultat == f"{config.ECHELLE_COULEURS}_r"


# ---------------------------------------------------------
# 6. Tests de creer_nuage()
# ---------------------------------------------------------


def test_creer_nuage_type(donnees_nuage):
    """Vérifie que le nuage de points est une figure Plotly."""

    figure = nuage.creer_nuage(
        donnees_nuage,
        "part_75_plus",
        "taux_pauvrete",
        None,
    )

    assert isinstance(figure, go.Figure)


def test_creer_nuage_nombre_points(donnees_nuage):
    """Vérifie qu'un point représente un EPCI."""

    figure = nuage.creer_nuage(
        donnees_nuage,
        "part_75_plus",
        "taux_pauvrete",
        None,
    )

    assert len(figure.data) == 1
    assert len(figure.data[0].x) == 4
    assert len(figure.data[0].y) == 4


def test_creer_nuage_valeurs(donnees_nuage):
    """Vérifie les coordonnées des points du nuage."""

    figure = nuage.creer_nuage(
        donnees_nuage,
        "part_75_plus",
        "taux_pauvrete",
        None,
    )

    assert list(figure.data[0].x) == [
        10.0,
        15.0,
        20.0,
        25.0,
    ]

    assert list(figure.data[0].y) == [
        12.0,
        18.0,
        22.0,
        30.0,
    ]


def test_creer_nuage_valeurs_manquantes(donnees_nuage):
    """Vérifie qu'un EPCI incomplet n'apparaît pas."""

    donnees_nuage.loc[0, "taux_pauvrete"] = float("nan")

    figure = nuage.creer_nuage(
        donnees_nuage,
        "part_75_plus",
        "taux_pauvrete",
        None,
    )

    assert len(figure.data[0].x) == 3
    assert len(figure.data[0].y) == 3


def test_creer_nuage_sans_couleur(donnees_nuage):
    """Vérifie l'utilisation d'une couleur unique."""

    figure = nuage.creer_nuage(
        donnees_nuage,
        "part_75_plus",
        "taux_pauvrete",
        None,
    )

    assert figure.data[0].marker.color == (
        config.COULEUR_HISTOGRAMME
    )


def test_creer_nuage_avec_couleur(donnees_nuage):
    """Vérifie qu'un troisième indicateur colore les points."""

    figure = nuage.creer_nuage(
        donnees_nuage,
        "part_75_plus",
        "taux_pauvrete",
        "part_75_seuls",
    )

    assert len(figure.data) == 1

    assert list(figure.data[0].marker.color) == [
        5.0,
        10.0,
        15.0,
        20.0,
    ]


def test_creer_nuage_couleur_manquante(donnees_nuage):
    """Vérifie qu'un EPCI sans couleur est exclu."""

    donnees_nuage.loc[1, "part_75_seuls"] = float("nan")

    figure = nuage.creer_nuage(
        donnees_nuage,
        "part_75_plus",
        "taux_pauvrete",
        "part_75_seuls",
    )

    assert len(figure.data[0].x) == 3


def test_creer_nuage_titre(donnees_nuage):
    """Vérifie la construction du titre du nuage de points."""

    figure = nuage.creer_nuage(
        donnees_nuage,
        "part_75_plus",
        "taux_pauvrete",
        None,
    )

    attendu = (
        f"{config.INDICATEURS['taux_pauvrete'].nom} selon "
        f"{config.INDICATEURS['part_75_plus'].nom_en_phrase}"
    )

    assert figure.layout.title.text == attendu


def test_creer_nuage_noms_axes(donnees_nuage):
    """Vérifie les libellés affichés sur les axes."""

    figure = nuage.creer_nuage(
        donnees_nuage,
        "part_75_plus",
        "taux_pauvrete",
        None,
    )

    assert figure.layout.xaxis.title.text == (
        config.INDICATEURS["part_75_plus"].libelle
    )

    assert figure.layout.yaxis.title.text == (
        config.INDICATEURS["taux_pauvrete"].libelle
    )


def test_creer_nuage_hauteur(donnees_nuage):
    """Vérifie la hauteur et le style du nuage de points."""

    figure = nuage.creer_nuage(
        donnees_nuage,
        "part_75_plus",
        "taux_pauvrete",
        None,
    )

    assert figure.layout.height == config.HAUTEUR_GRAPHIQUE

    assert figure.data[0].marker.size == 7
    assert figure.data[0].marker.opacity == 0.8