"""Page « Accueil » : la question posée, les chiffres clés et les principales conclusions."""

from dash import dcc, html

import config
from src.utils.common_functions import (
    annees_disponibles,
    formater_valeur,
    noms_epci,
    tableau_comparaison,
    valeurs_par_annee,
)

# Principaux enseignements du rapport d'analyse, repris en version courte.
CONCLUSIONS = [
    (
        "La France vieillit, surtout au centre et au sud-ouest.",
        "La part des 75 ans et plus a doublé depuis 1968. Le vieillissement dessine une "
        "diagonale du Centre et du Limousin vers le Sud-Ouest, déjà visible en 1968.",
    ),
    (
        "Les territoires âgés sont plus souvent pauvres.",
        "C'est le seul lien net entre les indicateurs (corrélation de {correlation}), "
        "mais à âge égal, la pauvreté varie beaucoup d'un territoire à l'autre.",
    ),
    (
        "L'isolement et l'accès aux médecins suivent leur propre géographie.",
        "Ils ne dépendent pas du vieillissement : l'isolement est plus marqué au nord et à "
        "l'est, et les déserts médicaux se situent surtout au centre du Bassin parisien.",
    ),
    (
        "Les situations les plus fragiles cumulent ces difficultés.",
        "Ce sont surtout des territoires ruraux du centre de la France, du Massif central "
        "et du Sud-Ouest, à la fois âgés, pauvres et mal dotés en médecins.",
    ),
]


def moyenne_derniere_annee(nom_indicateur: str) -> float:
    """Renvoie la moyenne d'un indicateur sur les EPCI, pour sa dernière année disponible."""
    return float(
        valeurs_par_annee(nom_indicateur)[annees_disponibles(nom_indicateur)[-1]].mean()
    )


def creer_carte_chiffre(valeur: str, texte: str) -> html.Div:
    """Construit une carte de chiffre clé : une valeur mise en avant et sa légende."""
    return html.Div(
        [
            html.Div(valeur, className="chiffre-valeur"),
            html.Div(texte, className="chiffre-texte"),
        ],
        className="bloc chiffre",
    )


def creer_chiffres_cles() -> html.Div:
    """Construit les chiffres clés, calculés à partir de la base de données."""
    vieillissement = valeurs_par_annee("part_75_plus")
    annees = annees_disponibles("part_75_plus")
    debut = formater_valeur(float(vieillissement[annees[0]].mean()), " %")
    fin = formater_valeur(float(vieillissement[annees[-1]].mean()), " %")
    nombre_epci = f"{len(noms_epci()):,}".replace(",", " ")
    return html.Div(
        [
            creer_carte_chiffre(
                nombre_epci, "intercommunalités de France métropolitaine"
            ),
            creer_carte_chiffre(
                f"{debut} → {fin}",
                f"de 75 ans et plus en moyenne, de {annees[0]} à {annees[-1]}",
            ),
            creer_carte_chiffre(
                formater_valeur(moyenne_derniere_annee("part_75_seuls"), " %"),
                "des 75 ans et plus vivent seuls, en moyenne",
            ),
            creer_carte_chiffre(
                formater_valeur(moyenne_derniere_annee("taux_pauvrete"), " %"),
                "de taux de pauvreté moyen",
            ),
            creer_carte_chiffre(
                formater_valeur(moyenne_derniere_annee("apl_medecins"), ""),
                "consultations de médecin généraliste accessibles par an et par habitant",
            ),
        ],
        className="chiffres",
    )


def creer_conclusions() -> html.Div:
    """Construit la liste des principales conclusions, avec la corrélation calculée."""
    tableau = tableau_comparaison()
    correlation = float(tableau["part_75_plus"].corr(tableau["taux_pauvrete"]))
    correlation_texte = f"{correlation:.2f}".replace(".", ",")
    return html.Div(
        [
            html.H2("Ce que montrent les données"),
            html.Ul(
                [
                    html.Li(
                        [
                            html.Strong(titre),
                            " ",
                            texte.format(correlation=correlation_texte),
                        ]
                    )
                    for titre, texte in CONCLUSIONS
                ],
                className="conclusions",
            ),
        ],
        className="bloc",
    )


def creer_liens() -> html.Div:
    """Construit les liens vers les pages d'exploration, avec une phrase pour chacune."""
    return html.Div(
        [
            html.Div(
                [
                    dcc.Link(
                        "Explorer un indicateur",
                        href="/explorer",
                        className="bouton-lien",
                    ),
                    html.P(
                        "Une carte et un histogramme par indicateur, avec l'évolution "
                        "depuis 1968.",
                        className="note",
                    ),
                ],
                className="bloc lien-page",
            ),
            html.Div(
                [
                    dcc.Link(
                        "Comparer les indicateurs",
                        href="/comparer",
                        className="bouton-lien",
                    ),
                    html.P(
                        "Les liens entre vieillissement, isolement, pauvreté et accès aux "
                        "médecins.",
                        className="note",
                    ),
                ],
                className="bloc lien-page",
            ),
        ],
        className="liens-pages",
    )


def creer_mise_en_page() -> html.Div:
    """Construit la page d'accueil : question, chiffres clés, conclusions et liens."""
    return html.Div(
        [
            html.Div(
                [
                    html.H1(config.TITRE_DASHBOARD),
                    html.P(
                        "Les personnes âgées sont plus exposées à l'isolement, à la précarité "
                        "et aux difficultés d'accès aux soins. Ce dashboard cherche les "
                        "territoires où ces fragilités se concentrent, à partir de quatre "
                        "indicateurs publics calculés pour chaque intercommunalité."
                    ),
                ],
                className="entete",
            ),
            creer_chiffres_cles(),
            creer_conclusions(),
            creer_liens(),
            html.P(
                "Sources : Insee (recensements de la population, Filosofi) et DREES, via "
                "l'Observatoire des territoires. Contours des intercommunalités : data.gouv.fr.",
                className="pied",
            ),
        ],
        className="page",
    )
