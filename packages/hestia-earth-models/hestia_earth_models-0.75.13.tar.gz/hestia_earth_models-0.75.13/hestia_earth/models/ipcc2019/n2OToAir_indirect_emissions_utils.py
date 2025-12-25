from hestia_earth.schema import EmissionMethodTier, TermTermType
from hestia_earth.utils.lookup import extract_grouped_data
from hestia_earth.utils.tools import (
    safe_parse_float,
    non_empty_list,
    list_sum,
    omit,
    pick,
)
from hestia_earth.utils.model import find_term_match

from hestia_earth.models.log import logRequirements, logShouldRun, log_as_table
from hestia_earth.models.utils import multiply_values
from hestia_earth.models.utils.constant import Units, get_atomic_conversion
from hestia_earth.models.utils.emission import _new_emission, get_emissions_to_N
from hestia_earth.models.utils.cycle import get_ecoClimateZone
from hestia_earth.models.utils.term import get_lookup_value
from .utils import _is_wet
from . import MODEL

_TIER = EmissionMethodTier.TIER_1.value
_EF_4_FACTOR_NAME = "IPCC_2019_EF4_FACTORS"
_EF_5_FACTOR_NAME = "IPCC_2019_EF5_FACTORS"
_INPUTS_GROUP_KEYS = ["inputs", "operation"]


def _get_emission_factors(emission_id: str, ecoClimateZone: str = None):
    is_wet = _is_wet(ecoClimateZone)
    factors_key = "default" if is_wet is None else "wet" if is_wet else "dry"

    emission = {"@id": emission_id, "termType": TermTermType.EMISSION.value}

    # emission either contains EF4 or EF5
    ef4_factor = get_lookup_value(
        emission, _EF_4_FACTOR_NAME, model=MODEL, term=emission_id
    )
    ef5_factor = (
        get_lookup_value(emission, _EF_5_FACTOR_NAME, model=MODEL, term=emission_id)
        if not ef4_factor
        else None
    )
    values = (
        {
            "ef4-factor": extract_grouped_data(data=ef4_factor, key=factors_key),
            "ef4-factor-min": extract_grouped_data(
                data=get_lookup_value(
                    emission, _EF_4_FACTOR_NAME + "-min", model=MODEL, term=emission_id
                ),
                key=factors_key,
            ),
            "ef4-factor-max": extract_grouped_data(
                data=get_lookup_value(
                    emission, _EF_4_FACTOR_NAME + "-max", model=MODEL, term=emission_id
                ),
                key=factors_key,
            ),
        }
        if ef4_factor
        else (
            {
                "ef5-factor": ef5_factor,
                "ef5-factor-min": get_lookup_value(
                    emission, _EF_5_FACTOR_NAME + "-min", model=MODEL, term=emission_id
                ),
                "ef5-factor-max": get_lookup_value(
                    emission, _EF_5_FACTOR_NAME + "-max", model=MODEL, term=emission_id
                ),
            }
            if ef5_factor
            else {}
        )
    )
    return {k: safe_parse_float(v, default=None) for k, v in values.items()}


def _emission(
    term_id: str,
    value: float,
    min: float,
    max: float,
    aggregated: bool = False,
    inputs: list = None,
    operation: dict = None,
):
    emission = _new_emission(term=term_id, model=MODEL, value=value, min=min, max=max)
    emission["methodTier"] = _TIER
    emission["methodModelDescription"] = (
        "Aggregated version" if aggregated else "Disaggregated version"
    )
    if inputs:
        emission["inputs"] = inputs
    if operation:
        emission["operation"] = operation
    return emission


def _calculate_value(values: list, suffix: str = ""):
    value = list_sum(
        non_empty_list(
            [
                multiply_values(
                    [
                        value.get("emission-value"),
                        value.get("ef4-factor" + suffix)
                        or value.get("ef5-factor" + suffix),
                    ]
                )
                for value in values
            ]
        ),
        default=None,
    )
    return (
        value * get_atomic_conversion(Units.KG_N2O, Units.TO_N)
        if value is not None
        else None
    )


def _run(emission_id: str, values: list, ecoClimateZone: str = None):
    value = _calculate_value(values)
    min = _calculate_value(values, suffix="-min")
    max = _calculate_value(values, suffix="-max")
    return [
        _emission(
            emission_id,
            value,
            min,
            max,
            aggregated=ecoClimateZone is None,
            **pick(values[0], _INPUTS_GROUP_KEYS)
        )
    ]


def _should_run(
    emission_id: str, emission_ids: list, cycle: dict, group_by_inputs: bool = False
):
    ecoClimateZone = get_ecoClimateZone(cycle)

    emission_values = get_emissions_to_N(cycle, emission_ids)
    values = [
        {"emission-id": emission_id, "emission-value": emission_values[index]}
        | _get_emission_factors(emission_id, ecoClimateZone)
        | (
            pick(
                find_term_match(cycle.get("emissions", []), emission_id),
                _INPUTS_GROUP_KEYS,
            )
            if group_by_inputs
            else {}
        )
        for index, emission_id in enumerate(emission_ids)
        if emission_id is not None
    ]

    logRequirements(
        cycle,
        model=MODEL,
        term=emission_id,
        ecoClimateZone=ecoClimateZone,
        values=log_as_table([omit(v, _INPUTS_GROUP_KEYS) for v in values]),
    )

    should_run = all(
        [
            all(
                [
                    value.get("emission-value") is not None,
                    value.get("ef4-factor") or value.get("ef5-factor") is not None,
                ]
            )
            for value in values
        ]
    )
    logShouldRun(cycle, MODEL, emission_id, should_run, methodTier=_TIER)
    return should_run, values, ecoClimateZone


def run(
    emission_id: str, emission_ids: list, cycle: dict, group_by_inputs: bool = False
):
    should_run, values, ecoClimateZone = _should_run(
        emission_id, emission_ids, cycle, group_by_inputs
    )
    return _run(emission_id, values, ecoClimateZone) if should_run else []
