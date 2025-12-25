from hestia_earth.utils.model import find_primary_product

from hestia_earth.models.log import logShouldRun
from hestia_earth.models.utils.measurement import _new_measurement
from hestia_earth.models.utils.site import related_cycles
from . import MODEL

REQUIREMENTS = {
    "Site": {
        "related": {
            "Cycle": [
                {
                    "producst": [
                        {
                            "@type": "Product",
                            "primary": "True",
                            "term.@id": "riceGrainInHuskFlooded",
                        }
                    ]
                }
            ]
        }
    }
}
RETURNS = {"Measurement": [{"value": "0"}]}
TERM_ID = "slopeLength"


def _measurement():
    return _new_measurement(term=TERM_ID, model=MODEL, value=0)


def _is_valid_product(cycle: dict):
    return (find_primary_product(cycle) or {}).get("term", {}).get(
        "@id"
    ) == "riceGrainInHuskFlooded"


def _run(site: dict):
    logShouldRun(site, MODEL, TERM_ID, True)
    return [_measurement()]


def run(site: dict):
    is_relevant_product = all(map(_is_valid_product, related_cycles(site)))
    # do not log failure when the product is not relevant
    return _run(site) if is_relevant_product else []
