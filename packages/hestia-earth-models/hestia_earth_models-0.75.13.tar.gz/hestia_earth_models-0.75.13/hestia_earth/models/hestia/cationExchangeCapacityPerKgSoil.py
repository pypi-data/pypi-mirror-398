from hestia_earth.schema import MeasurementMethodClassification
from hestia_earth.utils.blank_node import get_node_value
from hestia_earth.utils.model import find_term_match

from hestia_earth.models.log import logRequirements, logShouldRun
from hestia_earth.models.utils.group_nodes import group_nodes_by
from hestia_earth.models.utils.measurement import _new_measurement
from hestia_earth.models.utils.source import get_source
from . import MODEL

REQUIREMENTS = {
    "Site": {
        "measurements": [
            {"@type": "Measurement", "value": "", "term.@id": "clayContent"},
            {"@type": "Measurement", "value": "", "term.@id": "soilPh"},
            {"@type": "Measurement", "value": "", "term.@id": "organicCarbonPerKgSoil"},
        ]
    }
}
RETURNS = {
    "Measurement": [
        {
            "value": "",
            "depthUpper": "",
            "depthLower": "",
            "methodClassification": "modelled using other measurements",
        }
    ]
}
TERM_ID = "cationExchangeCapacityPerKgSoil"
BIBLIO_TITLE = "Contribution of Organic Matter and Clay to Soil Cation-Exchange Capacity as Affected by the pH of the Saturating Solution"  # noqa: E501


def _measurement(
    site: dict, value: float, depthUpper: int = None, depthLower: int = None
):
    data = _new_measurement(term=TERM_ID, model=MODEL, value=value)
    if depthUpper is not None:
        data["depthUpper"] = depthUpper
    if depthLower is not None:
        data["depthLower"] = depthLower
    data["methodClassification"] = (
        MeasurementMethodClassification.MODELLED_USING_OTHER_MEASUREMENTS.value
    )
    return data | get_source(site, BIBLIO_TITLE)


def _run(site: dict, measurements: list):
    clayContent = find_term_match(measurements, "clayContent")
    clayContent_value = get_node_value(clayContent)
    soilPh = get_node_value(find_term_match(measurements, "soilPh"))
    organicCarbonPerKgSoil = get_node_value(
        find_term_match(measurements, "organicCarbonPerKgSoil")
    )

    value = (
        (51 * soilPh - 59) * (organicCarbonPerKgSoil / 10)
        + (30 + 4.4 * soilPh) * clayContent_value
    ) / 100

    depthUpper = clayContent.get("depthUpper")
    depthLower = clayContent.get("depthLower")

    return _measurement(site, value, depthUpper=depthUpper, depthLower=depthLower)


def _should_run_measurements(site: dict, key: tuple, measurements: list):
    clayContent = find_term_match(measurements, "clayContent", None)
    soilPh = find_term_match(measurements, "soilPh", None)
    organicCarbonPerKgSoil = find_term_match(
        measurements, "organicCarbonPerKgSoil", None
    )

    depth_logs = (
        {
            "-".join(f"{depth}" for depth in key[:2]): ";".join(
                [
                    f"id:clayContent_hasValue:{clayContent is not None}",
                    f"id:soilPh_hasValue:{soilPh is not None}",
                    f"id:organicCarbonPerKgSoil_hasValue:{organicCarbonPerKgSoil is not None}",
                ]
            )
        }
        if len(measurements) > 0
        else {}
    )

    logRequirements(site, model=MODEL, term=TERM_ID, **depth_logs)

    should_run = all(
        [
            clayContent is not None,
            soilPh is not None,
            organicCarbonPerKgSoil is not None,
        ]
    )
    return should_run


def _should_run(site: dict):
    grouped_measurements = group_nodes_by(
        site.get("measurements", []),
        ["depthUpper", "depthLower", "startDate", "endDate"],
        sort=False,
    )

    values = [
        (measurements, _should_run_measurements(site, key, measurements))
        for key, measurements in grouped_measurements.items()
    ]
    should_run = any([_should_run for _, _should_run in values])
    logShouldRun(site, MODEL, TERM_ID, should_run)
    return should_run, [
        measurements for measurements, _should_run in values if _should_run
    ]


def run(site: dict):
    should_run, values = _should_run(site)
    return [_run(site, value) for value in values] if should_run else []
