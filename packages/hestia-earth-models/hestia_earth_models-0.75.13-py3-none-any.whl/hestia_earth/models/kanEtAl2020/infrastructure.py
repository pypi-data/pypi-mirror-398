from hestia_earth.schema import TermTermType
from hestia_earth.utils.model import filter_list_term_type
from hestia_earth.utils.lookup import is_missing_value
from hestia_earth.utils.tools import pick, safe_parse_float, flatten
from hestia_earth.utils.term import download_term

from hestia_earth.models.log import logShouldRun, logRequirements, log_as_table
from hestia_earth.models.utils.term import get_lookup_value
from hestia_earth.models.utils.input import _new_input
from . import MODEL

REQUIREMENTS = {
    "Site": {
        "siteType": "glass or high accessible cover",
        "infrastructure": [
            {
                "@type": "Infrastructure",
                "term.termType": "building",
                "none": {"inputs": [{"@type": "Input"}]},
            }
        ],
    }
}
RETURNS = {"Infrastructure": [{"defaultLifespan": "", "inputs": ""}]}
LOOKUPS = {"building": ["defaultLifespan", "materialTermIds", "substrateTermIds"]}
MODEL_KEY = "infrastructure"
_LOOKUPS = LOOKUPS[TermTermType.BUILDING.value]


def _map_inputs(value: str, termType: TermTermType):
    # e.g., term1:120;term2:130
    values = value.split(";")
    return [
        _new_input(
            term=download_term(value.split(":")[0], termType=termType),
            value=safe_parse_float(value.split(":")[1]),
            model=MODEL,
        )
        for value in values
    ]


def _run_infrastructure(site: dict, data: dict):
    term_id = data["node"].get("term", {}).get("@id")
    default_lifespan = safe_parse_float(data.get("defaultLifespan"))
    inputs = flatten(
        [
            _map_inputs(value=data.get(key), termType=termType)
            for key, termType in [
                ("materialTermIds", TermTermType.MATERIAL),
                ("substrateTermIds", TermTermType.SUBSTRATE),
            ]
        ]
    )

    logRequirements(
        site, model=MODEL, term=term_id, model_key=MODEL_KEY, **pick(data, _LOOKUPS)
    )

    logShouldRun(site, MODEL, term_id, True, model_key=MODEL_KEY)

    return data["node"] | {"defaultLifespan": default_lifespan, "inputs": inputs}


def _infrastructure_data(infrastructure: dict):
    lookup_data = {
        lookup: get_lookup_value(infrastructure.get("term", {}), lookup)
        for lookup in _LOOKUPS
    }
    has_no_inputs = not infrastructure.get("inputs")
    valid = all(
        [has_no_inputs]
        + [not is_missing_value(value) for value in lookup_data.values()]
    )
    return (
        {"node": infrastructure}
        | lookup_data
        | {"has_no_inputs": has_no_inputs, "valid": valid}
    )


def _should_run(site: dict):
    infrastructure = filter_list_term_type(
        site.get("infrastructure", []), TermTermType.BUILDING
    )
    infrastructure_values = list(map(_infrastructure_data, infrastructure))

    logRequirements(
        site,
        model=MODEL,
        model_key=MODEL_KEY,
        infrastructure_values=log_as_table(
            [
                {"id": value["node"].get("term", {}).get("@id")}
                | pick(value, ["valid"] + _LOOKUPS)
                for value in infrastructure_values
            ]
        ),
    )

    should_run = all([infrastructure_values])
    logShouldRun(site, MODEL, None, should_run, model_key=MODEL_KEY)
    return should_run, infrastructure_values


def run(site: dict):
    should_run, infrastructure_values = _should_run(site)
    return (
        [
            _run_infrastructure(site, data)
            for data in infrastructure_values
            if data.get("valid")
        ]
        if should_run
        else []
    )
