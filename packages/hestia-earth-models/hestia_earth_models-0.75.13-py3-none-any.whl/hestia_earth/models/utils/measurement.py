from collections.abc import Iterable
from functools import reduce
from typing import Any, Optional, Union, List
from hestia_earth.schema import (
    MeasurementMethodClassification,
    SchemaType,
    TermTermType,
)
from hestia_earth.utils.blank_node import get_node_value
from hestia_earth.utils.model import linked_node, filter_list_term_type
from hestia_earth.utils.tools import list_sum
from hestia_earth.utils.term import download_term

from . import flatten_args, set_node_value
from .blank_node import filter_list_term_id
from .group_nodes import group_nodes_by
from .method import include_method
from .select_nodes import (
    closest_depthUpper_depthLower,
    closest_endDate,
    select_nodes_by,
    pick_shallowest,
)
from .term import get_lookup_value


SOIL_TEXTURE_IDS = ["sandContent", "siltContent", "clayContent"]

MEASUREMENT_METHOD_CLASSIFICATIONS = [e.value for e in MeasurementMethodClassification]


def _new_measurement(
    term: Union[dict, str],
    value: List[Union[float, bool]] = None,
    model: Optional[Union[dict, str]] = None,
):
    return include_method(
        {
            "@type": SchemaType.MEASUREMENT.value,
            "term": linked_node(
                term if isinstance(term, dict) else download_term(term)
            ),
        },
        model,
    ) | set_node_value("value", value, is_list=True)


def _most_relevant_measurement(
    measurements: list,
    target_date: str,
    target_depth_upper: Optional[float] = None,
    target_depth_lower: Optional[float] = None,
    depth_strict: bool = True,
    default=None,
):
    filter_depth = all([target_depth_upper is not None, target_depth_lower is not None])

    filters = (
        [
            lambda nodes: closest_depthUpper_depthLower(
                nodes, target_depth_upper, target_depth_lower, depth_strict=depth_strict
            )
        ]
        if filter_depth
        else []
    ) + [
        lambda nodes: closest_endDate(nodes, target_date),
        lambda nodes: pick_shallowest(nodes, default=default),
    ]

    return select_nodes_by(measurements, filters)


def most_relevant_measurement_by_term_id(
    measurements: list,
    term_id: Union[str, list[str]],
    target_date: str,
    target_depth_upper: Optional[float] = None,
    target_depth_lower: Optional[float] = None,
    depth_strict: bool = True,
    default={},
):
    """
    Returns the most relevant measurement node with a matching `term.@id`.

    Nodes are filtered in the following order:

    1. Select nodes with matching `term.@id`s.
    2. If both `target_depth_upper` AND `target_depth_lower` are specfied, select nodes with the closest `depthUpper`
    and `depthLower. If `depth_strict` == `True` only nodes with EXACTLY matching depths will be included.
    3. Select nodes with the closest `endDate`.
    4. Select nodes with the shallowest `depthUpper` (closest to the surface).
    5. If multiple nodes remain, select the first node in the list.

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

    target_depth_upper : float | None, optional, default = `None`,
        Target depth upper.

    target_depth_lower : float | None, optional, default = `None`,
        Target depth lower

    depth_strict: bool, optional, default = `True`,
        Whether or not a measurement must have exact depths to be selected.

    default: Any, optional, default = `{}`,
        What the function should return if no node matches the criteria.

    Returns
    -------
    most_relevant_measurement : dict | Any
        The most relevant measurement, or `default` if no measurement found.
    """
    filtered_nodes = filter_list_term_id(measurements, term_id)
    return _most_relevant_measurement(
        filtered_nodes,
        target_date,
        target_depth_upper=target_depth_upper,
        target_depth_lower=target_depth_lower,
        depth_strict=depth_strict,
        default=default,
    )


def most_relevant_measurement_by_term_type(
    measurements: list,
    term_type: Union[TermTermType, str, List[TermTermType], List[str]],
    target_date: str,
    target_depth_upper: Optional[float] = None,
    target_depth_lower: Optional[float] = None,
    depth_strict: bool = True,
    default={},
):
    """
    Returns the most relevant measurement node with a matching `term.termType`.

    Nodes are filtered in the following order:

    1. Select nodes with matching `term.termType`s.
    2. If both `target_depth_upper` AND `target_depth_lower` are specfied, select nodes with the closest `depthUpper`
    and `depthLower. If `depth_strict` == `True` only nodes with EXACTLY matching depths will be included.
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

    target_depth_upper : float | None, optional, default = `None`,
        Target depth upper.

    target_depth_lower : float | None, optional, default = `None`,
        Target depth lower

    depth_strict: bool, optional, default = `True`,
        Whether or not a measurement must have exact depths to be selected.

    default: Any, optional, default = `{}`,
        What the function should return if no node matches the criteria.

    Returns
    -------
    most_relevant_measurement : dict | Any
        The most relevant measurement, or `default` if no measurement found.
    """
    filtered_nodes = filter_list_term_type(measurements, term_type)
    return _most_relevant_measurement(
        filtered_nodes,
        target_date,
        target_depth_upper=target_depth_upper,
        target_depth_lower=target_depth_lower,
        depth_strict=depth_strict,
        default=default,
    )


def most_relevant_measurement_value(
    measurements: list,
    term_id: Union[str, set[str]],
    target_date: str,
    target_depth_upper: Optional[float] = None,
    target_depth_lower: Optional[float] = None,
    depth_strict: bool = True,
    default=None,
):
    """
    Returns the value of the most relevant measurement node with a matching `term.@id`.

    Nodes are filtered in the following order:

    1. Select nodes with matching `term.@id`s.
    2. If both `target_depth_upper` AND `target_depth_lower` are specfied, select nodes with the closest `depthUpper`
    and `depthLower. If `depth_strict` == `True` only nodes with EXACTLY matching depths will be included.
    3. Select nodes with the closest `endDate`.
    4. Select nodes with the shallowest `depthUpper` (closest to the surface).
    5. If multiple nodes remain, select the first node in the list.

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

    target_depth_upper : float | None, optional, default = `None`,
        Target depth upper.

    target_depth_lower : float | None, optional, default = `None`,
        Target depth lower

    depth_strict: bool, optional, default = `True`,
        Whether or not a measurement must have exact depths to be selected.

    default: Any, optional, default = `None`,
        What the function should return if no node matches the criteria.

    Returns
    -------
    most_relevant_measurement : dict | Any
        The most relevant measurement, or `default` if no measurement found.
    """
    measurement = most_relevant_measurement_by_term_id(
        measurements,
        term_id,
        target_date,
        target_depth_upper=target_depth_upper,
        target_depth_lower=target_depth_lower,
        depth_strict=depth_strict,
    )

    return get_node_value(measurement, default=default) if measurement else default


def has_all_months(dates: list):
    try:
        months = [int(d[5:7]) for d in dates]
        return all(m in months for m in range(1, 13))
    except Exception:
        return False


def group_get_node_values_by_year(
    measurement: dict,
    inner_key: Union[Any, None] = None,
    complete_years_only: bool = False,
) -> Union[dict, None]:
    """
    Groups the values of a monthly measurement by year.

    Only complete years (i.e. where all 12 months have a value) are returned and values are
    not transformed in any way (i.e. they are not averaged).

    Parameters
    ----------
    measurement : dict
        A HESTIA `Measurement` node, see: https://www.hestia.earth/schema/Measurement.
    inner_key: Any | None
        An optional inner dictionary key for the outputted annualised groups (can be used to merge annualised
        dictionaries together), default value: `None`.
    complete_years_only : bool
        Keep only years where there is a measurement value for each calendar month, default value: `False`.

    Returns
    -------
    dict | None
        The annualised dictionary of measurement values by year.
    """
    dates = measurement.get("dates", [])
    values = measurement.get("value", [])

    def group_values(groups: dict, index: int) -> dict:
        """
        Reducer function used to group the `Measurement` dates and values into years.
        """
        try:
            date = dates[index]
            value = values[index]
            year = int(date[0:4])  # Get the year from a date in the format `YYYY-MM-DD`
            groups[year] = groups.get(year, []) + [(date, value)]
        except (IndexError, ValueError):
            pass
        return groups

    grouped = reduce(group_values, range(0, len(dates)), dict())

    iterated = {
        key: (
            {inner_key: [v for _d, v in values]}
            if inner_key
            else [v for _d, v in values]
        )
        for key, values in grouped.items()
        if has_all_months([d for d, _v in values]) or not complete_years_only
    }

    return iterated


_MEASUREMENT_METHOD_CLASSIFICATION_RANKING = [
    MeasurementMethodClassification.ON_SITE_PHYSICAL_MEASUREMENT,
    MeasurementMethodClassification.MODELLED_USING_OTHER_MEASUREMENTS,
    MeasurementMethodClassification.TIER_3_MODEL,
    MeasurementMethodClassification.TIER_2_MODEL,
    MeasurementMethodClassification.TIER_1_MODEL,
    MeasurementMethodClassification.PHYSICAL_MEASUREMENT_ON_NEARBY_SITE,
    MeasurementMethodClassification.GEOSPATIAL_DATASET,
    MeasurementMethodClassification.REGIONAL_STATISTICAL_DATA,
    MeasurementMethodClassification.COUNTRY_LEVEL_STATISTICAL_DATA,
    MeasurementMethodClassification.EXPERT_OPINION,
    MeasurementMethodClassification.UNSOURCED_ASSUMPTION,
]
"""
A ranking of `MeasurementMethodClassification`s from strongest to weakest.
"""

_MeasurementMethodClassifications = Union[
    MeasurementMethodClassification,
    str,
    Iterable[Union[MeasurementMethodClassification, str]],
]
"""
A type alias for a single measurement method classification, as either an MeasurementMethodClassification enum or
string, or multiple measurement method classification, as either an iterable of MeasurementMethodClassification enums
or strings.
"""


def min_measurement_method_classification(
    *methods: _MeasurementMethodClassifications,
) -> MeasurementMethodClassification:
    """
    Get the minimum ranking measurement method from the provided methods.

    n.b., `max` function is used as weaker methods have higher indices.

    Parameters
    ----------
    *methods : MeasurementMethodClassification | str | Iterable[MeasurementMethodClassification] | Iterable[str]
        Measurement method classifications or iterables of measurement method classification.

    Returns
    -------
    MeasurementMethodClassification
        The measurement method classification with the minimum ranking.
    """
    methods_ = [
        to_measurement_method_classification(arg) for arg in flatten_args(methods)
    ]
    return max(
        methods_,
        key=lambda method: _MEASUREMENT_METHOD_CLASSIFICATION_RANKING.index(method),
        default=_MEASUREMENT_METHOD_CLASSIFICATION_RANKING[-1],
    )


def to_measurement_method_classification(
    method: Union[MeasurementMethodClassification, str],
) -> Optional[MeasurementMethodClassification]:
    """
    Convert the input to a `MeasurementMethodClassification` if possible.

    Parameters
    ----------
    method : MeasurementMethodClassification | str
        The measurement method as either a `str` or `MeasurementMethodClassification`.

    Returns
    -------
    MeasurementMethodClassification | None
        The matching `MeasurementMethodClassification` or `None` if invalid string.
    """
    return (
        method
        if isinstance(method, MeasurementMethodClassification)
        else (
            MeasurementMethodClassification(method)
            if method in MEASUREMENT_METHOD_CLASSIFICATIONS
            else None
        )
    )


def group_measurements_by_method_classification(
    nodes: list[dict],
) -> dict[MeasurementMethodClassification, list[dict]]:
    """
    Group [Measurement](https://www.hestia.earth/schema/Measurement) nodes by their method classification.

    The returned dict has the shape:
    ```
    {
        method (MeasurementMethodClassification): nodes (list[dict]),
        ...methods
    }
    ```

    Parameters
    ----------
    nodes : list[dict]
        A list of Measurement nodes.

    Returns
    -------
    dict[MeasurementMethodClassification, list[dict]]
        The measurement nodes grouped by method classification.
    """
    valid_nodes = (
        node for node in nodes if node.get("@type") == SchemaType.MEASUREMENT.value
    )

    def grouper(node: dict) -> MeasurementMethodClassification:
        return to_measurement_method_classification(node.get("methodClassification"))

    return group_nodes_by(valid_nodes, grouper, sort=False)


def total_other_soilType_value(measurements: list, term_id: str):
    sum_group = get_lookup_value(
        {"@id": term_id, "termType": TermTermType.SOILTYPE.value}, "sumMax100Group"
    )
    measurements = [
        m
        for m in filter_list_term_type(measurements, TermTermType.SOILTYPE)
        if all(
            [
                get_lookup_value(m.get("term"), "sumMax100Group") == sum_group,
                m.get("depthUpper", 0) == 0,
                m.get("depthLower", 0) == 30,
            ]
        )
    ]
    return list_sum([list_sum(m.get("value") or []) for m in measurements])
