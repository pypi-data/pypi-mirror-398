from functools import reduce
from itertools import zip_longest
from pydash import merge
from typing import Union

from hestia_earth.schema import MeasurementMethodClassification
from hestia_earth.utils.blank_node import get_node_value
from hestia_earth.utils.date import OLDEST_DATE
from hestia_earth.utils.tools import flatten

from hestia_earth.models.log import (
    log_as_table,
    logRequirements,
    logShouldRun,
    format_conditional_message,
)

from hestia_earth.models.utils import split_on_condition
from hestia_earth.models.utils.blank_node import (
    filter_list_term_id,
    split_nodes_by_dates,
)
from hestia_earth.models.utils.group_nodes import (
    group_nodes_by,
    group_nodes_by_depthUpper_depthLower,
    group_nodes_by_consecutive_depths,
)
from hestia_earth.models.utils.measurement import _new_measurement
from hestia_earth.models.utils.select_nodes import (
    closest_depthUpper_depthLower,
    closest_last_date,
    pick_shallowest,
    prioritise_nodes_where,
    select_nodes_by,
)
from hestia_earth.models.utils.source import get_source
from . import MODEL

REQUIREMENTS = {
    "Site": {
        "measurements": [
            {
                "@type": "Measurement",
                "value": "",
                "term.@id": "soilBulkDensity",
                "depthUpper": "",
                "depthLower": "",
                "methodClassification": [
                    "on-site physical measurement",
                    "modelled using other measurements",
                ],
            },
            {
                "@type": "Measurement",
                "value": "",
                "dates": "",
                "term.@id": "organicCarbonPerKgSoil",
                "depthUpper": "",
                "depthLower": "",
                "methodClassification": [
                    "on-site physical measurement",
                    "modelled using other measurements",
                ],
            },
        ]
    }
}
RETURNS = {
    "Measurement": [
        {
            "value": "",
            "dates": "",
            "depthUpper": "",
            "depthLower": "",
            "methodClassification": "modelled using other measurements",
        }
    ]
}
TERM_ID = "organicCarbonPerHa"
BIBLIO_TITLE = "Soil organic carbon sequestration rates in vineyard agroecosystems under different soil management practices: A meta-analysis"  # noqa: E501
RESCALE_DEPTH_UPPER = 0
RESCALE_DEPTH_LOWER = 30
METHOD = MeasurementMethodClassification.MODELLED_USING_OTHER_MEASUREMENTS.value

MAX_DEPTH_LOWER = 100
SOIL_BULK_DENSITY_TERM_ID = "soilBulkDensity"
ORGANIC_CARBON_PER_KG_SOIL_TERM_ID = "organicCarbonPerKgSoil"

VALID_CALC_METHOD_CLASSIFICATION = {
    MeasurementMethodClassification.ON_SITE_PHYSICAL_MEASUREMENT.value,
    MeasurementMethodClassification.MODELLED_USING_OTHER_MEASUREMENTS.value,
}

VALID_RESCALE_METHOD_CLASSIFICATION = {
    MeasurementMethodClassification.ON_SITE_PHYSICAL_MEASUREMENT.value,
    MeasurementMethodClassification.PHYSICAL_MEASUREMENT_ON_NEARBY_SITE.value,
    MeasurementMethodClassification.MODELLED_USING_OTHER_MEASUREMENTS.value,
    MeasurementMethodClassification.GEOSPATIAL_DATASET.value,
}


def _measurement(
    value: list[float],
    *,
    depthUpper: Union[int, float],
    depthLower: Union[int, float],
    **kwargs,
):
    return _new_measurement(term=TERM_ID, model=MODEL, value=value) | {
        "depthUpper": int(depthUpper),
        "depthLower": int(depthLower),
        "methodClassification": METHOD,
        **{k: v for k, v in kwargs.items() if v is not None},
    }


def _with_source(measurement: dict, site: dict):
    return measurement | get_source(site, BIBLIO_TITLE)


# --- CALCULATE `organicCarbonPerHa` ---


def _calc_organic_carbon_per_ha(
    depth_upper: float,
    depth_lower: float,
    soil_bulk_density: float,
    organic_carbon_per_kg_soil: float,
) -> float:
    """
    Calculate `organicCarbonPerHa` from `soilBulkDensity` and `organicCarbonPerKgSoil` using method adapted from
    [Payen et al (2021)](https://doi.org/10.1016/j.jclepro.2020.125736).

    Parameters
    ----------
    depth_upper : float
        Measurement depth upper in centimetres (min `0`).
    depth_lower : float,
        Measurement depth upper in centimetres (min `0`).
    soil_bulk_density : float,
        Soil bulk density between depth upper and depth lower, Mg soil m-3
    organic_carbon_per_kg_soil : float
        Soil organic carbon concentration between depth upper and depth lower, kg C kg soil-1

    Return
    ------
    float
        The SOC stock per hectare within the specified depth interval, kg C ha-1.
    """
    return (
        (depth_lower - depth_upper)
        * soil_bulk_density
        * organic_carbon_per_kg_soil
        * 100
    )


def _calc_node(occ_node: dict, bd_nodes: list[dict]) -> dict:
    """
    Convert an `organicCarbonPerKgSoil` to `organicCarbonPerHa` using the most relevant values of bulk density.
    """
    occ_values = occ_node.get("value")
    dates = occ_node.get("dates")

    depth_upper = occ_node.get("depthUpper")
    depth_lower = occ_node.get("depthLower")

    def _most_relevant_bd_value(date: str) -> dict:
        node = select_nodes_by(
            bd_nodes,
            [
                lambda nodes: closest_last_date(nodes, date, mode="start"),
                lambda nodes: pick_shallowest(nodes, {}),
            ],
        )
        return get_node_value(node, default=None)

    soc_values = [
        _calc_organic_carbon_per_ha(
            depth_upper, depth_lower, _most_relevant_bd_value(date), value
        )
        for value, date in zip_longest(occ_values, dates, fillvalue=OLDEST_DATE)
    ]

    return _measurement(
        soc_values, depthUpper=depth_upper, depthLower=depth_lower, dates=dates
    )


def _should_run_calculation(site: dict) -> tuple[bool, dict[str, list[dict]]]:
    """
    Pre-process site data and determine whether there is sufficient data to calculate `organicCarbonPerHa`.
    """
    measurements = site.get("measurements", [])
    soc_nodes = filter_list_term_id(measurements, TERM_ID)

    occ_nodes = prioritise_nodes_where(
        [
            node
            for node in filter_list_term_id(
                measurements, ORGANIC_CARBON_PER_KG_SOIL_TERM_ID
            )
            if _should_run_calculation_node(node)
        ],
        lambda node: node.get("dates"),  # get nodes with dates, if possible
    )

    bd_nodes = split_nodes_by_dates(
        [
            node
            for node in filter_list_term_id(measurements, SOIL_BULK_DENSITY_TERM_ID)
            if _should_run_calculation_node(node)
        ]
    )

    grouped_measurements = merge(
        {},
        group_nodes_by_depthUpper_depthLower(
            occ_nodes, inner_key=ORGANIC_CARBON_PER_KG_SOIL_TERM_ID
        ),
        group_nodes_by_depthUpper_depthLower(
            bd_nodes, inner_key=SOIL_BULK_DENSITY_TERM_ID
        ),
    )

    inventory = {
        depth_key: group
        for depth_key, group in grouped_measurements.items()
        if all(
            group.get(required)
            for required in (
                ORGANIC_CARBON_PER_KG_SOIL_TERM_ID,
                SOIL_BULK_DENSITY_TERM_ID,
            )
        )
    }

    should_run = not bool(soc_nodes) and bool(inventory)

    logs = {
        "should_run_calculation": should_run,
        "inventory_calculation": (
            log_as_table(
                {
                    "depth-key": "-".join(f"{depth}" for depth in depth_key),
                    "has-soil-bulk-density": (
                        bd := bool(group.get(SOIL_BULK_DENSITY_TERM_ID))
                    ),
                    "has-organic-carbon-per-kg-soil": (
                        occ := bool(group.get(ORGANIC_CARBON_PER_KG_SOIL_TERM_ID))
                    ),
                    "should-run": bd and occ,
                }
                for depth_key, group in grouped_measurements.items()
            )
            if inventory
            else "None"
        ),
    }

    return should_run, inventory, logs


def _valid_node(node: dict) -> bool:
    """Validate that a node has a `value`, `depthUpper` and `depthLower`."""
    return all(
        [
            node.get("value"),
            node.get("depthLower") is not None,
            node.get("depthUpper") is not None,
        ]
    )


def _should_run_calculation_node(node: dict) -> bool:
    """Validate that a node has is suitable for the calculation sub-model."""
    return (
        _valid_node(node)
        and node.get("methodClassification") in VALID_CALC_METHOD_CLASSIFICATION
    )


def _run_calculation(inventory: dict) -> list[dict]:
    """
    Returns an `organicCarbonPerHa` measurement node for each `organicCarbonPerKgSoil` node in depth group using the
    most relevant `soilBulkDensity` node available.

    Parameters
    ----------
    inventory : dict
        An inventory of soil measurements with shape:
        ```
        {
            (depthUpper (float), depthLower (float)): {
                "soilBulkDensity: nodes (list[dict]),
                "organicCarbonPerKgSoil: nodes (list[dict])
            }
            ... other depths
        }
        ```

    Return
    ------
    list[dict]
        A list of `organicCarbonPerHa` [Measurement nodes](https://www.hestia.earth/schema/Measurement).
    """

    return flatten(
        _calc_node(node, group[SOIL_BULK_DENSITY_TERM_ID])
        for group in inventory.values()
        for node in group[ORGANIC_CARBON_PER_KG_SOIL_TERM_ID]
    )


# --- COMBINE `organicCarbonPerHa` nodes ---


def _get_dates_key(node: dict) -> str:
    """Build a hashable key from a node's `dates` field. Used to group nodes with identical dates."""
    return "-".join(f"{date}" for date in node.get("dates", []))


def _merge_same_dates(nodes: list):
    """
    Merge duplicate nodes with identical depths, methods and dates.
    """
    grouped_nodes = group_nodes_by(
        nodes,
        [
            "term.@id",
            "depthUpper",
            "depthLower",
            "methodClassification",
            "method.@id",
            _get_dates_key,
        ],
        sort=False,
    )

    return list(map(lambda nodes: nodes[0], grouped_nodes.values()))


def _get_overlap_bounds(
    a: tuple[float, float], b: tuple[float, float]
) -> tuple[float, float]:
    """
    Calculate the upper and lower bounds of the overlapping portion of two ranges.

    If `a` and `b` do not overlap, return `(None, None)`
    """
    c1 = max(a[0], b[0])
    c2 = min(a[1], b[1])
    return (c1, c2) if c1 < c2 else (None, None)


def _rescale_and_add(a: dict, b: dict) -> dict:
    """
    Merge `organicCarbonPerHa` node `b` into `a` by rescaling and adding values. Nodes must have the same number of
    values and dates.

    Nodes are rescaled to prevent overlaps in their depth intervals and so their `depthLower` does not exceed the
    target depth of 0 - 30cm.
    """
    a_value = a.get("value", [])
    a_upper, a_lower = a.get("depthUpper"), a.get("depthLower")

    b_value = b.get("value")
    b_upper, b_lower = b.get("depthUpper"), b.get("depthLower")

    overlap_upper, overlap_lower = _get_overlap_bounds(
        (a_upper, a_lower), (b_upper, b_lower)
    )
    has_overlap = None not in (overlap_upper, overlap_lower)

    c_upper = overlap_lower if has_overlap else min(a_lower, b_upper)
    c_lower = min(b_lower, RESCALE_DEPTH_LOWER)

    should_add = (c_lower - c_upper) > 0

    c_value = (
        [
            _rescale_soc_value(value, b_upper, b_lower, c_upper, c_lower)
            for value in b_value
        ]
        if (c_upper, c_lower) != (b_upper, b_lower)
        else b_value
    )

    return a | (
        {
            "value": [x + y for x, y in zip(a_value, c_value)],
            "depthUpper": min(a_upper, c_upper),
            "depthLower": max(a_lower, c_lower),
        }
        if should_add
        else {}
    )


def _add_consecutive_soc_nodes(soc_nodes: list[dict]):
    """
    Merge a list of `organicCarbonPerHa` nodes with matching dates and consecutive depths by calculating the
    element-wise sum of their values.

    Node values are rescaled to prevent gaps (undercounting) and overlaps (double-counting).
    """
    sorted_nodes = sorted(
        soc_nodes,
        key=lambda node: (node.get("depthUpper"), -1 * node.get("depthLower")),
    )
    return reduce(_rescale_and_add, sorted_nodes[1:], sorted_nodes[0])


def _node_from_group(nodes: list):
    """Resolve a list of `organicCarbonPerHa` nodes into a single node."""
    # `nodes` contain list with consecutive depths
    return nodes[0] if len(nodes) == 1 else _add_consecutive_soc_nodes(nodes)


def _combine_soc_nodes(nodes: list):
    # `nodes` contain list with same `term.@id` and `dates`
    grouped = group_nodes_by_consecutive_depths(nodes, sort=False)
    return flatten(
        map(
            lambda nodes: _node_from_group(nodes), [group for group in grouped.values()]
        )
    )


def _run_combine(nodes: list[dict]) -> list[dict]:
    """Stack SOC nodes with matching dates and methods and add their values."""
    merged = _merge_same_dates(nodes)
    grouped = group_nodes_by(
        merged,
        ["term.@id", "methodClassification", "method.@id", _get_dates_key],
        sort=False,
    )
    return flatten(map(lambda nodes: _combine_soc_nodes(nodes), grouped.values()))


# --- RESCALE `organicCarbonPerHa` ---


def _c_to_depth(d: float) -> float:
    """
    The definite integral of `c_density_at_depth` between `0` and `d`.

    Parameters
    ----------
    d : float
        Measurement depth in metres (min `0`, max `1`).

    Returns
    -------
    float
        The carbon stock per m2 to depth `d`, kg C-2.
    """
    return 22.1 * d - (33.3 * pow(d, 2)) / 2 + (14.9 * pow(d, 3)) / 3


def _cdf(depth_upper: float, depth_lower: float) -> float:
    """
    The ratio between the carbon stock per m2 to depth `d` and the carbon stock per m2 to depth `1`.

    Parameters
    ----------
    depth_upper : float
        Measurement depth upper in metres (min `0`, max `1`).
    depth_lower : float
        Measurement depth lower in metres (min `0`, max `1`).

    Returns
    -------
    float
        The proportion of carbon stored between `depth_upper` and `depth_lower` compared to between `0` and `1` metres.
    """
    return (_c_to_depth(depth_lower) - _c_to_depth(depth_upper)) / _c_to_depth(1)


def _rescale_soc_value(
    source_value: float,
    source_depth_upper: float,
    source_depth_lower: float,
    target_depth_upper: float,
    target_depth_lower: float,
) -> float:
    """
    Rescale an SOC measurement value from a source depth interval to a target depth interval.

    Depths are converted from centimetres (HESTIA schema) to metres for use in `cdf` function.

    Parameters
    ----------
    source_value : float
        Source SOC stock (kg C ha-1).
    source_depth_upper : float
        Source measurement depth upper in centimetres (min `0`, max `100`).
    source_depth_lower : float
        Source measurement depth lower in centimetres, must be greater than `source_depth_upper` (min `0`, max `100`).
    target_depth_upper : float
        Target measurement depth upper in centimetres (min `0`, max `100`).
    target_depth_lower : float
        Target measurement depth lower in centimetres, must be greater than `target_depth_upper` (min `0`, max `100`).

    Returns
    -------
    float
        The estimated SOC stock for the target depth interval (kg C ha-1).
    """
    cd_target = _cdf(target_depth_upper / 100, target_depth_lower / 100)
    cd_measurement = _cdf(source_depth_upper / 100, source_depth_lower / 100)
    return source_value * (cd_target / cd_measurement)


def _rescale_node(node: dict):
    """
    Convert a node to 0 - 30cm depth interval.
    """
    values = node.get("value")
    dates = node.get("dates")

    method_id = node.get("method", {}).get("@id")
    methodClassification = node.get("methodClassification")

    methodDescription = (
        f"organicCarbonPerHa measurement with method.@id={method_id} and methodClassification={methodClassification} "
        "rescaled to 0 - 30cm depth interval"
    )

    should_run = not _is_standard_depth(
        node
    )  # Node has correct depths, so don't rescale values

    def _rescaled_values() -> dict:
        return [
            _rescale_soc_value(
                value,
                node.get("depthUpper"),
                node.get("depthLower"),
                RESCALE_DEPTH_UPPER,
                RESCALE_DEPTH_LOWER,
            )
            for value in values
        ]

    return _measurement(
        _rescaled_values() if should_run else values,
        depthUpper=RESCALE_DEPTH_UPPER,
        depthLower=RESCALE_DEPTH_LOWER,
        dates=dates,
        methodDescription=methodDescription,
    )


def _should_run_rescale_node(node: list) -> bool:
    """
    Validate that a node has `depthUpper` = `0` and a `depthLower` < `100`.
    """
    return (
        _valid_node(node)
        and node.get("depthLower") <= MAX_DEPTH_LOWER
        and node.get("methodClassification") in VALID_RESCALE_METHOD_CLASSIFICATION
    )


def _is_standard_depth(node: dict) -> bool:
    return all(
        [
            node.get("depthUpper") == RESCALE_DEPTH_UPPER,
            node.get("depthLower") == RESCALE_DEPTH_LOWER,
        ]
    )


def _should_run_rescale(soc_nodes: list[dict]):
    """
    Pre-process `organicCarbonPerHa` nodes and determine whether any need to be rescaled to a depth interval of 0-30cm.
    """
    valid_nodes = [node for node in soc_nodes if _should_run_rescale_node(node)]

    target_depth_nodes, other_depth_nodes = split_on_condition(
        valid_nodes, _is_standard_depth
    )

    has_0_to_30 = bool(target_depth_nodes)
    has_other_depths = bool(other_depth_nodes)
    has_other_depth_with_zero_upper = any(
        node for node in other_depth_nodes if node.get("depthUpper") == 0
    )

    should_run = all([(not has_0_to_30), has_other_depth_with_zero_upper])

    logs = {
        "should_run_rescale": should_run,
        "has_0_to_30": format_conditional_message(
            has_0_to_30,
            "Site has SOC measurements with depth interval 0-30cm",
            "Site does not have SOC measuresments with depth 0-30cm",
        ),
        "has_other_depths": format_conditional_message(
            has_other_depths,
            "Site has SOC measurements with other depth intervals",
            "Site does not have SOC measuresments with other depth intervals",
        ),
        "has_other_depth_with_zero_upper": has_other_depth_with_zero_upper,
    }

    return should_run, other_depth_nodes, logs


def _prioritise_surface(nodes: list[dict]) -> list[dict]:
    """If nodes with `depthUpper` = `0` available, select them."""
    return prioritise_nodes_where(
        nodes, lambda node: node.get("depthUpper") == RESCALE_DEPTH_UPPER
    )


def _prioritise_deeper(nodes: list[dict]) -> list[dict]:
    """If nodes with `depthLower` >= `30` availble, select them."""
    return prioritise_nodes_where(
        nodes, lambda node: node.get("depthLower") >= RESCALE_DEPTH_LOWER
    )


def _closest(nodes: list[dict]) -> list[dict]:
    """Select nodes with the closest depth interval to 0 - 30cm"""
    return closest_depthUpper_depthLower(
        nodes, RESCALE_DEPTH_UPPER, RESCALE_DEPTH_LOWER, depth_strict=False
    )


def _get_most_relevant_soc_nodes(soc_nodes: list[dict]):
    """
    Find the `organic_carbon_per_ha_node` with the closest depth interval to 0 - 30cm. `depthLowers` greater than 30cm
    are prioritised. Returns `{}` if input list is empty.
    """
    return select_nodes_by(
        soc_nodes,
        [_prioritise_surface, _prioritise_deeper, _closest],
    )


def _run_rescale(soc_nodes: list[dict]) -> list[dict]:
    """
    Rescale `organicCarbonPerHa` nodes to a depth of 0 - 30cm.

    First add together the value of nodes with matching dates and methods and consecutive depths to get as close to
    0 - 30cm as possible. Then rescale results if necessary.
    """
    condensed = _run_combine(soc_nodes)
    nodes = _get_most_relevant_soc_nodes(condensed)
    return [_rescale_node(node) for node in nodes]


# --- RUN MODEL ---


def run(site: dict):
    should_run_calc, inventory_calc, logs_calc = _should_run_calculation(site)
    result_calculation = _run_calculation(inventory_calc) if should_run_calc else []

    soc_nodes = result_calculation + filter_list_term_id(
        site.get("measurements", []), TERM_ID
    )

    should_run_rescale, soc_nodes_rescale, logs_rescale = _should_run_rescale(soc_nodes)
    result_rescale = _run_rescale(soc_nodes_rescale) if should_run_rescale else []

    logRequirements(site, model=MODEL, term=TERM_ID, **logs_calc, **logs_rescale)
    logShouldRun(site, MODEL, TERM_ID, should_run=should_run_calc or should_run_rescale)

    return [_with_source(node, site) for node in result_calculation + result_rescale]
