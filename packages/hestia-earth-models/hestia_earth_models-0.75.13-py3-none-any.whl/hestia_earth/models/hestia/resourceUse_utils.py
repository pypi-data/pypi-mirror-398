from datetime import datetime
from dateutil.relativedelta import relativedelta
from hestia_earth.schema import TermTermType
from hestia_earth.utils.tools import list_sum, flatten
from hestia_earth.utils.date import (
    DatestrFormat,
    datestrs_match,
    gapfill_datestr,
)

from hestia_earth.models.log import logRequirements, logShouldRun, log_as_table
from hestia_earth.models.utils.impact_assessment import get_site
from hestia_earth.models.utils.indicator import _new_indicator
from .utils import LAND_USE_TERMS_FOR_TRANSFORMATION, crop_ipcc_land_use_category
from . import MODEL

_MAXIMUM_OFFSET_DAYS = 365 * 2
_RESOURCE_USE_TERM_ID = "landOccupationDuringCycle"


def _gap_filled_date_obj(date_str: str) -> datetime:
    return datetime.strptime(
        gapfill_datestr(datestr=date_str, mode="middle"),
        DatestrFormat.YEAR_MONTH_DAY_HOUR_MINUTE_SECOND.value,
    )


def _find_closest_node_date(
    ia_date_str: str,
    management_nodes: list,
    historic_date_offset: int,
    node_date_field: str,
) -> str:
    historic_ia_date_obj = (
        _gap_filled_date_obj(ia_date_str) - relativedelta(years=historic_date_offset)
        if ia_date_str
        else None
    )
    # Calculate all distances in days which are less than MAXIMUM_OFFSET_DAYS from historic date
    # Assumption: if there are two dates are equidistant from the target, choose the second.
    filtered_dates = {
        abs(
            (
                _gap_filled_date_obj(node.get(node_date_field)) - historic_ia_date_obj
            ).days
        ): node.get(node_date_field)
        for node in management_nodes
        if node.get("term", {}).get("termType", "") == TermTermType.LANDCOVER.value
        and abs(
            (
                _gap_filled_date_obj(node.get(node_date_field)) - historic_ia_date_obj
            ).days
        )
        <= _MAXIMUM_OFFSET_DAYS
    }
    return filtered_dates[min(filtered_dates.keys())] if filtered_dates else ""


def _get_current_nodes(management_nodes: list, ia_date_str: str) -> list:
    return [
        node
        for node in management_nodes
        if (
            node.get("startDate")
            and node.get("endDate")
            and node.get("startDate") <= ia_date_str <= node.get("endDate")
        )
    ]


def should_run(
    impact_assessment: dict, term_id: str, historic_date_offset: int
) -> tuple[bool, list]:
    cycle = impact_assessment.get("cycle", {})
    has_otherSites = len(cycle.get("otherSites") or []) != 0

    site = get_site(impact_assessment)
    filtered_management_nodes = [
        node
        for node in site.get("management", [])
        if node.get("value", -1) >= 0
        and node.get("term", {}).get("termType") == TermTermType.LANDCOVER.value
    ]
    match_mode = (
        "start"
        if impact_assessment.get("cycle", {}).get("aggregated") is True
        else "end"
    )
    match_date = "startDate" if match_mode == "start" else "endDate"

    closest_date = _find_closest_node_date(
        ia_date_str=impact_assessment.get(match_date, ""),
        management_nodes=filtered_management_nodes,
        historic_date_offset=historic_date_offset,
        node_date_field=match_date,
    )
    closest_start_date, closest_end_date = (
        (closest_date, None) if match_date == "startDate" else (None, closest_date)
    )
    prior_management_nodes = [
        node
        for node in filtered_management_nodes
        if datestrs_match(node.get("endDate", ""), closest_end_date, "end")
        or datestrs_match(node.get("startDate", ""), closest_start_date, "end")
    ]

    current_nodes = _get_current_nodes(
        management_nodes=filtered_management_nodes,
        ia_date_str=gapfill_datestr(
            impact_assessment.get(match_date, ""), mode=match_mode
        )[:10],
    )

    should_run_node_results = [
        should_run_node(
            current_node=node,
            closest_end_date=closest_end_date,
            closest_start_date=closest_start_date,
            has_otherSites=has_otherSites,
            impact_assessment=impact_assessment,
            prior_management_nodes=prior_management_nodes,
            term_id=term_id,
        )
        for node in current_nodes
    ]
    should_run_result = all([n[0] for n in should_run_node_results])
    logShouldRun(impact_assessment, MODEL, term=term_id, should_run=should_run_result)
    return should_run_result, flatten([n[1] for n in should_run_node_results])


def should_run_node(
    current_node,
    closest_end_date,
    closest_start_date,
    has_otherSites: bool,
    impact_assessment: dict,
    prior_management_nodes: list,
    term_id: str,
) -> tuple[bool, list]:
    landCover_term_id = (current_node or {}).get("term", {}).get("@id")
    ipcc_land_use_category = crop_ipcc_land_use_category(landCover_term_id)
    total_landOccupationDuringCycle = list_sum(
        [
            node.get("value")
            for node in impact_assessment.get("emissionsResourceUse", [])
            if node.get("term", {}).get("@id", "") == _RESOURCE_USE_TERM_ID
            and crop_ipcc_land_use_category(node.get("landCover", {}).get("@id", ""))
            == ipcc_land_use_category
        ],
        default=None,
    )

    indicators = (
        [
            {
                "landCover-id": landCover_term_id,
                "previous-landCover-id": previous_land_cover_id,
                "landOccupationDuringCycle": total_landOccupationDuringCycle,
                "historical-landUse-change": list_sum(
                    [
                        node.get("value")
                        for node in prior_management_nodes
                        if node.get("term", {}).get("@id") == previous_land_cover_id
                    ],
                    default=None,
                ),
            }
            for previous_land_cover_id in [
                t[0] for t in LAND_USE_TERMS_FOR_TRANSFORMATION.values()
            ]
        ]
        if landCover_term_id
        else []
    )
    valid_indicators = [
        indicator
        for indicator in indicators
        if indicator["historical-landUse-change"] is not None
    ]

    logRequirements(
        impact_assessment,
        model=MODEL,
        term=term_id,
        has_otherSites=has_otherSites,
        closest_end_date=closest_end_date,
        closest_start_date=closest_start_date,
        landCover_term_id=landCover_term_id,
        ipcc_land_use_category=ipcc_land_use_category,
        indicators=log_as_table(indicators),
    )

    should_run_node_result = all(
        [
            not has_otherSites,
            ipcc_land_use_category,
            total_landOccupationDuringCycle is not None,
            valid_indicators,
        ]
    )
    return should_run_node_result, valid_indicators


def run_resource_use(
    impact_assessment: dict, historic_date_offset: int, term_id: str
) -> list:
    _should_run, indicators = should_run(
        impact_assessment=impact_assessment,
        term_id=term_id,
        historic_date_offset=historic_date_offset,
    )
    return (
        [
            _new_indicator(
                term=term_id,
                model=MODEL,
                land_cover_id=i["landCover-id"],
                previous_land_cover_id=i["previous-landCover-id"],
                value=(
                    i["landOccupationDuringCycle"]
                    * i["historical-landUse-change"]
                    / 100
                )
                / historic_date_offset,
            )
            for i in indicators
        ]
        if _should_run
        else []
    )
