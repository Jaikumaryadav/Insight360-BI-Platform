"""
config.py
=========
Central configuration module for the Insight360 synthetic data generation
pipeline (Meridian Retail Group).

This module contains ONLY constants and static configuration objects.
It performs no data generation itself. Every generation module
(generate_dates.py, generate_stores.py, etc.) imports from here so that
business-rule parameters (row counts, fiscal calendar, discount bands,
seasonality curves, etc.) are defined exactly once, per the Phase 3A
approved design.

No redesign decisions are made in this file — every constant below maps
directly to a specific section of the approved Phase 3A document.
"""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path
from typing import Final

# ---------------------------------------------------------------------------
# 1. PROJECT PATHS
# ---------------------------------------------------------------------------
# BASE_DIR resolves to the insight360/ project root regardless of which
# directory a script is invoked from, since it is derived from this file's
# own location rather than the current working directory.
BASE_DIR: Final[Path] = Path(__file__).resolve().parent.parent
DATA_DIR: Final[Path] = BASE_DIR / "data"
RAW_DATA_DIR: Final[Path] = DATA_DIR / "raw"
LOG_DIR: Final[Path] = BASE_DIR / "logs"

# Ensure required directories exist at import time. This is intentionally
# idempotent (exist_ok=True) so re-running any module never fails due to
# directories already being present.
for _directory in (DATA_DIR, RAW_DATA_DIR, LOG_DIR):
    _directory.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# 2. OUTPUT FILE NAMES (Phase 3A Section 1 — Dataset Inventory)
# ---------------------------------------------------------------------------
OUTPUT_FILENAMES: Final[dict[str, str]] = {
    "dim_date": "dim_date.csv",
    "dim_store": "dim_store.csv",
    "dim_product": "dim_product.csv",
    "dim_customer": "dim_customer.csv",
    "dim_campaign": "dim_campaign.csv",
    "fact_sales": "fact_sales.csv",
    "fact_returns": "fact_returns.csv",
    "fact_inventory_snapshot": "fact_inventory_snapshot.csv",
    "fact_staffing": "fact_staffing.csv",
}


def get_output_path(table_name: str) -> Path:
    """
    Resolve the full output path for a given approved table name.

    Args:
        table_name: One of the keys in OUTPUT_FILENAMES (e.g. "dim_date").

    Returns:
        Path: Full path to the CSV file under data/raw/.

    Raises:
        KeyError: If table_name is not a recognized Phase 3A dataset.
    """
    if table_name not in OUTPUT_FILENAMES:
        raise KeyError(
            f"'{table_name}' is not an approved Phase 3A dataset. "
            f"Valid names: {sorted(OUTPUT_FILENAMES.keys())}"
        )
    return RAW_DATA_DIR / OUTPUT_FILENAMES[table_name]


# ---------------------------------------------------------------------------
# 3. REPRODUCIBILITY
# ---------------------------------------------------------------------------
# A fixed seed ensures every module produces identical output across runs,
# which matters for validators.py (Phase 3C) and for anyone re-running the
# pipeline from the public GitHub repo and expecting matching results.
RANDOM_SEED: Final[int] = 42

# ---------------------------------------------------------------------------
# 4. APPROVED ROW COUNTS (Phase 3A Section 1 / Section 6 — exact, not ranges)
# ---------------------------------------------------------------------------
ROW_COUNTS: Final[dict[str, int]] = {
    "dim_date": 730,
    "dim_store": 216,
    "dim_product": 4200,
    "dim_customer": 850000,
    "dim_campaign": 65,
    "fact_sales": 4200000,
    "fact_returns": 220000,
    "fact_inventory_snapshot": 970000,
    "fact_staffing": 11128,
}

# ---------------------------------------------------------------------------
# 5. FISCAL CALENDAR (Phase 3A Section 2.1 — dim_date)
# ---------------------------------------------------------------------------
# Meridian's fiscal year runs April -> March. Two fiscal years are generated
# to support Year-over-Year comparisons: FY2025 (prior-year baseline) and
# FY2026 (current year). Together these span exactly 730 days.
FISCAL_YEAR_START_MONTH: Final[int] = 4  # April

# Prior-year baseline window (FY2025): Apr 1, 2024 -> Mar 31, 2025
PRIOR_FISCAL_YEAR_LABEL: Final[int] = 2025
PRIOR_FISCAL_YEAR_START: Final[date] = date(2024, 4, 1)
PRIOR_FISCAL_YEAR_END: Final[date] = date(2025, 3, 31)

# Current fiscal year window (FY2026): Apr 1, 2025 -> Mar 31, 2026
CURRENT_FISCAL_YEAR_LABEL: Final[int] = 2026
CURRENT_FISCAL_YEAR_START: Final[date] = date(2025, 4, 1)
CURRENT_FISCAL_YEAR_END: Final[date] = date(2026, 3, 31)

# Overall generation window used by every module that needs a date bound.
DATA_START_DATE: Final[date] = PRIOR_FISCAL_YEAR_START
DATA_END_DATE: Final[date] = CURRENT_FISCAL_YEAR_END

# ---------------------------------------------------------------------------
# 6. FESTIVE / EOSS CALENDAR (Phase 3A Section 5.2)
# ---------------------------------------------------------------------------
# Each entry defines a recurring festive window by (month, day) start/end.
# "wraps_year" = True indicates the window crosses a calendar year boundary
# (e.g., Year-End/New Year Sale runs Dec 24 -> Jan 2), which the date
# generator must expand carefully across both affected calendar years.
FESTIVE_WINDOWS: Final[list[dict]] = [
    {
        "name": "Republic Day Sale",
        "start_month": 1, "start_day": 15,
        "end_month": 1, "end_day": 26,
        "wraps_year": False,
        "demand_multiplier_range": (2.2, 2.6),
    },
    {
        "name": "Summer EOSS",
        "start_month": 6, "start_day": 1,
        "end_month": 6, "end_day": 15,
        "wraps_year": False,
        "demand_multiplier_range": (2.2, 2.6),
    },
    {
        "name": "Independence Day Sale",
        "start_month": 8, "start_day": 10,
        "end_month": 8, "end_day": 16,
        "wraps_year": False,
        "demand_multiplier_range": (2.3, 2.7),
    },
    {
        "name": "Diwali Festive Season",
        "start_month": 10, "start_day": 10,
        "end_month": 11, "end_day": 5,
        "wraps_year": False,
        "demand_multiplier_range": (2.8, 3.5),
    },
    {
        "name": "Year-End New Year Sale",
        "start_month": 12, "start_day": 24,
        "end_month": 1, "end_day": 2,
        "wraps_year": True,
        "demand_multiplier_range": (2.2, 2.6),
    },
]

# ---------------------------------------------------------------------------
# 7. REGIONS, STORE FORMATS, CHANNELS (Phase 3A Section 2.2 — dim_store)
# ---------------------------------------------------------------------------
REGIONS: Final[list[str]] = ["North", "South", "East", "West"]

STORE_FORMATS: Final[list[str]] = ["Flagship", "Express", "Outlet", "Online", "Wholesale"]
PHYSICAL_STORE_FORMATS: Final[list[str]] = ["Flagship", "Express", "Outlet"]
VIRTUAL_STORE_FORMATS: Final[list[str]] = ["Online", "Wholesale"]

CHANNELS: Final[list[str]] = ["Store", "Online", "Wholesale"]

# Physical store counts by format, fixed to sum to 214 (Phase 1 Section 4.1).
STORE_FORMAT_COUNTS: Final[dict[str, int]] = {
    "Flagship": 50,
    "Express": 120,
    "Outlet": 44,
}

# Assortment size (active SKUs stocked) by format, used by dim_store and
# fact_inventory_snapshot (Phase 3A Section 2.2 / 5.8).
ASSORTMENT_SIZE_BY_FORMAT: Final[dict[str, int]] = {
    "Flagship": 1500,
    "Express": 600,
    "Outlet": 400,
    "Online": 4200,   # full assortment, split across 3 regional DCs
    "Wholesale": 2000,
}

ONLINE_DISTRIBUTION_CENTER_COUNT: Final[int] = 3

# Square footage bands by physical format (min, max), used to generate
# realistic sqft values (Phase 3A Section 2.2, sqft validation rule).
SQFT_RANGE_BY_FORMAT: Final[dict[str, tuple[int, int]]] = {
    "Flagship": (12000, 25000),
    "Express": (3000, 8000),
    "Outlet": (800, 2500),
}

# East region is deliberately calibrated to underperform (Phase 3A Section 5.5).
UNDERPERFORMING_REGION: Final[str] = "East"
REGION_REVENUE_INDEX: Final[dict[str, float]] = {
    # Relative revenue-per-store index; 1.00 = North/South/West average baseline.
    "North": 1.04,
    "South": 1.06,
    "West": 0.98,
    "East": 0.88,   # 8-12% lower, per Section 5.5
}
REGION_MARGIN_BPS_ADJUSTMENT: Final[dict[str, float]] = {
    # Basis-point adjustment applied to baseline gross margin %.
    "North": 0.0,
    "South": 20.0,
    "West": -10.0,
    "East": -185.0,  # 150-220 bps lower, per Section 5.5 (midpoint used)
}

# ---------------------------------------------------------------------------
# 8. PRODUCT HIERARCHY (Phase 3A Section 2.3 — dim_product)
# ---------------------------------------------------------------------------
DIVISIONS: Final[list[str]] = [
    "Apparel & Footwear",
    "Home & Living",
    "Electronics & Accessories",
    "Daily Essentials",
]

CATEGORIES_BY_DIVISION: Final[dict[str, list[str]]] = {
    "Apparel & Footwear": ["Menswear", "Womenswear", "Kidswear", "Footwear", "Accessories"],
    "Home & Living": ["Kitchenware", "Home Decor", "Furnishings", "Storage & Organization"],
    "Electronics & Accessories": ["Audio", "Mobile Accessories", "Small Appliances", "Personal Care Tech"],
    "Daily Essentials": ["Grocery & Staples", "Personal Care", "Household Supplies"],
}

PRICE_TIERS: Final[list[str]] = ["Value", "Mid", "Premium"]

# Approximate division share of total SKU count (must sum to 1.0).
DIVISION_SKU_SHARE: Final[dict[str, float]] = {
    "Apparel & Footwear": 0.38,
    "Home & Living": 0.27,
    "Electronics & Accessories": 0.17,
    "Daily Essentials": 0.18,
}

# List price bands (INR) by division and tier: (min_price, max_price).
LIST_PRICE_RANGE: Final[dict[str, dict[str, tuple[float, float]]]] = {
    "Apparel & Footwear": {"Value": (299, 799), "Mid": (800, 1999), "Premium": (2000, 5999)},
    "Home & Living": {"Value": (199, 999), "Mid": (1000, 3499), "Premium": (3500, 12999)},
    "Electronics & Accessories": {"Value": (299, 1499), "Mid": (1500, 4999), "Premium": (5000, 24999)},
    "Daily Essentials": {"Value": (49, 299), "Mid": (300, 799), "Premium": (800, 1999)},
}

# Gross margin % band by division, used to derive unit_cost from list_price.
# Electronics & Accessories is the thinnest-margin division per Phase 3A 5.6.
GROSS_MARGIN_RANGE_BY_DIVISION: Final[dict[str, tuple[float, float]]] = {
    "Apparel & Footwear": (0.42, 0.55),
    "Home & Living": (0.38, 0.50),
    "Electronics & Accessories": (0.18, 0.30),
    "Daily Essentials": (0.22, 0.34),
}

PRIVATE_LABEL_SHARE: Final[float] = 0.30

# ---------------------------------------------------------------------------
# 9. CUSTOMER SEGMENTS (Phase 3A Section 2.4 — dim_customer / Section 5.4)
# ---------------------------------------------------------------------------
CUSTOMER_SEGMENTS: Final[list[str]] = ["Value Shopper", "Premium Shopper", "Digital Native"]

CUSTOMER_SEGMENT_SHARE: Final[dict[str, float]] = {
    "Value Shopper": 0.45,
    "Premium Shopper": 0.25,
    "Digital Native": 0.30,
}

ACQUISITION_CHANNELS: Final[list[str]] = [
    "Organic Walk-in", "Digital Ads Campaign", "Referral", "Email/SMS Campaign",
]

# Loyalty penetration trajectory: starts near 48%, trends toward but does not
# fully reach 70% by fiscal year-end (Phase 3A Section 5.4).
LOYALTY_PENETRATION_START: Final[float] = 0.48
LOYALTY_PENETRATION_END: Final[float] = 0.63

# ---------------------------------------------------------------------------
# 10. CAMPAIGNS (Phase 3A Section 2.5 — dim_campaign)
# ---------------------------------------------------------------------------
CAMPAIGN_CHANNELS: Final[list[str]] = ["Email", "SMS", "Digital Ads", "In-Store"]
CAMPAIGN_TYPES: Final[list[str]] = ["Acquisition", "Retention", "Brand"]
CAMPAIGN_SPEND_RANGE: Final[tuple[float, float]] = (150000.0, 2500000.0)

# ---------------------------------------------------------------------------
# 11. SALES / DISCOUNT STRATEGY (Phase 3A Section 2.6 / Section 5.6)
# ---------------------------------------------------------------------------
# Baseline (non-festive) discount rate range by division.
BASELINE_DISCOUNT_RANGE_BY_DIVISION: Final[dict[str, tuple[float, float]]] = {
    "Apparel & Footwear": (0.12, 0.18),
    "Home & Living": (0.08, 0.14),
    "Electronics & Accessories": (0.05, 0.10),
    "Daily Essentials": (0.02, 0.06),
}

# Additional percentage-point uplift applied during festive windows.
FESTIVE_DISCOUNT_UPLIFT_PP_BY_DIVISION: Final[dict[str, tuple[float, float]]] = {
    "Apparel & Footwear": (0.10, 0.15),
    "Home & Living": (0.08, 0.13),
    "Electronics & Accessories": (0.08, 0.12),
    "Daily Essentials": (0.08, 0.10),
}

DISCOUNT_MARGIN_ACCELERATION_THRESHOLD: Final[float] = 0.25  # 25% discount depth

# Weekend / weekday demand multipliers by channel (Phase 3A Section 5.3).
WEEKEND_MULTIPLIER_BY_CHANNEL: Final[dict[str, tuple[float, float]]] = {
    "Store": (1.4, 1.7),
    "Online": (1.1, 1.2),
    "Wholesale": (0.05, 0.15),  # near-zero weekend floor
}

# Wholesale bulk order quantity tiers: (min_qty, max_qty).
WHOLESALE_QUANTITY_RANGE: Final[tuple[int, int]] = (25, 500)
RETAIL_QUANTITY_RANGE: Final[tuple[int, int]] = (1, 5)

# ---------------------------------------------------------------------------
# 12. RETURNS (Phase 3A Section 2.7 / Section 5.7)
# ---------------------------------------------------------------------------
RETURN_REASONS: Final[list[str]] = ["Size/Fit", "Defective", "Changed Mind", "Not as Described", "Other"]

# Base return rate (of units sold) by channel; Online skews 1.6x-2.0x Store.
RETURN_RATE_BY_CHANNEL: Final[dict[str, float]] = {
    "Store": 0.040,
    "Online": 0.075,
    "Wholesale": 0.003,
}

RETURN_LAG_MAX_DAYS: Final[int] = 30
RETURN_LAG_CONCENTRATION_DAYS: Final[int] = 14  # right-skew concentration window

# Dominant return reason by division (used to weight the reason distribution).
DOMINANT_RETURN_REASON_BY_DIVISION: Final[dict[str, str]] = {
    "Apparel & Footwear": "Size/Fit",
    "Electronics & Accessories": "Defective",
    "Home & Living": "Changed Mind",
    "Daily Essentials": "Changed Mind",
}

# ---------------------------------------------------------------------------
# 13. INVENTORY (Phase 3A Section 2.8 / Section 5.8)
# ---------------------------------------------------------------------------
INVENTORY_CYCLE_COUNT_SAMPLE_RATE: Final[float] = 0.10  # ~10% of assortment/week
INVENTORY_TRIGGER_TOPUP_ROWS: Final[int] = 38000  # low-stock/near-reorder top-up

LEAD_TIME_DAYS_BY_DIVISION: Final[dict[str, tuple[int, int]]] = {
    "Apparel & Footwear": (5, 9),
    "Home & Living": (6, 10),
    "Electronics & Accessories": (8, 12),
    "Daily Essentials": (5, 8),
}

# Elevated stockout incidence in East region and Electronics division
# (Phase 3A Section 5.8) — expressed as a probability multiplier applied to
# the baseline stockout probability.
STOCKOUT_MULTIPLIER_BY_REGION: Final[dict[str, float]] = {
    "North": 1.0, "South": 1.0, "West": 1.05, "East": 1.6,
}
STOCKOUT_MULTIPLIER_BY_DIVISION: Final[dict[str, float]] = {
    "Apparel & Footwear": 1.0,
    "Home & Living": 1.0,
    "Electronics & Accessories": 1.5,
    "Daily Essentials": 0.8,
}
BASELINE_STOCKOUT_PROBABILITY: Final[float] = 0.06

# ---------------------------------------------------------------------------
# 14. STAFFING (Phase 3A Section 2.9)
# ---------------------------------------------------------------------------
HEADCOUNT_RANGE_BY_FORMAT: Final[dict[str, tuple[int, int]]] = {
    "Flagship": (22, 40),
    "Express": (10, 20),
    "Outlet": (5, 12),
}
AVG_WEEKLY_HOURS_PER_STAFF_RANGE: Final[tuple[float, float]] = (30.0, 42.0)
FESTIVE_OVERTIME_MULTIPLIER: Final[tuple[float, float]] = (1.8, 2.6)
BASELINE_OVERTIME_HOURS_RATIO: Final[tuple[float, float]] = (0.02, 0.06)  # share of total hours

# ---------------------------------------------------------------------------
# 15. LOGGING
# ---------------------------------------------------------------------------
LOG_FORMAT: Final[str] = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"


def get_logger(module_name: str) -> logging.Logger:
    """
    Create (or retrieve) a configured logger for a generation module.

    Each logger writes to both the console and a shared pipeline log file
    under logs/, using a consistent format so that Phase 3B's console output
    and the persisted log file tell the same story.

    Args:
        module_name: Typically __name__ of the calling module, used as the
            logger name so log lines are traceable to their source module.

    Returns:
        logging.Logger: A configured logger instance. Safe to call multiple
        times for the same module_name without creating duplicate handlers.
    """
    logger = logging.getLogger(module_name)

    # Guard against duplicate handlers if get_logger() is called more than
    # once for the same module (e.g., re-imports during interactive use).
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    try:
        file_handler = logging.FileHandler(LOG_DIR / "insight360_pipeline.log", encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError as exc:
        # If the log file cannot be created (e.g., read-only filesystem),
        # fall back to console-only logging rather than crashing generation.
        logger.warning("Could not attach file handler for logging: %s", exc)

    logger.propagate = False
    return logger
