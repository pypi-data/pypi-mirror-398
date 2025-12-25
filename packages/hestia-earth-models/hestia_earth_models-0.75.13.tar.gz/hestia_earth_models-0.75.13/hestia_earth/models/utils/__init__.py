from os.path import dirname, abspath
from collections.abc import Generator, Iterable
from itertools import tee
from decimal import Decimal
from statistics import mean
import sys
import datetime
from functools import reduce
import operator
from typing import Union, List, Callable, Any, Optional
from hestia_earth.schema import SchemaType, TermTermType
from hestia_earth.utils.api import download_hestia
from hestia_earth.utils.tools import (
    as_list,
    flatten,
    is_number,
    non_empty_list,
    safe_parse_date,
    to_precision,
)
from hestia_earth.utils.model import linked_node
from hestia_earth.utils.term import download_term

from .constant import Units

CURRENT_DIR = dirname(abspath(__file__)) + "/"
sys.path.append(CURRENT_DIR)
CACHE_KEY = "_cache"


def cached_value(node: dict, key: str = None, default=None):
    cache = node.get(CACHE_KEY) or {}
    value = cache.get(key) if key else cache
    return default if value is None else value


def value_with_precision(value, digits: int = 3):
    def _to_precision(value):
        return (
            to_precision(value, digits=digits) if is_number(value) and value else value
        )

    return (
        list(map(_to_precision, value))
        if isinstance(value, list)
        else _to_precision(value)
    )


def set_node_value(key: str, value: Any, is_list: bool = False):
    return (
        {
            key: (
                [value_with_precision(value)]
                if is_list and not isinstance(value, list)
                else value_with_precision(value)
            )
        }
        if value is not None
        else {}
    )


def set_node_stats(node: dict):
    include_stats = any([key in node for key in ["min", "max", "sd"]])
    return ({"statsDefinition": "modelled"} if include_stats else {}) | node


def set_node_term(key: str, term_id: str, term_type: Optional[TermTermType] = None):
    return {key: linked_node(download_term(term_id, term_type))} if term_id else {}


def _term_id(term):
    return term.get("@id") if isinstance(term, dict) else term


def _run_in_serie(data: dict, models: list):
    return reduce(lambda prev, model: model(prev), models, data)


def _load_calculated_node(node, type: SchemaType, data_state="recalculated"):
    # return original value if recalculated is not available
    return download_hestia(
        node.get("@id"), type, data_state=data_state
    ) or download_hestia(node.get("@id"), type)


def _unit_str(unit) -> str:
    return unit if isinstance(unit, str) else unit.value


def _filter_list_term_unit(values: list, unit: Union[str, List[str]]):
    units = unit if isinstance(unit, list) else [unit]
    units = list(map(_unit_str, units))
    return list(filter(lambda i: i.get("term", {}).get("units") in units, values))


def is_from_model(node: dict) -> bool:
    """
    Check if the Blank Node came from one of the HESTIA Models.

    Parameters
    ----------
    node : dict
        The Blank Node containing `added` and `updated`.

    Returns
    -------
    bool
        `True` if the value came from a model, `False` otherwise.
    """
    return "value" in node.get("added", []) or "value" in node.get("updated", [])


def sum_values(values: list):
    """
    Sum up the values while handling `None` values.
    If all values are `None`, the result is `None`.
    """
    filtered_values = [v for v in values if v is not None]
    return sum(filtered_values) if len(filtered_values) > 0 else None


def multiply_values(values: list):
    """
    Multiply the values while handling `None` values.
    If all values are `None`, the result is `None`.
    """
    filtered_values = [v for v in values if v is not None]
    return (
        reduce(operator.mul, filtered_values, 1) if len(filtered_values) > 1 else None
    )


def clamp(
    value: Union[int, float], min_value: Union[int, float], max_value: Union[int, float]
):
    return min(max_value, max(min_value, value))


def _numeric_weighted_average(values: list):
    total_weight = (
        sum(Decimal(str(weight)) for _v, weight in values) if values else Decimal(0)
    )
    weighted_values = [
        Decimal(str(value)) * Decimal(str(weight)) for value, weight in values
    ]
    average = (
        sum(weighted_values) / (total_weight if total_weight else 1)
        if weighted_values
        else None
    )
    return None if average is None else float(average)


def _bool_weighted_average(values: list):
    return mean(map(int, values)) >= 0.5


def weighted_average(weighted_values: list):
    values = [v for v, _w in weighted_values]
    all_boolean = all([isinstance(v, bool) for v in values])
    return (
        _bool_weighted_average(values)
        if all_boolean
        else _numeric_weighted_average(weighted_values)
    )


def term_id_prefix(term_id: str):
    return term_id.split("Kg")[0]


def get_kg_term_id(term_id: str):
    return f"{term_id_prefix(term_id)}KgMass"


def get_kg_N_term_id(term_id: str):
    return f"{term_id_prefix(term_id)}KgN"


def get_kg_P2O5_term_id(term_id: str):
    return f"{term_id_prefix(term_id)}KgP2O5"


def get_kg_K2O_term_id(term_id: str):
    return f"{term_id_prefix(term_id)}KgK2O"


def get_kg_VS_term_id(term_id: str):
    return f"{term_id_prefix(term_id)}KgVs"


def get_kg_term_units(term_id: str, units: str):
    return {
        Units.KG.value: get_kg_term_id,
        Units.KG_N.value: get_kg_N_term_id,
        Units.KG_P2O5.value: get_kg_P2O5_term_id,
        Units.KG_K2O.value: get_kg_K2O_term_id,
        Units.KG_VS.value: get_kg_VS_term_id,
    }.get(units, lambda x: None)(term_id)


def first_day_of_month(year: int, month: int):
    return datetime.date(int(year), int(month), 1)


def last_day_of_month(year: int, month: int):
    # handle special case month 12
    return (
        datetime.date(int(year), 12, 31)
        if month == 12
        else (
            datetime.date(int(year) + int(int(month) / 12), (int(month) % 12) + 1, 1)
            - datetime.timedelta(days=1)
        )
    )


def current_date():
    return datetime.datetime.now().date().strftime("%Y-%m-%d")


def current_year():
    return int(current_date()[:4])


def max_date(date_str: str):
    """
    If the date is after today, returns today. Otherwise returns the date.
    """
    date = safe_parse_date(date_str).date()
    max_date = datetime.datetime.now().date()
    return current_date() if date > max_date else date_str


def flatten_args(args) -> list:
    """
    Flatten the input args into a single list.
    """
    return non_empty_list(flatten([as_list(arg) for arg in args]))


def pairwise(iterable):
    """
    from https://docs.python.org/3.9/library/itertools.html#itertools-recipes
    s -> (s0,s1), (s1,s2), (s2, s3), ...
    """
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def days_to_years(days):
    return days / 365


def hectar_to_square_meter(value):
    return value * 10000


def square_meter_to_hectare(value):
    return value / 10000


def split_on_condition(iterable: Iterable, condition: Callable):
    """
    Split an iterable into two iterables of the same type based on whether or not each item satisfies a condition.
    """

    def construct(iterator: Generator) -> Iterable:
        return (
            "".join(iterable) if isinstance(iterable, str) else type(iterable)(iterator)
        )

    cond_true, cond_false = tee((condition(item), item) for item in iterable)
    return construct(i for p, i in cond_true if p), construct(
        i for p, i in cond_false if not p
    )


def has_unique_key(nodes: list, key: str):
    """All nodes share the same value for a key."""
    return len(set([n.get(key) for n in nodes])) == 1
