from typing import Union, Optional, List
from hestia_earth.schema import SchemaType
from hestia_earth.utils.model import linked_node
from hestia_earth.utils.term import download_term

from . import set_node_value, set_node_stats
from .method import include_model


def _new_practice(
    term: Union[dict, str],
    value: Optional[Union[float, List[float]]] = None,
    sd: float = None,
    min: float = None,
    max: float = None,
    model: Optional[Union[dict, str]] = None,
    end_date: str = None,
    start_date: str = None,
):
    return set_node_stats(
        include_model(
            {
                "@type": SchemaType.PRACTICE.value,
                "term": linked_node(
                    term if isinstance(term, dict) else download_term(term)
                ),
            },
            model,
        )
        | set_node_value("value", value, is_list=True)
        | (set_node_value("sd", sd, is_list=True) if sd is not None else {})
        | set_node_value("min", min, is_list=True)
        | set_node_value("max", max, is_list=True)
        | set_node_value("endDate", end_date)
        | set_node_value("startDate", start_date)
    )
