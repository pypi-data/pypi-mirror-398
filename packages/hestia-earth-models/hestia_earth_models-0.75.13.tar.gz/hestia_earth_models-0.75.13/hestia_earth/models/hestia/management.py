from typing import List
from datetime import timedelta, datetime
from hestia_earth.schema import SchemaType, TermTermType, COMPLETENESS_MAPPING
from hestia_earth.utils.lookup import download_lookup, get_table_value
from hestia_earth.utils.model import filter_list_term_type
from hestia_earth.utils.tools import (
    safe_parse_float,
    flatten,
    is_number,
    is_boolean,
    pick,
)
from hestia_earth.utils.blank_node import get_node_value
from hestia_earth.utils.date import DatestrFormat, DatestrGapfillMode, gapfill_datestr

from hestia_earth.models.log import logRequirements, logShouldRun, log_as_table
from hestia_earth.models.utils.management import _new_management
from hestia_earth.models.utils.term import get_lookup_value
from hestia_earth.models.utils.blank_node import condense_nodes
from hestia_earth.models.utils.crop import get_landCover_term_id
from hestia_earth.models.utils.group_nodes import group_nodes_by
from hestia_earth.models.utils.site import (
    related_cycles,
    get_land_cover_term_id as get_landCover_term_id_from_site_type,
)
from . import MODEL
from ..utils.property import get_property_lookup_value

REQUIREMENTS = {
    "Site": {
        "related": {
            "Cycle": [
                {
                    "@type": "Cycle",
                    "endDate": "",
                    "practices": [
                        {
                            "@type": "Practice",
                            "term.termType": [
                                "waterRegime",
                                "tillage",
                                "cropResidueManagement",
                                "landUseManagement",
                                "pastureManagement",
                                "system",
                                "landCover",
                            ],
                            "value": "",
                        }
                    ],
                    "inputs": [
                        {
                            "@type": "Input",
                            "term.termType": [
                                "inorganicFertiliser",
                                "organicFertiliser",
                                "soilAmendment",
                            ],
                        }
                    ],
                    "optional": {"startDate": "", "cycleDuration": ""},
                }
            ]
        }
    }
}
RETURNS = {
    "Management": [
        {
            "term.termType": [
                "landCover",
                "waterRegime",
                "tillage",
                "cropResidueManagement",
                "landUseManagement",
                "system",
            ],
            "value": "",
            "endDate": "",
            "startDate": "",
        }
    ]
}
LOOKUPS = {
    "biochar": "inputGapFillManagementTermId",
    "crop": ["landCoverTermId", "maximumCycleDuration"],
    "forage": ["landCoverTermId"],
    "inorganicFertiliser": "inputGapFillManagementTermId",
    "organicFertiliser": "inputGapFillManagementTermId",
    "soilAmendment": "inputGapFillManagementTermId",
    "landUseManagement": "GAP_FILL_TO_MANAGEMENT",
    "property": "GAP_FILL_TO_MANAGEMENT",
    "landCover": "sumIs100Group",
}
MODEL_KEY = "management"

_PRACTICES_TERM_TYPES = [
    TermTermType.WATERREGIME,
    TermTermType.TILLAGE,
    TermTermType.CROPRESIDUEMANAGEMENT,
    TermTermType.LANDUSEMANAGEMENT,
    TermTermType.PASTUREMANAGEMENT,
    TermTermType.SYSTEM,
    TermTermType.LANDCOVER,
]
_PRACTICES_COMPLETENESS_MAPPING = COMPLETENESS_MAPPING.get(
    SchemaType.PRACTICE.value, {}
)


def management(data: dict):
    start_date = (
        _gap_filled_date_only_str(date_str=data["startDate"], mode="start")
        if data.get("startDate")
        else None
    )
    node = _new_management(
        term=data.get("id"),
        model=MODEL,
        value=data["value"],
        end_date=_gap_filled_date_only_str(data["endDate"]),
        start_date=start_date,
    )
    if data.get("properties"):
        node["properties"] = data["properties"]
    return node


def _is_cover_crop(term_id: str) -> bool:
    return (
        get_property_lookup_value(
            model=MODEL, term_id=term_id, column="blankNodesGroup"
        )
        == "Cover crops"
    )


def _get_cycle_duration(cycle: dict, land_cover_id: str = None):
    cycle_duration = cycle.get("cycleDuration")
    lookup_value = (
        None
        if cycle_duration or not land_cover_id
        else safe_parse_float(
            get_table_value(
                download_lookup("crop.csv"),
                "landCoverTermId",
                land_cover_id,
                "maximumCycleDuration",
            ),
            default=None,
        )
    )
    return cycle_duration or lookup_value


def _gap_filled_date_only_str(date_str: str, mode: DatestrGapfillMode = "end") -> str:
    return gapfill_datestr(datestr=date_str, mode=mode)[:10]


def _gap_filled_date_obj(date_str: str, mode: DatestrGapfillMode = "end") -> datetime:
    return datetime.strptime(
        _gap_filled_date_only_str(date_str=date_str, mode=mode),
        DatestrFormat.YEAR_MONTH_DAY.value,
    )


def _gap_filled_start_date(
    cycle: dict, end_date: str, land_cover_id: str = None
) -> dict:
    """If possible, gap-fill the startDate based on the endDate - cycleDuration"""
    cycle_duration = _get_cycle_duration(cycle, land_cover_id)
    return (
        {
            "startDate": (
                _gap_filled_date_obj(cycle.get("startDate"), mode="start")
                if cycle.get("startDate")
                else _gap_filled_date_obj(end_date) - timedelta(days=cycle_duration - 1)
            )
        }
        if any([cycle_duration, cycle.get("startDate")])
        else {}
    )


def _include_with_date_gap_fill(value: dict, keys: list) -> dict:
    return {
        k: (
            _gap_filled_date_only_str(v)
            if k == "endDate"
            else _gap_filled_date_only_str(v, mode="start") if k == "startDate" else v
        )
        for k, v in value.items()
        if k in keys
    }


def _should_gap_fill(term: dict):
    value = get_lookup_value(lookup_term=term, column="GAP_FILL_TO_MANAGEMENT")
    return bool(value)


def _map_to_value(value: dict):
    return {
        "id": value.get("term", {}).get("@id"),
        "value": value.get("value"),
        "startDate": value.get("startDate"),
        "endDate": value.get("endDate"),
        "properties": value.get("properties"),
    }


def _extract_node_value(node: dict) -> dict:
    return node | {"value": get_node_value(node)}


def _get_relevant_items(
    cycle: dict,
    item_name: str,
    term_types: List[TermTermType],
    completeness_mapping: dict = {},
):
    """
    Get items from the list of cycles with any of the relevant terms.
    Also adds dates from Cycle.
    """
    # filter term types that are no complete
    complete_term_types = (
        term_types
        if not completeness_mapping
        else [
            term_type
            for term_type in term_types
            if any(
                [
                    not completeness_mapping.get(term_type.value),
                    cycle.get("completeness", {}).get(
                        completeness_mapping.get(term_type.value), False
                    ),
                ]
            )
        ]
    )
    blank_nodes = filter_list_term_type(cycle.get(item_name, []), complete_term_types)
    return [
        _include_with_date_gap_fill(cycle, ["startDate", "endDate"])
        | pick(
            (
                _gap_filled_start_date(
                    cycle=cycle,
                    end_date=(
                        item.get("endDate")
                        if "endDate" in item
                        else cycle.get("endDate", "")
                    ),
                    land_cover_id=get_landCover_term_id(item.get("term", {})),
                )
                if "startDate" not in item
                else {}
            ),
            "startDate",
        )
        | item
        for item in blank_nodes
    ]


def _input_gap_fill_term_id(input: dict):
    return get_lookup_value(
        input.get("term"), "inputGapFillManagementTermId", skip_debug=True
    )


def _input_value_valid(input: dict):
    value = get_node_value(input)
    return (
        value > 0
        if is_number(value)
        else bool(value) is True if is_boolean(value) else False
    )


def _run_from_inputs(cycle: dict) -> list:
    inputs_with_ids = [
        {
            "input-id": input.get("term", {}).get("@id"),
            "input-valid": _input_value_valid(input),
            "term-id": _input_gap_fill_term_id(input),
        }
        for input in cycle.get("inputs", [])
    ]
    return [
        {
            "id": input.get("term-id"),
            "value": True,
            "startDate": cycle.get("startDate"),
            "endDate": cycle.get("endDate"),
        }
        for input in inputs_with_ids
        if all([input.get("term-id"), input.get("input-valid")])
    ]


def _cycle_has_existing_non_cover_land_cover_nodes(cycle: dict) -> bool:
    # if there are any landCover blank nodes in Practices without a Property from the
    # blankNodesGroup = Cover crops lookup, return True, else False
    return any(
        [
            practice
            for practice in cycle.get("practices", [])
            if practice.get("term", {}).get("termType") == TermTermType.LANDCOVER.value
            and not any(
                prop
                for prop in practice.get("properties", [])
                if _is_cover_crop(prop.get("term", {}).get("@id"))
            )
        ]
    )


def _run_from_siteType(cycle: dict, site_type_id: str):
    start_date = cycle.get("startDate") or _gap_filled_start_date(
        cycle=cycle, end_date=cycle.get("endDate"), land_cover_id=site_type_id
    ).get("startDate")
    no_land_cover_blank_node = not _cycle_has_existing_non_cover_land_cover_nodes(cycle)

    should_run = all([site_type_id, start_date, no_land_cover_blank_node])
    return (
        [
            {
                "id": site_type_id,
                "termType": TermTermType.LANDCOVER.value,
                "value": 100,
                "startDate": start_date,
                "endDate": cycle.get("endDate"),
            }
        ]
        if should_run
        else []
    )


def _node_with_gap_filled_dates(node: dict, cycle: dict, site_type_id: str) -> dict:
    return node | {
        "endDate": node.get("endDate") or cycle.get("endDate"),
        "startDate": node.get("startDate")
        or cycle.get("startDate")
        or _gap_filled_start_date(
            cycle=cycle, end_date=cycle.get("endDate"), land_cover_id=site_type_id
        ).get("startDate"),
    }


def _dates_overlap(
    target_practice: dict, node: dict, cycle: dict, site_type_id: str
) -> bool:
    target_practice = _node_with_gap_filled_dates(
        node=target_practice, cycle=cycle, site_type_id=site_type_id
    )
    node = _node_with_gap_filled_dates(
        node=node, cycle=cycle, site_type_id=site_type_id
    )
    return all(
        [
            node["startDate"],
            node["endDate"],
            target_practice["startDate"],
            target_practice["endDate"],
            (
                node["startDate"] <= target_practice["startDate"] <= node["endDate"]
                or node["startDate"] < target_practice["endDate"] <= node["endDate"]
            ),
        ]
    )


def _should_run_practice(
    site: dict, management_nodes: list, cycle: dict, site_type_id: str
):
    """
    Include only landUseManagement practices where GAP_FILL_TO_MANAGEMENT = True
    """
    landCover_management_nodes = [
        _node_with_gap_filled_dates(node=node, cycle=cycle, site_type_id=site_type_id)
        | {
            "sumIs100Group": get_lookup_value(
                node.get("term", {}), "sumIs100Group", skip_debug=True, model=MODEL
            )
        }
        for node in filter_list_term_type(management_nodes, TermTermType.LANDCOVER)
    ]

    def exec(practice: dict):
        term = practice.get("term", {})
        term_id = term["@id"]
        should_gap_fill = term.get(
            "termType"
        ) != TermTermType.LANDUSEMANAGEMENT.value or _should_gap_fill(term)
        target_group = get_lookup_value(
            term, "sumIs100Group", skip_debug=True, model=MODEL
        )
        no_other_land_cover_in_same_group = (
            next(
                (
                    True
                    for node in landCover_management_nodes
                    if (
                        node["sumIs100Group"] == target_group
                        and _dates_overlap(
                            target_practice=practice,
                            node=node,
                            cycle=cycle,
                            site_type_id=site_type_id,
                        )
                    )
                ),
                None,
            )
            is None
        )
        # cannot gap-fill landCover without a `startDate`
        has_required_startDate = term.get(
            "termType"
        ) != TermTermType.LANDCOVER.value or practice.get("startDate")

        should_run = all(
            [should_gap_fill, has_required_startDate, no_other_land_cover_in_same_group]
        )
        if not should_run:
            logRequirements(
                site,
                model=MODEL,
                term=term_id,
                model_key=MODEL_KEY,
                should_gap_fill=should_gap_fill,
                has_required_startDate=has_required_startDate,
                no_other_land_cover_in_same_group=no_other_land_cover_in_same_group,
            )
            logShouldRun(site, MODEL, term_id, False, model_key=MODEL_KEY)
        return should_run

    return exec


def _run_from_practices(site: dict, cycle: dict, site_type_id: str):
    practices = [
        _extract_node_value(
            _include_with_date_gap_fill(
                value=practice,
                keys=["term", "value", "startDate", "endDate", "properties"],
            )
        )
        for practice in _get_relevant_items(
            cycle=cycle,
            item_name="practices",
            term_types=_PRACTICES_TERM_TYPES,
            completeness_mapping=_PRACTICES_COMPLETENESS_MAPPING,
        )
    ]
    management_nodes = site.get("management", [])
    return list(
        map(
            _map_to_value,
            filter(
                _should_run_practice(site, management_nodes, cycle, site_type_id),
                practices,
            ),
        )
    )


def _run_cycle(site: dict, cycle: dict):
    inputs = _run_from_inputs(cycle)
    site_type = site.get("siteType")
    site_type_id = get_landCover_term_id_from_site_type(site_type)
    site_types = _run_from_siteType(cycle=cycle, site_type_id=site_type_id)
    practices = _run_from_practices(site=site, cycle=cycle, site_type_id=site_type_id)
    return [
        node | {"cycle-id": cycle.get("@id")}
        for node in inputs + site_types + practices
    ]


def run(site: dict):
    cycles = related_cycles(site)
    nodes = flatten([_run_cycle(site=site, cycle=cycle) for cycle in cycles])

    # group nodes with same `id` to display as a single log per node
    grouped_nodes = group_nodes_by(nodes, "id")
    for id, values in grouped_nodes.items():
        logRequirements(
            site,
            model=MODEL,
            term=id,
            model_key=MODEL_KEY,
            details=log_as_table(values, ignore_keys=["id", "properties"]),
        )
        logShouldRun(site, MODEL, id, True, model_key=MODEL_KEY)

    return condense_nodes(list(map(management, nodes)))
