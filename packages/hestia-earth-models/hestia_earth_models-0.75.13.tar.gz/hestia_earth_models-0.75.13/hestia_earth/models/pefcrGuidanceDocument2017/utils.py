from hestia_earth.schema import EmissionMethodTier, TermTermType
from hestia_earth.utils.tools import flatten, list_sum
from hestia_earth.utils.blank_node import group_by_keys

from hestia_earth.models.log import logShouldRun, logRequirements, log_as_table
from hestia_earth.models.utils.emission import _new_emission
from hestia_earth.models.utils.pesticideAI import get_pesticides_from_inputs
from hestia_earth.models.utils.blank_node import get_lookup_value

from . import MODEL

_TIER = EmissionMethodTier.TIER_1.value


def _emission(term_id: str, value: float, key_id: str):
    emission = _new_emission(term=term_id, model=MODEL, value=value, key_id=key_id)
    emission["methodTier"] = _TIER
    return emission


def _run_input(emission_term_id: str, cycle: dict):
    emission_factor = get_lookup_value(
        {"termType": TermTermType.EMISSION.value, "@id": emission_term_id},
        "pefcr2017PesticideFateFactor",
    )

    def run(inputs: list):
        input = inputs[0]
        input_term_id = input.get("term", {}).get("@id")
        input_value = list_sum(flatten(input.get("value", []) for input in inputs))

        # grouping the inputs together in the logs
        input_parent_term_id = (input.get("parent", {})).get("@id") or input.get(
            "animalId", {}
        )
        extra_logs = {
            **(
                {"input_group_id": input_parent_term_id} if input_parent_term_id else {}
            ),
            **({"animalId": input.get("animalId")} if input.get("animalId") else {}),
            f"{emission_term_id}_factor": emission_factor,
        }

        logRequirements(
            cycle,
            model=MODEL,
            term=input_term_id,
            input_value=input_value,
            **extra_logs,
        )

        # log on both Input and Emission
        logShouldRun(cycle, MODEL, input_term_id, True, methodTier=_TIER)
        logShouldRun(
            cycle,
            MODEL,
            input_term_id,
            True,
            methodTier=_TIER,
            emission_id=emission_term_id,
        )

        return _emission(
            emission_term_id, input_value * emission_factor, key_id=input_term_id
        )

    return run


def run(emission_term_id: str, cycle: dict):
    inputs = get_pesticides_from_inputs(cycle)
    logRequirements(
        cycle,
        model=MODEL,
        term=emission_term_id,
        inputs=log_as_table([v.get("term", {}).get("@id") for v in inputs]),
    )

    should_run = all([inputs])
    logShouldRun(cycle, MODEL, emission_term_id, should_run, methodTier=_TIER)

    grouped_inputs = group_by_keys(inputs, ["term"])
    return flatten(map(_run_input(emission_term_id, cycle), grouped_inputs.values()))
