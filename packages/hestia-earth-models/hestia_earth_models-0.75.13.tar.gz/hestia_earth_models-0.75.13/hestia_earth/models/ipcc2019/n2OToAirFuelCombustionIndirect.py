from hestia_earth.schema import EmissionMethodTier
from hestia_earth.utils.tools import flatten
from hestia_earth.utils.blank_node import group_by_keys

from .n2OToAir_indirect_emissions_utils import _INPUTS_GROUP_KEYS, run as run_emission

REQUIREMENTS = {
    "Cycle": {
        "completeness.electricityFuel": "True",
        "emissions": [
            {
                "@type": "Emission",
                "value": "",
                "term.@id": "nh3ToAirFuelCombustion",
                "inputs": [
                    {
                        "@type": "Input",
                        "value": "",
                        "term.termType": "fuel",
                        "optional": {"operation": ""},
                    }
                ],
            },
            {
                "@type": "Emission",
                "value": "",
                "term.@id": "noxToAirFuelCombustion",
                "inputs": [
                    {
                        "@type": "Input",
                        "value": "",
                        "term.termType": "fuel",
                        "optional": {"operation": ""},
                    }
                ],
            },
        ],
        "optional": {
            "site": {
                "@type": "Site",
                "measurements": [
                    {"@type": "Measurement", "value": "", "term.@id": "ecoClimateZone"}
                ],
            }
        },
    }
}
LOOKUPS = {
    "emission": [
        "IPCC_2019_EF4_FACTORS",
        "IPCC_2019_EF4_FACTORS-max",
        "IPCC_2019_EF4_FACTORS-min",
        "IPCC_2019_EF5_FACTORS",
        "IPCC_2019_EF5_FACTORS-max",
        "IPCC_2019_EF5_FACTORS-min",
    ]
}
RETURNS = {
    "Emission": [{"value": "", "methodTier": "tier 1", "inputs": "", "operation": ""}]
}
TERM_ID = "n2OToAirFuelCombustionIndirect"
TIER = EmissionMethodTier.TIER_1.value
_EMISSION_IDS = [e["term.@id"] for e in REQUIREMENTS["Cycle"]["emissions"]]


def run(cycle: dict):
    # group emissions by inputs first
    grouped_emissions = group_by_keys(cycle.get("emissions", []), _INPUTS_GROUP_KEYS)

    return flatten(
        [
            run_emission(
                TERM_ID,
                _EMISSION_IDS,
                cycle | {"emissions": emissions},
                group_by_inputs=True,
            )
            for key, emissions in grouped_emissions.items()
            if key
        ]
    )
