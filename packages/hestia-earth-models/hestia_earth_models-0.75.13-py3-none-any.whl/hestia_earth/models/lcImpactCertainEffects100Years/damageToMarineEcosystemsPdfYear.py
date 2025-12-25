from hestia_earth.models.log import logRequirements, logShouldRun
from hestia_earth.models.utils.indicator import _new_indicator
from hestia_earth.models.utils.impact_assessment import impact_endpoint_value
from . import MODEL

REQUIREMENTS = {
    "ImpactAssessment": {
        "impacts": [
            {
                "@type": "Indicator",
                "value": "",
                "methodModel": {
                    "@type": "Term",
                    "@id": "lcImpactCertainEffects100Years",
                },
            }
        ]
    }
}
RETURNS = {"Indicator": {"value": ""}}
LOOKUPS = {"characterisedIndicator": "pdfYearsDamageToMarineEcosystemsLCImpact"}
TERM_ID = "damageToMarineEcosystemsPdfYear"


def run(impact_assessment: dict):
    value = impact_endpoint_value(
        MODEL, TERM_ID, impact_assessment, LOOKUPS["characterisedIndicator"]
    )
    logRequirements(impact_assessment, model=MODEL, term=TERM_ID, value=value)
    logShouldRun(impact_assessment, MODEL, TERM_ID, value is not None)
    return _new_indicator(term=TERM_ID, model=MODEL, value=value)
