from functools import reduce
from typing import Callable, Optional, Union

from hestia_earth.schema import TermTermType
from hestia_earth.utils.date import (
    DatestrGapfillMode,
    diff_in,
    gapfill_datestr,
    OLDEST_DATE,
    TimeUnit,
)
from hestia_earth.utils.model import filter_list_term_type

from .blank_node import filter_list_term_id
from .group_nodes import (
    group_nodes_by,
    group_nodes_by_depthUpper_depthLower,
    group_nodes_by_endDate,
    group_nodes_by_last_date,
)


MAX_DEPTH = 1000


def closest_depthUpper_depthLower(
    nodes: list[dict],
    target_depth_upper: float,
    target_depth_lower: float,
    depth_strict: bool = True,
) -> list[dict]:
    """
    Select the nodes with the closest `depthUpper` and `depthLower to the target.
    """
    DEFAULT_KEY = (None, None)

    def depth_distance(key: tuple[Optional[float], Optional[float]]) -> float:
        return sum(
            abs(depth - target if isinstance(depth, (float, int)) else 9999)
            for depth, target in zip(key, (target_depth_upper, target_depth_lower))
        )

    grouped = group_nodes_by_depthUpper_depthLower(nodes)
    nearest_key = min(grouped.keys(), key=depth_distance, default=DEFAULT_KEY)

    return (
        grouped.get(nearest_key, [])
        if depth_distance(nearest_key) <= 0 or not depth_strict
        else []
    )


def closest_depth(
    nodes: list[dict],
    target_depth: float,
    depth_strict: bool = True,
) -> list[dict]:
    """
    Select the nodes with the closest `depth` to the target.
    """
    DEFAULT_KEY = (None, None)

    def depth_distance(key: Optional[float]) -> float:
        return abs(key - target_depth if isinstance(key, (float, int)) else 9999)

    grouped = group_nodes_by(nodes, by="depth")
    nearest_key = min(grouped.keys(), key=depth_distance, default=DEFAULT_KEY)

    return (
        grouped.get(nearest_key, [])
        if depth_distance(nearest_key) <= 0 or not depth_strict
        else []
    )


def closest_last_date(
    nodes: list[dict], target_date: str, mode: DatestrGapfillMode = "end"
) -> list[dict]:
    DEFAULT_KEY = None

    def date_distance(date: str) -> float:
        date_ = date if date != DEFAULT_KEY else OLDEST_DATE
        return abs(
            diff_in(
                gapfill_datestr(date_, mode),
                gapfill_datestr(target_date, mode),
                TimeUnit.SECOND,
            )
        )

    grouped = group_nodes_by_last_date(nodes)
    nearest_key = min(grouped.keys(), key=date_distance, default=DEFAULT_KEY)

    return grouped.get(nearest_key, [])


def closest_endDate(
    nodes: list[dict], target_date: str, mode: DatestrGapfillMode = "end"
) -> list[dict]:
    DEFAULT_KEY = None

    def date_distance(date: str) -> float:
        date_ = date if date != DEFAULT_KEY else OLDEST_DATE
        return abs(
            diff_in(
                gapfill_datestr(date_, mode),
                gapfill_datestr(target_date, mode),
                TimeUnit.SECOND,
            )
        )

    grouped = group_nodes_by_endDate(nodes)
    nearest_key = min(grouped.keys(), key=date_distance, default=DEFAULT_KEY)

    return grouped.get(nearest_key, [])


def prioritise_nodes_where(nodes: list[dict], condition: Callable[[dict], bool]):
    """
    Filter nodes by a condition. If any nodes pass the condition, return them. If no nodes pass the condition, return
    the original list of nodes.

    Used in cases where you would prefer to run a model using certain types of nodes (_e.g._, nodes with
    `depthLower` >= `30`), but the model can run with other nodes, if the preferred nodes are not available.

    Parameters
    ----------
    nodes : list[dict]
        A list of HESTIA nodes.
    condition : Callable
        Validation function with signature `(dict) -> bool`

    Returns
    -------
    list[dict]
        A list of HESTIA nodes.
    """
    return [node for node in nodes if condition(node)] or nodes


def _shallowest_node(nodes: list) -> dict:
    min_depth = min([m.get("depthUpper", MAX_DEPTH) for m in nodes])
    return next((m for m in nodes if m.get("depthUpper", MAX_DEPTH) == min_depth), {})


def pick_shallowest(nodes: list[dict], default=None):
    return (
        default
        if len(nodes) == 0
        else _shallowest_node(nodes) if len(nodes) > 1 else nodes[0]
    )


def select_nodes_by(
    nodes: list[dict], filters: list[Callable[[list[dict]], list[dict]]]
) -> Union[dict, list[dict]]:
    """
    Applies a series of filters to a list of blank nodes. Filters are applied in the order they are specifed in the
    filters arg.
    """
    return reduce(lambda result, func: func(result), filters, nodes)


def _most_relevant_blank_node(
    nodes: list,
    target_date: str,
    default=None,
):
    return select_nodes_by(
        nodes,
        [
            lambda nodes: closest_endDate(nodes, target_date),
            lambda nodes: pick_shallowest(nodes, default=default),
        ],
    )


def most_relevant_blank_node_by_term_id(
    nodes: list,
    term_id: Union[str, list[str]],
    target_date: str,
    default=None,
):
    """
    Returns the most relevant blank node with a matching `term.@id`.

    Nodes are filtered in the following order:

    1. Select nodes with matching `term.@id`s.
    2. Select nodes with the closest `endDate`.
    3. Select nodes with the shallowest `depthUpper` (closest to the surface).
    4. If multiple nodes remain, select the first node in the list.

    If alternative selection criteria are required, a custom node selector can be built using the `utils.select_nodes`
    module.

    Parameters
    ----------
    measurements : list[dict]
        A list of HESTIA measurement nodes.

    term_id : str | list[str]
        One (or several) HESTIA term ids.

    target_date : str
        A datestr with format `YYYY-MM-DD`, `YYYY-MM`, `YYYY` or `YYYY-MM-DDTHH:mm:ss`.

    default: Any, optional, default = `None`,
        What the function should return if no node matches the criteria.

    Returns
    -------
    most_relevant_measurement : dict | Any
        The most relevant measurement, or `default` if no measurement found.
    """
    filtered_nodes = filter_list_term_id(nodes, term_id)
    return _most_relevant_blank_node(filtered_nodes, target_date, default=default)


def most_relevant_blank_node_by_term_type(
    nodes: list[dict],
    term_type: Union[TermTermType, str, list[TermTermType], list[str]],
    target_date: str,
    default=None,
):
    """
    Returns the most relevant blank node with a matching `term.termType`.

    Nodes are filtered in the following order:

    1. Select nodes with matching `term.termType`s.
    3. Select nodes with the closest `endDate`.
    4. Select nodes with the shallowest `depthUpper` (closest to the surface).
    5. If multiple nodes remain, select the first node in the list.

    If alternative selection criteria are required, a custom node selector can be built using the `utils.select_nodes`
    module.

    Parameters
    ----------
    measurements : list[dict]
        A list of HESTIA measurement nodes.

    term_type : str | TermTermType | list[str] | list[TermTermType]
        One (or several) HESTIA term types.

    target_date : str
        A datestr with format `YYYY-MM-DD`, `YYYY-MM`, `YYYY` or `YYYY-MM-DDTHH:mm:ss`.

    default: Any, optional, default = `None`,
        What the function should return if no node matches the criteria.

    Returns
    -------
    most_relevant_measurement : dict | Any
        The most relevant measurement, or `default` if no measurement found.
    """
    filtered_nodes = filter_list_term_type(nodes, term_type)

    return _most_relevant_blank_node(filtered_nodes, target_date, default=default)
