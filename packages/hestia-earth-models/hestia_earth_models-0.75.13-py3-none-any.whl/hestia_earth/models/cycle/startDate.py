from datetime import timedelta
from hestia_earth.utils.date import DatestrFormat, validate_datestr_format

from hestia_earth.models.log import logRequirements, logShouldRun
from hestia_earth.models.utils.date import parse_node_date
from . import MODEL

REQUIREMENTS = {
    "Cycle": {
        "none": {"startDate": "in day precision"},
        "optional": {
            "endDate": "in day precision",
            "cycleDuration": "",
        },
    }
}
RETURNS = {"The startDate as a string": ""}
MODEL_KEY = "startDate"


def _run_by_cycleDuration(cycle: dict):
    endDate = parse_node_date(cycle, "endDate")
    cycleDuration = cycle.get("cycleDuration")
    days = max(cycleDuration - 1, 1)
    return (endDate - timedelta(days=days)).strftime(DatestrFormat.YEAR_MONTH_DAY.value)


def _should_run_by_cycleDuration(cycle: dict):
    has_endDate = cycle.get("endDate") is not None
    has_endDate_day_precision = has_endDate and validate_datestr_format(
        cycle.get("endDate"), DatestrFormat.YEAR_MONTH_DAY
    )
    has_cycleDuration = cycle.get("cycleDuration") is not None

    logRequirements(
        cycle,
        model=MODEL,
        key=MODEL_KEY,
        by="cycleDuration",
        has_endDate=has_endDate,
        has_endDate_day_precision=has_endDate_day_precision,
        has_cycleDuration=has_cycleDuration,
    )

    should_run = all([has_endDate, has_endDate_day_precision, has_cycleDuration])
    logShouldRun(cycle, MODEL, None, should_run, key=MODEL_KEY, by="cycleDuration")
    return should_run


def _run_by_startDate(cycle: dict):
    startDate = cycle.get("startDate")
    is_same_month = startDate[0:7] == cycle.get("endDate", "")[0:7]
    # start of the month if same month as end date
    return f"{startDate}-01" if is_same_month else f"{startDate}-15"


def _should_run_by_startDate(cycle: dict):
    has_startDate = cycle.get("startDate") is not None
    has_month_precision = has_startDate and validate_datestr_format(
        cycle.get("startDate"), DatestrFormat.YEAR_MONTH
    )
    no_cycleDuration = cycle.get("cycleDuration") is None

    logRequirements(
        cycle,
        model=MODEL,
        key=MODEL_KEY,
        by="startDate",
        has_startDate=has_startDate,
        has_month_precision=has_month_precision,
        no_cycleDuration=no_cycleDuration,
    )

    should_run = all([has_startDate, has_month_precision, no_cycleDuration])
    logShouldRun(cycle, MODEL, None, should_run, key=MODEL_KEY, by="startDate")
    return should_run


def run(cycle: dict):
    # do not run model if `startDate` is already set with a day precision
    startDate = cycle.get("startDate")
    has_startDate_day_precision = startDate and validate_datestr_format(
        startDate, DatestrFormat.YEAR_MONTH_DAY
    )
    return (
        (
            _run_by_cycleDuration(cycle)
            if _should_run_by_cycleDuration(cycle)
            else (_run_by_startDate(cycle) if _should_run_by_startDate(cycle) else None)
        )
        if not has_startDate_day_precision
        else None
    )
