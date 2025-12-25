from enum import Enum
from functools import reduce
from itertools import product
import numpy as np
import numpy.typing as npt
from typing import Any, Callable, Literal, NotRequired, Optional, TypedDict, Union
from hestia_earth.schema import (
    EmissionMethodTier,
    EmissionStatsDefinition,
    SiteSiteType,
)

from hestia_earth.utils.descriptive_stats import calc_descriptive_stats
from hestia_earth.utils.lookup import download_lookup, get_table_value, column_name
from hestia_earth.utils.tools import safe_parse_float
from hestia_earth.utils.stats import truncated_normal_1d

from hestia_earth.models.log import (
    debugMissingLookup,
    format_bool,
    format_decimal_percentage,
    format_float,
    format_nd_array,
    format_str,
    log_as_table,
    logRequirements,
    logShouldRun,
)
from hestia_earth.models.utils.ecoClimateZone import EcoClimateZone
from hestia_earth.models.utils.lookup import get_region_lookup_value

from . import MODEL
from .biomass_utils import BiomassCategory

_LOOKUPS = {
    "region-percentageAreaBurnedDuringForestClearance": "percentage_area_burned_during_forest_clearance"
}

ITERATIONS = (
    10000  # N interations for which the model will run as a Monte Carlo simulation
)
TIER = EmissionMethodTier.TIER_1.value
DEFAULT_FACTOR = {"value": 0}
_DEFAULT_PERCENT_BURNED = 0

_STATS_DEFINITION = EmissionStatsDefinition.SIMULATED.value

AMORTISATION_PERIOD = 20  # Emissions should be amortised over 20 years

EXCLUDED_ECO_CLIMATE_ZONES = {EcoClimateZone.POLAR_MOIST, EcoClimateZone.POLAR_DRY}
EXCLUDED_SITE_TYPES = {SiteSiteType.GLASS_OR_HIGH_ACCESSIBLE_COVER.value}
NATURAL_VEGETATION_CATEGORIES = {
    BiomassCategory.FOREST,
    BiomassCategory.NATURAL_FOREST,
    BiomassCategory.PLANTATION_FOREST,
}


class FuelCategory(Enum):
    """
    Natural vegetation fuel categories from IPCC (2019).
    """

    BOREAL_FOREST = "boreal-forest"
    DRAINED_EXTRATROPICAL_ORGANIC_SOILS_WILDFIRE = (
        "drained-extratropical-organic-soils-wildfire"  # boreal/temperate
    )
    DRAINED_TROPICAL_ORGANIC_SOILS_WILDFIRE = "drained-tropical-organic-soils-wildfire"
    EUCALYPT_FOREST = "eucalypt-forest"
    NATURAL_TROPICAL_FOREST = (
        "natural-tropical-forest"  # mean of primary and secondary tropical forest
    )
    PRIMARY_TROPICAL_FOREST = "primary-tropical-forest"
    SAVANNA_GRASSLAND_EARLY_DRY_SEASON_BURNS = (
        "savanna-grassland-early-dry-season-burns"
    )
    SAVANNA_GRASSLAND_MID_TO_LATE_DRY_SEASON_BURNS = (
        "savanna-grassland-mid-to-late-dry-season-burns"
    )
    SAVANNA_WOODLAND_EARLY_DRY_SEASON_BURNS = "savanna-woodland-early-dry-season-burns"
    SAVANNA_WOODLAND_MID_TO_LATE_DRY_SEASON_BURNS = (
        "savanna-woodland-mid-to-late-dry-season-burns"
    )
    SECONDARY_TROPICAL_FOREST = "secondary-tropical-forest"
    SHRUBLAND = "shrubland"
    TEMPERATE_FOREST = "temperate-forest"
    TERTIARY_TROPICAL_FOREST = "tertiary-tropical-forest"
    TROPICAL_ORGANIC_SOILS_PRESCRIBED_FIRE = "tropical-organic-soils-prescribed-fire"
    UNDRAINED_EXTRATROPICAL_ORGANIC_SOILS_WILDFIRE = (
        "undrained-extratropical-organic-soils-wildfire"
    )
    UNKNOWN_TROPICAL_FOREST = "unknown-tropical-forest"  # mean of primary, secondary and tertiary tropical forest


class EmissionCategory(Enum):
    """
    Natural vegetation and organic soil burning emission categories from IPCC (2019).
    """

    AGRICULTURAL_RESIDUES = "agricultural-residues"
    BIOFUEL_BURNING = "biofuel-burning"
    EXTRATROPICAL_ORGANIC_SOILS = "extratropical-organic-soils"
    OTHER_FOREST = "other-forest"
    SAVANNA_AND_GRASSLAND = "savanna-and-grassland"
    TROPICAL_FOREST = "tropical-forest"
    TROPICAL_ORGANIC_SOILS = "tropical-organic-soils"


class InventoryYear(TypedDict, total=False):
    biomass_category_summary: dict[BiomassCategory, float]
    natural_vegetation_delta: dict[BiomassCategory, float]
    fuel_burnt_per_category: dict[FuelCategory, npt.NDArray]
    annual_emissions: dict[str, npt.NDArray]
    amortised_emissions: dict[str, npt.NDArray]
    share_of_emissions: dict[str, float]  # {cycle_id (str): value, ...}
    allocated_emissions: dict[str, dict[str, npt.NDArray]]
    percent_organic_soils: NotRequired[float]


InventoryKey = Literal[
    "biomass_category_summary",
    "natural_vegetation_delta",
    "fuel_burnt_per_category",
    "annual_emissions",
    "amortised_emissions",
    "share_of_emissions",
    "allocated_emissions",
    "percent_organic_soils",
]

Inventory = dict[int, InventoryYear]
"""
{year (int): data (_InventoryYear)}
"""


_FUEL_CATEGORY_TO_EMISSION_CATEGORY = {
    FuelCategory.BOREAL_FOREST: EmissionCategory.OTHER_FOREST,
    FuelCategory.EUCALYPT_FOREST: EmissionCategory.OTHER_FOREST,
    FuelCategory.NATURAL_TROPICAL_FOREST: EmissionCategory.TROPICAL_FOREST,
    FuelCategory.PRIMARY_TROPICAL_FOREST: EmissionCategory.TROPICAL_FOREST,
    FuelCategory.SAVANNA_GRASSLAND_EARLY_DRY_SEASON_BURNS: EmissionCategory.SAVANNA_AND_GRASSLAND,
    FuelCategory.SAVANNA_GRASSLAND_MID_TO_LATE_DRY_SEASON_BURNS: EmissionCategory.SAVANNA_AND_GRASSLAND,
    FuelCategory.SAVANNA_WOODLAND_EARLY_DRY_SEASON_BURNS: EmissionCategory.SAVANNA_AND_GRASSLAND,
    FuelCategory.SAVANNA_WOODLAND_MID_TO_LATE_DRY_SEASON_BURNS: EmissionCategory.SAVANNA_AND_GRASSLAND,
    FuelCategory.SECONDARY_TROPICAL_FOREST: EmissionCategory.TROPICAL_FOREST,
    FuelCategory.SHRUBLAND: EmissionCategory.SAVANNA_AND_GRASSLAND,
    FuelCategory.TEMPERATE_FOREST: EmissionCategory.OTHER_FOREST,
    FuelCategory.TERTIARY_TROPICAL_FOREST: EmissionCategory.TROPICAL_FOREST,
    FuelCategory.UNKNOWN_TROPICAL_FOREST: EmissionCategory.TROPICAL_FOREST,
    FuelCategory.DRAINED_EXTRATROPICAL_ORGANIC_SOILS_WILDFIRE: EmissionCategory.EXTRATROPICAL_ORGANIC_SOILS,
    FuelCategory.DRAINED_TROPICAL_ORGANIC_SOILS_WILDFIRE: EmissionCategory.TROPICAL_ORGANIC_SOILS,
    FuelCategory.TROPICAL_ORGANIC_SOILS_PRESCRIBED_FIRE: EmissionCategory.TROPICAL_ORGANIC_SOILS,
    FuelCategory.UNDRAINED_EXTRATROPICAL_ORGANIC_SOILS_WILDFIRE: EmissionCategory.EXTRATROPICAL_ORGANIC_SOILS,
}
"""
Mapping from natural vegetation and organic soil fuel category to emission category.
"""


def get_emission_category(fuel_category: FuelCategory) -> EmissionCategory:
    """
    Get the IPCC (2019) emission category that corresponds to a fuel category.
    """
    return _FUEL_CATEGORY_TO_EMISSION_CATEGORY.get(fuel_category)


def _sample_truncated_normal(
    *,
    iterations: int,
    value: float,
    sd: float,
    seed: Union[int, np.random.Generator, None] = None,
    **_,
) -> npt.NDArray:
    """
    Randomly sample a model parameter with a truncated normal distribution. Neither fuel factors nor emission factors
    can be below 0, so truncated normal sampling used.
    """
    return truncated_normal_1d(
        shape=(1, iterations), mu=value, sigma=sd, low=0, high=np.inf, seed=seed
    )


def _sample_constant(*, value: float, **_) -> npt.NDArray:
    """Sample a constant model parameter."""
    return np.array(value)


_KWARGS_TO_SAMPLE_FUNC = {
    # ("value", "se", "n"): _sample_standard_error_normal,
    ("value", "sd"): _sample_truncated_normal,
    ("value",): _sample_constant,
}
"""
Mapping from available distribution data to sample function.
"""


def get_sample_func(kwargs: dict) -> Callable:
    """
    Select the correct sample function for a parameter based on the distribution data available. All possible
    parameters for the model should have, at a minimum, a `value`, meaning that no default function needs to be
    specified.

    This function has been extracted into it's own method to allow for mocking of sample function.

    Keyword Args
    ------------
    value : float
        The distribution mean.
    sd : float
        The standard deviation of the distribution.
    se : float
        The standard error of the distribution.
    n : float
        Sample size.

    Returns
    -------
    Callable
        The sample function for the distribution.
    """
    return next(
        sample_func
        for required_kwargs, sample_func in _KWARGS_TO_SAMPLE_FUNC.items()
        if all(kwarg in kwargs.keys() for kwarg in required_kwargs)
    )


def _get_fuel_factor(fuel_category: FuelCategory, emission_term_ids: list[str]) -> dict:
    """
    Retrieve distribution data for a specific fuel category.
    """
    LOOKUP_KEY = "ipcc2019FuelCategory_tonnesDryMatterCombustedPerHaBurned"
    LOOKUP_FILENAME = f"{LOOKUP_KEY}.csv"
    TARGET_DATA = (
        "value",
        # "se",  # useless without n data
        # "n"  # TODO: add n data to lookup
    )

    row = fuel_category.name

    lookup = download_lookup(LOOKUP_FILENAME)

    data = {
        target: get_table_value(
            lookup, column_name("FuelCategory"), row, column_name(target)
        )
        for target in TARGET_DATA
    }

    for term_id, target in product(emission_term_ids, TARGET_DATA):
        debugMissingLookup(
            LOOKUP_FILENAME,
            "FuelCategory",
            row,
            target,
            data.get(target),
            model=MODEL,
            term=term_id,
        )

    return {
        k: parsed
        for k, v in data.items()
        if (parsed := safe_parse_float(v, default=None)) is not None
    } or DEFAULT_FACTOR  # remove missing  # if parsed dict empty, return default


def sample_fuel_factor(
    fuel_category: FuelCategory,
    emission_term_ids: list[str],
    *,
    seed: Union[int, np.random.Generator, None] = None,
) -> npt.NDArray:
    """
    Generate random samples from a fuel factor's distribution data.
    """
    factor_data = _get_fuel_factor(fuel_category, emission_term_ids)
    sample_func = get_sample_func(factor_data)
    return sample_func(iterations=ITERATIONS, seed=seed, **factor_data)


def get_percent_burned(site: str):
    LOOKUP_KEY = "region-percentageAreaBurnedDuringForestClearance"
    LOOKUP_FILENAME = f"{LOOKUP_KEY}.csv"
    country_id = site.get("country", {}).get("@id")

    value = get_region_lookup_value(LOOKUP_FILENAME, country_id, _LOOKUPS[LOOKUP_KEY])
    return safe_parse_float(value, _DEFAULT_PERCENT_BURNED)


def _sum_cycle_emissions(
    term_id: str, cycle_id: str, inventory: Inventory
) -> npt.NDArray:
    """
    Sum the emissions allocated to a cycle.
    """
    KEY = "allocated_emissions"

    def add_cycle_emissions(result: npt.NDArray, year: int) -> npt.NDArray:
        allocated_emissions = inventory.get(year, {}).get(KEY, {}).get(term_id, {})
        return result + allocated_emissions.get(cycle_id, np.array(0))

    return reduce(add_cycle_emissions, inventory.keys(), np.array(0))


def calc_emission(
    fuel_burnt: npt.NDArray, emission_factor: npt.NDArray, conversion_factor: float = 1
) -> npt.NDArray:
    """
    Calculate the emission from a fuel burning.

    Parameters
    ----------
    fuel_burnt : NDArray
        The mass of burnt fuel (kg).
    emission_factor : NDArray
        Emission conversion factor (kg emission per kg of fuel burnt).
    conversion_factor : float, optional
        Optional factor to convert emission factor to other units (e.g., from CO2-C to CO2).

    Returns
    -------
    NDArray
        The mass of emission (kg)
    """
    return fuel_burnt * emission_factor * conversion_factor


def run_emission(term_id: str, cycle_id: str, inventory: Inventory) -> list[dict]:
    """
    Retrieve the sum relevant emissions and format them as a HESTIA
    [Emission node](https://www.hestia.earth/schema/Emission).
    """
    emission = _sum_cycle_emissions(term_id, cycle_id, inventory)
    kwargs = (
        calc_descriptive_stats(emission, _STATS_DEFINITION)
        if emission.size > 1
        else {"value": [emission]}
    )
    return term_id, kwargs


def _format_column_header(*keys: tuple[Union[Enum, str], ...]) -> str:
    """Format a variable number of enums and strings for logging as a table column header."""
    return " ".join(
        format_str(k.value if isinstance(k, Enum) else format_str(k)) for k in keys
    )


def _format_eco_climate_zone(value: EcoClimateZone) -> str:
    """Format an eco-climate zone for logging."""
    return (
        format_str(str(value.name).lower().replace("_", " ").capitalize())
        if isinstance(value, EcoClimateZone)
        else "None"
    )


_LOGS_FORMAT_DATA: dict[str, Callable] = {
    "has_valid_site_type": format_bool,
    "eco_climate_zone": _format_eco_climate_zone,
    "has_valid_eco_climate_zone": format_bool,
    "has_land_cover_nodes": format_bool,
    "should_compile_inventory": format_bool,
    "percent_burned": lambda x: format_float(x, "pct"),
}
_DEFAULT_FORMAT_FUNC = format_str


def _format_logs(logs: dict) -> dict[str, str]:
    """
    Format model logs - excluding the inventory data, which must be formatted separately.
    """
    return {
        key: _LOGS_FORMAT_DATA.get(key, _DEFAULT_FORMAT_FUNC)(value)
        for key, value in logs.items()
    }


_INVENTORY_FORMAT_DATA: dict[
    InventoryKey, dict[Literal["filter_by", "format_func"], Any]
] = {
    "fuel_burnt_per_category": {"format_func": lambda x: format_nd_array(x, "kg")},
    "annual_emissions": {
        "filter_by": ("term_id",),
        "format_func": lambda x: format_nd_array(x, "kg"),
    },
    "amortised_emissions": {
        "filter_by": ("term_id",),
        "format_func": lambda x: format_nd_array(x, "kg"),
    },
    "share_of_emissions": {
        "filter_by": ("cycle_id",),
        "format_func": format_decimal_percentage,
    },
    "allocated_emissions": {
        "filter_by": ("term_id", "cycle_id"),
        "format_func": lambda x: format_nd_array(x, "kg"),
    },
    "percent_organic_soils": {"format_func": lambda x: format_float(x, "pct")},
}
"""
Mapping between inventory key and formatting options for logging in a table. Inventory keys not included in the dict
will not be logged in the table.
"""


def _flatten_dict(nested_dict: dict) -> dict[tuple, Any]:
    """
    Flatten a nested dict, returns dict with keys as tuples with format `(key_level_1, key_level_2, ..., key_level_n)`.
    """

    def flatten(current: dict, path: tuple = ()):

        if isinstance(current, dict):
            for key, value in current.items():
                yield from flatten(value, path + (key,))
        else:
            yield (path, current)

    return dict(flatten(nested_dict))


def _get_relevant_inner_keys(
    term_id: str,
    cycle_id: str,
    key: str,
    inventory: Inventory,
    *,
    filter_by: Optional[tuple[Literal["term_id", "cycle_id"], ...]] = None,
    **_,
) -> list[tuple]:
    """
    Get the column headings for the formatted table. Nested inventory values should be flattened, with nested keys
    being transformed into a tuple with the format `(key_level_1, key_level_2, ..., key_level_n)`.

    Inner keys not relevant to the emission term being logged or the cycle the model is running on should be excluded.
    """
    FILTER_VALUES = {"term_id": term_id, "cycle_id": cycle_id}
    filter_target = (
        tuple(val for f in filter_by if (val := FILTER_VALUES.get(f)))
        if filter_by
        else None
    )

    inner_keys = {
        tuple(k)
        for inner in inventory.values()
        for k in _flatten_dict(inner.get(key, {}))
        if not filter_target or k == filter_target
    }

    return sorted(
        inner_keys,
        key=lambda category: (
            category.value if isinstance(category, Enum) else str(category)
        ),
    )


def _format_inventory(term_id: str, cycle_id: str, inventory: dict) -> str:
    """
    Format the inventory for logging as a table.

    Extract relevant data, flatten nested dicts and format inventory values based on expected data type.
    """
    relevant_inventory_keys = {
        inventory_key: _get_relevant_inner_keys(
            term_id, cycle_id, inventory_key, inventory, **kwargs
        )
        for inventory_key, kwargs in _INVENTORY_FORMAT_DATA.items()
    }

    return (
        log_as_table(
            {
                "year": year,
                **{
                    _format_column_header(
                        inventory_key, *inner_key
                    ): _INVENTORY_FORMAT_DATA[inventory_key]["format_func"](
                        reduce(
                            lambda d, k: d.get(k, {}),
                            [year, inventory_key, *inner_key],
                            inventory,
                        )
                    )
                    for inventory_key, relevant_inner_keys in relevant_inventory_keys.items()
                    for inner_key in relevant_inner_keys
                },
            }
            for year in inventory
        )
        if inventory
        else "None"
    )


def log_emission_data(
    should_run: bool, term_id: str, cycle: dict, inventory: dict, logs: dict
):
    """
    Format and log the model logs and inventory.
    """
    formatted_logs = _format_logs(logs)
    formatted_inventory = _format_inventory(term_id, cycle.get("@id"), inventory)

    logRequirements(
        cycle,
        model=MODEL,
        term=term_id,
        **formatted_logs,
        inventory=formatted_inventory,
    )
    logShouldRun(cycle, MODEL, term_id, should_run, methodTier=TIER)
