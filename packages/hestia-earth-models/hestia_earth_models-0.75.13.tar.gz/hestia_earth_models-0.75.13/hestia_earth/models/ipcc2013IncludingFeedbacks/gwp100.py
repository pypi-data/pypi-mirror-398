from hestia_earth.models.log import logRequirements, logShouldRun
from hestia_earth.models.utils.indicator import _new_indicator
from hestia_earth.models.utils.impact_assessment import impact_emission_lookup_value
from . import MODEL

REQUIREMENTS = {
    "ImpactAssessment": {
        "emissionsResourceUse": [
            {"@type": "Indicator", "value": "", "term.termType": "emission"}
        ]
    }
}
RETURNS = {"Indicator": {"value": ""}}
LOOKUPS = {"emission": "co2EqGwp100IncludingClimate-CarbonFeedbacksIpcc2013"}
TERM_ID = "gwp100"


def run(impact_assessment: dict):
    value = impact_emission_lookup_value(
        MODEL, TERM_ID, impact_assessment, LOOKUPS["emission"]
    )
    logRequirements(impact_assessment, model=MODEL, term=TERM_ID, value=value)
    logShouldRun(impact_assessment, MODEL, TERM_ID, value is not None)
    return _new_indicator(term=TERM_ID, model=MODEL, value=value)
