"""
generate_customers.py
======================
Generates dim_customer.csv — the customer/loyalty dimension for Insight360.

Implements the Phase 3A approved schema (Section 2.4) exactly:
    customer_key, loyalty_id, is_loyalty_member, segment, enrollment_date,
    region, preferred_channel, acquisition_channel, first_purchase_date,
    is_wholesale_account

Grain: 1 row per customer, 850,000 rows total (Phase 3A Section 6 sizing
refinement, replacing the original Phase 1 planning placeholder).

All distribution parameters (segment shares, loyalty rate, region weights)
are sourced from config.py where already defined, or set locally here
where Phase 3A left them unspecified (e.g., preferred-channel bias by
segment, acquisition-channel mix). No redesign of the approved schema or
row count occurs in this module. Generation is fully vectorized with
numpy given the 850,000-row scale.
"""

from __future__ import annotations

import sys
from typing import Final

import numpy as np
import pandas as pd
from faker import Faker

import config

logger = config.get_logger(__name__)

# ---------------------------------------------------------------------------
# Local distribution parameters (not specified numerically in Phase 3A,
# so defined locally rather than added to the shared config.py contract).
# ---------------------------------------------------------------------------

# Regional distribution of the customer base. Kept close to even, slightly
# lighter in East, consistent with the same directional logic used for
# dim_store's regional allocation (Module 2).
CUSTOMER_REGION_WEIGHTS: Final[dict[str, float]] = {
    "North": 0.25,
    "South": 0.27,
    "West": 0.26,
    "East": 0.22,
}

# Preferred-channel bias by segment (retail customers only; wholesale
# accounts are forced to "Wholesale" regardless of segment, per rule).
PREFERRED_CHANNEL_BIAS_BY_SEGMENT: Final[dict[str, dict[str, float]]] = {
    "Value Shopper": {"Store": 0.78, "Online": 0.22},
    "Premium Shopper": {"Store": 0.50, "Online": 0.50},
    "Digital Native": {"Store": 0.20, "Online": 0.80},
}

ACQUISITION_CHANNEL_WEIGHTS: Final[dict[str, float]] = {
    "Organic Walk-in": 0.35,
    "Digital Ads Campaign": 0.30,
    "Referral": 0.15,
    "Email/SMS Campaign": 0.20,
}

# Overall loyalty membership rate, applied within the non-wholesale
# population (wholesale accounts are always non-members by rule), which
# lands the blended overall rate at approximately the target 48%.
LOYALTY_MEMBERSHIP_RATE: Final[float] = 0.48

# Share of the customer base that are B2B wholesale accounts.
WHOLESALE_ACCOUNT_RATE: Final[float] = 0.01

_faker = Faker("en_IN")


def generate_customer_keys(total_customers: int) -> np.ndarray:
    """
    Generate the sequential, unique customer_key array.

    Args:
        total_customers: Number of customer keys to generate.

    Returns:
        np.ndarray: Array of integers 1..total_customers.

    Raises:
        ValueError: If total_customers is not positive.
    """
    if total_customers <= 0:
        raise ValueError(f"total_customers must be positive, got {total_customers}")
    return np.arange(1, total_customers + 1, dtype=np.int64)


def generate_segments(total_customers: int, rng: np.random.Generator) -> np.ndarray:
    """
    Draw customer segments per the approved config.CUSTOMER_SEGMENT_SHARE
    distribution (Apparel/Home/etc. affinity is derived later at the
    transaction level, not stored here).

    Args:
        total_customers: Number of segment values to draw.
        rng: A seeded numpy random Generator.

    Returns:
        np.ndarray: Array of segment label strings.
    """
    segments = list(config.CUSTOMER_SEGMENT_SHARE.keys())
    probabilities = list(config.CUSTOMER_SEGMENT_SHARE.values())
    return rng.choice(segments, size=total_customers, p=probabilities)


def generate_regions(total_customers: int, rng: np.random.Generator) -> np.ndarray:
    """
    Draw customer regions per CUSTOMER_REGION_WEIGHTS.

    Args:
        total_customers: Number of region values to draw.
        rng: A seeded numpy random Generator.

    Returns:
        np.ndarray: Array of region label strings.
    """
    regions = list(CUSTOMER_REGION_WEIGHTS.keys())
    probabilities = list(CUSTOMER_REGION_WEIGHTS.values())
    return rng.choice(regions, size=total_customers, p=probabilities)


def generate_wholesale_flags(total_customers: int, rng: np.random.Generator) -> np.ndarray:
    """
    Draw the is_wholesale_account boolean flag at WHOLESALE_ACCOUNT_RATE.

    Args:
        total_customers: Number of flags to draw.
        rng: A seeded numpy random Generator.

    Returns:
        np.ndarray: Boolean array, ~1% True.
    """
    return rng.random(total_customers) < WHOLESALE_ACCOUNT_RATE


def generate_loyalty_information(
    customer_keys: np.ndarray, is_wholesale_account: np.ndarray, rng: np.random.Generator
) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate is_loyalty_member and loyalty_id, enforcing:
      - Wholesale accounts are always non-members (loyalty_id = None).
      - Non-wholesale customers are members at LOYALTY_MEMBERSHIP_RATE.
      - loyalty_id format is "MRG-LY-XXXXXX", derived from the customer's
        own key (zero-padded to 6 digits) to guarantee uniqueness trivially
        without a separate ID pool or collision-checking pass.

    Args:
        customer_keys: The customer_key array (used to derive loyalty_id).
        is_wholesale_account: Boolean array marking wholesale accounts.
        rng: A seeded numpy random Generator.

    Returns:
        tuple[np.ndarray, np.ndarray]: (is_loyalty_member bool array,
        loyalty_id object array with None for non-members).

    Raises:
        ValueError: If customer_keys and is_wholesale_account lengths differ.
    """
    if len(customer_keys) != len(is_wholesale_account):
        raise ValueError("customer_keys and is_wholesale_account must be the same length")

    is_loyalty_member = rng.random(len(customer_keys)) < LOYALTY_MEMBERSHIP_RATE
    # Rule: wholesale accounts are never loyalty members, overriding the draw.
    is_loyalty_member = is_loyalty_member & (~is_wholesale_account)

    loyalty_id = np.where(
        is_loyalty_member,
        np.array([f"MRG-LY-{key:06d}" for key in customer_keys], dtype=object),
        None,
    )

    return is_loyalty_member, loyalty_id


def generate_channels(
    segments: np.ndarray, is_wholesale_account: np.ndarray, rng: np.random.Generator
) -> np.ndarray:
    """
    Generate preferred_channel, biased by segment for retail customers and
    forced to "Wholesale" for wholesale accounts, per the approved rule.

    Args:
        segments: The segment label array.
        is_wholesale_account: Boolean array marking wholesale accounts.
        rng: A seeded numpy random Generator.

    Returns:
        np.ndarray: Array of preferred_channel label strings.

    Raises:
        ValueError: If segments and is_wholesale_account lengths differ.
    """
    if len(segments) != len(is_wholesale_account):
        raise ValueError("segments and is_wholesale_account must be the same length")

    preferred_channel = np.empty(len(segments), dtype=object)

    for segment, channel_probs in PREFERRED_CHANNEL_BIAS_BY_SEGMENT.items():
        mask = (segments == segment) & (~is_wholesale_account)
        n = int(mask.sum())
        if n == 0:
            continue
        channels = list(channel_probs.keys())
        probabilities = list(channel_probs.values())
        preferred_channel[mask] = rng.choice(channels, size=n, p=probabilities)

    preferred_channel[is_wholesale_account] = "Wholesale"

    if (preferred_channel == None).any():  # noqa: E711 (vectorized None check)
        raise ValueError("generate_channels produced unassigned rows; segment coverage incomplete")

    return preferred_channel


def generate_acquisition_channels(total_customers: int, rng: np.random.Generator) -> np.ndarray:
    """
    Draw acquisition_channel per ACQUISITION_CHANNEL_WEIGHTS.

    Args:
        total_customers: Number of values to draw.
        rng: A seeded numpy random Generator.

    Returns:
        np.ndarray: Array of acquisition_channel label strings.
    """
    channels = list(ACQUISITION_CHANNEL_WEIGHTS.keys())
    probabilities = list(ACQUISITION_CHANNEL_WEIGHTS.values())
    return rng.choice(channels, size=total_customers, p=probabilities)


def generate_dates(
    total_customers: int, is_loyalty_member: np.ndarray, rng: np.random.Generator
) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate first_purchase_date (all customers) and enrollment_date
    (loyalty members only), both within the approved reporting window.

    enrollment_date is generated on or after each customer's
    first_purchase_date, and never after config.DATA_END_DATE, reflecting
    that a customer typically joins the loyalty program at or after their
    first transaction.

    Args:
        total_customers: Number of customers to generate dates for.
        is_loyalty_member: Boolean array marking loyalty members.
        rng: A seeded numpy random Generator.

    Returns:
        tuple[np.ndarray, np.ndarray]: (first_purchase_date as
        datetime64[ns] array, enrollment_date as object array of
        pd.Timestamp/None).

    Raises:
        ValueError: If total_customers does not match is_loyalty_member length.
    """
    if total_customers != len(is_loyalty_member):
        raise ValueError("total_customers must match len(is_loyalty_member)")

    window_start = pd.Timestamp(config.DATA_START_DATE)
    window_end = pd.Timestamp(config.DATA_END_DATE)
    window_span_days = (window_end - window_start).days

    first_purchase_offsets = rng.integers(0, window_span_days + 1, size=total_customers)
    first_purchase_date = window_start + pd.to_timedelta(first_purchase_offsets, unit="D")

    # For enrollment, draw an offset from first_purchase_date up to the
    # remaining days left in the window, then clip to window_end.
    remaining_days = (window_end - first_purchase_date).days.to_numpy()
    remaining_days = np.clip(remaining_days, 0, None)
    enrollment_offsets = np.array(
        [rng.integers(0, remaining + 1) if remaining > 0 else 0 for remaining in remaining_days]
    )
    enrollment_date_all = first_purchase_date + pd.to_timedelta(enrollment_offsets, unit="D")

    enrollment_date = np.where(is_loyalty_member, enrollment_date_all, np.datetime64("NaT"))

    return first_purchase_date.to_numpy(), enrollment_date


def generate_dim_customer() -> pd.DataFrame:
    """
    Generate the complete dim_customer table: 850,000 customers with
    loyalty, segment, region, channel, and acquisition attributes.

    Returns:
        pd.DataFrame: 850,000 rows with columns in the exact Phase 3A
        order: customer_key, loyalty_id, is_loyalty_member, segment,
        enrollment_date, region, preferred_channel, acquisition_channel,
        first_purchase_date, is_wholesale_account.

    Raises:
        ValueError: If the resulting row count does not match the approved
            count of 850000 (config.ROW_COUNTS["dim_customer"]).
    """
    logger.info("Generating dim_customer")
    rng = np.random.default_rng(config.RANDOM_SEED)
    Faker.seed(config.RANDOM_SEED)

    total_customers = config.ROW_COUNTS["dim_customer"]

    customer_keys = generate_customer_keys(total_customers)
    segments = generate_segments(total_customers, rng)
    regions = generate_regions(total_customers, rng)
    is_wholesale_account = generate_wholesale_flags(total_customers, rng)
    is_loyalty_member, loyalty_id = generate_loyalty_information(customer_keys, is_wholesale_account, rng)
    preferred_channel = generate_channels(segments, is_wholesale_account, rng)
    acquisition_channel = generate_acquisition_channels(total_customers, rng)
    first_purchase_date, enrollment_date = generate_dates(total_customers, is_loyalty_member, rng)

    dim_customer = pd.DataFrame({
        "customer_key": customer_keys,
        "loyalty_id": loyalty_id,
        "is_loyalty_member": is_loyalty_member,
        "segment": segments,
        "enrollment_date": pd.to_datetime(enrollment_date).strftime("%Y-%m-%d"),
        "region": regions,
        "preferred_channel": preferred_channel,
        "acquisition_channel": acquisition_channel,
        "first_purchase_date": pd.to_datetime(first_purchase_date).strftime("%Y-%m-%d"),
        "is_wholesale_account": is_wholesale_account,
    })

    # strftime on NaT produces the literal string "NaT"; convert those back
    # to a true missing value so enrollment_date is correctly null for
    # non-loyalty-members rather than holding a placeholder string.
    dim_customer.loc[dim_customer["enrollment_date"] == "NaT", "enrollment_date"] = None

    expected_rows = total_customers
    if len(dim_customer) != expected_rows:
        raise ValueError(
            f"dim_customer generated {len(dim_customer)} rows, expected exactly "
            f"{expected_rows} per the Phase 3A approved design."
        )

    logger.info("dim_customer generation complete: %d rows", len(dim_customer))
    return dim_customer


def validate_dataframe(dim_customer: pd.DataFrame) -> None:
    """
    Run structural validation on the generated dim_customer table before export.

    Args:
        dim_customer: The DataFrame produced by generate_dim_customer().

    Returns:
        None. Raises on the first failed check.

    Raises:
        ValueError: If any validation rule fails.
    """
    expected_rows = config.ROW_COUNTS["dim_customer"]
    if len(dim_customer) != expected_rows:
        raise ValueError(f"Row count mismatch: expected {expected_rows}, got {len(dim_customer)}")

    if dim_customer["customer_key"].duplicated().any():
        raise ValueError("dim_customer.customer_key contains duplicate values; PK uniqueness violated")

    # Loyalty rules: loyalty_id present iff is_loyalty_member is True.
    loyalty_mismatch = dim_customer["is_loyalty_member"] != dim_customer["loyalty_id"].notna()
    if loyalty_mismatch.any():
        raise ValueError(
            f"dim_customer has {loyalty_mismatch.sum()} row(s) where loyalty_id "
            f"nullability is inconsistent with is_loyalty_member"
        )

    if dim_customer.loc[dim_customer["loyalty_id"].notna(), "loyalty_id"].duplicated().any():
        raise ValueError("dim_customer.loyalty_id contains duplicate values among loyalty members")

    # Enrollment date rules: present iff is_loyalty_member is True.
    enrollment_mismatch = dim_customer["is_loyalty_member"] != dim_customer["enrollment_date"].notna()
    if enrollment_mismatch.any():
        raise ValueError(
            f"dim_customer has {enrollment_mismatch.sum()} row(s) where enrollment_date "
            f"nullability is inconsistent with is_loyalty_member"
        )

    invalid_regions = set(dim_customer["region"].unique()) - set(config.REGIONS)
    if invalid_regions:
        raise ValueError(f"dim_customer.region contains invalid values: {invalid_regions}")

    invalid_segments = set(dim_customer["segment"].unique()) - set(config.CUSTOMER_SEGMENTS)
    if invalid_segments:
        raise ValueError(f"dim_customer.segment contains invalid values: {invalid_segments}")

    invalid_channels = set(dim_customer["preferred_channel"].unique()) - set(config.CHANNELS)
    if invalid_channels:
        raise ValueError(f"dim_customer.preferred_channel contains invalid values: {invalid_channels}")

    invalid_acquisition = (
        set(dim_customer["acquisition_channel"].unique()) - set(ACQUISITION_CHANNEL_WEIGHTS.keys())
    )
    if invalid_acquisition:
        raise ValueError(f"dim_customer.acquisition_channel contains invalid values: {invalid_acquisition}")

    # Wholesale rules.
    wholesale_rows = dim_customer[dim_customer["is_wholesale_account"]]
    if not wholesale_rows.empty:
        if (wholesale_rows["preferred_channel"] != "Wholesale").any():
            raise ValueError("dim_customer has wholesale accounts with preferred_channel != 'Wholesale'")
        if wholesale_rows["is_loyalty_member"].any():
            raise ValueError("dim_customer has wholesale accounts with is_loyalty_member = True")
        if wholesale_rows["loyalty_id"].notna().any():
            raise ValueError("dim_customer has wholesale accounts with a non-null loyalty_id")

    non_wholesale_rows = dim_customer[~dim_customer["is_wholesale_account"]]
    if (non_wholesale_rows["preferred_channel"] == "Wholesale").any():
        raise ValueError("dim_customer has non-wholesale accounts with preferred_channel = 'Wholesale'")

    mandatory_fields = [
        "customer_key", "is_loyalty_member", "segment", "region",
        "preferred_channel", "acquisition_channel", "first_purchase_date",
        "is_wholesale_account",
    ]
    for field in mandatory_fields:
        if dim_customer[field].isnull().any():
            raise ValueError(f"dim_customer.{field} contains nulls but is a mandatory field")

    logger.info("dim_customer validation passed: %d rows, all checks green", len(dim_customer))


def save_csv(dim_customer: pd.DataFrame) -> None:
    """
    Write the dim_customer DataFrame to data/raw/dim_customer.csv.

    Args:
        dim_customer: The validated DataFrame to export.

    Returns:
        None.

    Raises:
        OSError: If the file cannot be written.
    """
    output_path = config.get_output_path("dim_customer")
    try:
        dim_customer.to_csv(output_path, index=False)
        logger.info("dim_customer exported to %s (%d rows)", output_path, len(dim_customer))
    except OSError:
        logger.exception("Failed to write dim_customer to %s", output_path)
        raise


def main() -> None:
    """
    Entry point for standalone execution: generate, validate, and export
    dim_customer.csv. Exits with a non-zero status code on failure.
    """
    logger.info("=== Starting dim_customer generation (Phase 3B) ===")
    try:
        dim_customer = generate_dim_customer()
        validate_dataframe(dim_customer)
        save_csv(dim_customer)

        segment_counts = dim_customer["segment"].value_counts().to_dict()
        region_counts = dim_customer["region"].value_counts().to_dict()
        loyalty_share = dim_customer["is_loyalty_member"].mean()
        wholesale_share = dim_customer["is_wholesale_account"].mean()
        channel_counts = dim_customer["preferred_channel"].value_counts().to_dict()
        logger.info(
            "Summary: %d total rows | segments=%s | regions=%s | "
            "loyalty=%.1f%% | wholesale=%.2f%% | channels=%s",
            len(dim_customer), segment_counts, region_counts,
            loyalty_share * 100, wholesale_share * 100, channel_counts,
        )
        logger.info("=== dim_customer generation finished successfully ===")
    except Exception:
        logger.exception("dim_customer generation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
