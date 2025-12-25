from datetime import datetime
from typing import Any, Literal, NamedTuple, Optional

from hestia_earth.utils.date import (
    DatestrGapfillMode,
    diff_in,
    parse_gapfilled_datestr,
    TimeUnit,
)

from . import has_unique_key


DatetimeRange = NamedTuple("DatetimeRange", [("start", datetime), ("end", datetime)])
"""
A named tuple for storing a datetime range.

Attributes
----------
start : datetime
    The start of the datetime range.
end : datetime
    The end of the datetime range.
"""


def datetime_within_range(datetime: datetime, range: DatetimeRange) -> bool:
    """
    Determine whether or not a `datetime` falls within a `DatetimeRange`.
    """
    return range.start <= datetime <= range.end


def _datetime_range_duration(range: DatetimeRange, add_second=False) -> float:
    """
    Determine the length of a `DatetimeRange` in seconds.

    Option to `add_second` to account for 1 second between 23:59:59 and 00:00:00
    """
    return diff_in(*range, TimeUnit.SECOND, add_second=add_second)


def calc_datetime_range_intersection_duration(
    range_a: DatetimeRange, range_b: DatetimeRange, add_second=False
) -> float:
    """
    Determine the length of a `DatetimeRange` in seconds.

    Option to `add_second` to account for 1 second between 23:59:59 and 00:00:00
    """
    latest_start = max(range_a.start, range_b.start)
    earliest_end = min(range_a.end, range_b.end)

    intersection_range = DatetimeRange(start=latest_start, end=earliest_end)

    duration = _datetime_range_duration(intersection_range)

    # if less than 0 the ranges do not intersect, so return 0.
    return (
        _datetime_range_duration(intersection_range, add_second=add_second)
        if duration > 0
        else 0
    )


def parse_node_date(
    node: dict, key: Literal["startDate", "endDate"], default: Any = None
):
    gapfill_mode: DatestrGapfillMode = "start" if key == "startDate" else "end"
    return parse_gapfilled_datestr(
        node.get(key), gapfill_mode=gapfill_mode, default=default
    )


def nodes_have_same_dates(nodes: list) -> bool:
    """Return `True` if all nodes have the same `startDate` and `endDate`, `False` if otherwise."""
    return all([has_unique_key(nodes, "startDate"), has_unique_key(nodes, "endDate")])


def validate_startDate_endDate(node: dict) -> bool:
    """Return `True` if `node.startDate` is before `node.endDate`, `False` if otherwise."""
    start_date = parse_node_date(node, "startDate", datetime.min)
    end_date = parse_node_date(node, "endDate", datetime.min)

    return start_date < end_date


def get_last_date(node: dict, default=None) -> Optional[str]:
    """
    Get the last date of a node's date field
    """
    datestrs = node.get("dates", [])
    return sorted(datestrs)[-1] if len(datestrs) > 0 else default
