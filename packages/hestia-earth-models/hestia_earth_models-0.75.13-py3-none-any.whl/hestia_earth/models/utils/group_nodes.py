from collections import defaultdict
from datetime import datetime
from dateutil.relativedelta import relativedelta
from functools import reduce
from itertools import product
from pydash import get
from typing import Any, Callable, Hashable, Literal, Optional, Union

from hestia_earth.utils.date import (
    convert_datestr,
    DatestrFormat,
    DatestrGapfillMode,
    diff_in,
    gapfill_datestr,
    TimeUnit,
    TIME_UNIT_TO_DATESTR_FORMAT,
    validate_datestr_format,
)
from hestia_earth.utils.tools import (
    as_tuple,
    is_list_like,
    non_empty_list,
    safe_parse_date,
)

from .date import (
    calc_datetime_range_intersection_duration,
    DatetimeRange,
    parse_node_date,
    validate_startDate_endDate,
)

_Grouper = Callable[[dict, Hashable], Union[Hashable, tuple[Hashable]]]
"""
(node: dict) -> group_keys: Hashable | tuple[Hashable]
"""


def _get_group_by_field(node: dict, *, field: str, default: Hashable = None):
    value = get(node, field, default=default)
    return "-".join(str(v) for v in value) if is_list_like(value) else value


def _make_field_grouper(*, field: str, default: Hashable = None) -> _Grouper:
    def grouper(node: dict) -> Hashable:
        return _get_group_by_field(node, field=field, default=default)

    return grouper


def _get_end_start_date_group(
    node: dict,
    *,
    datestr_format: DatestrFormat = DatestrFormat.YEAR_MONTH_DAY,
    field: Literal["endDate", "startDate"],
    gapfill_mode: DatestrGapfillMode = "start",
    default: Hashable = None,
) -> Optional[str]:
    date = convert_datestr(node.get(field), datestr_format, gapfill_mode)
    return date if date else default


def _make_end_start_date_grouper(
    *,
    datestr_format: DatestrFormat = DatestrFormat.YEAR_MONTH_DAY,
    field: Literal["endDate", "startDate"],
    gapfill_mode: DatestrGapfillMode = "start",
    default: Hashable = None,
) -> _Grouper:
    def grouper(node: dict) -> Hashable:
        return _get_end_start_date_group(
            node,
            field=field,
            datestr_format=datestr_format,
            gapfill_mode=gapfill_mode,
            default=default,
        )

    return grouper


_SelectMode = Literal["all", "first", "last"]


_SELECT_FUNCTION: dict[_SelectMode, Callable[[list[str]], str]] = {
    "all": lambda dates: sorted(dates),
    "first": lambda dates: sorted(dates)[0:1],
    "last": lambda dates: sorted(dates)[-1:],
}


def _get_dates_groups(
    node: dict,
    *,
    datestr_format: DatestrFormat = DatestrFormat.YEAR_MONTH_DAY,
    gapfill_mode: DatestrGapfillMode = "start",
    select_mode: _SelectMode = "all",
    default: Hashable = None,
) -> Optional[str]:
    select_func = _SELECT_FUNCTION.get(select_mode)
    dates = node.get("dates", [])
    return (
        (
            convert_datestr(date, datestr_format, gapfill_mode)
            for date in select_func(dates)
        )
        if dates
        else default
    )


def _make_dates_grouper(
    *,
    datestr_format: DatestrFormat = DatestrFormat.YEAR_MONTH_DAY,
    gapfill_mode: DatestrGapfillMode = "start",
    select_mode: _SelectMode = "all",
    default: Hashable = None,
) -> _Grouper:
    def grouper(node: dict) -> Hashable:
        return _get_dates_groups(
            node,
            datestr_format=datestr_format,
            select_mode=select_mode,
            gapfill_mode=gapfill_mode,
            default=default,
        )

    return grouper


_FIELD_TO_GROUPER: dict[str, _Grouper] = {
    "dates": _make_dates_grouper(),
    "endDate": _make_end_start_date_grouper(gapfill_mode="end", field="endDate"),
    "startDate": _make_end_start_date_grouper(gapfill_mode="start", field="startDate"),
    None: lambda *_: None,
}


def _get_group_keys(
    node: dict, groupers: list[_Grouper]
) -> tuple[tuple[Hashable, ...], ...]:
    return tuple(product(*(as_tuple(grouper(node)) for grouper in groupers)))


def _get_groupers(by: list[Union[str, _Grouper]]) -> list[_Grouper]:
    return (
        [
            (
                x
                if isinstance(x, Callable)
                else _FIELD_TO_GROUPER.get(x, _make_field_grouper(field=x))
            )
            for x in as_tuple(by)
        ]
        if by
        else as_tuple(_FIELD_TO_GROUPER[None])
    )


def _sort_grouped(grouped: dict) -> dict:
    """
    Safely sort group keys, all `None` keys are moved to the end.
    """
    return dict(
        sorted(
            grouped.items(),
            key=lambda kv: as_tuple((x is None, x) for x in as_tuple(kv[0])),
        )
    )


def group_nodes_by(
    nodes: list[dict],
    by: Union[str, _Grouper, list[Union[str, _Grouper]]],
    inner_key: Union[Hashable, None] = None,
    sort: bool = True,
    unwrap_single_element_group_keys: bool = True,
) -> dict:
    """
    Group a list of nodes by the value of a field, the output of a grouper function, or a combination multiple fields
    and grouper functions.

    Nested fields can be specified using `.` delimited strings (e.g., `term.@id`).

    Grouper functions are used to determine which groups a node is part of. They should follow the signature:

    ```
    (node: dict) -> group_keys: Hashable | tuple[Hashable]
    ```

    If a grouper function returns a single value (or a tuple containing one value) the node will be added to the group
    corresponding to that value. If a grouper function returns multiple values, the node will be added to multiple
    groups corresponding to each value.

    If multiple fields/groupers are specified, the final group keys will be a tuple with a value for each grouper in
    the order they are specified. e.g., `by=["depthUpper", "depthLower]` will result in groups with keys with the shape
    `(node.depthUpper: float, node.depthLower: float)`.

    Nodes are added to groups WITHOUT modification or validation. This is a breaking change from the deprecated
    `blank_node.group_nodes_by_year` and `blank_node.group_nodes_by_year_and_month` functions. Any node transformations
    (e.g., splitting a node with multiple measurement values into multiple nodes with single measurement values) or
    validations (e.g., filtering out nodes without required data) must be performed before nodes are grouped.

    Parameters
    ----------
    nodes: list[dict]
        A list of HESTIA nodes (or other `dict` objects).

    by: str | _Grouper | list[str] | list[_Grouper], optional, default = `True`
        A node field (`str`) a grouper function with signature `(node: dict) -> group_keys: Hashable | tuple[Hashable]`
        or a list of such.

    inner_key: Hashable | None, optional, default = `None`
        An optional inner key to wrap grouped nodes in. Useful for occasions where the grouped `dict` will be merged
        with other `dict`s.

    sort: bool, optional, default = `True`
        A flag to determine whether the grouped `dict` will be sorted before being returned.

    unwrap_single_element_group_keys: bool, optional, default = `True`
        A flag to determine whether group keys with a single value are returned as a tuple `(value, )` or a single
        unwrapped `value`.

    Returns
    -------
    dict[Hashable, list[dict]]
        A dictionary mapping group keys to lists of nodes within that group.
    """
    groupers = _get_groupers(by)

    def _group(result: defaultdict, node: dict) -> defaultdict:
        keys = _get_group_keys(node, groupers)

        for key in keys:
            key_ = key[0] if unwrap_single_element_group_keys and len(key) == 1 else key
            result[key_] += [node]

        return result

    grouped = dict(reduce(_group, nodes, defaultdict(list)))

    iterated = (
        {year: {inner_key: group} for year, group in grouped.items()}
        if inner_key
        else grouped
    )

    return _sort_grouped(iterated) if sort else iterated


def group_nodes_by_term_id(
    nodes: list[dict],
    inner_key: Union[Any, None] = None,
    sort: bool = True,
) -> dict:
    """
    Group nodes by `term.@id`.

    Nodes without relevant data are sorted into `None` group.
    """
    return group_nodes_by(nodes, "term.@id", inner_key=inner_key, sort=sort)


def group_nodes_by_depthUpper_depthLower(
    nodes: list[dict],
    inner_key: Union[Any, None] = None,
    sort: bool = True,
) -> dict:
    """
    Group nodes by (`depthUpper`, `depthLower`).
    """
    return group_nodes_by(
        nodes, ["depthUpper", "depthLower"], inner_key=inner_key, sort=sort
    )


def group_nodes_by_last_date(
    nodes: list[dict],
    inner_key: Union[Any, None] = None,
    sort: bool = True,
) -> dict:
    """
    Group nodes by the final date in their `dates` field.

    Incomplete dates are gapfilled to the latest possible date (e.g., `2000-06` -> `2000-06-30`) and group keys follow
    datestr format `YYYY-MM-DD`.
    """
    grouper = _make_dates_grouper(gapfill_mode="end", select_mode="last")
    return group_nodes_by(nodes, grouper, inner_key=inner_key, sort=sort)


def group_nodes_by_endDate(
    nodes: list[dict],
    inner_key: Union[Any, None] = None,
    sort: bool = True,
) -> dict:
    """
    Group nodes by `endDate` field.

    Incomplete dates are gapfilled to the latest possible date (e.g., `2000-06` -> `2000-06-30`) and group keys follow
    datestr format `YYYY-MM-DD`.
    """
    return group_nodes_by(nodes, "endDate", inner_key=inner_key, sort=sort)


def group_nodes_by_term_id_value_and_properties(
    nodes: list[dict],
    inner_key: Union[Any, None] = None,
    sort: bool = True,
) -> dict:
    """
    Group nodes by (`term.@id`, `value` and `properties`).
    """

    def _property_grouper(node: dict) -> str:
        properties = node.get("properties", [])
        return (
            "_".join(
                non_empty_list(
                    [
                        ":".join(
                            non_empty_list(
                                [p.get("term", {}).get("@id"), f"{p.get('value')}"]
                            )
                        )
                        for p in properties
                    ]
                )
            )
            if properties
            else None
        )

    return group_nodes_by(
        nodes,
        ["term.@id", "value", _property_grouper],
        inner_key=inner_key,
        sort=sort,
    )


VALID_DATE_FORMATS_GROUP_NODES_BY_TIME_PERIOD = {
    DatestrFormat.YEAR,
    DatestrFormat.YEAR_MONTH,
    DatestrFormat.YEAR_MONTH_DAY,
    DatestrFormat.YEAR_MONTH_DAY_HOUR_MINUTE_SECOND,
}


_FieldMode = Literal["dates", "startDate endDate"]


def _should_run_node_by_startDate_endDate(node: dict) -> bool:
    """
    Validate nodes for `group_nodes_by_year` using the "startDate" and "endDate" fields.

    "startDate" is not mandatory, but must be in a valid format if provided.
    """
    start_date = node.get("startDate")
    end_date = node.get("endDate")
    return (
        validate_datestr_format(end_date, VALID_DATE_FORMATS_GROUP_NODES_BY_TIME_PERIOD)
        and (
            start_date is None
            or validate_datestr_format(
                node.get("startDate"), VALID_DATE_FORMATS_GROUP_NODES_BY_TIME_PERIOD
            )
        )
        and validate_startDate_endDate(node)
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
            validate_datestr_format(
                datestr, VALID_DATE_FORMATS_GROUP_NODES_BY_TIME_PERIOD
            )
            for datestr in node.get("dates")
        )
    )


GROUP_NODES_BY_YEAR_MODE_TO_SHOULD_RUN_NODE_FUNCTION: dict[_FieldMode, Callable] = {
    "dates": _should_run_node_by_dates,
    "startDate endDate": _should_run_node_by_startDate_endDate,
}


def _get_node_start_end_from_startDate_endDate(
    node: dict, *, default_node_duration: relativedelta
) -> DatetimeRange:
    """
    Get the datetime range from a node's "startDate" and "endDate" fields.

    If "startDate" field is not available, a start date is calculated using the end date and `default_node_duration`.
    """
    end = parse_node_date(node, "endDate")
    start = (
        parse_node_date(node, "startDate") or end - default_node_duration
        if end
        else None
    )

    return start, end


def _get_node_start_end_from_dates(node: dict, **_) -> DatetimeRange:
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

    return start, end


_FIELD_MODE_TO_GET_START_END_FUNCTION: dict[
    _FieldMode, Callable[[dict, Any], tuple[str, str]]
] = {
    "dates": _get_node_start_end_from_dates,
    "startDate endDate": _get_node_start_end_from_startDate_endDate,
}


_UNIT_TO_GET_FIRST_PERIOD = {
    TimeUnit.YEAR: lambda d: datetime(d.year, 1, 1, 0, 0),
    TimeUnit.MONTH: lambda d: datetime(d.year, d.month, 1, 0, 0),
}


_UNIT_TO_TIMESTEP = {
    TimeUnit.YEAR: relativedelta(years=1),
    TimeUnit.MONTH: relativedelta(months=1),
}


def _get_time_period_groups(
    node: dict,
    *,
    field_mode: _FieldMode,
    unit_mode: TimeUnit,
    default_node_duration: relativedelta = relativedelta(years=1, seconds=-1),
) -> tuple[Hashable]:
    get_node_start_end_func = _FIELD_MODE_TO_GET_START_END_FUNCTION[field_mode]
    timestep = _UNIT_TO_TIMESTEP[unit_mode]
    datestr_format = TIME_UNIT_TO_DATESTR_FORMAT[unit_mode].value
    get_first_period = _UNIT_TO_GET_FIRST_PERIOD[unit_mode]

    start, end = get_node_start_end_func(
        node, default_node_duration=default_node_duration
    )

    node_datetime_range = DatetimeRange(start, end)

    diff = diff_in(
        *node_datetime_range, unit_mode, calendar=True
    )  # get node duration in calendar units
    first_period = get_first_period(node_datetime_range.start)

    potential_periods = [
        DatetimeRange(
            first_period + timestep * n,
            first_period + timestep * (n + 1) - relativedelta(seconds=1),
        )
        for n in range(diff + 2)
    ]

    groups = as_tuple(
        period.start.strftime(datestr_format)
        for period in potential_periods
        if calc_datetime_range_intersection_duration(node_datetime_range, period)
    )

    return groups


def _group_nodes_by_time_period(
    nodes: list[dict],
    field_mode: _FieldMode = "startDate endDate",
    inner_key: Union[Any, None] = None,
    sort: bool = True,
    unit_mode: Literal[TimeUnit.YEAR, TimeUnit.MONTH] = TimeUnit.YEAR,
) -> dict:

    def grouper(node: dict) -> str:
        return _get_time_period_groups(node, field_mode=field_mode, unit_mode=unit_mode)

    should_run_node_func = GROUP_NODES_BY_YEAR_MODE_TO_SHOULD_RUN_NODE_FUNCTION[
        field_mode
    ]
    valid_nodes = [node for node in nodes if should_run_node_func(node)]

    return group_nodes_by(valid_nodes, grouper, inner_key=inner_key, sort=sort)


def group_nodes_by_year(
    nodes: list[dict],
    field_mode: _FieldMode = "startDate endDate",
    inner_key: Union[Any, None] = None,
    sort: bool = True,
) -> dict:
    """
    Group nodes by calendar year.

    Nodes are considered to take place during a year if ANY portion of their duration overlaps with the start and end
    of a calendar year.

    Unlike the deprecated `blank_node.group_nodes_by_year` function, nodes that spill over into a year by a small
    duration are NOT omitted from year groups. These "spill over" nodes must be removed by other means after this
    function as run.

    Group keys follow datestr format `YYYY`.
    """
    return _group_nodes_by_time_period(
        nodes,
        field_mode=field_mode,
        inner_key=inner_key,
        unit_mode=TimeUnit.YEAR,
        sort=sort,
    )


def group_nodes_by_month(
    nodes: list[dict],
    field_mode: _FieldMode = "startDate endDate",
    inner_key: Union[Any, None] = None,
    sort: bool = True,
) -> dict:
    """
    Group nodes by calendar month.

    Nodes are considered to take place during a year if ANY portion of their duration overlaps with the start and end
    of a calendar month.

    Group keys follow datestr format `YYYY-MM`.
    """
    return _group_nodes_by_time_period(
        nodes,
        field_mode=field_mode,
        inner_key=inner_key,
        unit_mode=TimeUnit.MONTH,
        sort=sort,
    )


def _should_group_node_by_consecutive_dates(node: dict) -> bool:
    return node.get("startDate") and node.get("endDate")


def _group_nodes_by_consecutive_dates(nodes: list[dict]) -> list[list[dict]]:
    groups = []
    group = []

    # make sure the nodes are sorted by dates to group by consecutive dates
    for node in sorted(
        nodes,
        key=lambda n: ";".join(
            non_empty_list(
                [
                    str(parse_node_date(n, "startDate")),
                    str(parse_node_date(n, "endDate")),
                ]
            )
        ),
    ):
        if not group or (
            _should_group_node_by_consecutive_dates(node)
            and diff_in(
                parse_node_date(group[-1], "endDate"),
                parse_node_date(node, "startDate"),
                TimeUnit.DAY,
                add_second=True,
            )
            <= 1
        ):
            group.append(node)
        else:
            groups.append(group)
            group = [node]

    if group:
        groups.append(group)

    return groups


def _get_consecutive_dates_group_key(nodes: list[dict]) -> tuple[str, str]:
    start = min(
        (
            parse_node_date(node, "startDate")
            for node in nodes
            if node.get("startDate") is not None
        ),
        default=None,
    )
    end = max(
        (
            parse_node_date(node, "endDate")
            for node in nodes
            if node.get("endDate") is not None
        ),
        default=None,
    )

    return as_tuple(
        (
            date.strftime(DatestrFormat.YEAR_MONTH_DAY.value)
            if isinstance(date, datetime)
            else None
        )
        for date in (start, end)
    )


def group_nodes_by_consecutive_dates(
    nodes: list[dict],
    inner_key: Union[Any, None] = None,
    sort: bool = True,
) -> dict:
    """
    Groups dictionaries in a dict based on consecutive start and end dates within a 1-day tolerance.

    Parameters
    ----------
    nodes : list[dict]
        A list of dictionaries containing 'startDate' and 'endDate' keys.

    Returns
    -------
    dict[tuple[str, str]: list[dict]]
        A dictionary mapping group keys (`startDate`, `endDate`) to lists of nodes within that group.
    """
    grouped = {
        _get_consecutive_dates_group_key(group): group
        for group in _group_nodes_by_consecutive_dates(nodes)
    }

    iterated = (
        {year: {inner_key: group} for year, group in grouped.items()}
        if inner_key
        else grouped
    )

    return _sort_grouped(iterated) if sort else iterated


def _should_group_node_by_consecutive_depths(node: dict) -> bool:
    return node.get("depthUpper") is not None and node.get("depthLower") is not None


def _group_nodes_by_consecutive_depths(nodes: list[dict]) -> list[list[dict]]:
    groups = []
    group = []

    valid_nodes = [
        node for node in nodes if _should_group_node_by_consecutive_depths(node)
    ]

    # make sure the nodes are sorted by dates to group by consecutive dates
    for node in sorted(
        valid_nodes,
        key=lambda n: (n.get("depthUpper", n.get("depthLower"))),
    ):
        if not group or (
            node.get("depthUpper") - group[-1].get("depthLower") < 1  # Less than 1cm
        ):
            group.append(node)
        else:
            groups.append(group)
            group = [node]

    if group:
        groups.append(group)

    return groups


def _get_consecutive_depths_group_key(nodes: list[dict]) -> tuple[str, str]:
    start = min(
        (
            node.get("depthUpper")
            for node in nodes
            if node.get("depthUpper") is not None
        ),
        default=None,
    )
    end = max(
        (
            node.get("depthLower")
            for node in nodes
            if node.get("depthLower") is not None
        ),
        default=None,
    )

    return (start, end)


def group_nodes_by_consecutive_depths(
    nodes: list[dict],
    inner_key: Union[Any, None] = None,
    sort: bool = True,
) -> dict:
    """
    Groups dictionaries in a dict based on consecutive depthUpper and depthLower within a 1-centimetre tolerance.

    Parameters
    ----------
    nodes : list[dict]
        A list of dictionaries containing 'depthUpper' and 'depthLower' keys.

    Returns
    -------
    dict[tuple[float, float]: list[dict]]
        A dictionary mapping group keys (`depthUpper`, `depthLower`) to lists of nodes within that group.
    """
    grouped = {
        _get_consecutive_depths_group_key(group): group
        for group in _group_nodes_by_consecutive_depths(nodes)
    }

    iterated = (
        {year: {inner_key: group} for year, group in grouped.items()}
        if inner_key
        else grouped
    )

    return _sort_grouped(iterated) if sort else iterated
