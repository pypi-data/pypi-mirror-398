from typing import Union, Optional
from hestia_earth.schema import SchemaType, TermTermType
from hestia_earth.utils.model import linked_node
from hestia_earth.utils.term import download_term

from . import set_node_value, set_node_term, set_node_stats
from .method import include_methodModel


def _new_indicator(
    term: Union[dict, str],
    value: float,
    sd: float = None,
    min: float = None,
    max: float = None,
    inputs: list = None,
    model: Optional[Union[dict, str]] = None,
    land_cover_id: str = None,
    previous_land_cover_id: str = None,
    country_id: str = None,
    key_id: str = None,
):
    return (
        set_node_stats(
            include_methodModel(
                {
                    "@type": SchemaType.INDICATOR.value,
                    "term": linked_node(
                        term if isinstance(term, dict) else download_term(term)
                    ),
                },
                model,
            )
            | set_node_value("value", value)
            | set_node_value("sd", sd)
            | set_node_value("min", min)
            | set_node_value("max", max)
            | (set_node_value("inputs", inputs) if inputs else {})
            | set_node_term("landCover", land_cover_id, TermTermType.LANDCOVER)
            | set_node_term(
                "previousLandCover", previous_land_cover_id, TermTermType.LANDCOVER
            )
            | set_node_term("country", country_id, TermTermType.REGION)
            | set_node_term("key", key_id)
        )
        if value is not None
        else None
    )  # cannot return an indicator without a value
