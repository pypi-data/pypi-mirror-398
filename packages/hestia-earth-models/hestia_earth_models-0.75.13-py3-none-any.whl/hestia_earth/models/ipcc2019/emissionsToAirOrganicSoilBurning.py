from functools import lru_cache, reduce
import numpy as np
import numpy.typing as npt
from typing import Callable, Union

from hestia_earth.utils.stats import gen_seed
from hestia_earth.utils.tools import safe_parse_float

from hestia_earth.models.utils import split_on_condition
from hestia_earth.models.utils.blank_node import (
    filter_list_term_id,
    get_node_value,
    split_nodes_by_dates,
)
from hestia_earth.models.utils.constant import Units, get_atomic_conversion
from hestia_earth.models.utils.ecoClimateZone import (
    EcoClimateZone,
    get_eco_climate_zone_value,
)
from hestia_earth.models.utils.emission import _new_emission
from hestia_earth.models.utils.select_nodes import (
    closest_last_date,
    closest_depthUpper_depthLower,
    pick_shallowest,
    select_nodes_by,
)
from hestia_earth.models.utils.site import related_cycles
from hestia_earth.models.utils.term import get_lookup_value

from . import MODEL
from .biomass_utils import get_valid_management_nodes, summarise_land_cover_nodes
from .burning_utils import (
    calc_emission,
    DEFAULT_FACTOR,
    EmissionCategory,
    EXCLUDED_ECO_CLIMATE_ZONES,
    EXCLUDED_SITE_TYPES,
    FuelCategory,
    ITERATIONS,
    get_emission_category,
    get_percent_burned,
    get_sample_func,
    Inventory,
    InventoryYear,
    NATURAL_VEGETATION_CATEGORIES,
    run_emission,
    sample_fuel_factor,
    AMORTISATION_PERIOD,
    log_emission_data,
    TIER,
)
from .utils import group_nodes_by_year

REQUIREMENTS = {
    "Cycle": {
        "site": {
            "@type": "Site",
            "management": [
                {
                    "@type": "Management",
                    "value": "",
                    "term.termType": "landCover",
                    "endDate": "",
                    "optional": {"startDate": ""},
                }
            ],
            "measurements": [
                {
                    "@type": "Measurement",
                    "value": "",
                    "term.@id": "ecoClimateZone",
                    "none": {"value": ["5, 6"]},
                },
                {"@type": "Measurement", "value": "", "term.@id": "organicSoils"},
            ],
            "none": {"siteType": ["glass or high accessible cover"]},
        }
    }
}
LOOKUPS = {
    "emission": [
        "IPCC_2013_G_EMITTED_PER_KG_DRY_MATTER_COMBUSTED_EXTRATROPICAL_ORGANIC_SOILS_value",
        "IPCC_2013_G_EMITTED_PER_KG_DRY_MATTER_COMBUSTED_TROPICAL_ORGANIC_SOILS_value",
    ],
    "ipcc2019FuelCategory_tonnesDryMatterCombustedPerHaBurned": "value",
    "landCover": "BIOMASS_CATEGORY",
    "region-percentageAreaBurnedDuringForestClearance": "percentage_area_burned_during_forest_clearance",
}
RETURNS = {
    "Emission": [
        {
            "value": "",
            "sd": "",
            "min": "",
            "max": "",
            "statsDefinition": "simulated",
            "observations": "",
            "dates": "",
            "methodClassification": "tier 1 model",
            "depth": 30,
        }
    ]
}
TERM_ID = "ch4ToAirOrganicSoilBurning,co2ToAirOrganicSoilBurning,coToAirOrganicSoilBurning,n2OToAirOrganicSoilBurningDirect,nh3ToAirOrganicSoilBurning,noxToAirOrganicSoilBurning"  # noqa: E501

_EMISSION_TERM_IDS = TERM_ID.split(",")

_ORGANIC_SOILS_TERM_ID = "organicSoils"
_DEFAULT_ORGANIC_SOILS = 0
_DEPTH_UPPER = 0
_DEPTH_LOWER = 30  # TODO: add depth

_CONVERSION_FACTORS = {
    "co2ToAirOrganicSoilBurning": get_atomic_conversion(Units.KG_CO2, Units.TO_C)
}

_ECO_CLIMATE_ZONE_TO_FUEL_CATEGORY = {
    EcoClimateZone.WARM_TEMPERATE_MOIST: FuelCategory.DRAINED_EXTRATROPICAL_ORGANIC_SOILS_WILDFIRE,
    EcoClimateZone.WARM_TEMPERATE_DRY: FuelCategory.DRAINED_EXTRATROPICAL_ORGANIC_SOILS_WILDFIRE,
    EcoClimateZone.COOL_TEMPERATE_MOIST: FuelCategory.DRAINED_EXTRATROPICAL_ORGANIC_SOILS_WILDFIRE,
    EcoClimateZone.COOL_TEMPERATE_DRY: FuelCategory.DRAINED_EXTRATROPICAL_ORGANIC_SOILS_WILDFIRE,
    EcoClimateZone.BOREAL_MOIST: FuelCategory.DRAINED_EXTRATROPICAL_ORGANIC_SOILS_WILDFIRE,
    EcoClimateZone.BOREAL_DRY: FuelCategory.DRAINED_EXTRATROPICAL_ORGANIC_SOILS_WILDFIRE,
    EcoClimateZone.TROPICAL_MONTANE: FuelCategory.DRAINED_TROPICAL_ORGANIC_SOILS_WILDFIRE,
    EcoClimateZone.TROPICAL_WET: FuelCategory.DRAINED_TROPICAL_ORGANIC_SOILS_WILDFIRE,
    EcoClimateZone.TROPICAL_MOIST: FuelCategory.DRAINED_TROPICAL_ORGANIC_SOILS_WILDFIRE,
    EcoClimateZone.TROPICAL_DRY: FuelCategory.DRAINED_TROPICAL_ORGANIC_SOILS_WILDFIRE,
}


def _emission(term_id: str, kwargs) -> dict:
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
        "depth": _DEPTH_LOWER,
        **{k: kwargs.get(k) for k in other_keys},
    }


def _get_emission_factor(term_id: str, emission_category: EmissionCategory) -> dict:
    """
    Retrieve distribution data for a specific emission and emission category.
    """
    TERM_TYPE = "emission"
    TARGET_DATA = "value"  # No uncertainty data available yet

    COLUMN_ROOT = "IPCC_2013_G_EMITTED_PER_KG_DRY_MATTER_COMBUSTED"

    data = {
        TARGET_DATA: get_lookup_value(
            {"@id": term_id, "termType": TERM_TYPE},
            "_".join([COLUMN_ROOT, emission_category.name, TARGET_DATA]),
            model=MODEL,
            term=term_id,
        )
    }

    return {
        k: parsed
        for k, v in data.items()
        if (parsed := safe_parse_float(v, default=None)) is not None
    } or DEFAULT_FACTOR  # remove missing  # if parsed dict empty, return default


def _sample_emission_factor(
    term_id: str,
    emission_category: EmissionCategory,
    *,
    seed: Union[int, np.random.Generator, None] = None,
) -> npt.NDArray:
    """
    Generate random samples from an emission factor's distribution data.
    """
    factor_data = _get_emission_factor(term_id, emission_category)
    sample_func = get_sample_func(factor_data)
    return sample_func(iterations=ITERATIONS, seed=seed, **factor_data)


def _calc_burnt_fuel(
    area_converted: npt.NDArray,
    fuel_factor: npt.NDArray,
    frac_burnt: npt.NDArray,
    frac_organic_soils: float,
) -> npt.NDArray:
    """
    Calculate the amount of fuel burnt during a fire event.

    Parameters
    ----------
    area_converted : NDArray
        Area of land converted (ha).
    fuel_factor : NDArray
        Conversion factor (kg fuel per ha of land cover converted).
    frac_burnt : NDArray
        The fraction of land converted using burning during a land use change event (decimal percentage, 0-1).
    frac_organic_soils : float
        The fraction of land occupied by organic soils (decimal percentage, 0-1)

    Returns
    -------
    NDArray
        The mass of burnt fuel (kg)
    """
    return area_converted * fuel_factor * frac_burnt * frac_organic_soils


def _build_fuel_burnt_accumulator(
    percent_burned: npt.ArrayLike,
    eco_climate_zone: EcoClimateZone,
    sample_fuel_factor_func: Callable[[FuelCategory], npt.NDArray],
):
    """
    Build an `accumulate_fuel_burnt` function to reduce natural vegetation deltas into mass of fuel burnt per
    `_FuelCategory`.

    Parameters
    ----------
    percent_burned : NDArray
        The percentage of land converted using burning during a land use change event (percentage, 0-100%).
    eco_climate_zone : EcoClimateZone
        The eco-climate zone of the Site.
    sample_fuel_factor_func : Callable[[_FuelCategory], npt.NDArray]
        Function to sample fuel factor parameter.

    Returns
    -------
    NDArray
        The mass of burnt fuel (kg)
    """
    frac_burnt = percent_burned / 100

    def accumulate_fuel_burnt(
        result: dict[FuelCategory, npt.NDArray],
        delta: float,
        percent_organic_soils: float,
    ) -> dict[FuelCategory, npt.NDArray]:
        """
        Calculate the amount of fuel burnt when natural vegetation is lost. Accumulate fuel burnt by `_FuelCategory`.

        Parameters
        ----------
        result : dict[_FuelCategory, npt.NDArray]
            A dict with the format `{_FuelCategory: kg_fuel_burnt (npt.NDArray)}`.
        delta : float
            The change in land cover for the biomass category (% area).
        percent_organic_soils : NDArray
            The percentage of land occupied by organic soils (percentage, 0-100%).

        Returns
        -------
        dict[_FuelCategory, npt.NDArray]
        """
        frac_organic_soils = percent_organic_soils / 100

        fuel_category = _ECO_CLIMATE_ZONE_TO_FUEL_CATEGORY.get(eco_climate_zone)
        fuel_factor = sample_fuel_factor_func(fuel_category)

        area_converted = (
            abs(delta) / 100 if delta < 0 else 0
        )  # We only care about losses

        already_burnt = result.get(fuel_category, np.array(0))

        update_dict = (
            {}
            if area_converted == 0
            else {
                fuel_category: already_burnt
                + _calc_burnt_fuel(
                    area_converted, fuel_factor, frac_burnt, frac_organic_soils
                )
            }
        )

        return result | update_dict

    return accumulate_fuel_burnt


def _compileInventory(
    cycle: dict,
    site: dict,
    land_cover_nodes: list[dict],
    organic_soil_nodes: list[dict],
    eco_climate_zone: EcoClimateZone,
):
    """
    Compile the run data for the model, collating data from `site.management` and related cycles. An annualised
    inventory of land cover change and natural vegetation burning events is constructed. Emissions from burning events
    are estimated, amortised over 20 years and allocated to cycles.

    Parameters
    ----------
    cycle : dict
        The HESTIA [Cycle](https://www.hestia.earth/schema/Cycle) the model is running on.
    site : dict
        The HESTIA [Site](https://www.hestia.earth/schema/Site) the Cycle takes place on.
    land_cover_nodes : list[dict]
        Valid land cover [Management nodes](https://www.hestia.earth/schema/Management) extracted from the Site.
    organic_soil_nodes : list[dict]
        Valid `organicSoils` [Measurement nodes](https://www.hestia.earth/schema/Measurement) extracted from the Site.
    eco_climate_zone : EcoClimateZone
        The eco-climate zone of the Site.

    Returns
    -------
    should_run : bool
        Whether the model should be run.
    inventory : Inventory
        An inventory of model data.
    logs : dict
        Data about the inventory compilation to be logged.
    """
    cycle_id = cycle.get("@id")
    related_cycles_ = related_cycles(site, cycles_mapping={cycle_id: cycle})

    seed = gen_seed(site, MODEL, TERM_ID)
    rng = np.random.default_rng(seed)

    cycles_grouped = group_nodes_by_year(related_cycles_)
    land_cover_grouped = group_nodes_by_year(land_cover_nodes)
    percent_burned = get_percent_burned(site)

    @lru_cache(maxsize=len(FuelCategory))
    def sample_fuel_factor_(*args):
        """Fuel factors should not be re-sampled between years, so cache results."""
        return sample_fuel_factor(*args, _EMISSION_TERM_IDS, seed=rng)

    @lru_cache(maxsize=len(_EMISSION_TERM_IDS) * len(EmissionCategory))
    def sample_emission_factor_(*args):
        """Emission factors should not be re-sampled between years, so cache results."""
        return _sample_emission_factor(*args, seed=rng)

    accumulate_fuel_burnt = _build_fuel_burnt_accumulator(
        percent_burned, eco_climate_zone, sample_fuel_factor_
    )

    def buildInventory_year(inventory: Inventory, year: int) -> dict:
        """
        Parameters
        ----------
        inventory : Inventory
            An inventory of model data.
        year : int
            The year of the inventory to build.

        Returns
        -------
        inventory : dict
            An inventory of model data, updated to include the input year.
        """
        most_relevant_organic_soils_node = select_nodes_by(
            organic_soil_nodes,
            [
                lambda nodes: closest_last_date(nodes, year),
                lambda nodes: pick_shallowest(
                    nodes, default={}
                ),  # resolve down to a single node
            ],
        )

        percent_organic_soils = get_node_value(
            most_relevant_organic_soils_node, default=_DEFAULT_ORGANIC_SOILS
        )

        land_cover_nodes = land_cover_grouped.get(
            next(
                (
                    k for k in sorted(land_cover_grouped) if k >= year
                ),  # backfill if possible
                min(
                    land_cover_grouped, key=lambda k: abs(k - year)
                ),  # else forward-fill
            ),
            [],
        )

        biomass_category_summary = summarise_land_cover_nodes(land_cover_nodes)
        prev_biomass_category_summary = inventory.get(year - 1, {}).get(
            "biomass_category_summary", {}
        )

        natural_vegetation_delta = {
            category: biomass_category_summary.get(category, 0)
            - prev_biomass_category_summary.get(category, 0)
            for category in NATURAL_VEGETATION_CATEGORIES
        }

        fuel_burnt_per_category = reduce(
            lambda result, delta: accumulate_fuel_burnt(
                result, delta, percent_organic_soils
            ),
            natural_vegetation_delta.values(),
            dict(),
        )

        annual_emissions = {
            term_id: sum(
                calc_emission(
                    amount,
                    sample_emission_factor_(
                        term_id, get_emission_category(fuel_category)
                    ),
                    _CONVERSION_FACTORS.get(term_id, 1),
                )
                for fuel_category, amount in fuel_burnt_per_category.items()
            )
            for term_id in _EMISSION_TERM_IDS
        }

        previous_years = list(inventory.keys())
        amortisation_slice_index = max(
            0, len(previous_years) - (AMORTISATION_PERIOD - 1)
        )
        amortisation_years = previous_years[
            amortisation_slice_index:
        ]  # get the previous 19 years, if available

        amortised_emissions = {
            term_id: 0.05
            * (
                annual_emissions[term_id]
                + sum(
                    inventory[year_]["annual_emissions"][term_id]
                    for year_ in amortisation_years
                )
            )
            for term_id in _EMISSION_TERM_IDS
        }

        cycles = cycles_grouped.get(year, [])
        total_cycle_duration = sum(
            c.get("fraction_of_group_duration", 0) for c in cycles
        )

        share_of_emissions = {
            cycle["@id"]: cycle.get("fraction_of_group_duration", 0)
            / total_cycle_duration
            for cycle in cycles
        }

        allocated_emissions = {
            term_id: {
                cycle_id: share_of_emission * amortised_emissions[term_id]
                for cycle_id, share_of_emission in share_of_emissions.items()
            }
            for term_id in _EMISSION_TERM_IDS
        }

        inventory[year] = InventoryYear(
            biomass_category_summary=biomass_category_summary,
            natural_vegetation_delta=natural_vegetation_delta,
            fuel_burnt_per_category=fuel_burnt_per_category,
            annual_emissions=annual_emissions,
            amortised_emissions=amortised_emissions,
            share_of_emissions=share_of_emissions,
            allocated_emissions=allocated_emissions,
            percent_organic_soils=percent_organic_soils,
        )

        return inventory

    all_years = list(cycles_grouped.keys()) + list(land_cover_grouped.keys())
    min_year, max_year = min(all_years), max(all_years)

    inventory = reduce(buildInventory_year, range(min_year, max_year + 1), dict())

    n_land_cover_years = len(land_cover_grouped)

    logs = {
        "n_land_cover_years": n_land_cover_years,
        "percent_burned": percent_burned,
        "seed": seed,
    }

    should_run = bool(inventory and n_land_cover_years > 1)

    return should_run, inventory, logs


def _should_run(cycle: dict):
    """
    Extract, organise and pre-process required data from the input [Cycle node](https://www.hestia.earth/schema/Site)
    and determine whether the model should run.

    Parameters
    ----------
    cycle : dict
        A HESTIA [Cycle](https://www.hestia.earth/schema/Cycle).

    Returns
    -------
    tuple[bool, Inventory]
        should_run, inventory
    """
    site = cycle.get("site", {})

    site_type = site.get("siteType")
    eco_climate_zone = get_eco_climate_zone_value(site, as_enum=True)

    land_cover_nodes = get_valid_management_nodes(site)

    organic_soil_nodes = split_nodes_by_dates(
        select_nodes_by(
            site.get("measurements", []),
            [
                lambda nodes: filter_list_term_id(nodes, _ORGANIC_SOILS_TERM_ID),
                lambda nodes: closest_depthUpper_depthLower(
                    nodes, _DEPTH_UPPER, _DEPTH_LOWER, depth_strict=False
                ),
            ],
        )
    )

    has_valid_site_type = all([site_type, site_type not in EXCLUDED_SITE_TYPES])
    has_valid_eco_climate_zone = all(
        [eco_climate_zone, eco_climate_zone not in EXCLUDED_ECO_CLIMATE_ZONES]
    )
    has_land_cover_nodes = len(land_cover_nodes) > 1
    has_organic_soil_nodes = bool(organic_soil_nodes)

    should_compileInventory = all(
        [
            has_valid_site_type,
            has_valid_eco_climate_zone,
            has_land_cover_nodes,
            has_organic_soil_nodes,
        ]
    )

    should_run, inventory, compilation_logs = (
        _compileInventory(
            cycle, site, land_cover_nodes, organic_soil_nodes, eco_climate_zone
        )
        if should_compileInventory
        else (False, {}, {})
    )

    logs = {
        "site_id": site.get("@id"),
        "site_type": site_type,
        "has_valid_site_type": has_valid_site_type,
        "eco_climate_zone": eco_climate_zone,
        "has_valid_eco_climate_zone": has_valid_eco_climate_zone,
        "has_land_cover_nodes": has_land_cover_nodes,
        "has_organic_soil_nodes": has_organic_soil_nodes,
        "should_compileInventory": should_compileInventory,
        **compilation_logs,
    }

    for term_id in _EMISSION_TERM_IDS:
        log_emission_data(should_run, term_id, cycle, inventory, logs)

    return should_run, inventory


def run(cycle: dict):
    """
    Run the `nonCo2EmissionsToAirOrganicSoilBurning` model on a Cycle.

    Parameters
    ----------
    cycle : dict
        A HESTIA [Cycle](https://www.hestia.earth/schema/Cycle).

    Returns
    -------
    list[dict]
        A list of HESTIA [Emission](https://www.hestia.earth/schema/Emission) nodes with `term.termType` =
        `ch4ToAirOrganicSoilBurning` **OR** `co2ToAirOrganicSoilBurning` **OR** `coToAirOrganicSoilBurning` **OR**
        `n2OToAirOrganicSoilBurningDirect` **OR** `noxToAirOrganicSoilBurning`.
    """
    should_run, inventory = _should_run(cycle)
    return (
        [
            _emission(*run_emission(term_id, cycle.get("@id"), inventory))
            for term_id in _EMISSION_TERM_IDS
        ]
        if should_run
        else []
    )
