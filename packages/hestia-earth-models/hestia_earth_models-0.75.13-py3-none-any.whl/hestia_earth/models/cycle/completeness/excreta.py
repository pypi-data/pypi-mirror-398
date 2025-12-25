from functools import reduce
from hestia_earth.schema import SiteSiteType, TermTermType
from hestia_earth.utils.model import filter_list_term_type
from hestia_earth.utils.tools import list_sum
from hestia_earth.utils.blank_node import get_node_value, get_lookup_value

from hestia_earth.models.log import logRequirements, log_as_table
from . import MODEL

REQUIREMENTS = {"Cycle": {"completeness.excreta": "False"}}
RETURNS = {"Completeness": {"excreta": ""}}
LOOKUPS = {
    "animalProduct": [
        "excretaKgMassTermIds",
        "excretaKgNTermIds",
        "excretaKgVsTermIds",
    ],
    "liveAnimal": ["excretaKgMassTermIds", "excretaKgNTermIds", "excretaKgVsTermIds"],
    "liveAquaticSpecies": [
        "excretaKgMassTermIds",
        "excretaKgNTermIds",
        "excretaKgVsTermIds",
    ],
}
MODEL_KEY = "excreta"

_NO_EXCRETA_SITE_TYPES = [
    SiteSiteType.CROPLAND.value,
    SiteSiteType.GLASS_OR_HIGH_ACCESSIBLE_COVER.value,
    SiteSiteType.FOOD_RETAILER.value,
    SiteSiteType.AGRI_FOOD_PROCESSOR.value,
]
_EXCRETA_LOOKUPS = LOOKUPS["animalProduct"]
_EXCRETA_ALLOWED_MODELS = [None, "hestia", "pooreNemecek2018"]


def _excreta_product(
    excreta_products_map: dict, product: dict, lookup_column: str
) -> dict:
    term_ids = (get_lookup_value(product, lookup_column) or "").split(";")
    term_ids = [
        term_id.split(":")[1] if ":" in term_id else term_id for term_id in term_ids
    ]
    return next(
        (
            excreta_products_map[term_id]
            for term_id in term_ids
            if term_id in excreta_products_map
        ),
        None,
    )


def _extend_with_excreta_product(
    excreta_products_map: dict, product: dict, lookup_column: str
):
    product = _excreta_product(excreta_products_map, product, lookup_column)
    return (
        {
            f"{lookup_column}-id": product.get("term", {}).get("@id"),
            f"{lookup_column}-model": product.get("model", {}).get("@id"),
        }
        if product
        else {}
    )


def _run_by_excreta_products(cycle: dict):
    animal_products = filter_list_term_type(
        cycle.get("products", []),
        [
            TermTermType.LIVEANIMAL,
            TermTermType.ANIMALPRODUCT,
            TermTermType.LIVEAQUATICSPECIES,
        ],
    )
    excreta_products = filter_list_term_type(
        cycle.get("products", []), TermTermType.EXCRETA
    )
    excreta_products_map = {p.get("term", {}).get("@id"): p for p in excreta_products}

    animal_products_with_excreta = [
        {
            "product": p.get("term", {}).get("@id"),
        }
        | reduce(
            lambda prev, curr: prev
            | _extend_with_excreta_product(excreta_products_map, p, curr),
            _EXCRETA_LOOKUPS,
            {},
        )
        for p in animal_products
    ]
    animal_products_with_excreta = [
        p
        | {
            "valid": all(
                [
                    all(
                        [
                            p.get(f"{lookup}-id"),
                            p.get(f"{lookup}-model") in _EXCRETA_ALLOWED_MODELS,
                        ]
                    )
                    for lookup in _EXCRETA_LOOKUPS
                ]
            )
        }
        for p in animal_products_with_excreta
    ]

    excreta_management = filter_list_term_type(
        cycle.get("practices", []), TermTermType.EXCRETAMANAGEMENT
    )
    total_excreta_management = list_sum(
        [get_node_value(p) for p in excreta_management], default=0
    )

    logRequirements(
        cycle,
        model=MODEL,
        model_key=MODEL_KEY,
        animal_products_with_excreta=log_as_table(animal_products_with_excreta),
        excreta_allowed_models=log_as_table(_EXCRETA_ALLOWED_MODELS),
        sum_excreta_management=total_excreta_management,
    )

    return all(
        [p.get("valid") for p in animal_products_with_excreta]
        + [total_excreta_management == 100]
    )


def run(cycle: dict):
    site_type = cycle.get("site", {}).get("siteType")
    return site_type in _NO_EXCRETA_SITE_TYPES or _run_by_excreta_products(cycle)
