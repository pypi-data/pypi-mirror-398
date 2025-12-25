from typing import Union, Optional, List
from hestia_earth.schema import SchemaType
from hestia_earth.utils.model import linked_node
from hestia_earth.utils.term import download_term

from . import set_node_value
from .method import include_model


def _new_management(
    term: Union[dict, str],
    value: Optional[Union[float, List[float]]] = None,
    model: Optional[Union[dict, str]] = None,
    end_date: str = None,
    start_date: str = None,
):
    return (
        include_model(
            {
                "@type": SchemaType.MANAGEMENT.value,
                "term": linked_node(
                    term if isinstance(term, dict) else download_term(term)
                ),
            },
            model,
        )
        | set_node_value("value", value)
        | set_node_value("endDate", end_date)
        | set_node_value("startDate", start_date)
    )
