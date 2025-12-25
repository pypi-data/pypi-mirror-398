from collections import defaultdict
from datetime import datetime
from functools import reduce
from dateutil.relativedelta import relativedelta
from typing import Any, Callable, Union

from hestia_earth.schema import TermTermType
from hestia_earth.utils.date import _get_datestr_format, gapfill_datestr
from hestia_earth.utils.model import find_term_match, filter_list_term_type
from hestia_earth.utils.tools import (
    flatten,
    safe_parse_date,
    safe_parse_float,
    non_empty_list,
)
from hestia_earth.utils.lookup import download_lookup, get_table_value

from hestia_earth.models.log import debugValues
from hestia_earth.models.utils.input import get_total_irrigation_m3
from hestia_earth.models.utils.blank_node import split_node_by_dates
from hestia_earth.models.utils.cycle import get_ecoClimateZone
from hestia_earth.models.utils.date import (
    _datetime_range_duration,
    calc_datetime_range_intersection_duration,
    datetime_within_range,
    DatetimeRange,
    validate_startDate_endDate,
)
from hestia_earth.models.utils.group_nodes import (
    VALID_DATE_FORMATS_GROUP_NODES_BY_TIME_PERIOD,
    _FieldMode,
)
from hestia_earth.models.utils.term import get_lookup_value, get_milkYield_terms
from . import MODEL

# From IPCC2019 Indirect N2O emission factor, in N [avg, min, max, std]
COEFF_NO3_N2O = [0.011, 0.00, 0.02, 0.005]
# Volatilized Nitrogen as NH3-N and NOx-N per kg N applied organic fertilisers and animal dung and urine
COEFF_N_NH3NOX_organic_animal = [0.21, 0.00, 0.31, 0.0775]
# Volatilized Nitrogen as NH3-N and NOx-N per kg N applied inorganic fertilisers
COEFF_N_NH3NOX_inorganic = [0.11, 0.02, 0.33, 0.0775]


def get_FracLEACH_H(cycle: dict, term_id: str):
    eco_climate_zone = get_ecoClimateZone(cycle)
    is_eco_climate_zone_dry = eco_climate_zone % 2 == 0
    irrigation_value_m3 = get_total_irrigation_m3(cycle)
    is_drip_irrigated = (
        find_term_match(cycle.get("practices", []), "irrigatedDripIrrigation", None)
        is not None
    )

    debugValues(
        cycle,
        model=MODEL,
        term=term_id,
        is_eco_climate_zone_dry=is_eco_climate_zone_dry,
        irrigation_value_m3=irrigation_value_m3,
        is_drip_irrigated=is_drip_irrigated,
    )

    return (
        (0, 0, 0, 0)
        if all(
            [
                is_eco_climate_zone_dry,
                any([irrigation_value_m3 <= 250, is_drip_irrigated]),
            ]
        )
        else (0.24, 0.01, 0.73, 0.18)
    )  # value, min, max, sd


# Indirect N2O emissions from volatilized NH3 and NOx
def get_FracNH3NOx_N2O(cycle: dict, term_id: str):
    eco_climate_zone = get_ecoClimateZone(cycle)
    is_eco_climate_zone_dry = eco_climate_zone % 2 == 0
    irrigation_value_m3 = get_total_irrigation_m3(cycle)
    is_drip_irrigated = (
        find_term_match(cycle.get("practices", []), "irrigatedDripIrrigation", None)
        is not None
    )

    debugValues(
        cycle,
        model=MODEL,
        term=term_id,
        is_eco_climate_zone_dry=is_eco_climate_zone_dry,
        irrigation_value_m3=irrigation_value_m3,
        is_drip_irrigated=is_drip_irrigated,
    )

    return (
        (0.005, 0, 0.011, 0.00275)
        if all(
            [
                is_eco_climate_zone_dry,
                any([irrigation_value_m3 <= 250, is_drip_irrigated]),
            ]
        )
        else (0.014, 0.011, 0.017, 0.0015)
    )  # value, min, max, sd


def get_yield_dm(term_id: str, term: dict):
    return safe_parse_float(
        get_lookup_value(
            term, "IPCC_2019_Ratio_AGRes_YieldDM", model=MODEL, term=term_id
        ),
        default=None,
    )


def get_milkYield_practice(node: dict):
    terms = get_milkYield_terms()
    return next(
        (p for p in node.get("practices", []) if p.get("term", {}).get("@id") in terms),
        {},
    )


def check_consecutive(ints: list[int]) -> bool:
    """
    Checks whether a list of integers are consecutive.

    Used to determine whether annualised data is complete from every year from beggining to end.

    Parameters
    ----------
    ints : list[int]
        A list of integer values.

    Returns
    -------
    bool
        Whether or not the list of integers is consecutive.
    """
    range_list = list(range(min(ints), max(ints) + 1)) if ints else []
    return all(a == b for a, b in zip(ints, range_list))


N2O_FACTORS = {
    # All N inputs in dry climate
    "dry": {"value": 0.005, "min": 0, "max": 0.011},
    "wet": {
        # Synthetic fertiliser inputs in wet climate
        TermTermType.INORGANICFERTILISER: {"value": 0.016, "min": 0.013, "max": 0.019},
        # Other N inputs in wet climate
        TermTermType.ORGANICFERTILISER: {"value": 0.006, "min": 0.001, "max": 0.011},
        TermTermType.CROPRESIDUE: {"value": 0.006, "min": 0.001, "max": 0.011},
    },
    "default": {"value": 0.01, "min": 0.001, "max": 0.018},
    "flooded_rice": {"value": 0.004, "min": 0, "max": 0.029},
}


def _get_waterRegime_lookup(model_term_id: str, practice: dict, col: str):
    return safe_parse_float(
        get_lookup_value(
            practice.get("term", {}), col, model=MODEL, term=model_term_id
        ),
        default=None,
    )


def _is_wet(ecoClimateZone: str = None):
    lookup = download_lookup("ecoClimateZone.csv")
    return (
        None
        if ecoClimateZone is None
        else get_table_value(lookup, "ecoClimateZone", int(ecoClimateZone), "wet")
    )


def ecoClimate_factors(
    factors: dict, input_term_type: TermTermType = None, ecoClimateZone: str = None
):
    is_wet = _is_wet(ecoClimateZone)
    factors_key = "default" if is_wet is None else "wet" if is_wet else "dry"
    return (
        factors[factors_key].get(input_term_type, factors[factors_key]),
        ecoClimateZone is None,
    )


def _flooded_rice_factors(model_term_id: str, cycle: dict):
    lookup_name = "IPCC_2019_N2O_rice"
    practices = filter_list_term_type(
        cycle.get("practices", []), TermTermType.WATERREGIME
    )
    practice = next(
        (
            p
            for p in practices
            if _get_waterRegime_lookup(model_term_id, p, lookup_name) is not None
        ),
        None,
    )

    factors = (
        {
            "value": _get_waterRegime_lookup(model_term_id, practice, lookup_name),
            "min": _get_waterRegime_lookup(
                model_term_id, practice, lookup_name + "-min"
            ),
            "max": _get_waterRegime_lookup(
                model_term_id, practice, lookup_name + "-max"
            ),
        }
        if practice
        else N2O_FACTORS["flooded_rice"]
    )

    return (factors, practice is None)


def get_N2O_factors(
    model_term_id: str,
    cycle: dict,
    input_term_type: TermTermType,
    ecoClimateZone: str = None,
    flooded_rice: bool = False,
):
    return (
        _flooded_rice_factors(model_term_id, cycle)
        if flooded_rice
        else ecoClimate_factors(N2O_FACTORS, input_term_type, ecoClimateZone)
    )


def _should_run_node_by_end_date(node: dict) -> bool:
    """
    Validate nodes for `group_nodes_by_year` using the "startDate" and "endDate" fields.
    """
    return _get_datestr_format(
        node.get("endDate")
    ) in VALID_DATE_FORMATS_GROUP_NODES_BY_TIME_PERIOD and validate_startDate_endDate(
        node
    )


def _should_run_node_by_dates(node: dict) -> bool:
    """
    Validate nodes for `group_nodes_by_year` using the "dates" field.
    """
    value = node.get("value")
    dates = node.get("dates")
    return (
        value
        and dates
        and len(dates) > 0
        and len(value) == len(dates)
        and all(
            _get_datestr_format(datestr)
            in VALID_DATE_FORMATS_GROUP_NODES_BY_TIME_PERIOD
            for datestr in node.get("dates")
        )
    )


_GROUP_NODES_BY_YEAR_MODE_TO_SHOULD_RUN_NODE_FUNCTION: dict[
    _FieldMode, Callable[[dict], bool]
] = {
    "dates": _should_run_node_by_dates,
    "startDate endDate": _should_run_node_by_end_date,
}


def _get_node_datetime_range_by_startDate_endDate(
    node: dict, default_node_duration: int = 1
) -> Union[DatetimeRange, None]:
    """
    Get the datetime range from a node's "startDate" and "endDate" fields.

    If "startDate" field is not available, a start date is calculated using the end date
    and `default_node_duration`.
    """
    end = safe_parse_date(gapfill_datestr(node.get("endDate"), "end"))
    start = (
        safe_parse_date(gapfill_datestr(node.get("startDate"), "start"))
        or end - relativedelta(years=default_node_duration, seconds=-1)
        if end
        else None
    )

    valid = isinstance(start, datetime) and isinstance(end, datetime)
    return DatetimeRange(start, end) if valid else None


def _get_node_datetime_range_by_dates(node: dict, **_) -> Union[DatetimeRange, None]:
    """
    Get the datetime range from a node's "dates" field.
    """
    dates = node.get("dates")
    end = max(
        non_empty_list(
            safe_parse_date(gapfill_datestr(datestr, "end")) for datestr in dates
        ),
        default=None,
    )
    start = min(
        non_empty_list(
            safe_parse_date(gapfill_datestr(datestr, "start")) for datestr in dates
        ),
        default=None,
    )

    valid = isinstance(start, datetime) and isinstance(end, datetime)
    return DatetimeRange(start, end) if valid else None


_GROUP_NODES_BY_YEAR_MODE_TO_GET_DATETIME_RANGE_FUNCTION: dict[
    _FieldMode, Callable[[dict], DatetimeRange]
] = {
    "dates": _get_node_datetime_range_by_dates,
    "startDate endDate": _get_node_datetime_range_by_startDate_endDate,
}


def _build_time_fraction_dict(
    group_datetime_range: DatetimeRange, node_datetime_range: DatetimeRange
) -> dict:
    """
    Build a dictionary containing fractions of the year and node duration based on datetime ranges.

    This function calculates the duration of the group or year, the duration of the node, and the intersection
    duration between the two. It then computes the fractions of the year and node duration represented by the
    intersection. The results are returned in a dictionary.

    Parameters
    ----------
    group_datetime_range : DatetimeRange
        The datetime range representing the entire group or year.
    node_datetime_range : DatetimeRange
        The datetime range representing the node.

    Returns
    -------
    dict
        A dictionary containing "fraction_of_group_duration" and "fraction_of_node_duration".
    """
    group_duration = _datetime_range_duration(group_datetime_range, add_second=True)
    node_duration = _datetime_range_duration(node_datetime_range, add_second=True)

    intersection_duration = calc_datetime_range_intersection_duration(
        node_datetime_range, group_datetime_range, add_second=True
    )

    fraction_of_group_duration = (
        intersection_duration / group_duration if group_duration > 0 else 0
    )
    fraction_of_node_duration = (
        intersection_duration / node_duration if node_duration > 0 else 0
    )

    return {
        "fraction_of_group_duration": fraction_of_group_duration,
        "fraction_of_node_duration": fraction_of_node_duration,
    }


def _validate_time_fraction_dict(
    time_fraction_dict: dict, is_final_group: bool
) -> bool:
    """
    Return `True` if the the node intersections with a year group by
    more than 30% OR the year group represents more than 50% of a node's
    duration. Return `False` otherwise.

    This is to prevent cycles/managements being categorised into a year group
    when due to overlapping by just a few days. In these cases, nodes will only
    be counted in the year group if the majority of that node takes place in
    that year.
    """
    FRACTION_OF_GROUP_DURATION_THRESHOLD = 0.3
    FRACTION_OF_NODE_DURATION_THRESHOLD = 0.5

    return any(
        [
            time_fraction_dict["fraction_of_group_duration"]
            > FRACTION_OF_GROUP_DURATION_THRESHOLD,
            time_fraction_dict["fraction_of_node_duration"]
            > FRACTION_OF_NODE_DURATION_THRESHOLD,
            is_final_group
            and time_fraction_dict["fraction_of_node_duration"]
            == FRACTION_OF_NODE_DURATION_THRESHOLD,
        ]
    )


def group_nodes_by_year(
    nodes: list[dict],
    default_node_duration: int = 1,
    sort_result: bool = True,
    include_spillovers: bool = False,
    inner_key: Union[Any, None] = None,
    mode: _FieldMode = "startDate endDate",
) -> dict[int, list[dict]]:
    """
    Group nodes by year based on either their "startDate" and "endDate" fields or their
    "dates" field. Incomplete date strings are gap-filled automatically using `_gapfill_datestr`
    function.

    Parameters
    ----------
    nodes : list[dict]
        A list of nodes with start and end date information.
    default_node_duration : int, optional
        Default duration of a node years if start date is not available, by default 1.
    sort_result : bool, optional
        Flag to sort the result by year, by default True.
    include_spillovers : bool, optional
        If grouping by start and end date, flag to determine whether nodes should be included in year groups that they
        spill-over into. If `False` year groups will not include nodes that overlap with them by less than 30% of a
        year, unless it is the only year group it overlaps with. By default False.
    inner_key: Any | None
        An optional inner dictionary key for the outputted annualised groups (can be used to merge annualised
        dictionaries together), default value: `None`.
    mode : _FieldMode, optional
        The mode to determine how nodes are grouped by year (`"dates"` or `"startDate endDate"`).

    Returns
    -------
    dict[int, list[dict]]
        A dictionary where keys are years and values are lists of nodes.
    """

    should_run_node = _GROUP_NODES_BY_YEAR_MODE_TO_SHOULD_RUN_NODE_FUNCTION[mode]
    get_node_datetime_range = _GROUP_NODES_BY_YEAR_MODE_TO_GET_DATETIME_RANGE_FUNCTION[
        mode
    ]

    valid_nodes = non_empty_list(
        flatten(split_node_by_dates(node) for node in nodes if should_run_node(node))
    )

    def group_node(groups: dict, index: int):
        node = valid_nodes[index]

        node_datetime_range = get_node_datetime_range(
            node, default_node_duration=default_node_duration
        )

        range_start = node_datetime_range.start.year if node_datetime_range else 0
        range_end = node_datetime_range.end.year + 1 if node_datetime_range else 0

        for year in range(range_start, range_end):

            group_datetime_range = DatetimeRange(
                start=safe_parse_date(gapfill_datestr(year, "start")),
                end=safe_parse_date(gapfill_datestr(year, "end")),
            )

            is_final_year = datetime_within_range(
                node_datetime_range.end, group_datetime_range
            )

            time_fraction_dict = _build_time_fraction_dict(
                group_datetime_range, node_datetime_range
            )

            should_run = (
                mode == "dates"
                or include_spillovers
                or _validate_time_fraction_dict(time_fraction_dict, is_final_year)
            )

            should_run and groups[year].append(node | time_fraction_dict)

        return groups

    grouped = reduce(group_node, range(len(valid_nodes)), defaultdict(list))

    iterated = {
        year: {inner_key: group} if inner_key else group
        for year, group in grouped.items()
    }

    return dict(sorted(iterated.items())) if sort_result else iterated


def group_nodes_by_year_and_month(
    nodes: list[dict],
    default_node_duration: int = 1,
    sort_result: bool = True,
    inner_key: Union[Any, None] = None,
) -> dict[int, list[dict]]:
    """
    Group nodes by year based on either their "startDate" and "endDate" fields. Incomplete date strings are gap-filled
    automatically using `_gapfill_datestr` function.

    Returns a dict in the shape:
    ```
    {
        year (int): {
            month (int): nodes (list[dict])  # for each month 1 - 12
        }
    }
    ```

    Parameters
    ----------
    nodes : list[dict]
        A list of nodes with start and end date information.
    default_node_duration : int, optional
        Default duration of a node years if start date is not available, by default 1.
    sort_result : bool, optional
        Flag to sort the result by year, by default True.
    inner_key: Any | None
        An optional inner dictionary key for the outputted annualised groups (can be used to merge annualised
        dictionaries together), default value: `None`.

    Returns
    -------
    dict[int, list[dict]]
        A dictionary where keys are years and values are lists of nodes.
    """
    valid_nodes = [node for node in nodes if _should_run_node_by_end_date(node)]

    def group_node(groups: dict, index: int):
        node = valid_nodes[index]

        node_datetime_range = _get_node_datetime_range_by_startDate_endDate(
            node, default_node_duration=default_node_duration
        )

        range_start = node_datetime_range.start.year if node_datetime_range else 0
        range_end = node_datetime_range.end.year + 1 if node_datetime_range else 0

        for year in range(range_start, range_end):
            for month in range(1, 13):

                datestr_incomplete = f"{year}-{month:02}"
                group_datetime_range = DatetimeRange(
                    start=safe_parse_date(gapfill_datestr(datestr_incomplete, "start")),
                    end=safe_parse_date(gapfill_datestr(datestr_incomplete, "end")),
                )

                is_final_month = datetime_within_range(
                    node_datetime_range.end, group_datetime_range
                )
                time_fraction_dict = _build_time_fraction_dict(
                    group_datetime_range, node_datetime_range
                )
                should_run = _validate_time_fraction_dict(
                    time_fraction_dict, is_final_month
                )

                should_run and groups[year][month].append(node)

        return groups

    grouped = reduce(
        group_node, range(len(valid_nodes)), defaultdict(lambda: defaultdict(list))
    )

    iterated = {
        year: {inner_key: dict(group)} if inner_key else dict(group)
        for year, group in grouped.items()
    }

    return dict(sorted(iterated.items())) if sort_result else iterated
