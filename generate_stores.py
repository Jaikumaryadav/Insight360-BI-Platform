"""
generate_stores.py
===================
Generates dim_store.csv — the store/channel dimension for Insight360.

Implements the Phase 3A approved schema (Section 2.2) exactly:
    store_key, store_name, store_format, region, city, state, sqft,
    open_date, store_status, is_mature_store, assortment_sku_count, channel

Grain: 1 row per store/channel, 216 rows total:
    - 214 physical stores (50 Flagship + 120 Express + 44 Outlet)
    - 2 virtual channel pseudo-stores (Online, Wholesale)

All sizing parameters (sqft bands, assortment baselines, format counts)
are sourced from config.py, which encodes the Phase 3A approved design.
No redesign occurs here. City/state/region pools and store-naming logic
are local to this module since Phase 3A did not specify literal city
names, only the requirement that cities be realistic and correctly
matched to their state.
"""

from __future__ import annotations

import sys
from datetime import date, timedelta
from typing import Final

import numpy as np
import pandas as pd
from faker import Faker

import config

logger = config.get_logger(__name__)

# ---------------------------------------------------------------------------
# Local reference data (not part of config.py's Phase 3A business-rule
# constants — this is purely realistic label data for store naming/location).
# ---------------------------------------------------------------------------

# City -> (state, region) mapping. Every city is tied to exactly one real
# Indian state and one Meridian reporting region, satisfying the "every
# city must match the correct state" requirement.
CITY_REFERENCE: Final[dict[str, dict[str, str]]] = {
    "Delhi": {"state": "Delhi", "region": "North"},
    "Lucknow": {"state": "Uttar Pradesh", "region": "North"},
    "Jaipur": {"state": "Rajasthan", "region": "North"},
    "Chandigarh": {"state": "Chandigarh", "region": "North"},
    "Bengaluru": {"state": "Karnataka", "region": "South"},
    "Hyderabad": {"state": "Telangana", "region": "South"},
    "Chennai": {"state": "Tamil Nadu", "region": "South"},
    "Kochi": {"state": "Kerala", "region": "South"},
    "Kolkata": {"state": "West Bengal", "region": "East"},
    "Bhubaneswar": {"state": "Odisha", "region": "East"},
    "Patna": {"state": "Bihar", "region": "East"},
    "Ranchi": {"state": "Jharkhand", "region": "East"},
    "Guwahati": {"state": "Assam", "region": "East"},
    "Mumbai": {"state": "Maharashtra", "region": "West"},
    "Ahmedabad": {"state": "Gujarat", "region": "West"},
    "Pune": {"state": "Maharashtra", "region": "West"},
    "Indore": {"state": "Madhya Pradesh", "region": "West"},
    "Nagpur": {"state": "Maharashtra", "region": "West"},
}

# Regional distribution weights for physical store allocation. Kept close
# to even, with East allocated a modest number fewer than the other three —
# a plausible real-world contributor to (not the sole cause of) the
# East-region underperformance calibrated in Phase 3A Section 5.5, which
# is otherwise driven by discount rate and division mix, not store count.
REGION_STORE_WEIGHTS: Final[dict[str, float]] = {
    "North": 0.25,
    "South": 0.27,
    "West": 0.26,
    "East": 0.22,
}

# Nominal HQ region for the two virtual channels, per Phase 3A Section 2.2
# ("Online/Wholesale assigned a nominal HQ region for filter consistency").
VIRTUAL_STORE_NOMINAL_REGION: Final[str] = "West"

# Assortment jitter applied around config.py's fixed per-format baseline,
# to give store-level realism (not every Flagship stocks an identical SKU
# count) while keeping the *average* consistent with the Phase 3A Section 6
# combinatorics that justified fact_inventory_snapshot's approved row count.
ASSORTMENT_JITTER_FRACTION: Final[float] = 0.10

# Store status: 95-98% Active, 2-5% Closed (this message's spec, and
# consistent with Phase 3A Section 2.2's store_status field intent).
CLOSED_STORE_RATE_RANGE: Final[tuple[float, float]] = (0.02, 0.05)

# Open date generation window for physical and virtual stores.
STORE_OPEN_DATE_RANGE: Final[tuple[date, date]] = (date(2015, 1, 1), date(2025, 12, 31))

# Reference date used to evaluate is_mature_store (Phase 3A: opened >365
# days before the latest reporting date).
LATEST_REPORTING_DATE: Final[date] = config.DATA_END_DATE

_faker = Faker("en_IN")


def _allocate_counts(total: int, weights: dict[str, float]) -> dict[str, int]:
    """
    Allocate an integer total across categories proportionally to `weights`,
    using the largest-remainder method so the allocated counts sum exactly
    to `total` even though raw proportional shares are fractional.

    Args:
        total: The total count to allocate (e.g., 214 physical stores).
        weights: A mapping of category -> relative weight. Need not sum to 1.

    Returns:
        dict[str, int]: Category -> allocated integer count, summing to total.

    Raises:
        ValueError: If total is negative or weights is empty.
    """
    if total < 0:
        raise ValueError(f"total must be non-negative, got {total}")
    if not weights:
        raise ValueError("weights must not be empty")

    weight_sum = sum(weights.values())
    raw_shares = {key: (weight / weight_sum) * total for key, weight in weights.items()}
    floored = {key: int(np.floor(share)) for key, share in raw_shares.items()}
    remainder = total - sum(floored.values())

    # Distribute the remaining units to the categories with the largest
    # fractional remainders, for the most proportionally-accurate rounding.
    remainders = sorted(
        raw_shares.keys(), key=lambda k: raw_shares[k] - floored[k], reverse=True
    )
    for key in remainders[:remainder]:
        floored[key] += 1

    return floored


def _build_city_cycle_by_region() -> dict[str, list[str]]:
    """
    Group CITY_REFERENCE into a region -> ordered city list lookup, used to
    cycle through a region's cities when assigning stores to locations.

    Returns:
        dict[str, list[str]]: Region name -> list of city names in that region.

    Raises:
        ValueError: If any configured region in config.REGIONS has no cities
            defined in CITY_REFERENCE (would indicate incomplete reference data).
    """
    cities_by_region: dict[str, list[str]] = {region: [] for region in config.REGIONS}
    for city, info in CITY_REFERENCE.items():
        cities_by_region[info["region"]].append(city)

    for region in config.REGIONS:
        if not cities_by_region[region]:
            raise ValueError(f"No cities defined for region '{region}' in CITY_REFERENCE")

    return cities_by_region


def _generate_physical_store_formats(rng: np.random.Generator) -> list[str]:
    """
    Build a shuffled list of 214 format labels matching config.STORE_FORMAT_COUNTS
    exactly (50 Flagship, 120 Express, 44 Outlet), so that format assignment
    is randomized across store_key order rather than grouped sequentially.

    Args:
        rng: A seeded numpy random Generator for reproducible shuffling.

    Returns:
        list[str]: 214 format labels, shuffled.

    Raises:
        ValueError: If config.STORE_FORMAT_COUNTS does not sum to 214.
    """
    total_physical = sum(config.STORE_FORMAT_COUNTS.values())
    if total_physical != 214:
        raise ValueError(
            f"config.STORE_FORMAT_COUNTS sums to {total_physical}, expected 214"
        )

    formats: list[str] = []
    for store_format, count in config.STORE_FORMAT_COUNTS.items():
        formats.extend([store_format] * count)

    rng.shuffle(formats)
    return formats


def _generate_physical_store_regions(rng: np.random.Generator) -> list[str]:
    """
    Build a shuffled list of 214 region labels proportional to
    REGION_STORE_WEIGHTS, using the largest-remainder allocation method.

    Args:
        rng: A seeded numpy random Generator for reproducible shuffling.

    Returns:
        list[str]: 214 region labels, shuffled.
    """
    counts = _allocate_counts(214, REGION_STORE_WEIGHTS)
    regions: list[str] = []
    for region, count in counts.items():
        regions.extend([region] * count)

    rng.shuffle(regions)
    logger.info("Physical store region allocation: %s", counts)
    return regions


def _generate_store_name(store_format: str, city: str, occurrence_index: int) -> str:
    """
    Build a professional store display name, disambiguated with a numeric
    suffix when a format/city combination repeats (to guarantee uniqueness).

    Args:
        store_format: One of the physical store formats (Flagship/Express/Outlet).
        city: The assigned city name.
        occurrence_index: 1-based count of this format/city combination seen
            so far; 1 produces no suffix, 2+ appends " 2", " 3", etc.

    Returns:
        str: e.g. "Meridian Flagship – Bengaluru" or "Meridian Express – Pune 2".
    """
    base_name = f"Meridian {store_format} \u2013 {city}"
    if occurrence_index == 1:
        return base_name
    return f"{base_name} {occurrence_index}"


def _jittered_assortment(base_value: int, rng: np.random.Generator) -> int:
    """
    Apply +/-ASSORTMENT_JITTER_FRACTION jitter to a base assortment size,
    for store-level realism while keeping the average anchored to the
    Phase 3A-approved per-format baseline.

    Args:
        base_value: The config.py fixed baseline for this store format.
        rng: A seeded numpy random Generator.

    Returns:
        int: Jittered assortment SKU count, always >= 1.
    """
    low = base_value * (1 - ASSORTMENT_JITTER_FRACTION)
    high = base_value * (1 + ASSORTMENT_JITTER_FRACTION)
    return max(1, int(round(rng.uniform(low, high))))


def _generate_open_date(rng: np.random.Generator) -> date:
    """
    Generate a realistic store opening date within STORE_OPEN_DATE_RANGE
    using Faker's date_between for natural distribution.

    Args:
        rng: A seeded numpy random Generator, used to seed Faker's draw
            deterministically for this call via an integer offset.

    Returns:
        date: A randomly chosen date between 2015-01-01 and 2025-12-31.
    """
    start, end = STORE_OPEN_DATE_RANGE
    span_days = (end - start).days
    offset = int(rng.integers(0, span_days + 1))
    return start + timedelta(days=offset)


def _generate_physical_stores(rng: np.random.Generator) -> list[dict]:
    """
    Generate all 214 physical store records (Flagship/Express/Outlet).

    Args:
        rng: A seeded numpy random Generator for reproducible generation.

    Returns:
        list[dict]: 214 physical store records, columns matching the
        Phase 3A dim_store schema (store_key assigned later by the caller).
    """
    formats = _generate_physical_store_formats(rng)
    regions = _generate_physical_store_regions(rng)
    cities_by_region = _build_city_cycle_by_region()

    # Track how many times each (format, city) pair has been used, to
    # disambiguate store names deterministically.
    name_occurrence_counter: dict[tuple[str, str], int] = {}
    # Track a rotating index per region so cities are cycled through evenly
    # rather than randomly re-picked (avoids over-concentrating one city).
    city_rotation_index: dict[str, int] = {region: 0 for region in config.REGIONS}

    records: list[dict] = []
    closed_rate = rng.uniform(*CLOSED_STORE_RATE_RANGE)
    closed_flags = rng.random(len(formats)) < closed_rate
    logger.info("Target closed-store rate for this run: %.2f%%", closed_rate * 100)

    for store_format, region in zip(formats, regions):
        region_cities = cities_by_region[region]
        city = region_cities[city_rotation_index[region] % len(region_cities)]
        city_rotation_index[region] += 1

        name_key = (store_format, city)
        name_occurrence_counter[name_key] = name_occurrence_counter.get(name_key, 0) + 1
        store_name = _generate_store_name(store_format, city, name_occurrence_counter[name_key])

        sqft_low, sqft_high = config.SQFT_RANGE_BY_FORMAT[store_format]
        sqft = int(rng.integers(sqft_low, sqft_high + 1))

        open_date_value = _generate_open_date(rng)
        is_mature = (LATEST_REPORTING_DATE - open_date_value).days > 365

        assortment_base = config.ASSORTMENT_SIZE_BY_FORMAT[store_format]
        assortment_sku_count = _jittered_assortment(assortment_base, rng)

        records.append({
            "store_name": store_name,
            "store_format": store_format,
            "region": region,
            "city": city,
            "state": CITY_REFERENCE[city]["state"],
            "sqft": sqft,
            "open_date": open_date_value.isoformat(),
            "store_status": None,  # assigned below via closed_flags
            "is_mature_store": is_mature,
            "assortment_sku_count": assortment_sku_count,
            "channel": "Store",
        })

    for record, is_closed in zip(records, closed_flags):
        record["store_status"] = "Closed" if is_closed else "Active"

    logger.info("Generated %d physical store records", len(records))
    return records


def _generate_virtual_stores() -> list[dict]:
    """
    Generate the 2 virtual channel pseudo-stores: Online and Wholesale.

    Returns:
        list[dict]: 2 virtual store records (store_key assigned later by caller).
    """
    virtual_open_date = STORE_OPEN_DATE_RANGE[0]  # both channels present since launch
    is_mature = (LATEST_REPORTING_DATE - virtual_open_date).days > 365

    records = [
        {
            "store_name": "Meridian Online",
            "store_format": "Online",
            "region": VIRTUAL_STORE_NOMINAL_REGION,
            "city": "N/A \u2014 Digital",
            "state": "N/A \u2014 Digital",
            "sqft": None,
            "open_date": virtual_open_date.isoformat(),
            "store_status": "Active",
            "is_mature_store": is_mature,
            "assortment_sku_count": config.ASSORTMENT_SIZE_BY_FORMAT["Online"],
            "channel": "Online",
        },
        {
            "store_name": "Meridian Wholesale",
            "store_format": "Wholesale",
            "region": VIRTUAL_STORE_NOMINAL_REGION,
            "city": "N/A \u2014 Digital",
            "state": "N/A \u2014 Digital",
            "sqft": None,
            "open_date": virtual_open_date.isoformat(),
            "store_status": "Active",
            "is_mature_store": is_mature,
            "assortment_sku_count": config.ASSORTMENT_SIZE_BY_FORMAT["Wholesale"],
            "channel": "Wholesale",
        },
    ]

    logger.info("Generated %d virtual store records (Online, Wholesale)", len(records))
    return records


def generate_dim_store() -> pd.DataFrame:
    """
    Generate the complete dim_store table: 214 physical stores + 2 virtual
    channel pseudo-stores, with sequential store_key assignment.

    Returns:
        pd.DataFrame: 216 rows with columns in the exact Phase 3A order:
        store_key, store_name, store_format, region, city, state, sqft,
        open_date, store_status, is_mature_store, assortment_sku_count, channel.

    Raises:
        ValueError: If the resulting row count does not match the approved
            count of 216 (config.ROW_COUNTS["dim_store"]).
    """
    logger.info("Generating dim_store")
    rng = np.random.default_rng(config.RANDOM_SEED)
    Faker.seed(config.RANDOM_SEED)

    physical_records = _generate_physical_stores(rng)
    virtual_records = _generate_virtual_stores()

    all_records = physical_records + virtual_records
    for store_key, record in enumerate(all_records, start=1):
        record["store_key"] = store_key

    column_order = [
        "store_key", "store_name", "store_format", "region", "city", "state",
        "sqft", "open_date", "store_status", "is_mature_store",
        "assortment_sku_count", "channel",
    ]
    dim_store = pd.DataFrame.from_records(all_records)[column_order]

    expected_rows = config.ROW_COUNTS["dim_store"]
    if len(dim_store) != expected_rows:
        raise ValueError(
            f"dim_store generated {len(dim_store)} rows, expected exactly "
            f"{expected_rows} per the Phase 3A approved design."
        )

    logger.info("dim_store generation complete: %d rows", len(dim_store))
    return dim_store


def validate_dim_store(dim_store: pd.DataFrame) -> None:
    """
    Run structural validation on the generated dim_store table before export.

    Args:
        dim_store: The DataFrame produced by generate_dim_store().

    Returns:
        None. Raises on the first failed check.

    Raises:
        ValueError: If any validation rule fails.
    """
    expected_rows = config.ROW_COUNTS["dim_store"]
    if len(dim_store) != expected_rows:
        raise ValueError(f"Row count mismatch: expected {expected_rows}, got {len(dim_store)}")

    if dim_store["store_key"].duplicated().any():
        raise ValueError("dim_store.store_key contains duplicate values; PK uniqueness violated")

    if dim_store["store_name"].duplicated().any():
        duplicates = dim_store.loc[dim_store["store_name"].duplicated(), "store_name"].tolist()
        raise ValueError(f"dim_store.store_name contains duplicates: {duplicates}")

    invalid_regions = set(dim_store["region"].unique()) - set(config.REGIONS)
    if invalid_regions:
        raise ValueError(f"dim_store.region contains invalid values: {invalid_regions}")

    invalid_formats = set(dim_store["store_format"].unique()) - set(config.STORE_FORMATS)
    if invalid_formats:
        raise ValueError(f"dim_store.store_format contains invalid values: {invalid_formats}")

    expected_channel_map = {
        "Flagship": "Store", "Express": "Store", "Outlet": "Store",
        "Online": "Online", "Wholesale": "Wholesale",
    }
    channel_mismatches = dim_store[
        dim_store.apply(lambda row: expected_channel_map[row["store_format"]] != row["channel"], axis=1)
    ]
    if not channel_mismatches.empty:
        raise ValueError(
            f"dim_store.channel does not match expected format->channel mapping for "
            f"{len(channel_mismatches)} row(s)"
        )

    city_state_mismatches = dim_store[
        (dim_store["city"] != "N/A \u2014 Digital")
        & (dim_store.apply(lambda row: CITY_REFERENCE.get(row["city"], {}).get("state") != row["state"], axis=1))
    ]
    if not city_state_mismatches.empty:
        raise ValueError(
            f"dim_store has {len(city_state_mismatches)} row(s) with a city/state mismatch"
        )

    physical_mask = dim_store["store_format"].isin(config.PHYSICAL_STORE_FORMATS)
    for store_format, (low, high) in config.SQFT_RANGE_BY_FORMAT.items():
        format_rows = dim_store[dim_store["store_format"] == store_format]
        out_of_range = format_rows[(format_rows["sqft"] < low) | (format_rows["sqft"] > high)]
        if not out_of_range.empty:
            raise ValueError(
                f"dim_store has {len(out_of_range)} '{store_format}' row(s) with sqft "
                f"outside the approved range [{low}, {high}]"
            )

    virtual_mask = ~physical_mask
    if not dim_store.loc[virtual_mask, "sqft"].isna().all():
        raise ValueError("dim_store: virtual stores (Online/Wholesale) must have NULL sqft")

    if dim_store.loc[physical_mask, "sqft"].isna().any():
        raise ValueError("dim_store: physical stores must not have NULL sqft")

    mandatory_fields = [
        "store_key", "store_name", "store_format", "region", "city", "state",
        "open_date", "store_status", "is_mature_store", "assortment_sku_count", "channel",
    ]
    for field in mandatory_fields:
        if dim_store[field].isnull().any():
            raise ValueError(f"dim_store.{field} contains nulls but is a mandatory field")

    valid_statuses = {"Active", "Closed"}
    invalid_statuses = set(dim_store["store_status"].unique()) - valid_statuses
    if invalid_statuses:
        raise ValueError(f"dim_store.store_status contains invalid values: {invalid_statuses}")

    logger.info("dim_store validation passed: %d rows, all checks green", len(dim_store))


def export_dim_store(dim_store: pd.DataFrame) -> None:
    """
    Write the dim_store DataFrame to data/raw/dim_store.csv.

    Args:
        dim_store: The validated DataFrame to export.

    Returns:
        None.

    Raises:
        OSError: If the file cannot be written.
    """
    output_path = config.get_output_path("dim_store")
    try:
        dim_store.to_csv(output_path, index=False)
        logger.info("dim_store exported to %s (%d rows)", output_path, len(dim_store))
    except OSError:
        logger.exception("Failed to write dim_store to %s", output_path)
        raise


def main() -> None:
    """
    Entry point for standalone execution: generate, validate, and export
    dim_store.csv. Exits with a non-zero status code on failure.
    """
    logger.info("=== Starting dim_store generation (Phase 3B) ===")
    try:
        dim_store = generate_dim_store()
        validate_dim_store(dim_store)
        export_dim_store(dim_store)

        status_counts = dim_store["store_status"].value_counts().to_dict()
        format_counts = dim_store["store_format"].value_counts().to_dict()
        region_counts = dim_store["region"].value_counts().to_dict()
        logger.info(
            "Summary: %d total rows | status=%s | formats=%s | regions=%s",
            len(dim_store), status_counts, format_counts, region_counts,
        )
        logger.info("=== dim_store generation finished successfully ===")
    except Exception:
        logger.exception("dim_store generation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
