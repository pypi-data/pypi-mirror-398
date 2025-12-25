import numpy as np
import numpy.typing as npt

from hestia_earth.schema import (
    EmissionMethodTier,
    EmissionStatsDefinition,
    SiteSiteType,
    TermTermType,
)
from typing import Callable, Literal, Optional

from hestia_earth.utils.blank_node import get_node_value
from hestia_earth.utils.date import OLDEST_DATE
from hestia_earth.utils.descriptive_stats import calc_descriptive_stats
from hestia_earth.utils.stats import gen_seed, normal_1d, repeat_single

from hestia_earth.models.log import (
    format_conditional_message,
    format_float,
    format_nd_array,
    log_as_table,
    logRequirements,
    logShouldRun,
)
from hestia_earth.models.utils import split_on_condition
from hestia_earth.models.utils.blank_node import filter_list_term_id
from hestia_earth.models.utils.constant import Units, get_atomic_conversion
from hestia_earth.models.utils.ecoClimateZone import (
    EcoClimateZone,
    get_eco_climate_zone_value,
)
from hestia_earth.models.utils.emission import _new_emission
from hestia_earth.models.utils.product import has_flooded_rice
from hestia_earth.models.utils.select_nodes import (
    _most_relevant_blank_node,
    closest_depth,
    select_nodes_by,
)

from .utils import get_N2O_factors
from . import MODEL

REQUIREMENTS = {
    "Cycle": {
        "emissions": [
            {
                "@type": "Emission",
                "value": "",
                "term.@id": "co2ToAirSoilOrganicCarbonStockChangeLandUseChange",
                "depth": "30",
            },
            {
                "@type": "Emission",
                "value": "",
                "term.@id": "co2ToAirSoilOrganicCarbonStockChangeManagementChange",
                "depth": "30",
            },
        ],
        "optional": {
            "endDate": "",
            "site": {
                "@type": "Site",
                "measurements": [
                    {"@type": "Measurement", "value": "", "term.@id": "ecoClimateZone"}
                ],
            },
            "products": [{"@type": "Product", "term.@id": "riceGrainInHuskFlooded"}],
            "practices": [{"@type": "Practice", "term.termType": "waterRegime"}],
        },
    }
}
RETURNS = {
    "Emission": [
        {
            "value": "",
            "min": "",
            "max": "",
            "sd": "",
            "methodTier": "tier 1",
            "statsDefinition": "simulated",
            "methodModelDescription": ["Aggregated version", "Disaggregated version"],
            "depth": 30,
        }
    ]
}
LOOKUPS = {
    "waterRegime": [
        "IPCC_2019_N2O_rice",
        "IPCC_2019_N2O_rice-min",
        "IPCC_2019_N2O_rice-max",
    ]
}
TERM_ID = "n2OToAirDiminishingSoilCarbonStocksLandUseChangeDirect,n2OToAirDiminishingSoilCarbonStocksManagementChangeDirect"  # noqa: E501
TIER = EmissionMethodTier.TIER_1.value

_TERM_IDS = TERM_ID.split(",")

_LU_TERM_ID = _TERM_IDS[0]
_MG_TERM_ID = _TERM_IDS[1]

_LU_SOC_TERM_ID = "co2ToAirSoilOrganicCarbonStockChangeLandUseChange"
_MG_SOC_TERM_ID = "co2ToAirSoilOrganicCarbonStockChangeManagementChange"

_TERM_ID_MAPPING = {_LU_TERM_ID: _LU_SOC_TERM_ID, _MG_TERM_ID: _MG_SOC_TERM_ID}

_DEPTH_LOWER = 30
_ITERATIONS = 1000
_STATS_DEFINITION = EmissionStatsDefinition.SIMULATED.value
_VALID_SITE_TYPES = [SiteSiteType.CROPLAND.value]

_C_TO_N_RATIOS = {
    _LU_TERM_ID: {"value": 15, "min": 10, "max": 30},
    _MG_TERM_ID: {"value": 10, "min": 8, "max": 15},
}
"""
Conversion factors valid for croplands only.
"""


def _emission(term_id: str, aggregated: bool = False, **kwargs) -> dict:
    """
    Build a HESTIA [Emission node](https://www.hestia.earth/schema/Emission) using model output data.
    """
    value_keys, other_keys = split_on_condition(
        [*kwargs], lambda k: k in ("value", "sd", "min", "max")
    )
    emission = _new_emission(
        term=term_id, model=MODEL, **{k: kwargs.get(k) for k in value_keys}
    )
    return emission | {
        "methodTier": TIER,
        "methodModelDescription": (
            "Aggregated version" if aggregated else "Disaggregated version"
        ),
        "depth": _DEPTH_LOWER,
        **{k: kwargs.get(k) for k in other_keys},
    }


def _sample_normal_clipped(
    *,
    iterations: int,
    value: float,
    min: float,
    max: float,
    seed: int | np.random.Generator | None = None,
    **_,
) -> npt.NDArray:
    sigma = (max - min) / 4  # assumed sd, following other n2o emission models
    arr = normal_1d(shape=(1, iterations), mu=value, sigma=sigma, seed=seed)
    return np.clip(arr, min, max)


def _sample_constant(*, value: float, **_) -> npt.NDArray:
    """Sample a constant model parameter."""
    return repeat_single(shape=(1, 1), value=value)


_KWARGS_TO_SAMPLE_FUNC = {
    ("value", "min", "max"): _sample_normal_clipped,
    ("value",): _sample_constant,
}
"""
Mapping from available distribution data to sample function.
"""


def _get_sample_func(kwargs: dict) -> Callable:
    """
    Select the correct sample function for a parameter based on the distribution data available.
    """
    return next(
        sample_func
        for required_kwargs, sample_func in _KWARGS_TO_SAMPLE_FUNC.items()
        if all(kwarg in kwargs.keys() for kwarg in required_kwargs)
    )


def _sample_emission_factor(
    model_term_id: str,
    cycle: dict,
    eco_climate_zone: Optional[EcoClimateZone] = None,
    flooded_rice: bool = False,
    seed: int | np.random.Generator | None = None,
):
    ecz_str = f"{eco_climate_zone.value}" if eco_climate_zone else None

    factor_data, aggregated = get_N2O_factors(
        model_term_id,
        cycle,
        TermTermType.ORGANICFERTILISER,
        ecoClimateZone=ecz_str,
        flooded_rice=flooded_rice,
    )
    sample_func = _get_sample_func(factor_data)
    return (
        sample_func(iterations=_ITERATIONS, seed=seed, **factor_data),
        factor_data,
        aggregated,
    )


def _sample_c_to_n_ratio(
    term_id: Literal[
        "n2OToAirDiminishingSoilCarbonStocksLandUseChangeDirect",
        "n2OToAirDiminishingSoilCarbonStocksManagementChangeDirect",
    ],
    seed: int | np.random.Generator | None = None,
):
    factor_data = _C_TO_N_RATIOS[term_id]
    sample_func = _get_sample_func(factor_data)
    return sample_func(iterations=_ITERATIONS, seed=seed, **factor_data)


def _most_relevant_emission(emissions: list[dict], term_id: str, target_date: str):
    """
    Select the most relevant emission by date with a depth 0f 30cm.
    """
    return select_nodes_by(
        emissions,
        [
            lambda nodes: filter_list_term_id(nodes, term_id),
            lambda nodes: closest_depth(nodes, _DEPTH_LOWER),
            lambda nodes: _most_relevant_blank_node(nodes, target_date),
        ],
    )


def _should_run(cycle: dict):
    seed = gen_seed(cycle, MODEL, TERM_ID)
    emissions = cycle.get("emissions", [])
    products = cycle.get("products", [])
    end_date = cycle.get("endDate", OLDEST_DATE)

    site_type = cycle.get("site", {}).get("siteType")
    valid_site_type = site_type in _VALID_SITE_TYPES

    eco_climate_zone = get_eco_climate_zone_value(cycle, True)
    flooded_rice = has_flooded_rice(products)

    n2o_factor, n2o_factor_data, aggregated = _sample_emission_factor(
        TERM_ID,
        cycle,
        eco_climate_zone=eco_climate_zone,
        flooded_rice=flooded_rice,
        seed=seed,
    )

    def should_run_emission(term_id):
        soc_term_id = _TERM_ID_MAPPING[term_id]

        c_to_n_ratio = _sample_c_to_n_ratio(term_id, seed=seed)
        soc_emission_node = _most_relevant_emission(emissions, soc_term_id, end_date)
        soc_emission_value = get_node_value(soc_emission_node, default=None)

        should_run = all(
            [
                valid_site_type,
                all(
                    var is not None
                    for var in [n2o_factor, c_to_n_ratio, soc_emission_value]
                ),
            ]
        )

        logRequirements(
            cycle,
            model=MODEL,
            term=term_id,
            seed=seed,
            valid_site_type=format_conditional_message(
                valid_site_type,
                "True",
                f"False (C to N ratio only valid for siteTypes {"and ".join(_VALID_SITE_TYPES)})",
            ),
            eco_climate_zone=eco_climate_zone,
            has_flooded_rice=flooded_rice,
            soc_emission_term_id=soc_term_id,
            soc_emission=format_float(soc_emission_value),
            c_to_n_ratio=format_nd_array(c_to_n_ratio),
            n2o_factor=format_nd_array(n2o_factor),
            n2o_factor_data=log_as_table(n2o_factor_data),
            n2o_factor_aggregated=aggregated,
        )

        logShouldRun(cycle, MODEL, term_id, should_run, methodTier=TIER)

        return should_run, term_id, soc_emission_value, c_to_n_ratio

    run_params = [should_run_emission(term_id) for term_id in _TERM_IDS]
    should_run = any(should_run_emission for should_run_emission, *_ in run_params)

    return should_run, run_params, n2o_factor, aggregated


def _co2_to_c(value: float) -> float:
    """Convert mass of CO2 to mass of C."""
    return value / get_atomic_conversion(Units.KG_CO2, Units.TO_C)


def _n_to_n2o(value: float) -> float:
    """Convert mass of N to mass of N2O."""
    return value * get_atomic_conversion(Units.KG_N2O, Units.TO_N)


def _co2_to_n2o(
    value: float | npt.NDArray,
    c_n_ratio: float | npt.NDArray,
    n2o_factor: float | npt.NDArray,
) -> float:
    """Convert mass of CO2 emitted by SOC stock change to the mass of N2O emitted."""
    return _n_to_n2o(_co2_to_c(value) * 1 / c_n_ratio) * n2o_factor


def _run(
    run_params: list[tuple[bool, str, float, npt.NDArray]],
    n2o_factor: npt.NDArray,
    aggregated: bool,
):
    """
    Run for model for each run param.

    Parameters
    ----------
    run_params : list[tuple[bool, str, float, npt.NDArray]]
        A list of run parameters to calculate each `n2OToAirDiminishingSoilCarbonStocks...` emission. Each tuple
        should follow the format: `(should_run (bool), term_id (str), co2_emission (float), c_to_n_ratio (NDArray))`.
    n2o_factor: npt.NDArray
        The portion of N applied to mineral soils that is emitted as N2O, kg N (kg N)-1.
    aggregated: bool
        Whether the N2O factor is based on aggregated data.

    Returns
    -------
    dict
        Model results. HESTIA `Emission` nodes, see: https://www.hestia.earth/schema/Measurement representing
        `n2OToAirDiminishingSoilCarbonStocksLandUseChangeDirect` and
        `n2OToAirDiminishingSoilCarbonStocksManagementChangeDirect`
    """

    def run_emission(term_id, soc_emission, c_to_n_ratio):
        """
        Run the model for an `n2OToAirDiminishingSoilCarbonStocks...` emission.
        """
        kwargs = (
            {"value": 0}
            if soc_emission <= 0
            else calc_descriptive_stats(
                _co2_to_n2o(np.maximum(soc_emission, 0), c_to_n_ratio, n2o_factor),
                _STATS_DEFINITION,
            )
        )
        return _emission(term_id=term_id, aggregated=aggregated, **kwargs)

    return [
        run_emission(term_id, soc_emission, c_to_n_ratio)
        for should_run_emission, term_id, soc_emission, c_to_n_ratio in run_params
        if should_run_emission
    ]


def run(cycle: dict):
    should_run, *args = _should_run(cycle)
    return _run(*args) if should_run else []
