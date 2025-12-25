from functools import reduce
from typing import NamedTuple, Optional
from pydash import merge

from hestia_earth.schema import MeasurementMethodClassification, TermTermType
from hestia_earth.utils.blank_node import get_node_value, flatten
from hestia_earth.utils.model import filter_list_term_type

from hestia_earth.models.hestia.soilMeasurement import _STANDARD_DEPTHS
from hestia_earth.models.ipcc2019.organicCarbonPerHa_utils import (
    IPCC_SOIL_CATEGORY_TO_SOIL_TYPE_LOOKUP_VALUE,
    IpccSoilCategory,
)
from hestia_earth.models.log import (
    format_bool,
    format_float,
    format_str,
    log_as_table,
    logRequirements,
    logShouldRun,
)
from hestia_earth.models.utils import split_on_condition
from hestia_earth.models.utils.blank_node import node_lookup_match, split_nodes_by_dates
from hestia_earth.models.utils.measurement import _new_measurement
from . import MODEL

REQUIREMENTS = {
    "Site": {
        "optional": {
            "measurements": [
                {
                    "@type": "Measurement",
                    "value": "",
                    "depthUpper": "",
                    "depthLower": "",
                    "term.termType": ["soilType", "usdaSoilType"],
                    "optional": {"dates": ""},
                }
            ]
        }
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
LOOKUPS = {"soilType": "IPCC_SOIL_CATEGORY", "usdaSoilType": "IPCC_SOIL_CATEGORY"}
TERM_ID = "organicSoils,mineralSoils"

MEASUREMENT_TERM_IDS = TERM_ID.split(",")
ORGANIC_SOILS_TERM_ID = MEASUREMENT_TERM_IDS[0]
MINERAL_SOILS_TERM_ID = MEASUREMENT_TERM_IDS[1]
METHOD = MeasurementMethodClassification.MODELLED_USING_OTHER_MEASUREMENTS.value

_INPUT_TERM_TYPES = (TermTermType.SOILTYPE, TermTermType.USDASOILTYPE)
TARGET_LOOKUP_VALUE = IPCC_SOIL_CATEGORY_TO_SOIL_TYPE_LOOKUP_VALUE[
    IpccSoilCategory.ORGANIC_SOILS
]

IS_100_THRESHOLD = 99.5


def _measurement(term_id: str, **kwargs):
    measurement = _new_measurement(term_id)
    return measurement | {
        **{k: v for k, v in kwargs.items()},
        "methodClassification": METHOD,
    }


class _SoilTypeDatum(NamedTuple):
    term_id: str
    term_type: str
    depth_upper: float
    depth_lower: float
    dates: list[str]
    value: float
    is_organic: bool
    is_complete_depth: bool
    is_standard_depth: bool


class _InventoryKey(NamedTuple):
    depth_upper: float
    depth_lower: float
    date: Optional[str]


_InventoryGroup = dict[str, float]

_SoilTypeInventory = dict[_InventoryKey, _InventoryGroup]


_DEFAULT_INVENTORY: _SoilTypeInventory = {
    _InventoryKey(None, None, None): {"organicSoils": 0, "mineralSoils": 100}
}


def _soil_type_data_to_inventory_keys(datum: _SoilTypeDatum):
    return (
        [_InventoryKey(datum.depth_upper, datum.depth_lower, date) for date in dates]
        if len((dates := datum.dates)) > 0
        else [_InventoryKey(datum.depth_upper, datum.depth_lower, None)]
    )


def _extract_soil_type_data(node: dict) -> _SoilTypeDatum:
    depth_upper = node.get("depthUpper")
    depth_lower = node.get("depthLower")
    depth_interval = (depth_upper, depth_lower)
    term_type = node.get("term", {}).get("termType")

    return _SoilTypeDatum(
        term_id=node.get("term", {}).get("@id"),
        term_type=term_type,
        depth_upper=depth_upper,
        depth_lower=depth_lower,
        dates=node.get("dates", []),
        value=get_node_value(node),
        is_organic=node_lookup_match(node, LOOKUPS[term_type], TARGET_LOOKUP_VALUE),
        is_complete_depth=all(depth is not None for depth in depth_interval),
        is_standard_depth=depth_interval in _STANDARD_DEPTHS,
    )


def _classify_soil_type_data(soil_type_data: list[_SoilTypeDatum]):
    """
    Calculate the values of `organicSoils` and `mineralSoils` from `soilType` measurements for each unique combination
    of depth interval and date.
    """

    def classify(
        inventory: _SoilTypeInventory, datum: _SoilTypeDatum
    ) -> _SoilTypeInventory:
        """
        Sum the values of organic and mineral `soilType`/`usdaSoilType` Measurements by depth interval and date.
        """
        keys = _soil_type_data_to_inventory_keys(datum)

        inner_key = ORGANIC_SOILS_TERM_ID if datum.is_organic else MINERAL_SOILS_TERM_ID

        update_dict = {
            key: (inner := inventory.get(key, {}))
            | {inner_key: min(inner.get(inner_key, 0) + datum.value, 100)}
            for key in keys
        }

        return merge(dict(), inventory, update_dict)

    inventory = _select_most_complete_groups(reduce(classify, soil_type_data, {}))

    return {
        key: {
            ORGANIC_SOILS_TERM_ID: (org := group.get(ORGANIC_SOILS_TERM_ID, 0)),
            MINERAL_SOILS_TERM_ID: 100 - org,
        }
        for key, group in inventory.items()
    }


def _group_keys_by_depth(
    inventory: _SoilTypeInventory,
) -> dict[tuple, list[_InventoryKey]]:

    def group(
        result: dict[tuple, list[_InventoryKey]], key: _InventoryKey
    ) -> dict[tuple, list[_InventoryKey]]:
        depth_interval = (key.depth_upper, key.depth_lower)
        update_dict = {depth_interval: result.get(depth_interval, []) + [key]}
        return result | update_dict

    return reduce(group, inventory.keys(), {})


def _select_most_complete_groups(inventory: _SoilTypeInventory):
    """
    For each depth interval, we need to choose the inventory items that have the most complete information.

    Items should be prioritised in the following order:

    - If only dated items are available, use dated
    - If only undated items are available, use undated
    - If there are a mix of dated and undated items:
        - If dated items include organic soils measurements, use dated
        - If undated items include organic soils measurements, use undated
        - Otherwise, use dated
    """
    grouped = _group_keys_by_depth(inventory)

    def select(
        result: set[_InventoryKey], keys: list[_InventoryKey]
    ) -> set[_InventoryKey]:
        with_dates, without_dates = split_on_condition(
            set(keys), lambda k: k.date is not None
        )

        with_dates_have_org_value = any(
            (
                ORGANIC_SOILS_TERM_ID in (group := inventory.get(key, {}))
                or group.get(MINERAL_SOILS_TERM_ID, 0) >= IS_100_THRESHOLD
            )
            for key in with_dates
        )

        without_dates_have_org_value = any(
            (
                ORGANIC_SOILS_TERM_ID in (group := inventory.get(key, {}))
                or group.get(MINERAL_SOILS_TERM_ID, 0) >= IS_100_THRESHOLD
            )
            for key in without_dates
        )

        run_with_dates = with_dates_have_org_value or (
            with_dates and not without_dates_have_org_value
        )

        return result | (with_dates if run_with_dates else without_dates)

    selected_keys = reduce(select, grouped.values(), set())

    return {k: v for k, v in inventory.items() if k in selected_keys}


def _format_dates(dates: list[str]):
    """Format a list of datestrings for logging."""
    return (
        " ".join(format_str(date) for date in dates)
        if isinstance(dates, list) and len(dates)
        else "None"
    )


_DATUM_KEY_TO_FORMAT_FUNC = {
    "depth_upper": lambda x: format_float(x, "cm"),
    "depth_lower": lambda x: format_float(x, "cm"),
    "dates": _format_dates,
    "value": lambda x: format_float(x, "pct area"),
    "is_organic": format_bool,
    "is_complete_depth": format_bool,
    "is_standard_depth": format_bool,
}
DEFAULT_FORMAT_FUNC = format_str


def _format_soil_data(data: list[_SoilTypeDatum]):
    return (
        log_as_table(
            {
                format_str(k): _DATUM_KEY_TO_FORMAT_FUNC.get(k, DEFAULT_FORMAT_FUNC)(v)
                for k, v in datum._asdict().items()
            }
            for datum in data
        )
        if data
        else "None"
    )


_FILTER_BY = ("is_standard_depth", "is_complete_depth")


def _filter_data_by_depth_availability(data: list[_SoilTypeDatum]):
    """
    If measurements with depth available -> discard measurements without depth
    If measurements with standard depth available -> discard non-standard depths
    Else, use measurements with depth
    """
    return next(
        (
            (filter_, result)
            for filter_ in _FILTER_BY
            if (result := [datum for datum in data if datum.__getattribute__(filter_)])
        ),
        (None, data),
    )


def _should_run(site: dict):
    soil_type_nodes = split_nodes_by_dates(get_soil_type_nodes(site))

    filtered_by, soil_type_data = _filter_data_by_depth_availability(
        [_extract_soil_type_data(node) for node in soil_type_nodes]
    )

    inventory = (
        _classify_soil_type_data(soil_type_data)
        if soil_type_data
        else _DEFAULT_INVENTORY
    )

    should_run = all([inventory])

    for term_id in MEASUREMENT_TERM_IDS:

        logRequirements(
            site,
            model=MODEL,
            term=term_id,
            soil_type_data=_format_soil_data(soil_type_data),
            filtered_by=format_str(filtered_by),
        )

        logShouldRun(site, MODEL, term_id, should_run)

    return should_run, inventory


def get_soil_type_nodes(site: dict) -> list[dict]:
    measurements = site.get("measurements", [])
    return next(
        (
            nodes
            for term_type in _INPUT_TERM_TYPES
            if (nodes := filter_list_term_type(measurements, term_type))
        ),
        [],
    )


_INVENTORY_KEY_TO_FIELD_KEY = {
    "depth_upper": "depthUpper",
    "depth_lower": "depthLower",
    "date": "dates",
}
_INVENTORY_KEY_TO_FIELD_VALUE = {"date": lambda x: [x]}


def _key_to_measurement_fields(key: _InventoryKey):
    return {
        _INVENTORY_KEY_TO_FIELD_KEY.get(k, k): _INVENTORY_KEY_TO_FIELD_VALUE.get(
            k, lambda x: x
        )(v)
        for k, v in key._asdict().items()
        if v is not None
    }


def _run(inventory: _SoilTypeInventory) -> list[dict]:
    return flatten(
        [
            _measurement(term_id, value=[value], **_key_to_measurement_fields(key))
            for term_id, value in value.items()
        ]
        for key, value in inventory.items()
    )


def run(site: dict):
    should_run, valid_inventory = _should_run(site)
    return _run(valid_inventory) if should_run else []
