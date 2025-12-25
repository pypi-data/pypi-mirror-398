import os
from functools import lru_cache
from hestia_earth.schema import TermTermType
from hestia_earth.utils.lookup import download_lookup, get_table_value
from hestia_earth.utils.tools import non_empty_list, safe_parse_float, omit

from hestia_earth.models.utils.term import get_lookup_value
from hestia_earth.models.utils.background_emissions import convert_background_lookup

_LOOKUP_INDEX_KEY = "ecoalimMappingName"


def get_input_mappings(model: str, input: dict):
    term = input.get("term", {})
    term_id = term.get("@id")
    value = get_lookup_value(term, "ecoalimMapping", model=model, term=term_id)
    mappings = non_empty_list(value.split(";")) if value else []
    return [(m.split(":")[0], m.split(":")[1]) for m in mappings]


def extract_input_mapping(mapping: tuple, term_type: TermTermType):
    gadm_id, mapping_name = mapping
    # # all countries have the same coefficient
    coefficient = 1
    values = ecoalim_values(mapping_name, term_type)
    return values, coefficient


@lru_cache()
def _build_lookup(term_type: str):
    lookup = download_lookup(f"ecoalim-{term_type}.csv", keep_in_memory=False)
    return convert_background_lookup(lookup=lookup, index_column=_LOOKUP_INDEX_KEY)


@lru_cache()
def ecoalim_values(mapping: str, term_type: TermTermType):
    data = _build_lookup(term_type.value)
    return list(data[mapping].items())


CUTOFF_KEY = "cutoff_coeff"
_CUTOFF_MAX_PERCENTAGE = int(os.getenv("ECOALIM_CUTOFF_MAX_PERCENT", "99"))


def get_cutoff_lookup(term_type: TermTermType):
    filename = f"ecoalim-{term_type.value}-cutoff.csv"
    return (
        download_lookup(filename, keep_in_memory=False)
        if _CUTOFF_MAX_PERCENTAGE
        else None
    )


def _cutoff_id(term_id: str, country_id: str = None, key_id: str = None):
    return (
        term_id
        + (f"+inputs[{key_id}]" if key_id else "")
        + (f"+country[{country_id}]" if country_id else "")
    )


def cutoff_value(
    cutoff_lookup, term_id: str, country_id: str = None, key_id: str = None
):
    cutoff_id = _cutoff_id(term_id=term_id, country_id=country_id, key_id=key_id)
    return (
        None
        if cutoff_lookup is None
        else safe_parse_float(
            get_table_value(cutoff_lookup, "term.id", cutoff_id, "percentage"),
            default=None,
        )
    )


def filter_blank_nodes_cutoff(blank_nodes: list):
    # use the generic contibution of the blank node towards EF Score to remove the lowest percentage
    total_contributions = sum([v.get(CUTOFF_KEY, 0) for v in blank_nodes])
    blank_nodes_with_contributions = sorted(
        [(v, v.get(CUTOFF_KEY, 0) * 100 / total_contributions) for v in blank_nodes],
        key=lambda v: v[1],
        reverse=True,
    )

    sum_contributions = 0
    filtered_blank_nodes = []
    for blank_node, contribution in blank_nodes_with_contributions:
        sum_contributions = sum_contributions + contribution
        if sum_contributions > _CUTOFF_MAX_PERCENTAGE:
            break
        filtered_blank_nodes.append(omit(blank_node, [CUTOFF_KEY]))

    return filtered_blank_nodes
