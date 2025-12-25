from functools import reduce
from typing import List, Callable, Optional, Union
from hestia_earth.schema import TermTermType
from hestia_earth.utils.blank_node import ArrayTreatment, get_node_value
from hestia_earth.utils.model import filter_list_term_type
from hestia_earth.utils.tools import (
    as_set,
    flatten,
    list_average,
    list_sum,
    non_empty_list,
)
from hestia_earth.utils.lookup_utils import (
    is_model_siteType_allowed,
    is_model_product_id_allowed,
    is_model_measurement_id_allowed,
    is_siteType_allowed,
    is_site_measurement_id_allowed,
    is_product_id_allowed,
    is_product_termType_allowed,
    is_input_id_allowed,
    is_input_termType_allowed,
)
from hestia_earth.utils.term import download_term

from hestia_earth.models.log import debugValues, log_as_table
from . import is_from_model, _filter_list_term_unit
from .constant import Units, get_atomic_conversion
from .date import nodes_have_same_dates
from .group_nodes import (
    group_nodes_by,
    group_nodes_by_term_id,
    group_nodes_by_term_id_value_and_properties,
    group_nodes_by_consecutive_dates,
)
from .lookup import _node_value
from .property import get_node_property, get_node_property_value
from .term import get_lookup_value

# TODO: verify those values
MAX_DEPTH = 1000


def merge_blank_nodes(source: list, new_values: list):
    """
    Merge a list of blank nodes into an existing list of blank nodes.
    Warning: we only consider the `term.@id` here, and not the full list of properties that make the nodes unique.
    This should only be used when merging simple list of nested blank nodes.
    """
    for new_value in non_empty_list(new_values):
        term_id = new_value.get("term", {}).get("@id")
        index = next(
            (
                i
                for i, data in enumerate(source)
                if data.get("term", {}).get("@id") == term_id
            ),
            None,
        )
        if index is None:
            source.append(new_value)
        else:
            source[index] = source[index] | new_value
    return source


def lookups_logs(model: str, blank_nodes: list, lookups_per_termType: dict, **log_args):
    def mapper(blank_node: dict):
        term = blank_node.get("term", {})
        term_id = term.get("@id")
        term_type = term.get("termType")
        lookups = lookups_per_termType.get(term_type, [])
        lookups = lookups if isinstance(lookups, list) else [lookups]

        def _reduce_lookups_logs(logs: dict, column: str):
            lookup_value = get_lookup_value(term, column, model=model, **log_args)
            return logs | {column: str(lookup_value).replace(":", "-")}

        return reduce(_reduce_lookups_logs, lookups, {"id": term_id})

    logs = list(map(mapper, blank_nodes))

    return log_as_table(logs)


def properties_logs(blank_nodes: list, properties: Union[dict, list]):
    def mapper(blank_node: dict):
        term = blank_node.get("term", {})
        term_id = term.get("@id")
        term_type = term.get("termType")
        props = (
            properties.get(term_type, [])
            if isinstance(properties, dict)
            else properties
        )
        props = props if isinstance(props, list) else [props]

        def _reduce_properties_logs(logs: dict, prop: str):
            value = get_node_property(blank_node, prop).get("value")
            return logs | {prop: value}

        return reduce(_reduce_properties_logs, properties, {"id": term_id})

    logs = list(map(mapper, blank_nodes))

    return log_as_table(logs)


def _module_term_id(term_id: str, module):
    term_id_str = term_id.split(".")[-1] if "." in term_id else term_id
    return getattr(module, "TERM_ID", term_id_str).split(",")[0]


def _run_model_required(model: str, term_id: str, data: dict, skip_logs: bool = False):
    siteType_allowed = is_model_siteType_allowed(model, term_id, data)
    product_id_allowed = is_model_product_id_allowed(model, term_id, data)
    site_measurement_id_allowed = is_model_measurement_id_allowed(model, term_id, data)

    run_required = all(
        [siteType_allowed, product_id_allowed, site_measurement_id_allowed]
    )
    if not skip_logs:
        debugValues(
            data,
            model=model,
            term=term_id,
            run_required=run_required,
            siteType_allowed=siteType_allowed,
            site_measurement_id_allowed=site_measurement_id_allowed,
            product_id_allowed=product_id_allowed,
        )
    return run_required


def _run_required(model: str, term_id: str, data: dict):
    siteType_allowed = is_siteType_allowed(data, term_id)
    site_measurement_id_allowed = is_site_measurement_id_allowed(data, term_id)
    product_id_allowed = is_product_id_allowed(data, term_id)
    product_termType_allowed = is_product_termType_allowed(data, term_id)
    input_id_allowed = is_input_id_allowed(data, term_id)
    input_termType_allowed = is_input_termType_allowed(data, term_id)

    run_required = all(
        [
            siteType_allowed,
            site_measurement_id_allowed,
            product_id_allowed,
            product_termType_allowed,
            input_id_allowed,
            input_termType_allowed,
        ]
    )
    # model is only used for logs here, skip logs if model not provided
    if model:
        debugValues(
            data,
            model=model,
            term=term_id,
            # logging this for the model would cause issues parsing statuses
            **({} if model.endswith("NotRelevant") else {"run_required": run_required}),
            siteType_allowed=siteType_allowed,
            site_measurement_id_allowed=site_measurement_id_allowed,
            product_id_allowed=product_id_allowed,
            product_termType_allowed=product_termType_allowed,
            input_id_allowed=input_id_allowed,
            input_termType_allowed=input_termType_allowed,
        )
    return run_required


def is_run_required(model: str, term_id: str, node: dict):
    """
    Determines whether the term for the model should run or not, based on lookup values.

    Parameters
    ----------
    model : str
        The `@id` of the model. Example: `pooreNemecek2018`.
    term_id : str
        The `@id` of the `Term` or the full JSON-LD of the Term. Example: `sandContent`.
    node : dict
        The node on which the model is applied. Logging purpose ony.

    Returns
    -------
    bool
        True if the model is required to run.
    """
    return (
        (
            (_run_model_required(model, term_id, node) if model else True)
            and _run_required(model, term_id, node)
        )
        if term_id
        else True
    )


def run_if_required(model: str, term_id: str, data: dict, module):
    return (
        getattr(module, "run")(data)
        if is_run_required(model, _module_term_id(term_id, module), data)
        else []
    )


def find_terms_value(nodes: list, term_id: str, default: Union[int, None] = 0):
    """
    Returns the sum of all blank nodes in the list which match the `Term` with the given `@id`.

    Parameters
    ----------
    values : list
        The list in which to search for. Example: `cycle['nodes']`.
    term_id : str
        The `@id` of the `Term`. Example: `sandContent`

    Returns
    -------
    float
        The total `value` as a number.
    """
    return list_sum(
        get_total_value(
            filter(lambda node: node.get("term", {}).get("@id") == term_id, nodes)
        ),
        default,
    )


def has_gap_filled_by_ids(nodes: list, term_ids: List[str]):
    nodes = [n for n in nodes if n.get("term", {}).get("@id") in term_ids]
    return any([is_from_model(n) for n in nodes])


def has_original_by_ids(nodes: list, term_ids: List[str]):
    nodes = [n for n in nodes if n.get("term", {}).get("@id") in term_ids]
    return any([not is_from_model(n) for n in nodes])


def get_total_value(nodes: list):
    """
    Get the total `value` of a list of Blank Nodes.
    This method does not take into account the `units` and possible conversions.

    Parameters
    ----------
    nodes : list
        A list of Blank Node.

    Returns
    -------
    list
        The total `value` as a list of numbers.
    """
    return list(map(lambda node: list_sum(node.get("value", []), None), nodes))


def _value_as(term_id: str, convert_to_property: bool = True, **log_args):
    def get_value(node: dict):
        factor = (
            get_node_property_value(
                None, node, term_id, default=0, handle_percents=False
            )
            or get_lookup_value(lookup_term=node.get("term", {}), column=term_id)
            or 0
        )
        # ignore node value if property is not found
        value = list_sum(node.get("value", []))
        property = get_node_property(
            node, term_id, find_default_property=False, download_from_hestia=True
        )
        ratio = (
            factor / 100 if property.get("term", {}).get("units", "") == "%" else factor
        )

        if log_args.get("log_node"):
            debugValues(
                **log_args,
                **{"convert_value": value, f"conversion_with_{term_id}": factor},
            )

        return (
            0
            if ratio == 0
            else (value * ratio if convert_to_property else value / ratio)
        )

    return get_value


def get_total_value_converted(
    nodes: list,
    conversion_property: Union[List[str], str],
    convert_to_property: bool = True,
    **log_args,
):
    """
    Get the total `value` of a list of Blank Nodes converted using a property of each Blank Node.

    Parameters
    ----------
    nodes : list
        A list of Blank Node.
    conversion_property : str|List[str]
        Property (or multiple properties) used for the conversion. Example: `nitrogenContent`.
        See https://hestia.earth/glossary?termType=property for a list of `Property`.
    convert_to_property : bool
        By default, property is multiplied on value to get result. Set `False` to divide instead.

    Returns
    -------
    list
        The total `value` as a list of numbers.
    """

    def convert_multiple(node: dict):
        value = 0
        for prop in conversion_property:
            value = _value_as(prop, convert_to_property, **log_args)(node)
            node["value"] = [value]
        return value

    return [
        (
            _value_as(conversion_property, convert_to_property, **log_args)(node)
            if isinstance(conversion_property, str)
            else convert_multiple(node)
        )
        for node in nodes
    ]


def get_total_value_converted_with_min_ratio(
    model: str,
    term: str,
    node: dict = {},
    blank_nodes: list = [],
    prop_id: str = "energyContentHigherHeatingValue",
    min_ratio: float = 0.8,
    is_sum: bool = True,
):
    values = [
        (
            blank_node.get("@type"),
            blank_node.get("term", {}).get("@id"),
            list_sum(blank_node.get("value", [])),
            get_node_property_value(model, blank_node, prop_id),
        )
        for blank_node in blank_nodes
    ]
    value_logs = log_as_table(
        [
            {
                f"{node_type}-id": term_id,
                f"{node_type}-value": value,
                f"{prop_id}-value": prop_value,
            }
            for node_type, term_id, value, prop_value in values
        ]
    )

    total_value = list_sum([value for node_type, term_id, value, prop_value in values])
    total_value_with_property = list_sum(
        [value for node_type, term_id, value, prop_value in values if prop_value]
    )
    total_value_ratio = (
        total_value_with_property / total_value if total_value > 0 else 0
    )

    logs = {
        f"{prop_id}-term-id": prop_id,
        f"{prop_id}-total-value": total_value,
        f"{prop_id}-total-value-with-property": total_value_with_property,
        f"{prop_id}-total-value-with-ratio": total_value_ratio,
        f"{prop_id}-min-value-ratio": min_ratio,
        f"{prop_id}-values": value_logs,
    }

    debugValues(node, model=model, term=term, **logs)

    total_converted_value = list_sum(
        [
            value * prop_value
            for node_type, term_id, value, prop_value in values
            if all([value, prop_value])
        ]
    )

    return (
        (
            total_converted_value * total_value / total_value_with_property
            if is_sum
            else total_converted_value / total_value_with_property
        )
        if total_value_ratio >= min_ratio
        else None
    )


def get_N_total(nodes: list) -> list:
    """
    Get the total nitrogen content of a list of Blank Node.

    The result contains the values of the following nodes:
    1. Every blank node in `kg N` will be used.
    2. Every blank node specified in `kg` or `kg dry matter` will be multiplied by the `nitrogenContent` property.

    Parameters
    ----------
    nodes : list
        A list of Blank Node.

    Returns
    -------
    list
        The nitrogen values as a list of numbers.
    """
    kg_N_nodes = _filter_list_term_unit(nodes, Units.KG_N)
    kg_nodes = _filter_list_term_unit(nodes, [Units.KG, Units.KG_DRY_MATTER])
    return get_total_value(kg_N_nodes) + get_total_value_converted(
        kg_nodes, "nitrogenContent"
    )


def get_KG_total(nodes: list) -> list:
    """
    Get the total kg mass of a list of Blank Node.

    The result contains the values of the following nodes:
    1. Every blank node in `kg` will be used.
    2. Every blank node specified in `kg N` will be divided by the `nitrogenContent` property.

    Parameters
    ----------
    nodes : list
        A list of Blank Node.

    Returns
    -------
    list
        The nitrogen values as a list of numbers.
    """
    kg_N_nodes = _filter_list_term_unit(nodes, Units.KG_N)
    kg_nodes = _filter_list_term_unit(nodes, Units.KG)
    return get_total_value(kg_nodes) + get_total_value_converted(
        kg_N_nodes, "nitrogenContent", False
    )


def get_P_total(nodes: list) -> list:
    """
    Get the total phosphorous content of a list of Blank Node.

    The result contains the values of the following nodes:
    1. Every blank node specified in `kg P` will be used.
    1. Every blank node specified in `kg N` will be multiplied by the `phosphateContentAsP` property.
    2. Every blank node specified in `kg` will be multiplied by the `phosphateContentAsP` property.

    Parameters
    ----------
    nodes : list
        A list of Blank Node.

    Returns
    -------
    list
        The phosphorous values as a list of numbers.
    """
    kg_P_nodes = _filter_list_term_unit(nodes, Units.KG_P)
    kg_N_nodes = _filter_list_term_unit(nodes, Units.KG_N)
    kg_nodes = _filter_list_term_unit(nodes, Units.KG)
    return get_total_value(kg_P_nodes) + get_total_value_converted(
        kg_N_nodes + kg_nodes, "phosphateContentAsP"
    )


def get_P2O5_total(nodes: list) -> list:
    """
    Get the total phosphate content of a list of Blank Node.

    The result contains the values of the following nodes:
    1. Every blank node specified in `kg P2O5` will be used.
    1. Every blank node specified in `kg N` will be multiplied by the `phosphateContentAsP2O5` property.
    2. Every blank node specified in `kg` will be multiplied by the `phosphateContentAsP2O5` property.

    Parameters
    ----------
    nodes : list
        A list of Blank Node.

    Returns
    -------
    list
        The phosphate values as a list of numbers.
    """
    kg_P2O5_nodes = _filter_list_term_unit(nodes, Units.KG_P2O5)
    kg_N_nodes = _filter_list_term_unit(nodes, Units.KG_N)
    kg_nodes = _filter_list_term_unit(nodes, Units.KG)
    return get_total_value(kg_P2O5_nodes) + get_total_value_converted(
        kg_N_nodes + kg_nodes, "phosphateContentAsP2O5"
    )


def convert_to_nitrogen(node: dict, model: str, blank_nodes: list, **log_args):
    def fallback_value(input: dict):
        value = get_node_property_value(
            model, input, "crudeProteinContent", default=None, **log_args
        )
        return None if value is None else value / 6.25

    def prop_value(input: dict):
        value = get_node_property_value(
            model, input, "nitrogenContent", default=None, **log_args
        )
        return value if value is not None else fallback_value(input)

    values = [(i, prop_value(i)) for i in blank_nodes]
    missing_nitrogen_property = [
        i.get("term", {}).get("@id") for i, value in values if value is None
    ]

    debugValues(
        node,
        model=model,
        conversion_details=log_as_table(
            [
                {
                    "id": i.get("term", {}).get("@id"),
                    "value": list_sum(i.get("value", [])),
                    "nitrogenContent": value,
                }
                for i, value in values
            ]
        ),
        missing_nitrogen_property=";".join(set(missing_nitrogen_property)),
        **log_args,
    )

    return (
        list_sum(
            [
                list_sum(i.get("value", [])) * p_value
                for i, p_value in values
                if p_value is not None
            ]
        )
        if len(missing_nitrogen_property) == 0
        else None
    )


def convert_to_carbon(node: dict, model: str, blank_nodes: list, **log_args):
    def prop_value(input: dict):
        value = get_node_property_value(
            model, input, "carbonContent", default=None, **log_args
        )
        return (
            value
            or get_node_property_value(
                model, input, "energyContentHigherHeatingValue", default=0, **log_args
            )
            * 0.021
        )

    values = [(i, prop_value(i)) for i in blank_nodes]
    missing_carbon_property = [
        i.get("term", {}).get("@id") for i, p_value in values if not p_value
    ]

    debugValues(
        node,
        model=model,
        missing_carbon_property=";".join(missing_carbon_property),
        **log_args,
    )

    return (
        list_sum(
            [
                list_sum(i.get("value", [])) * p_value
                for i, p_value in values
                if p_value is not None
            ]
        )
        if len(missing_carbon_property) == 0
        else None
    )


def node_term_match(node: dict, target_term_ids: Union[str, set[str]]) -> bool:
    """
    Check if the term ID of the given node matches any of the target term IDs.

    Parameters
    ----------
    node : dict
        The dictionary representing the node.
    target_term_ids : str | set[str]
        A single term ID or an set of term IDs to check against.

    Returns
    -------
    bool
        `True` if the term ID of the node matches any of the target
        term IDs, `False` otherwise.

    """
    target_term_ids = as_set(target_term_ids)
    return node.get("term", {}).get("@id", None) in target_term_ids


def filter_list_term_id(
    nodes: list[dict], target_term_ids: Union[str, set[str]]
) -> list[dict]:
    return [node for node in nodes if node_term_match(node, target_term_ids)]


def node_lookup_match(
    node: dict, lookup: str, target_lookup_values: Union[str, set[str]]
) -> bool:
    """
    Check if the lookup value in the node's term matches any of the
    target lookup values.

    Parameters
    ----------
    node : dict
        The dictionary representing the node.
    lookup : str
        The lookup key.
    target_lookup_values : str | set[str]
        A single target lookup value or a set of target lookup values
        to check against.

    Returns
    -------
    bool
        `True` if there is a match, `False` otherwise.
    """
    target_lookup_values = as_set(target_lookup_values)
    return get_lookup_value(node.get("term", {}), lookup) in target_lookup_values


def cumulative_nodes_match(
    function: Callable[[dict], bool],
    nodes: list[dict],
    *,
    cumulative_threshold: float,
    default_node_value: float = 0,
    is_larger_unit: bool = False,
    array_treatment: Optional[ArrayTreatment] = None,
) -> bool:
    """
    Check if the cumulative values of nodes that satisfy the provided
    function exceed the threshold.

    Parameters
    ----------
    function : Callable[[dict], bool]
        A function to determine whether a node should be included in
        the calculation.
    nodes : list[dict]
        The list of nodes to be considered.
    cumulative_threshold : float
        The threshold that the cumulative values must exceed for the
        function to return `True`.
    default_node_value : float, optional
        The default value for nodes without a specified value, by
        default `0`.
    is_larger_unit : bool, optional
        A flag indicating whether the node values are in a larger unit
        of time, by default `False`.
    array_treatment : ArrayTreatment | None, optional
        The treatment to apply to arrays of values, by default `None`.

    Returns
    -------
    bool
        `True` if the cumulative values exceed the threshold, `False`
        otherwise.

    """
    values = [
        get_node_value(
            node,
            key="value",
            is_larger_unit=is_larger_unit,
            array_treatment=array_treatment,
        )
        or default_node_value
        for node in nodes
        if function(node)
    ]

    return list_sum(non_empty_list(flatten(values))) > cumulative_threshold


def cumulative_nodes_term_match(
    nodes: list[dict],
    *,
    target_term_ids: Union[str, set[str]],
    cumulative_threshold: float,
    default_node_value: float = 0,
    is_larger_unit: bool = False,
    array_treatment: Optional[ArrayTreatment] = None,
) -> bool:
    """
    Check if the cumulative values of nodes with matching term IDs
    exceed the threshold.

    Parameters
    ----------
    nodes : list[dict]
        The list of nodes to be considered.
    target_term_ids : str | set[str]
        The term ID or a set of term IDs to match.
    cumulative_threshold : float
        The threshold that the cumulative values must exceed for the function to return `True`.
    default_node_value : float, optional
        The default value for nodes without a specified value, by default `0`.
    is_larger_unit : bool, optional
        A flag indicating whether the node values are in a larger unit of time, by default `False`.
    array_treatment : ArrayTreatment | None, optional
        The treatment to apply to arrays of values, by default `None`.

    Returns
    -------
    bool
        `True` if the cumulative values exceed the threshold, `False` otherwise.
    """
    target_term_ids = as_set(target_term_ids)

    def match_function(node: dict) -> bool:
        return node_term_match(node, target_term_ids)

    return cumulative_nodes_match(
        match_function,
        nodes,
        cumulative_threshold=cumulative_threshold,
        default_node_value=default_node_value,
        is_larger_unit=is_larger_unit,
        array_treatment=array_treatment,
    )


def cumulative_nodes_lookup_match(
    nodes: list[dict],
    *,
    lookup: str,
    target_lookup_values: Union[str, set[str]],
    cumulative_threshold: float,
    default_node_value: float = 0,
    is_larger_unit: bool = False,
    array_treatment: Optional[ArrayTreatment] = None,
) -> bool:
    """
    Check if the cumulative values of nodes with matching lookup values exceed the threshold.

    Parameters
    ----------
    nodes : list[dict]
        The list of nodes to be considered.
    lookup : str
        The lookup key to match against in the nodes.
    target_lookup_values : str | set[str]
        The lookup value or a set of lookup values to match.
    cumulative_threshold : float
        The threshold that the cumulative values must exceed for the
        function to return `True`.
    default_node_value : float, optional
        The default value for nodes without a specified value, by
        default `0`.
    is_larger_unit : bool, optional
        A flag indicating whether the node values are in a larger unit
        of time, by default `False`.
    array_treatment : ArrayTreatment | None, optional
        The treatment to apply to arrays of values, by default `None`.

    Returns
    -------
    bool
        `True` if the cumulative values exceed the threshold, `False`
        otherwise.
    """
    target_lookup_values = as_set(target_lookup_values)

    def match_function(node: dict) -> bool:
        return node_lookup_match(node, lookup, target_lookup_values)

    return cumulative_nodes_match(
        match_function,
        nodes,
        cumulative_threshold=cumulative_threshold,
        default_node_value=default_node_value,
        is_larger_unit=is_larger_unit,
        array_treatment=array_treatment,
    )


def split_node_by_dates(node: dict) -> list[dict]:
    """
    Split a node with an array-like `value` and `dates` with multiple elements into a list of nodes with a single
    `value` and `dates`. All other array-like node fields (`sd`, `min`, `max`,  and `observations`) will be also be
    split. Any other fields will be copied with no modifications.

    All split fields will still be array-like, but will only contain one element. Any array-like fields with a
    different number of elements to `value` will not be split.

    This function should only run on nodes with array-like `value` and `dates` (e.g., nodes with `@type` == `Emission`,
    `Input`,`Measurement`, `Practice` or `Product`).

    Parameters
    ----------
    node : dict
        A HESTIA blank node with array-like `value` and `dates` (and optional array-like fields `sd`, `min`, `max`, and
        `observations`).

    Returns
    -------
    list[dict]
        A list of nodes with single `value` and `dates`.
    """
    REQUIRED_KEYS = ["value", "dates"]
    OPTIONAL_KEYS = ["sd", "min", "max", "observations"]

    value = node.get("value", [])
    target_len = len(value) if isinstance(value, list) else -1

    def should_run_key(key: str) -> bool:
        item = node.get(key, [])
        return isinstance(item, list) and len(item) == target_len

    should_run = all(
        [target_len > 0, all(should_run_key(key) for key in REQUIRED_KEYS)]
    )

    valid_keys = REQUIRED_KEYS + [key for key in OPTIONAL_KEYS if should_run_key(key)]

    def split(result: list[dict], index: int) -> list[dict]:
        update = {key: [node[key][index]] for key in valid_keys}
        result.append(node | update)
        return result

    return (
        sorted(
            reduce(split, range(len(value)), list()),
            key=lambda node: node.get("dates", []),
        )
        if should_run
        else [node]
    )


def split_nodes_by_dates(nodes: list[dict]) -> list[dict]:
    return non_empty_list(flatten(split_node_by_dates(node) for node in nodes))


def get_inputs_from_properties(
    input: dict, term_types: Union[TermTermType, List[TermTermType]]
):
    """
    Compute a list of inputs from the input properties, in the `key:value` form.

    Parameters
    ----------
    input : dict
        The Input.
    term_types : TermTermType | List[TermTermType]
        List of `termType` valid for the properties `key`.

    Return
    ------
    dict
        A dictionary of nodes grouped by latest date, in the format `{date: list[node]}`.
    """
    term = input.get("term", {})
    input_value = list_sum(input.get("value", []))
    properties = (
        input.get("properties")
        or term.get("defaultProperties")
        or download_term(term).get("defaultProperties")
    )
    inputs = (
        non_empty_list(
            [
                {
                    "term": p.get("key"),
                    "value": [
                        (p.get("value") / 100)
                        * (p.get("share", 100) / 100)
                        * input_value
                    ],
                    # for grouping
                    "parent": term,
                }
                for p in (properties or [])
                if all([p.get("key"), p.get("value")])
            ]
        )
        if input_value > 0
        else []
    )
    return filter_list_term_type(inputs, term_types)


def _node_from_group(nodes: list):
    # `nodes` contain list with consecutive dates
    start_dates = non_empty_list([n.get("startDate") for n in nodes])
    end_dates = non_empty_list([n.get("endDate") for n in nodes])
    return (
        nodes[0]
        if len(nodes) == 1
        else (
            # if all nodes have the same dates, sum up the values
            nodes[0]
            | (
                {"value": sum_nodes_value(nodes)}
                if nodes_have_same_dates(nodes)
                else (
                    ({"endDate": max(end_dates)} if end_dates else {})
                    | ({"startDate": min(start_dates)} if start_dates else {})
                )
            )
        )
    )


def _condense_nodes(nodes: list):
    # `nodes` contain list with same `term.@id` and `value`
    grouped_nodes = group_nodes_by_consecutive_dates(nodes, sort=False)
    return flatten(map(_node_from_group, grouped_nodes.values()))


def _average_properties(properties: list):
    # group properties by term
    grouped_properties = group_nodes_by_term_id(properties)
    return [
        props[0]
        | {
            "value": list_average(
                non_empty_list([p.get("value") for p in props]),
                default=props[0].get("value"),
            )
        }
        for props in grouped_properties.values()
    ]


def _merge_same_dates(nodes: list):
    # group by term, startDate and endDate
    grouped_nodes = group_nodes_by(
        nodes, ["startDate", "endDate", "term.@id"], sort=False
    )

    def merge_nodes(nodes: list):
        properties = flatten([n.get("properties", []) for n in nodes])
        return (
            nodes[0]
            | (
                {"value": sum_nodes_value(nodes)}
                | (
                    {"properties": _average_properties(properties)}
                    if properties
                    else {}
                )
            )
            if len(nodes) > 1
            else nodes[0]
        )

    return list(map(merge_nodes, grouped_nodes.values()))


def condense_nodes(nodes: list) -> list:
    # merge nodes with the same term and dates as they need to be unique
    values = _merge_same_dates(nodes)
    grouped_nodes = group_nodes_by_term_id_value_and_properties(values, sort=False)
    return flatten(map(_condense_nodes, grouped_nodes.values()))


PROPERTY_UNITS_CONVERSIONS = {
    Units.KG.value: {
        Units.MJ.value: [
            "energyContentLowerHeatingValue",  # "kg" to "mj"
        ]
    },
    Units.M3.value: {
        Units.MJ.value: [
            "density",  # "m3" to "kg"
            "energyContentLowerHeatingValue",  # "kg" to "mj"
        ]
    },
}


def _convert_via_property(
    node: dict, node_value: Union[int, float], property_field: str
) -> Optional[float]:
    """
    Converts a node_value number from one unit to another using a property_field  associated
    with a term inside term node such as "density" or 'energyContentHigherHeatingValue' or listed
    in https://www.hestia.earth/glossary?page=1&termType=property

    Will return none if the property_field is not found

    Parameters
    ----------
    node: dict
        Blank node containing a term
    node_value: int | float
        Value to be converted as float or int
    property_field: str
        E.g., "density"

    Returns
    -------
        Float or None
    """
    node_property_value = get_node_property_value(
        model=None, node=node, prop_id=property_field, default=0, handle_percents=False
    )
    return (
        node_value * node_property_value
        if node_value is not None and bool(node_property_value)
        else None
    )


def convert_unit(
    node, dest_unit: Units, node_value: Union[int, float] = None
) -> Optional[Union[int, float]]:
    """
    Convert a number `value` inside a node or a optional `node_value` belonging to a term `node`, to unit `dest_unit`
    using the ATOMIC_WEIGHT_CONVERSIONS map or failing that, the PROPERTY_UNITS_CONVERSIONS map and lookups
    """
    src_unit = node.get("units") or node.get("term", {}).get("units", "")

    node_value = _node_value(node) if node_value is None else node_value

    return (
        node_value
        if src_unit == dest_unit.value
        else (
            (
                node_value * get_atomic_conversion(src_unit, dest_unit)
                if get_atomic_conversion(src_unit, dest_unit, default_value=None)
                is not None
                else convert_unit_properties(node_value, node, dest_unit)
            )
            if node_value
            else None
        )
    )


def convert_unit_properties(
    node_value: Union[int, float], node: dict, dest_unit: Units
) -> Optional[Union[int, float]]:
    """
    Convert a number `node_value` belonging to a term `node`, to unit `to_units` by chaining multiple unit conversions
    together.
    Uses terms properties for the conversion.
    Returns None if no conversion possible.
    """
    src_unit = node.get("units") or node.get("term", {}).get("units", "")
    conversions = PROPERTY_UNITS_CONVERSIONS.get(src_unit, {}).get(dest_unit.value, [])
    return (
        reduce(
            lambda value, conversion_property_field: _convert_via_property(
                node, value, conversion_property_field
            ),
            conversions,
            node_value,
        )
        if conversions
        else None
    )


def sum_nodes_value(nodes: list):
    values = flatten([n.get("value", []) for n in nodes])
    is_boolean = all([isinstance(v, bool) for v in values])
    return (
        values[0]
        if is_boolean
        else (
            [list_sum(values)]
            if isinstance(nodes[0]["value"], list)
            else list_sum(values)
        )
    )
