from collections.abc import Iterable
from typing import Optional, Union, List
from hestia_earth.schema import EmissionMethodTier, SchemaType, TermTermType
from hestia_earth.utils.model import linked_node, find_term_match
from hestia_earth.utils.emission import (
    cycle_emissions_in_system_boundary,
    emissions_in_system_boundary,
)
from hestia_earth.utils.term import download_term
from hestia_earth.utils.blank_node import get_node_value

from . import flatten_args, set_node_value, set_node_stats, set_node_term
from .method import include_methodModel
from .constant import Units, get_atomic_conversion

EMISSION_METHOD_TIERS = [e.value for e in EmissionMethodTier]


def _new_emission(
    term: Union[dict, str],
    value: List[Optional[float]] = None,
    sd: float = None,
    min: float = None,
    max: float = None,
    model: Optional[Union[dict, str]] = None,
    country_id: str = None,
    key_id: str = None,
):
    return set_node_stats(
        include_methodModel(
            {
                "@type": SchemaType.EMISSION.value,
                "term": linked_node(
                    term if isinstance(term, dict) else download_term(term)
                ),
            },
            model,
        )
        | set_node_value("value", value, is_list=True)
        | (set_node_value("sd", sd, is_list=True) if sd is not None else {})
        | set_node_value("min", min, is_list=True)
        | set_node_value("max", max, is_list=True)
        | set_node_term("country", country_id, TermTermType.REGION)
        | set_node_term("key", key_id)
    )


def get_emission_to_N(cycle: dict, term_id: str):
    emission = find_term_match(cycle.get("emissions", []), term_id, None)
    units = (emission or {}).get("term", {}).get("units")
    value = get_node_value(emission) if emission else None
    return None if value is None else value / get_atomic_conversion(units, Units.TO_N)


def get_emissions_to_N(cycle: dict, emission_ids: List[str]):
    return [get_emission_to_N(cycle, term_id) for term_id in emission_ids]


_EMISSION_METHOD_TIER_RANKING = [
    EmissionMethodTier.MEASURED,
    EmissionMethodTier.TIER_3,
    EmissionMethodTier.TIER_2,
    EmissionMethodTier.TIER_1,
    EmissionMethodTier.BACKGROUND,
    EmissionMethodTier.NOT_RELEVANT,
]
"""
A ranking of `EmissionMethodTier`s from strongest to weakest.
"""


_EmissionMethodTiers = Union[
    EmissionMethodTier, str, Iterable[Union[EmissionMethodTier, str]]
]
"""
A type alias for a single emission method tier, as either an EmissionMethodTier enum or string, or multiple emission
method tiers, as either an iterable of EmissionMethodTier enums or strings.
"""


def min_emission_method_tier(*methods: _EmissionMethodTiers) -> EmissionMethodTier:
    """
    Get the minimum ranking emission method tier from the provided methods.

    n.b., `max` function is used as weaker methods have higher indices.

    Parameters
    ----------
    *methods : EmissionMethodTier | str | Iterable[EmissionMethodTier] | Iterable[str]
        Emission method tiers or iterables of emission method tiers.

    Returns
    -------
    EmissionMethodTier
        The emission method tier method with the minimum ranking.
    """
    methods_ = [to_emission_method_tier(arg) for arg in flatten_args(methods)]
    return max(
        methods_,
        key=lambda method: _EMISSION_METHOD_TIER_RANKING.index(method),
        default=_EMISSION_METHOD_TIER_RANKING[-1],
    )


def to_emission_method_tier(
    method: Union[EmissionMethodTier, str],
) -> Optional[EmissionMethodTier]:
    """
    Convert the input str to an `EmissionMethodTier` if possible.

    Parameters
    ----------
    method : EmissionMethodTier | str
        The emission method tier as either a `str` or `EmissionMethodTier`.

    Returns
    -------
    EmissionMethodTier | None
        The matching `EmissionMethodTier` or `None` if invalid string.
    """
    return (
        method
        if isinstance(method, EmissionMethodTier)
        else EmissionMethodTier(method) if method in EMISSION_METHOD_TIERS else None
    )


def filter_emission_inputs(emission: dict, term_type: TermTermType):
    inputs = emission.get("inputs", [])
    return [i for i in inputs if i.get("termType") == term_type.value]


def background_emissions_in_system_boundary(
    node: dict, term_type: TermTermType = TermTermType.EMISSION
):
    term_ids = (
        cycle_emissions_in_system_boundary(node, term_type)
        if term_type == TermTermType.EMISSION
        else emissions_in_system_boundary(term_type)
    )
    return [id for id in term_ids if "InputsProduction" in id]
