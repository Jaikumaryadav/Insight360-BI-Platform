"""
generate_sales.py
==================
Generates fact_sales.csv — the core transaction fact table for Insight360.

Implements the Phase 3A approved schema (Section 2.6) exactly:
    sales_id, date_key, store_key, product_key, customer_key, channel,
    quantity, unit_price, discount_amount, net_sales_amount, cost_amount,
    loyalty_flag, promotion_id, return_flag

Grain: 1 row per transaction line, 4,200,000 rows total.

Encodes the Phase 3A Section 5 business rules: seasonal demand, festive
spikes, weekend uplift by channel, regional revenue variance, customer
segment behavior, the loyalty penetration trajectory (Section 5.4), and
division-based discount strategy (Section 5.6).

PERFORMANCE: the full 4.2M-row table is never held in memory at once.
Generation proceeds date-by-date (730 iterations) x channel (up to 3),
each chunk built with vectorized numpy/pandas operations and appended
directly to the output CSV.
"""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
from faker import Faker

import config

logger = config.get_logger(__name__)

# ---------------------------------------------------------------------------
# Local generation parameters (not numerically specified in Phase 3A / this
# module's spec, so defined locally rather than added to config.py).
# ---------------------------------------------------------------------------

TRANSACTION_CHANNEL_SHARE: Final[dict[str, float]] = {
    "Store": 0.68, "Online": 0.29, "Wholesale": 0.03,
}

# Regional demand index used only within this module for store-selection
# weighting. North > South > West > East, per this message's explicit
# clarification; East retained at the Phase 3A-approved underperformance
# magnitude (config.REGION_REVENUE_INDEX["East"] = 0.88).
REGION_DEMAND_INDEX: Final[dict[str, float]] = {
    "North": 1.08, "South": 1.02, "West": 0.98, "East": config.REGION_REVENUE_INDEX["East"],
}

# Store-format weighting within the Store channel (Flagship stores drive
# disproportionately more transactions than Outlet, reflecting footfall).
STORE_FORMAT_TRAFFIC_WEIGHT: Final[dict[str, float]] = {
    "Flagship": 3.0, "Express": 1.4, "Outlet": 1.0,
}

# Product-tier preference by customer segment, used to weight product
# selection so Premium Shopper transactions skew toward Premium-tier SKUs
# and Value Shopper transactions skew toward Value-tier SKUs.
TIER_PREFERENCE_BY_SEGMENT: Final[dict[str, dict[str, float]]] = {
    "Value Shopper": {"Value": 0.60, "Mid": 0.30, "Premium": 0.10},
    "Premium Shopper": {"Value": 0.10, "Mid": 0.35, "Premium": 0.55},
    "Digital Native": {"Value": 0.30, "Mid": 0.45, "Premium": 0.25},
}

# Retail quantity bias by segment, nested within the approved
# config.RETAIL_QUANTITY_RANGE (1-5).
QUANTITY_RANGE_BY_SEGMENT: Final[dict[str, tuple[int, int]]] = {
    "Value Shopper": (2, 5),
    "Premium Shopper": (1, 2),
    "Digital Native": (1, 3),
}

# East region's extra discount bump (percentage points), per this
# message's explicit rule ("East gets slightly more discounts").
EAST_DISCOUNT_BUMP_RANGE: Final[tuple[float, float]] = (0.02, 0.04)

# Discount-sensitivity adjustment by segment (percentage points), applied
# on top of the division baseline: Value Shopper skews higher, Premium
# Shopper skews lower, per Phase 3A Section 5.4.
DISCOUNT_SEGMENT_ADJUSTMENT_PP: Final[dict[str, float]] = {
    "Value Shopper": 0.02, "Premium Shopper": -0.03, "Digital Native": 0.0,
}

# Wholesale uses volume-tiered discount breakpoints instead of the
# promotional/division discount logic, per Phase 3A Section 5.6.
WHOLESALE_DISCOUNT_TIERS: Final[list[tuple[int, float]]] = [
    (150, 0.10), (50, 0.06), (0, 0.03),
]

MAX_DISCOUNT_RATE: Final[float] = 0.45  # safety ceiling after stacking adjustments
PROMOTION_ATTACH_RATE: Final[float] = 0.10  # minority of eligible transactions

_faker = Faker("en_IN")


# ---------------------------------------------------------------------------
# Dimension loading and sampling-pool construction
# ---------------------------------------------------------------------------

def load_dimension_tables() -> dict[str, pd.DataFrame]:
    """
    Load the five previously generated dimension CSVs from data/raw/.

    Returns:
        dict[str, pd.DataFrame]: Keys "dim_date", "dim_store", "dim_product",
        "dim_customer", "dim_campaign".

    Raises:
        FileNotFoundError: If any required dimension CSV is missing (i.e.,
            an earlier module has not been run yet).
    """
    tables: dict[str, pd.DataFrame] = {}
    for name in ("dim_date", "dim_store", "dim_product", "dim_customer", "dim_campaign"):
        path = config.get_output_path(name)
        if not path.exists():
            raise FileNotFoundError(
                f"Required dimension file not found: {path}. "
                f"Run the corresponding generate_*.py module first."
            )
        tables[name] = pd.read_csv(path)
        logger.info("Loaded %s: %d rows", name, len(tables[name]))
    return tables


def build_store_pools(dim_store: pd.DataFrame) -> dict:
    """
    Build store-sampling pools: a weighted array for physical Store-channel
    stores, plus the single Online and Wholesale pseudo-store keys.

    Args:
        dim_store: The loaded dim_store DataFrame.

    Returns:
        dict: {
            "store_keys": np.ndarray of physical Active store_keys,
            "store_weights": np.ndarray of matching sampling probabilities,
            "store_region_map": dict[int, str] store_key -> region,
            "store_format_map": dict[int, str] store_key -> store_format,
            "online_store_key": int,
            "wholesale_store_key": int,
        }

    Raises:
        ValueError: If no active physical stores exist, or Online/Wholesale
            pseudo-stores are missing.
    """
    active_physical = dim_store[
        (dim_store["store_status"] == "Active") & (dim_store["channel"] == "Store")
    ]
    if active_physical.empty:
        raise ValueError("No active physical stores found in dim_store")

    weights = active_physical.apply(
        lambda row: REGION_DEMAND_INDEX[row["region"]] * STORE_FORMAT_TRAFFIC_WEIGHT[row["store_format"]],
        axis=1,
    ).to_numpy(dtype=float)
    weights = weights / weights.sum()

    online_rows = dim_store[dim_store["channel"] == "Online"]
    wholesale_rows = dim_store[dim_store["channel"] == "Wholesale"]
    if online_rows.empty or wholesale_rows.empty:
        raise ValueError("dim_store is missing the Online or Wholesale pseudo-store")

    return {
        "store_keys": active_physical["store_key"].to_numpy(),
        "store_weights": weights,
        "store_region_map": dict(zip(dim_store["store_key"], dim_store["region"])),
        "store_format_map": dict(zip(dim_store["store_key"], dim_store["store_format"])),
        "online_store_key": int(online_rows["store_key"].iloc[0]),
        "wholesale_store_key": int(wholesale_rows["store_key"].iloc[0]),
    }


def build_product_pools(dim_product: pd.DataFrame) -> dict:
    """
    Build product-sampling pools, grouped by division_price_tier for
    segment-weighted selection.

    Args:
        dim_product: The loaded dim_product DataFrame.

    Returns:
        dict: {
            "by_tier": dict[str, pd.DataFrame] tier -> active products in
                that tier (columns: product_key, division, list_price, unit_cost),
            "product_division_map": dict[int, str],
            "product_price_map": dict[int, float],
            "product_cost_map": dict[int, float],
        }

    Raises:
        ValueError: If any price tier has zero active products.
    """
    active = dim_product[dim_product["is_active"]]
    by_tier: dict[str, pd.DataFrame] = {}
    for tier in config.PRICE_TIERS:
        tier_products = active[active["division_price_tier"] == tier]
        if tier_products.empty:
            raise ValueError(f"No active products found for price tier '{tier}'")
        by_tier[tier] = tier_products[["product_key", "division", "list_price", "unit_cost"]].reset_index(drop=True)

    return {
        "by_tier": by_tier,
        "product_division_map": dict(zip(dim_product["product_key"], dim_product["division"])),
        "product_price_map": dict(zip(dim_product["product_key"], dim_product["list_price"])),
        "product_cost_map": dict(zip(dim_product["product_key"], dim_product["unit_cost"])),
    }


def build_customer_pools(dim_customer: pd.DataFrame) -> dict:
    """
    Build customer-sampling pools: loyalty members' customer_key array
    (with a parallel segment array for lookup), and wholesale accounts'
    customer_key array.

    Args:
        dim_customer: The loaded dim_customer DataFrame.

    Returns:
        dict: {
            "loyalty_customer_keys": np.ndarray,
            "loyalty_customer_segments": np.ndarray (parallel to keys),
            "wholesale_customer_keys": np.ndarray,
        }

    Raises:
        ValueError: If no loyalty members or no wholesale accounts exist.
    """
    loyalty = dim_customer[dim_customer["is_loyalty_member"]]
    wholesale = dim_customer[dim_customer["is_wholesale_account"]]
    if loyalty.empty:
        raise ValueError("dim_customer has no loyalty members to sample from")
    if wholesale.empty:
        raise ValueError("dim_customer has no wholesale accounts to sample from")

    return {
        "loyalty_customer_keys": loyalty["customer_key"].to_numpy(),
        "loyalty_customer_segments": loyalty["segment"].to_numpy(),
        "wholesale_customer_keys": wholesale["customer_key"].to_numpy(),
    }


def build_campaign_lookup(dim_campaign: pd.DataFrame, dim_date: pd.DataFrame) -> dict[str, list[str]]:
    """
    Precompute, for every date in dim_date, the list of campaign_ids
    active on that date (start_date <= date <= end_date).

    Args:
        dim_campaign: The loaded dim_campaign DataFrame.
        dim_date: The loaded dim_date DataFrame.

    Returns:
        dict[str, list[str]]: date_key (ISO string) -> list of active
        campaign_ids (empty list if none active that day).
    """
    campaign_starts = pd.to_datetime(dim_campaign["start_date"])
    campaign_ends = pd.to_datetime(dim_campaign["end_date"])
    campaign_ids = dim_campaign["campaign_id"].to_numpy()

    lookup: dict[str, list[str]] = {}
    for date_key in dim_date["date_key"]:
        current = pd.Timestamp(date_key)
        active_mask = (campaign_starts <= current) & (current <= campaign_ends)
        lookup[date_key] = campaign_ids[active_mask.to_numpy()].tolist()

    logger.info("Campaign lookup built for %d dates", len(lookup))
    return lookup


def build_festive_multiplier_map() -> dict[str, float]:
    """
    Build a festive_period_name -> midpoint demand multiplier map from
    config.FESTIVE_WINDOWS, used for calibrating daily transaction volume.

    Returns:
        dict[str, float]: Festive window name -> midpoint of its
        demand_multiplier_range.
    """
    return {
        window["name"]: sum(window["demand_multiplier_range"]) / 2
        for window in config.FESTIVE_WINDOWS
    }


# ---------------------------------------------------------------------------
# Calibration: compute exact target row counts per (date, channel)
# ---------------------------------------------------------------------------

def build_calibration_plan(dim_date: pd.DataFrame, total_rows: int) -> pd.DataFrame:
    """
    Compute the exact number of fact_sales rows to generate for every
    (date, channel) combination, such that the grand total equals
    `total_rows` exactly, while respecting the relative weighting from
    channel share, weekend uplift, and festive-period uplift.

    Args:
        dim_date: The loaded dim_date DataFrame.
        total_rows: The approved total row count (config.ROW_COUNTS["fact_sales"]).

    Returns:
        pd.DataFrame: Columns [date_key, channel, row_count], summing
        row_count to exactly total_rows.
    """
    festive_multipliers = build_festive_multiplier_map()
    channels = list(TRANSACTION_CHANNEL_SHARE.keys())

    records: list[dict] = []
    for _, day_row in dim_date.iterrows():
        festive_mult = festive_multipliers.get(day_row["festive_period_name"], 1.0) if day_row["is_festive_period"] else 1.0
        for channel in channels:
            weekend_mult = 1.0
            if day_row["is_weekend"]:
                low, high = config.WEEKEND_MULTIPLIER_BY_CHANNEL[channel]
                weekend_mult = (low + high) / 2
            raw_weight = TRANSACTION_CHANNEL_SHARE[channel] * weekend_mult * festive_mult
            records.append({"date_key": day_row["date_key"], "channel": channel, "raw_weight": raw_weight})

    plan = pd.DataFrame.from_records(records)
    weight_sum = plan["raw_weight"].sum()
    plan["exact_share"] = plan["raw_weight"] / weight_sum * total_rows
    plan["row_count"] = np.floor(plan["exact_share"]).astype(int)

    remainder = total_rows - plan["row_count"].sum()
    if remainder > 0:
        # Largest-remainder method: give the leftover rows to the combos
        # with the largest fractional shares, guaranteeing an exact total.
        fractional = (plan["exact_share"] - plan["row_count"]).sort_values(ascending=False)
        top_indices = fractional.index[:remainder]
        plan.loc[top_indices, "row_count"] += 1

    plan = plan[["date_key", "channel", "row_count"]]
    logger.info(
        "Calibration plan built: %d (date,channel) combos, total planned rows = %d",
        len(plan), plan["row_count"].sum(),
    )
    return plan


# ---------------------------------------------------------------------------
# Loyalty trajectory
# ---------------------------------------------------------------------------

def compute_loyalty_rate(day_row: pd.Series) -> float:
    """
    Compute the target loyalty-linked transaction share for a given day,
    per Phase 3A Section 5.4: flat ~48% for the prior-year baseline,
    trending 48% -> 63% across the current fiscal year.

    Args:
        day_row: A row from dim_date (must include fiscal_year,
            is_prior_year_baseline, and date_key).

    Returns:
        float: Target loyalty share in [config.LOYALTY_PENETRATION_START,
        config.LOYALTY_PENETRATION_END].
    """
    if day_row["is_prior_year_baseline"]:
        return config.LOYALTY_PENETRATION_START

    current = pd.Timestamp(day_row["date_key"])
    start = pd.Timestamp(config.CURRENT_FISCAL_YEAR_START)
    end = pd.Timestamp(config.CURRENT_FISCAL_YEAR_END)
    position = (current - start).days / max((end - start).days, 1)
    position = min(max(position, 0.0), 1.0)

    return config.LOYALTY_PENETRATION_START + position * (
        config.LOYALTY_PENETRATION_END - config.LOYALTY_PENETRATION_START
    )


# ---------------------------------------------------------------------------
# Core chunk generator
# ---------------------------------------------------------------------------

def generate_chunk(
    day_row: pd.Series,
    channel: str,
    count: int,
    store_pools: dict,
    product_pools: dict,
    customer_pools: dict,
    active_campaign_ids: list[str],
    sequence_start: int,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """
    Generate `count` fact_sales rows for a single (date, channel) combo.

    Args:
        day_row: The dim_date row for this date.
        channel: One of "Store", "Online", "Wholesale".
        count: Number of rows to generate.
        store_pools: Output of build_store_pools().
        product_pools: Output of build_product_pools().
        customer_pools: Output of build_customer_pools().
        active_campaign_ids: Campaign IDs active on this date.
        sequence_start: The next available per-day sales_id sequence number.
        rng: A seeded numpy random Generator.

    Returns:
        pd.DataFrame: `count` rows with all 14 fact_sales columns.

    Raises:
        ValueError: If count is negative or channel is unrecognized.
    """
    if count < 0:
        raise ValueError(f"count must be non-negative, got {count}")
    if channel not in TRANSACTION_CHANNEL_SHARE:
        raise ValueError(f"Unrecognized channel '{channel}'")
    if count == 0:
        return pd.DataFrame(columns=[
            "sales_id", "date_key", "store_key", "product_key", "customer_key", "channel",
            "quantity", "unit_price", "discount_amount", "net_sales_amount", "cost_amount",
            "loyalty_flag", "promotion_id", "return_flag",
        ])

    date_key = day_row["date_key"]
    is_festive = bool(day_row["is_festive_period"])

    # --- store_key + region -------------------------------------------------
    if channel == "Store":
        store_key = rng.choice(store_pools["store_keys"], size=count, p=store_pools["store_weights"])
        region = np.array([store_pools["store_region_map"][sk] for sk in store_key])
    elif channel == "Online":
        store_key = np.full(count, store_pools["online_store_key"])
        regions = list(REGION_DEMAND_INDEX.keys())
        weights = np.array(list(REGION_DEMAND_INDEX.values()))
        weights = weights / weights.sum()
        region = rng.choice(regions, size=count, p=weights)
    else:  # Wholesale
        store_key = np.full(count, store_pools["wholesale_store_key"])
        regions = list(REGION_DEMAND_INDEX.keys())
        weights = np.array(list(REGION_DEMAND_INDEX.values()))
        weights = weights / weights.sum()
        region = rng.choice(regions, size=count, p=weights)

    # --- loyalty_flag + customer_key + behavioral segment -------------------
    loyalty_flag = np.zeros(count, dtype=bool)
    customer_key = np.full(count, np.nan)
    behavioral_segment = np.empty(count, dtype=object)

    if channel == "Wholesale":
        customer_key = rng.choice(customer_pools["wholesale_customer_keys"], size=count).astype(float)
        # Wholesale buyers still get a behavioral segment label for
        # logging/consistency purposes, drawn from the approved segment mix;
        # it does not influence wholesale quantity/discount, which follow
        # dedicated bulk rules regardless of segment.
        behavioral_segment[:] = rng.choice(
            list(config.CUSTOMER_SEGMENT_SHARE.keys()), size=count, p=list(config.CUSTOMER_SEGMENT_SHARE.values())
        )
    else:
        target_rate = compute_loyalty_rate(day_row)
        loyalty_flag = rng.random(count) < target_rate

        n_loyal = int(loyalty_flag.sum())
        if n_loyal > 0:
            loyal_idx = rng.choice(len(customer_pools["loyalty_customer_keys"]), size=n_loyal)
            customer_key[loyalty_flag] = customer_pools["loyalty_customer_keys"][loyal_idx]
            behavioral_segment[loyalty_flag] = customer_pools["loyalty_customer_segments"][loyal_idx]

        n_walkin = count - n_loyal
        if n_walkin > 0:
            # Walk-ins: NULL customer_key (per rule), but still carry an
            # internal-only pseudo-segment to drive realistic quantity/price
            # behavior, matching the approved config.CUSTOMER_SEGMENT_SHARE mix.
            behavioral_segment[~loyalty_flag] = rng.choice(
                list(config.CUSTOMER_SEGMENT_SHARE.keys()), size=n_walkin, p=list(config.CUSTOMER_SEGMENT_SHARE.values())
            )

    # --- product selection (segment-weighted by price tier) -----------------
    product_key = np.empty(count, dtype=np.int64)
    for segment in config.CUSTOMER_SEGMENTS:
        seg_mask = behavioral_segment == segment
        n_seg = int(seg_mask.sum())
        if n_seg == 0:
            continue
        tier_probs = TIER_PREFERENCE_BY_SEGMENT[segment]
        tiers_drawn = rng.choice(list(tier_probs.keys()), size=n_seg, p=list(tier_probs.values()))
        seg_product_keys = np.empty(n_seg, dtype=np.int64)
        for tier in config.PRICE_TIERS:
            tier_mask = tiers_drawn == tier
            n_tier = int(tier_mask.sum())
            if n_tier == 0:
                continue
            pool = product_pools["by_tier"][tier]
            chosen = rng.choice(pool["product_key"].to_numpy(), size=n_tier)
            seg_product_keys[tier_mask] = chosen
        product_key[seg_mask] = seg_product_keys

    division = np.array([product_pools["product_division_map"][pk] for pk in product_key])
    unit_price = np.array([product_pools["product_price_map"][pk] for pk in product_key])
    unit_cost = np.array([product_pools["product_cost_map"][pk] for pk in product_key])

    # --- quantity -------------------------------------------------------------
    quantity = np.empty(count, dtype=np.int64)
    if channel == "Wholesale":
        low, high = config.WHOLESALE_QUANTITY_RANGE
        quantity[:] = rng.integers(low, high + 1, size=count)
    else:
        for segment, (low, high) in QUANTITY_RANGE_BY_SEGMENT.items():
            seg_mask = behavioral_segment == segment
            n_seg = int(seg_mask.sum())
            if n_seg == 0:
                continue
            quantity[seg_mask] = rng.integers(low, high + 1, size=n_seg)

    # --- discount ---------------------------------------------------------
    discount_rate = np.zeros(count, dtype=float)
    if channel == "Wholesale":
        for threshold, rate in WHOLESALE_DISCOUNT_TIERS:
            mask = quantity >= threshold
            discount_rate = np.where(mask & (discount_rate == 0), rate, discount_rate)
    else:
        for div in config.DIVISIONS:
            div_mask = division == div
            n_div = int(div_mask.sum())
            if n_div == 0:
                continue
            low, high = config.BASELINE_DISCOUNT_RANGE_BY_DIVISION[div]
            base_rate = rng.uniform(low, high, size=n_div)

            if is_festive:
                uplift_low, uplift_high = config.FESTIVE_DISCOUNT_UPLIFT_PP_BY_DIVISION[div]
                base_rate = base_rate + rng.uniform(uplift_low, uplift_high, size=n_div)

            discount_rate[div_mask] = base_rate

        # East region bump.
        east_mask = region == "East"
        if east_mask.any():
            discount_rate[east_mask] += rng.uniform(*EAST_DISCOUNT_BUMP_RANGE, size=int(east_mask.sum()))

        # Segment discount-sensitivity adjustment.
        for segment, adjustment in DISCOUNT_SEGMENT_ADJUSTMENT_PP.items():
            seg_mask = behavioral_segment == segment
            discount_rate[seg_mask] += adjustment

    discount_rate = np.clip(discount_rate, 0.0, MAX_DISCOUNT_RATE)

    line_total = unit_price * quantity
    discount_amount = np.round(discount_rate * line_total, 2)
    discount_amount = np.minimum(discount_amount, line_total)  # never exceed line total
    net_sales_amount = np.round(line_total - discount_amount, 2)
    cost_amount = np.round(unit_cost * quantity, 2)

    # --- promotion_id -------------------------------------------------------
    promotion_id = np.full(count, None, dtype=object)
    if channel != "Wholesale" and active_campaign_ids:
        attach_mask = rng.random(count) < PROMOTION_ATTACH_RATE
        n_attach = int(attach_mask.sum())
        if n_attach > 0:
            promotion_id[attach_mask] = rng.choice(active_campaign_ids, size=n_attach)

    # --- sales_id -------------------------------------------------------------
    date_compact = date_key.replace("-", "")
    sales_id = [
        f"SL-{date_compact}-{seq:07d}" for seq in range(sequence_start, sequence_start + count)
    ]

    return pd.DataFrame({
        "sales_id": sales_id,
        "date_key": date_key,
        "store_key": store_key,
        "product_key": product_key,
        "customer_key": customer_key,  # float with NaN for walk-ins; cast on export
        "channel": channel,
        "quantity": quantity,
        "unit_price": unit_price,
        "discount_amount": discount_amount,
        "net_sales_amount": net_sales_amount,
        "cost_amount": cost_amount,
        "loyalty_flag": loyalty_flag,
        "promotion_id": promotion_id,
        "return_flag": False,
    })


# ---------------------------------------------------------------------------
# Orchestration: stream all chunks to CSV
# ---------------------------------------------------------------------------

def generate_and_export_fact_sales(dimensions: dict[str, pd.DataFrame]) -> Path:
    """
    Generate the full fact_sales table date-by-date and channel-by-channel,
    writing each chunk directly to CSV (append mode) so the full 4.2M-row
    table is never held in memory at once.

    Args:
        dimensions: Output of load_dimension_tables().

    Returns:
        Path: The output CSV path.

    Raises:
        ValueError: If the final written row count does not match the
            approved total (config.ROW_COUNTS["fact_sales"]).
    """
    rng = np.random.default_rng(config.RANDOM_SEED)
    Faker.seed(config.RANDOM_SEED)

    dim_date = dimensions["dim_date"]
    total_target = config.ROW_COUNTS["fact_sales"]

    store_pools = build_store_pools(dimensions["dim_store"])
    product_pools = build_product_pools(dimensions["dim_product"])
    customer_pools = build_customer_pools(dimensions["dim_customer"])
    campaign_lookup = build_campaign_lookup(dimensions["dim_campaign"], dim_date)
    calibration_plan = build_calibration_plan(dim_date, total_target)

    output_path = config.get_output_path("fact_sales")
    if output_path.exists():
        output_path.unlink()  # start clean; this module owns this file's full lifecycle

    plan_lookup = calibration_plan.set_index(["date_key", "channel"])["row_count"]

    rows_written = 0
    header_written = False

    for _, day_row in dim_date.iterrows():
        date_key = day_row["date_key"]
        active_campaign_ids = campaign_lookup.get(date_key, [])
        sequence_counter = 1

        for channel in TRANSACTION_CHANNEL_SHARE:
            count = int(plan_lookup.get((date_key, channel), 0))
            if count == 0:
                continue

            chunk = generate_chunk(
                day_row=day_row, channel=channel, count=count,
                store_pools=store_pools, product_pools=product_pools,
                customer_pools=customer_pools, active_campaign_ids=active_campaign_ids,
                sequence_start=sequence_counter, rng=rng,
            )
            sequence_counter += count

            # customer_key: cast to nullable pandas Int64 so walk-ins export
            # as truly empty CSV cells rather than "nan" strings or floats.
            chunk["customer_key"] = chunk["customer_key"].astype("Int64")

            chunk.to_csv(output_path, mode="a", header=not header_written, index=False)
            header_written = True
            rows_written += len(chunk)

        if day_row.name % 100 == 0:
            logger.info("Progress: date %s processed, %d rows written so far", date_key, rows_written)

    if rows_written != total_target:
        raise ValueError(
            f"fact_sales wrote {rows_written} rows, expected exactly {total_target} "
            f"per the Phase 3A approved design. Check build_calibration_plan()."
        )

    logger.info("fact_sales generation complete: %d rows written to %s", rows_written, output_path)
    return output_path


# ---------------------------------------------------------------------------
# Chunked validation (reads the exported CSV back in batches; the full
# table is not loaded into memory at once for this check either)
# ---------------------------------------------------------------------------

def validate_fact_sales(output_path: Path, dimensions: dict[str, pd.DataFrame]) -> None:
    """
    Validate the exported fact_sales.csv by streaming it back in chunks,
    checking row count, key uniqueness, foreign-key integrity, formula
    correctness, and value-range rules without loading the full table.

    Args:
        output_path: Path to the exported fact_sales.csv.
        dimensions: Output of load_dimension_tables(), used for FK checks.

    Returns:
        None. Raises on the first failed check.

    Raises:
        ValueError: If any validation rule fails.
    """
    valid_store_keys = set(dimensions["dim_store"]["store_key"])
    valid_product_keys = set(dimensions["dim_product"]["product_key"])
    valid_customer_keys = set(dimensions["dim_customer"]["customer_key"])
    valid_date_keys = set(dimensions["dim_date"]["date_key"])
    store_channel_map = dict(zip(dimensions["dim_store"]["store_key"], dimensions["dim_store"]["channel"]))

    seen_sales_ids: set[str] = set()
    total_rows = 0

    chunk_iter = pd.read_csv(
        output_path, chunksize=500_000, dtype={"customer_key": "Int64", "promotion_id": "object"},
        low_memory=False,
    )
    for chunk_number, chunk in enumerate(chunk_iter, start=1):
        total_rows += len(chunk)

        duplicate_in_chunk = chunk["sales_id"].duplicated()
        if duplicate_in_chunk.any():
            raise ValueError(f"fact_sales chunk {chunk_number} contains duplicate sales_id within itself")
        overlap = seen_sales_ids.intersection(chunk["sales_id"])
        if overlap:
            raise ValueError(f"fact_sales has sales_id values duplicated across chunks: {list(overlap)[:5]}")
        seen_sales_ids.update(chunk["sales_id"])

        if not set(chunk["store_key"]).issubset(valid_store_keys):
            raise ValueError(f"fact_sales chunk {chunk_number} has store_key values not present in dim_store")
        if not set(chunk["product_key"]).issubset(valid_product_keys):
            raise ValueError(f"fact_sales chunk {chunk_number} has product_key values not present in dim_product")
        if not set(chunk["date_key"]).issubset(valid_date_keys):
            raise ValueError(f"fact_sales chunk {chunk_number} has date_key values not present in dim_date")

        non_null_customers = chunk["customer_key"].dropna()
        if not set(non_null_customers).issubset(valid_customer_keys):
            raise ValueError(f"fact_sales chunk {chunk_number} has customer_key values not present in dim_customer")

        if (chunk["quantity"] <= 0).any():
            raise ValueError(f"fact_sales chunk {chunk_number} has non-positive quantity")
        if (chunk["unit_price"] <= 0).any():
            raise ValueError(f"fact_sales chunk {chunk_number} has non-positive unit_price")
        if (chunk["discount_amount"] < 0).any():
            raise ValueError(f"fact_sales chunk {chunk_number} has negative discount_amount")
        if (chunk["net_sales_amount"] <= 0).any():
            raise ValueError(f"fact_sales chunk {chunk_number} has non-positive net_sales_amount")
        if (chunk["cost_amount"] <= 0).any():
            raise ValueError(f"fact_sales chunk {chunk_number} has non-positive cost_amount")

        expected_net = np.round(chunk["unit_price"] * chunk["quantity"] - chunk["discount_amount"], 2)
        if not np.allclose(chunk["net_sales_amount"], expected_net, atol=0.02):
            raise ValueError(
                f"fact_sales chunk {chunk_number} has net_sales_amount not matching "
                f"unit_price*quantity - discount_amount for at least one row"
            )

        # Channel must always match the store dimension's channel.
        expected_channel = chunk["store_key"].map(store_channel_map)
        if not (chunk["channel"] == expected_channel).all():
            raise ValueError(f"fact_sales chunk {chunk_number} has channel not matching dim_store.channel")

        # Walk-in rule: loyalty_flag False + channel != Wholesale => customer_key NULL.
        walkin_mask = (~chunk["loyalty_flag"]) & (chunk["channel"] != "Wholesale")
        if chunk.loc[walkin_mask, "customer_key"].notna().any():
            raise ValueError(f"fact_sales chunk {chunk_number} has non-loyalty non-wholesale rows with a customer_key")

        # Wholesale rule: customer_key always present.
        wholesale_mask = chunk["channel"] == "Wholesale"
        if chunk.loc[wholesale_mask, "customer_key"].isna().any():
            raise ValueError(f"fact_sales chunk {chunk_number} has Wholesale rows with a NULL customer_key")

        # loyalty_flag True => customer_key present.
        if chunk.loc[chunk["loyalty_flag"], "customer_key"].isna().any():
            raise ValueError(f"fact_sales chunk {chunk_number} has loyalty_flag=True rows with a NULL customer_key")

        if (chunk["return_flag"] != False).any():  # noqa: E712 (explicit False check)
            raise ValueError(f"fact_sales chunk {chunk_number} has return_flag != False (must be False at this stage)")

    expected_rows = config.ROW_COUNTS["fact_sales"]
    if total_rows != expected_rows:
        raise ValueError(f"fact_sales row count mismatch: expected {expected_rows}, got {total_rows}")

    logger.info("fact_sales validation passed: %d rows across all chunks, all checks green", total_rows)


def main() -> None:
    """
    Entry point for standalone execution: load dimensions, generate and
    stream fact_sales.csv chunk-by-chunk, then validate it by re-reading
    it in chunks. Exits with a non-zero status code on failure.
    """
    logger.info("=== Starting fact_sales generation (Phase 3B) ===")
    try:
        dimensions = load_dimension_tables()
        output_path = generate_and_export_fact_sales(dimensions)
        validate_fact_sales(output_path, dimensions)
        logger.info("=== fact_sales generation finished successfully ===")
    except Exception:
        logger.exception("fact_sales generation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
