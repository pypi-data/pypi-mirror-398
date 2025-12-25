from hestia_earth.schema import EmissionMethodTier

from .utils import run as run_term

REQUIREMENTS = {
    "Cycle": {
        "inputs": [
            {
                "@type": "Input",
                "term.termType": ["pesticideAI", "pesticideBrandName"],
                "value": "> 0",
            }
        ]
    }
}
LOOKUPS = {"emission": "pefcr2017PesticideFateFactor"}
RETURNS = {"Emission": [{"value": "", "key": "", "methodTier": "tier 1"}]}

TERM_ID = "pesticideToWaterPesticideApplication"
TIER = EmissionMethodTier.TIER_1.value


def run(cycle: dict):
    return run_term(TERM_ID, cycle)
