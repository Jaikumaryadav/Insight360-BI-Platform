"""
generate_campaigns.py
======================
Generates dim_campaign.csv — the marketing campaign dimension for Insight360.

Implements the Phase 3A approved schema (Section 2.5) exactly:
    campaign_id, campaign_name, campaign_channel, target_segment,
    campaign_type, start_date, end_date, spend_amount, target_region

Grain: 1 row per campaign, 65 rows total (midpoint of the Phase 3A
approved 50-80 range, per Section 6 sizing justification).

Channel, type, and spend-range parameters are sourced from config.py.
Campaign-name pools, targeting-null rates, and per-type spend skew are
local to this module since Phase 3A did not specify literal campaign
names or those particular probability weights. No redesign of the
approved schema or row count occurs here.
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
# Local reference data (naming pools / probability weights — not Phase 3A
# business-rule constants, which live in config.py).
# ---------------------------------------------------------------------------

# Pool of realistic retail campaign names, oversized relative to the 65
# required so that 65 can be sampled without replacement (guaranteeing
# unique names without needing a disambiguation suffix pass).
CAMPAIGN_NAME_POOL: Final[list[str]] = [
    "Diwali Mega Sale", "Summer EOSS", "Republic Day Sale", "Independence Day Sale",
    "Year-End Clearance", "Winter Clearance", "Monsoon Special", "New Year Kickoff",
    "Festive Wardrobe Refresh", "Home Makeover Days", "Tech Upgrade Fest",
    "Essentials Restock Sale", "Weekend Flash Sale", "Loyalty Appreciation Week",
    "Premium Rewards Week", "Digital Native Cashback", "First Purchase Welcome Offer",
    "Referral Bonus Drive", "App-Only Flash Deal", "Store Anniversary Sale",
    "Back to School Sale", "Wedding Season Edit", "Kids Fest Special",
    "Footwear Frenzy", "Kitchen Essentials Sale", "Decor Refresh Week",
    "Audio Fest", "Mobile Accessories Mania", "Grocery Saver Days",
    "Personal Care Fest", "Health & Wellness Week", "Regional Spotlight Sale",
    "North Zone Special", "South Zone Special", "East Zone Boost",
    "West Zone Celebration", "Value Shopper Bonanza", "Premium Member Preview",
    "Online Exclusive Days", "In-Store Walk-in Rewards", "Email Subscriber Special",
    "SMS Flash Alert Sale", "Brand Awareness Push", "New Category Launch",
    "Clearance Blowout", "Mid-Season Sale", "Payday Sale", "Republic Week Extended",
    "EOSS Extension", "Diwali Digital Push", "Festive Combo Offers",
    "Loyalty Points Multiplier", "Cashback Carnival", "Style Refresh Sale",
    "Home Comfort Days", "Tech Deals Week", "Essentials Value Pack",
    "Founders Day Sale", "Customer Appreciation Month", "Spring Refresh Sale",
    "Rainy Day Specials", "Great Indian Shopping Days", "Smart Saver Week",
    "Trendsetter Showcase", "Everyday Value Days", "Festive Glow Sale",
    "New Arrivals Preview", "Combo Deal Days",
]

CAMPAIGN_CHANNEL_WEIGHTS: Final[dict[str, float]] = {
    "Digital Ads": 0.35,
    "Email": 0.25,
    "SMS": 0.20,
    "In-Store": 0.20,
}

CAMPAIGN_TYPE_WEIGHTS: Final[dict[str, float]] = {
    "Acquisition": 0.40,
    "Retention": 0.40,
    "Brand": 0.20,
}

# Share of campaigns with a NULL (i.e., "everyone" / "national") target.
TARGET_SEGMENT_NULL_RATE: Final[float] = 0.35
TARGET_REGION_NULL_RATE: Final[float] = 0.55

# Campaign duration bounds, per this module's spec.
CAMPAIGN_DURATION_DAYS_RANGE: Final[tuple[int, int]] = (7, 45)

# Spend skew by campaign type: Brand campaigns generally spend more, per
# the approved directional rule; ranges are sub-bands within config's
# overall approved CAMPAIGN_SPEND_RANGE (150000, 2500000).
SPEND_RANGE_BY_TYPE: Final[dict[str, tuple[float, float]]] = {
    "Retention": (150000.0, 1200000.0),
    "Acquisition": (500000.0, 1800000.0),
    "Brand": (1200000.0, 2500000.0),
}

_faker = Faker("en_IN")


def _generate_campaign_ids(start_dates: list[date]) -> list[str]:
    """
    Build unique campaign_id values in the "CMP-YYYY-NNN" format shown in
    the Phase 3A example (e.g., "CMP-2025-047"), using each campaign's
    start-date year and a global 1-based sequence number for uniqueness.

    Args:
        start_dates: The list of campaign start dates, in generation order.

    Returns:
        list[str]: Campaign IDs, one per input date, guaranteed unique
        because the sequence number alone is unique regardless of year reuse.
    """
    return [f"CMP-{d.year}-{seq:03d}" for seq, d in enumerate(start_dates, start=1)]


def _generate_campaign_names(count: int, rng: np.random.Generator) -> list[str]:
    """
    Sample `count` unique campaign names from CAMPAIGN_NAME_POOL without
    replacement.

    Args:
        count: Number of unique names required.
        rng: A seeded numpy random Generator.

    Returns:
        list[str]: `count` unique campaign names.

    Raises:
        ValueError: If count exceeds the size of CAMPAIGN_NAME_POOL.
    """
    if count > len(CAMPAIGN_NAME_POOL):
        raise ValueError(
            f"Requested {count} unique campaign names but CAMPAIGN_NAME_POOL "
            f"only has {len(CAMPAIGN_NAME_POOL)} entries"
        )
    chosen_indices = rng.choice(len(CAMPAIGN_NAME_POOL), size=count, replace=False)
    return [CAMPAIGN_NAME_POOL[i] for i in chosen_indices]


def _generate_campaign_dates(count: int, rng: np.random.Generator) -> tuple[list[date], list[date]]:
    """
    Generate start_date/end_date pairs, each duration 7-45 days, with
    start_date chosen so the full campaign fits inside the reporting window
    (config.DATA_START_DATE to config.DATA_END_DATE).

    Args:
        count: Number of campaigns to generate dates for.
        rng: A seeded numpy random Generator.

    Returns:
        tuple[list[date], list[date]]: (start_dates, end_dates), each of
        length `count`, with end_date always strictly after start_date.

    Raises:
        ValueError: If the reporting window is too short to fit even the
            minimum campaign duration.
    """
    min_duration, max_duration = CAMPAIGN_DURATION_DAYS_RANGE
    latest_possible_start = config.DATA_END_DATE - timedelta(days=min_duration)
    window_span_days = (latest_possible_start - config.DATA_START_DATE).days

    if window_span_days < 0:
        raise ValueError(
            "Reporting window is shorter than the minimum campaign duration; "
            "cannot generate valid campaign dates"
        )

    start_dates: list[date] = []
    end_dates: list[date] = []
    for _ in range(count):
        start_offset = int(rng.integers(0, window_span_days + 1))
        start_date_value = config.DATA_START_DATE + timedelta(days=start_offset)

        max_duration_for_this_start = min(
            max_duration, (config.DATA_END_DATE - start_date_value).days
        )
        duration = int(rng.integers(min_duration, max(min_duration, max_duration_for_this_start) + 1))
        end_date_value = start_date_value + timedelta(days=duration)

        start_dates.append(start_date_value)
        end_dates.append(end_date_value)

    return start_dates, end_dates


def _generate_target_segments(count: int, rng: np.random.Generator) -> list[str | None]:
    """
    Generate target_segment values: NULL (national/all-segment campaign)
    at TARGET_SEGMENT_NULL_RATE, otherwise a single segment.

    Args:
        count: Number of values to generate.
        rng: A seeded numpy random Generator.

    Returns:
        list[str | None]: Segment labels or None.
    """
    is_null = rng.random(count) < TARGET_SEGMENT_NULL_RATE
    segments = rng.choice(config.CUSTOMER_SEGMENTS, size=count)
    return [None if null else str(seg) for null, seg in zip(is_null, segments)]


def _generate_target_regions(count: int, rng: np.random.Generator) -> list[str | None]:
    """
    Generate target_region values: NULL (national campaign) at
    TARGET_REGION_NULL_RATE, otherwise a single region.

    Args:
        count: Number of values to generate.
        rng: A seeded numpy random Generator.

    Returns:
        list[str | None]: Region labels or None.
    """
    is_null = rng.random(count) < TARGET_REGION_NULL_RATE
    regions = rng.choice(config.REGIONS, size=count)
    return [None if null else str(reg) for null, reg in zip(is_null, regions)]


def _generate_spend_amounts(campaign_types: list[str], rng: np.random.Generator) -> list[float]:
    """
    Generate spend_amount per campaign, drawn from a type-specific sub-band
    of the approved spend range so that Brand campaigns skew higher than
    Acquisition and Retention, per the approved directional rule.

    Args:
        campaign_types: The campaign_type value for each campaign, in order.
        rng: A seeded numpy random Generator.

    Returns:
        list[float]: Spend amounts in INR, rounded to 2 decimal places.

    Raises:
        KeyError: If a campaign_type is not defined in SPEND_RANGE_BY_TYPE.
    """
    spend_amounts: list[float] = []
    for campaign_type in campaign_types:
        low, high = SPEND_RANGE_BY_TYPE[campaign_type]
        spend_amounts.append(round(float(rng.uniform(low, high)), 2))
    return spend_amounts


def generate_dim_campaign() -> pd.DataFrame:
    """
    Generate the complete dim_campaign table: 65 campaigns spanning the
    reporting window, with realistic channel/type/targeting/spend attributes.

    Returns:
        pd.DataFrame: 65 rows with columns in the exact Phase 3A order:
        campaign_id, campaign_name, campaign_channel, target_segment,
        campaign_type, start_date, end_date, spend_amount, target_region.

    Raises:
        ValueError: If the resulting row count does not match the approved
            count of 65 (config.ROW_COUNTS["dim_campaign"]).
    """
    logger.info("Generating dim_campaign")
    rng = np.random.default_rng(config.RANDOM_SEED)
    Faker.seed(config.RANDOM_SEED)

    total_campaigns = config.ROW_COUNTS["dim_campaign"]

    start_dates, end_dates = _generate_campaign_dates(total_campaigns, rng)
    campaign_ids = _generate_campaign_ids(start_dates)
    campaign_names = _generate_campaign_names(total_campaigns, rng)

    campaign_channels = rng.choice(
        list(CAMPAIGN_CHANNEL_WEIGHTS.keys()), size=total_campaigns,
        p=list(CAMPAIGN_CHANNEL_WEIGHTS.values()),
    )
    campaign_types = rng.choice(
        list(CAMPAIGN_TYPE_WEIGHTS.keys()), size=total_campaigns,
        p=list(CAMPAIGN_TYPE_WEIGHTS.values()),
    )
    target_segments = _generate_target_segments(total_campaigns, rng)
    target_regions = _generate_target_regions(total_campaigns, rng)
    spend_amounts = _generate_spend_amounts(list(campaign_types), rng)

    dim_campaign = pd.DataFrame({
        "campaign_id": campaign_ids,
        "campaign_name": campaign_names,
        "campaign_channel": campaign_channels,
        "target_segment": target_segments,
        "campaign_type": campaign_types,
        "start_date": [d.isoformat() for d in start_dates],
        "end_date": [d.isoformat() for d in end_dates],
        "spend_amount": spend_amounts,
        "target_region": target_regions,
    })

    expected_rows = total_campaigns
    if len(dim_campaign) != expected_rows:
        raise ValueError(
            f"dim_campaign generated {len(dim_campaign)} rows, expected exactly "
            f"{expected_rows} per the Phase 3A approved design."
        )

    logger.info("dim_campaign generation complete: %d rows", len(dim_campaign))
    return dim_campaign


def validate_dim_campaign(dim_campaign: pd.DataFrame) -> None:
    """
    Run structural validation on the generated dim_campaign table before export.

    Args:
        dim_campaign: The DataFrame produced by generate_dim_campaign().

    Returns:
        None. Raises on the first failed check.

    Raises:
        ValueError: If any validation rule fails.
    """
    expected_rows = config.ROW_COUNTS["dim_campaign"]
    if len(dim_campaign) != expected_rows:
        raise ValueError(f"Row count mismatch: expected {expected_rows}, got {len(dim_campaign)}")

    if dim_campaign["campaign_id"].duplicated().any():
        raise ValueError("dim_campaign.campaign_id contains duplicate values; PK uniqueness violated")

    if dim_campaign["campaign_name"].duplicated().any():
        duplicates = dim_campaign.loc[dim_campaign["campaign_name"].duplicated(), "campaign_name"].tolist()
        raise ValueError(f"dim_campaign.campaign_name contains duplicates: {duplicates}")

    if (dim_campaign["spend_amount"] <= 0).any():
        raise ValueError("dim_campaign.spend_amount contains non-positive values")

    start_dates = pd.to_datetime(dim_campaign["start_date"])
    end_dates = pd.to_datetime(dim_campaign["end_date"])
    if (end_dates <= start_dates).any():
        raise ValueError("dim_campaign has rows where end_date is not strictly after start_date")

    min_window = pd.Timestamp(config.DATA_START_DATE)
    max_window = pd.Timestamp(config.DATA_END_DATE)
    if (start_dates < min_window).any() or (end_dates > max_window).any():
        raise ValueError("dim_campaign has campaign dates outside the approved reporting window")

    duration_days = (end_dates - start_dates).dt.days
    min_dur, max_dur = CAMPAIGN_DURATION_DAYS_RANGE
    if (duration_days < min_dur).any() or (duration_days > max_dur).any():
        raise ValueError(
            f"dim_campaign has campaign durations outside the approved "
            f"[{min_dur}, {max_dur}] day range"
        )

    invalid_channels = set(dim_campaign["campaign_channel"].unique()) - set(config.CAMPAIGN_CHANNELS)
    if invalid_channels:
        raise ValueError(f"dim_campaign.campaign_channel contains invalid values: {invalid_channels}")

    invalid_types = set(dim_campaign["campaign_type"].unique()) - set(config.CAMPAIGN_TYPES)
    if invalid_types:
        raise ValueError(f"dim_campaign.campaign_type contains invalid values: {invalid_types}")

    non_null_segments = set(dim_campaign["target_segment"].dropna().unique()) - set(config.CUSTOMER_SEGMENTS)
    if non_null_segments:
        raise ValueError(f"dim_campaign.target_segment contains invalid values: {non_null_segments}")

    non_null_regions = set(dim_campaign["target_region"].dropna().unique()) - set(config.REGIONS)
    if non_null_regions:
        raise ValueError(f"dim_campaign.target_region contains invalid values: {non_null_regions}")

    mandatory_fields = [
        "campaign_id", "campaign_name", "campaign_channel", "campaign_type",
        "start_date", "end_date", "spend_amount",
    ]
    for field in mandatory_fields:
        if dim_campaign[field].isnull().any():
            raise ValueError(f"dim_campaign.{field} contains nulls but is a mandatory field")

    logger.info("dim_campaign validation passed: %d rows, all checks green", len(dim_campaign))


def export_dim_campaign(dim_campaign: pd.DataFrame) -> None:
    """
    Write the dim_campaign DataFrame to data/raw/dim_campaign.csv.

    Args:
        dim_campaign: The validated DataFrame to export.

    Returns:
        None.

    Raises:
        OSError: If the file cannot be written.
    """
    output_path = config.get_output_path("dim_campaign")
    try:
        dim_campaign.to_csv(output_path, index=False)
        logger.info("dim_campaign exported to %s (%d rows)", output_path, len(dim_campaign))
    except OSError:
        logger.exception("Failed to write dim_campaign to %s", output_path)
        raise


def main() -> None:
    """
    Entry point for standalone execution: generate, validate, and export
    dim_campaign.csv. Exits with a non-zero status code on failure.
    """
    logger.info("=== Starting dim_campaign generation (Phase 3B) ===")
    try:
        dim_campaign = generate_dim_campaign()
        validate_dim_campaign(dim_campaign)
        export_dim_campaign(dim_campaign)

        channel_counts = dim_campaign["campaign_channel"].value_counts().to_dict()
        type_counts = dim_campaign["campaign_type"].value_counts().to_dict()
        avg_spend_by_type = dim_campaign.groupby("campaign_type")["spend_amount"].mean().round(0).to_dict()
        national_share = dim_campaign["target_region"].isna().mean()
        all_segment_share = dim_campaign["target_segment"].isna().mean()
        logger.info(
            "Summary: %d total rows | channels=%s | types=%s | avg_spend_by_type=%s | "
            "national=%.1f%% | all_segment=%.1f%%",
            len(dim_campaign), channel_counts, type_counts, avg_spend_by_type,
            national_share * 100, all_segment_share * 100,
        )
        logger.info("=== dim_campaign generation finished successfully ===")
    except Exception:
        logger.exception("dim_campaign generation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
