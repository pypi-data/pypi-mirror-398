from hestia_earth.schema import MeasurementMethodClassification, TermTermType
from hestia_earth.utils.model import filter_list_term_type
from hestia_earth.utils.blank_node import get_node_value
from hestia_earth.utils.tools import pick

from hestia_earth.models.log import logRequirements, logShouldRun, log_as_table
from hestia_earth.models.utils.measurement import _new_measurement
from hestia_earth.models.utils.source import get_source
from .utils import download, has_geospatial_data, should_download
from . import MODEL

REQUIREMENTS = {
    "Site": {
        "or": [
            {"latitude": "", "longitude": ""},
            {"boundary": {}},
            {"region": {"@type": "Term", "termType": "region"}},
        ],
        "none": {
            "measurements": [
                {
                    "@type": "Measurement",
                    "value": "> 0",
                    "depthUpper": "0",
                    "depthLower": "30",
                    "term.termType": ["soilType", "usdaSoilType"],
                }
            ]
        },
    }
}
RETURNS = {
    "Measurement": [
        {
            "value": "",
            "depthUpper": "0",
            "depthLower": "30",
            "methodClassification": "geospatial dataset",
        }
    ]
}
TERM_ID = "histosol"
EE_PARAMS = {
    "collection": "histosols_corrected",
    "ee_type": "raster",
    "reducer": "mean",
}
BIBLIO_TITLE = "Harmonized World Soil Database Version 1.2. Food and Agriculture Organization of the United Nations (FAO)."  # noqa: E501
_DEPTH_UPPER = 0
_DEPTH_LOWER = 30


def _measurement(site: dict, value: float):
    measurement = _new_measurement(term=TERM_ID, value=value)
    measurement["depthUpper"] = _DEPTH_UPPER
    measurement["depthLower"] = _DEPTH_LOWER
    measurement["methodClassification"] = (
        MeasurementMethodClassification.GEOSPATIAL_DATASET.value
    )
    return measurement | get_source(site, BIBLIO_TITLE)


def _run(site: dict):
    value = download(TERM_ID, site, EE_PARAMS)
    return [_measurement(site, value)] if value is not None else []


def _should_run(site: dict):
    contains_geospatial_data = has_geospatial_data(site)
    below_max_area_size = should_download(TERM_ID, site)

    measurements = filter_list_term_type(
        site.get("measurements", []), [TermTermType.SOILTYPE, TermTermType.USDASOILTYPE]
    )
    measurements = [
        m
        for m in measurements
        if all(
            [
                m.get("depthUpper", -1) == _DEPTH_UPPER,
                m.get("depthLower", 0) == _DEPTH_LOWER,
                get_node_value(m) > 0,
            ]
        )
    ]
    has_soil_type_measurements = len(measurements) > 0

    logRequirements(
        site,
        model=MODEL,
        term=TERM_ID,
        contains_geospatial_data=contains_geospatial_data,
        below_max_area_size=below_max_area_size,
        has_soil_type_measurements=has_soil_type_measurements,
        soil_type_measurements=log_as_table(
            [
                {
                    "id": m.get("term", {}).get("@id"),
                    "termType": m.get("term", {}).get("termType"),
                    "value": get_node_value(m),
                }
                | pick(m, ["depthUpper", "depthLower"])
                for m in measurements
            ]
        ),
    )

    should_run = all(
        [contains_geospatial_data, below_max_area_size, not has_soil_type_measurements]
    )
    logShouldRun(site, MODEL, TERM_ID, should_run)
    return should_run


def run(site: dict):
    return _run(site) if _should_run(site) else []
