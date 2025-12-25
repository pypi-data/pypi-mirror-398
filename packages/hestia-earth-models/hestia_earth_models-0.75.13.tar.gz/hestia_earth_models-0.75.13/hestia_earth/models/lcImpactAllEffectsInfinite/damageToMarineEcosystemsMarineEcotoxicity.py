from hestia_earth.models.utils.indicator import _new_indicator
from hestia_earth.models.utils.pesticideAI import impact_lookup_value
from . import MODEL

REQUIREMENTS = {
    "ImpactAssessment": {
        "cycle": {
            "@type": "Cycle",
            "completeness.pesticideVeterinaryDrug": "True",
            "inputs": [{"@type": "Input", "value": "", "term.termType": "pesticideAI"}],
        }
    }
}
RETURNS = {"Indicator": {"value": ""}}
LOOKUPS = {
    "pesticideAI": "pdfYearInfiniteMarineEcotoxicityDamageToMarineEcosystemsLCImpact"
}
TERM_ID = "damageToMarineEcosystemsMarineEcotoxicity"


def run(impact_assessment: dict):
    value = impact_lookup_value(
        MODEL, TERM_ID, impact_assessment, LOOKUPS["pesticideAI"]
    )
    return _new_indicator(term=TERM_ID, model=MODEL, value=value)
