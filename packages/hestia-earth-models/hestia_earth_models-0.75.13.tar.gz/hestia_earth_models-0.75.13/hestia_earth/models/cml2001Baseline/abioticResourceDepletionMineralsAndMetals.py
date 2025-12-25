from functools import lru_cache
from typing import Optional

from hestia_earth.schema import TermTermType
from hestia_earth.utils.lookup import get_table_value, download_lookup
from hestia_earth.utils.tools import list_sum
from hestia_earth.utils.lookup import is_missing_value

from hestia_earth.models.log import logRequirements, logShouldRun, log_as_table
from . import MODEL
from ..utils.indicator import _new_indicator
from ..utils.lookup import _node_value

REQUIREMENTS = {
    "ImpactAssessment": {
        "emissionsResourceUse": [
            {
                "@type": "Indicator",
                "value": "",
                "term.termType": "resourceUse",
                "term.@id": [
                    "resourceUseMineralsAndMetalsInputsProduction",
                    "resourceUseMineralsAndMetalsDuringCycle",
                ],
                "inputs": [
                    {
                        "@type": "Term",
                        "term.units": "kg",
                        "term.termType": [
                            "material",
                            "soilAmendment",
                            "otherInorganicChemical",
                        ],
                    }
                ],
            }
        ]
    }
}

LOOKUPS = {
    "@doc": "Different lookup files are used depending on the input material",
    "soilAmendment": "abioticResourceDepletionMineralsAndMetalsCml2001Baseline",
    "material": "abioticResourceDepletionMineralsAndMetalsCml2001Baseline",
    "otherInorganicChemical": "abioticResourceDepletionMineralsAndMetalsCml2001Baseline",
}

RETURNS = {"Indicator": {"value": ""}}

TERM_ID = "abioticResourceDepletionMineralsAndMetals"

_authorised_resource_use_term_types = [
    TermTermType.MATERIAL.value,
    TermTermType.SOILAMENDMENT.value,
    TermTermType.OTHERINORGANICCHEMICAL.value,
]
_authorised_resource_use_term_ids = [
    "resourceUseMineralsAndMetalsInputsProduction",
    "resourceUseMineralsAndMetalsDuringCycle",
]


def _valid_input(input: dict) -> bool:
    return (
        input.get("units", "").startswith("kg")
        and input.get("termType", "") in _authorised_resource_use_term_types
    )


def _valid_resource_indicator(resource: dict) -> bool:
    return len(resource.get("inputs", [])) == 1 and isinstance(
        _node_value(resource), (int, float)
    )


@lru_cache
def _get_resource_cf(input_term_id: str, input_term_type: str) -> Optional[float]:
    return get_table_value(
        lookup=download_lookup(filename=f"{input_term_type}.csv"),
        col_match="term.id",
        col_match_with=input_term_id,
        col_val=LOOKUPS.get(input_term_type),
        default_value=None,
    )


def _indicator(value: float):
    return _new_indicator(term=TERM_ID, model=MODEL, value=value)


def _run(resources: list):
    result = list_sum(
        [
            indicator_input["value"] * indicator_input["coefficient"]
            for indicator_input in resources
        ]
    )
    return _indicator(result)


def _should_run(impact_assessment: dict) -> tuple[bool, list]:
    emissions_resource_use = [
        resource
        for resource in impact_assessment.get("emissionsResourceUse", [])
        if all(
            [
                resource.get("term", {}).get("@id", "")
                in _authorised_resource_use_term_ids,
                resource.get("inputs"),
            ]
        )
    ]

    has_resource_use_entries = bool(emissions_resource_use)

    resource_uses_unpacked = [
        {
            "input-term-id": input.get("@id"),
            "input-term-type": input.get("termType"),
            "indicator-term-id": resource_indicator["term"]["@id"],
            "indicator-is-valid": _valid_resource_indicator(resource_indicator),
            "indicator-input-is-valid": _valid_input(input),
            "value": _node_value(resource_indicator),
            "coefficient": (
                _get_resource_cf(
                    input_term_id=input.get("@id"),
                    input_term_type=input.get("termType", ""),
                )
                if input
                else None
            ),
        }
        for resource_indicator in emissions_resource_use
        for input in resource_indicator.get("inputs", [])
    ]
    valid_resources_with_cf = [
        em
        for em in resource_uses_unpacked
        if all(
            [
                not is_missing_value(em["coefficient"]),
                em["indicator-is-valid"] is True,
                em["indicator-input-is-valid"] is True,
            ]
        )
    ]

    has_valid_input_requirements = all(
        [
            all([em["indicator-is-valid"], em["indicator-input-is-valid"]])
            for em in resource_uses_unpacked
        ]
    )

    all_resources_have_cf = all(
        [em["coefficient"] is not None for em in resource_uses_unpacked]
    ) and bool(resource_uses_unpacked)

    logRequirements(
        impact_assessment,
        model=MODEL,
        term=TERM_ID,
        has_resource_use_entries=has_resource_use_entries,
        has_valid_input_requirements=has_valid_input_requirements,
        all_resources_have_cf=all_resources_have_cf,
        resource_uses=log_as_table(resource_uses_unpacked),
    )

    should_run = all([has_valid_input_requirements, has_resource_use_entries])

    logShouldRun(impact_assessment, MODEL, TERM_ID, should_run)
    return should_run, valid_resources_with_cf


def run(impact_assessment: dict):
    should_run, resources = _should_run(impact_assessment)
    return _run(resources) if should_run else None
