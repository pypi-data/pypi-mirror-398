from hestia_earth.schema import EmissionMethodTier

from .fuelCombustion_utils import run as run_fuelCombustion

REQUIREMENTS = {
    "Cycle": {
        "or": {
            "inputs": [
                {
                    "@type": "Input",
                    "value": "",
                    "term.termType": "fuel",
                    "optional": {"operation": ""},
                }
            ],
            "completeness.electricityFuel": "True",
        }
    }
}
RETURNS = {
    "Emission": [{"value": "", "inputs": "", "operation": "", "methodTier": "tier 1"}]
}
LOOKUPS = {
    "fuel": "nmvocToAirFuelCombustionEmepEea2019",
    "operation": "nmvocToAirFuelCombustionEmepEea2019",
}
TERM_ID = "nmvocToAirFuelCombustion"
TIER = EmissionMethodTier.TIER_1.value


def run(cycle: dict):
    return run_fuelCombustion(cycle, term_id=TERM_ID)
