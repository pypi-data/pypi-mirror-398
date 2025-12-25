from hestia_earth.models.log import logRequirements, logShouldRun
from hestia_earth.models.utils.indicator import _new_indicator
from hestia_earth.models.utils.impact_assessment import impact_country_value
from . import MODEL

REQUIREMENTS = {
    "ImpactAssessment": {
        "emissionsResourceUse": [
            {"@type": "Indicator", "value": "", "term.termType": "resourceUse"}
        ],
        "site": {"@type": "Site", "country": {"@type": "Term", "termType": "region"}},
    }
}
RETURNS = {"Indicator": {"value": ""}}
LOOKUPS = {"region-resourceUse-WaterStressDamageToFreshwaterEcosystemsLCImpactCF": ""}
TERM_ID = "damageToFreshwaterEcosystemsWaterStress"


def run(impact_assessment: dict):
    value = impact_country_value(
        MODEL,
        TERM_ID,
        impact_assessment,
        f"{list(LOOKUPS.keys())[0]}.csv",
        "certainEffects",
    )
    logRequirements(impact_assessment, model=MODEL, term=TERM_ID, value=value)
    logShouldRun(impact_assessment, MODEL, TERM_ID, value is not None)
    return _new_indicator(term=TERM_ID, model=MODEL, value=value)
