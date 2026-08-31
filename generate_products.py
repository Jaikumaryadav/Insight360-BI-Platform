"""
generate_products.py
=====================
Generates dim_product.csv — the product/SKU dimension for Insight360.

Implements the Phase 3A approved schema (Section 2.3) exactly:
    product_key, sku_name, division, category, brand, list_price,
    unit_cost, launch_date, is_private_label, is_active, division_price_tier

Grain: 1 row per SKU, 4,200 rows total, distributed across divisions per
config.DIVISION_SKU_SHARE.

All sizing/pricing/margin parameters are sourced from config.py, which
encodes the Phase 3A approved design (category lists, price bands, gross
margin ranges by division). No redesign occurs here. Brand-name pools and
SKU-naming templates are local to this module since Phase 3A specified
only the private-label-vs-external mix, not literal brand/product names.
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
# Local reference data (naming/brand pools — not Phase 3A business-rule
# constants, which live in config.py).
# ---------------------------------------------------------------------------

# One private-label brand per division, per Phase 3A Section 5.6 /
# config.PRIVATE_LABEL_SHARE ("if private label, brand should be one of
# the Meridian brands").
PRIVATE_LABEL_BRAND_BY_DIVISION: Final[dict[str, str]] = {
    "Apparel & Footwear": "Meridian Essentials",
    "Home & Living": "Meridian Home",
    "Electronics & Accessories": "Meridian Tech",
    "Daily Essentials": "Meridian Daily",
}

# Fictional external brand pools per division. All names are invented for
# this project (no real trademarks), consistent with Phase 1's "entirely
# fictional" data mandate.
EXTERNAL_BRANDS_BY_DIVISION: Final[dict[str, list[str]]] = {
    "Apparel & Footwear": [
        "Urban Thread", "Highstreet Co.", "StrideLane", "Northgate Apparel",
        "Vantage Wear", "CasualEdge", "Meadowbrook Clothing", "Trailmark Footwear",
    ],
    "Home & Living": [
        "Casa Bloom", "Hearth & Oak", "Urban Nest", "Comfora",
        "Living Craft", "Homestead Studio", "Nordic Nest Basics", "Kitchen Loft",
    ],
    "Electronics & Accessories": [
        "Pulse Tech", "Nexbyte", "Sonic Wave", "Vortix Electronics",
        "Circuit Edge", "Orbit Gadgets", "ClearTone Audio", "ZenTech",
    ],
    "Daily Essentials": [
        "Purely Fresh", "CleanHome Basics", "NatureCare", "Wellness Root",
        "Freshline", "GentleCare", "HomeGuard Essentials", "VitalDay",
    ],
}

# Representative product-noun phrases per category, used to build sku_name.
# Falls back to a generic "{Category} Item" phrase for any category not
# explicitly listed here, so the generator never breaks if config.py's
# category list is extended later.
CATEGORY_PRODUCT_NOUNS: Final[dict[str, list[str]]] = {
    "Menswear": ["Slim Fit Cotton Shirt", "Casual Trousers", "Polo T-Shirt", "Denim Jacket"],
    "Womenswear": ["A-Line Kurta", "Casual Top", "Formal Blazer", "Printed Saree"],
    "Kidswear": ["Cotton T-Shirt Set", "Denim Dungaree", "School Uniform Shirt", "Winter Jacket"],
    "Footwear": ["Running Shoes", "Formal Leather Shoes", "Casual Sneakers", "Sandals"],
    "Accessories": ["Leather Belt", "Sunglasses", "Wallet", "Wristwatch"],
    "Kitchenware": ["Stainless Steel Cookware Set", "Non-Stick Frying Pan", "Cutlery Set", "Storage Container Set"],
    "Home Decor": ["Wall Art Frame", "Table Lamp", "Decorative Vase", "Wall Clock"],
    "Furnishings": ["Cotton Bedsheet Set", "Curtain Pair", "Cushion Cover Set", "Throw Blanket"],
    "Storage & Organization": ["Wardrobe Organizer", "Storage Box Set", "Shoe Rack", "Multi-Purpose Basket"],
    "Audio": ["Wireless Earbuds", "Bluetooth Speaker", "Over-Ear Headphones", "Soundbar"],
    "Mobile Accessories": ["Phone Case", "Tempered Glass Screen Guard", "Fast Charger", "Power Bank"],
    "Small Appliances": ["Electric Kettle", "Mixer Grinder", "Toaster", "Hand Blender"],
    "Personal Care Tech": ["Electric Trimmer", "Hair Dryer", "Electric Toothbrush", "Smart Fitness Band"],
    "Grocery & Staples": ["Organic Turmeric Powder 200g", "Basmati Rice 5kg", "Cold-Pressed Cooking Oil 1L", "Assorted Pulses Pack"],
    "Personal Care": ["Herbal Shampoo 340ml", "Moisturizing Body Lotion", "Face Wash 100g", "Toothpaste Combo Pack"],
    "Household Supplies": ["Multi-Surface Cleaner 500ml", "Dishwash Liquid 750ml", "Laundry Detergent 1kg", "Air Freshener"],
}

# Apparel/footwear size variants, used to add realism to sku_name.
APPAREL_SIZES: Final[list[str]] = ["XS", "S", "M", "L", "XL", "XXL"]
FOOTWEAR_SIZES: Final[list[str]] = [str(size) for size in range(6, 12)]

# Launch-date split: most SKUs predate the reporting window (existing
# catalog), a smaller share launch during it (new SKUs), giving Phase 8
# a genuine new-vs-existing SKU population for cannibalization analysis.
PRE_WINDOW_LAUNCH_SHARE: Final[float] = 0.85
PRE_WINDOW_LAUNCH_START: Final[date] = date(2015, 1, 1)

# Discontinuation rate: only a small share of SKUs are inactive.
DISCONTINUED_RATE_RANGE: Final[tuple[float, float]] = (0.03, 0.06)

# Price tier distribution (not specified numerically in Phase 1/3A, so
# defined locally): most of the catalog sits in Value/Mid, a smaller
# Premium tail, consistent with a general-merchandise retailer.
PRICE_TIER_WEIGHTS: Final[dict[str, float]] = {"Value": 0.42, "Mid": 0.40, "Premium": 0.18}

_faker = Faker("en_IN")


def _allocate_counts(total: int, weights: dict[str, float]) -> dict[str, int]:
    """
    Allocate an integer total across categories proportionally to `weights`,
    using the largest-remainder method so allocated counts sum exactly to total.

    Args:
        total: The total count to allocate (e.g., 4200 SKUs).
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

    remainders = sorted(raw_shares.keys(), key=lambda k: raw_shares[k] - floored[k], reverse=True)
    for key in remainders[:remainder]:
        floored[key] += 1

    return floored


def _assign_price_tier(rng: np.random.Generator) -> str:
    """
    Randomly draw a price tier according to PRICE_TIER_WEIGHTS.

    Args:
        rng: A seeded numpy random Generator.

    Returns:
        str: One of "Value", "Mid", "Premium".
    """
    tiers = list(PRICE_TIER_WEIGHTS.keys())
    probabilities = list(PRICE_TIER_WEIGHTS.values())
    return str(rng.choice(tiers, p=probabilities))


def _generate_list_price(division: str, tier: str, rng: np.random.Generator) -> float:
    """
    Draw a list price for a given division/tier combination from the
    approved config.LIST_PRICE_RANGE band, rounded to a realistic
    retail price ending in 9 or 99 (common Indian retail pricing pattern).

    Args:
        division: The product's division.
        tier: The product's price tier ("Value"/"Mid"/"Premium").
        rng: A seeded numpy random Generator.

    Returns:
        float: A list price in INR, > 0.

    Raises:
        KeyError: If division/tier is not defined in config.LIST_PRICE_RANGE.
    """
    low, high = config.LIST_PRICE_RANGE[division][tier]
    raw_price = rng.uniform(low, high)
    # Round to nearest 10, then subtract 1 for a "...99" ending — a common,
    # realistic Indian retail pricing convention.
    rounded = round(raw_price / 10) * 10 - 1
    return float(max(low, rounded))


def _generate_unit_cost(division: str, list_price: float, rng: np.random.Generator) -> float:
    """
    Derive unit_cost from list_price using the approved division gross
    margin range, guaranteeing 0 < unit_cost < list_price.

    Args:
        division: The product's division.
        list_price: The product's list price (must be > 0).
        rng: A seeded numpy random Generator.

    Returns:
        float: unit_cost in INR, strictly between 0 and list_price.

    Raises:
        ValueError: If list_price is not positive.
    """
    if list_price <= 0:
        raise ValueError(f"list_price must be positive, got {list_price}")

    margin_low, margin_high = config.GROSS_MARGIN_RANGE_BY_DIVISION[division]
    gross_margin = rng.uniform(margin_low, margin_high)
    unit_cost = list_price * (1 - gross_margin)
    # Round to 2 decimal places, then clamp to guarantee the strict
    # inequality even after rounding.
    unit_cost = round(unit_cost, 2)
    return min(unit_cost, round(list_price - 0.01, 2)) if unit_cost > 0 else 0.01


def _generate_launch_date(rng: np.random.Generator) -> date:
    """
    Generate a launch date, biased toward pre-window (existing catalog)
    per PRE_WINDOW_LAUNCH_SHARE, with the remainder launching during the
    reporting window (new SKUs).

    Args:
        rng: A seeded numpy random Generator.

    Returns:
        date: A launch date between PRE_WINDOW_LAUNCH_START and
        config.DATA_END_DATE.
    """
    if rng.random() < PRE_WINDOW_LAUNCH_SHARE:
        start, end = PRE_WINDOW_LAUNCH_START, config.DATA_START_DATE - timedelta(days=1)
    else:
        start, end = config.DATA_START_DATE, config.DATA_END_DATE

    span_days = (end - start).days
    offset = int(rng.integers(0, span_days + 1))
    return start + timedelta(days=offset)


def _generate_sku_name(division: str, category: str, rng: np.random.Generator) -> str:
    """
    Build a realistic SKU display name from a category-appropriate noun
    phrase plus a division-appropriate variant tag (color/size for
    apparel & footwear, color for other divisions).

    Args:
        division: The product's division.
        category: The product's category.
        rng: A seeded numpy random Generator.

    Returns:
        str: e.g. "Slim Fit Cotton Shirt — Navy, L" or
        "Wireless Earbuds — Black".
    """
    noun_phrases = CATEGORY_PRODUCT_NOUNS.get(category, [f"{category} Item"])
    noun_phrase = str(rng.choice(noun_phrases))
    color = _faker.safe_color_name().title()

    if category == "Footwear":
        size = str(rng.choice(FOOTWEAR_SIZES))
        return f"{noun_phrase} \u2014 {color}, UK {size}"
    if division == "Apparel & Footwear" and category != "Accessories":
        size = str(rng.choice(APPAREL_SIZES))
        return f"{noun_phrase} \u2014 {color}, {size}"
    return f"{noun_phrase} \u2014 {color}"


def _generate_division_records(division: str, count: int, rng: np.random.Generator) -> list[dict]:
    """
    Generate `count` product records for a single division.

    Args:
        division: The division these records belong to.
        count: Number of SKUs to generate for this division.
        rng: A seeded numpy random Generator.

    Returns:
        list[dict]: `count` product records (product_key assigned later
        by the caller), columns matching the Phase 3A dim_product schema.

    Raises:
        ValueError: If division is not a recognized config.DIVISIONS entry.
    """
    if division not in config.DIVISIONS:
        raise ValueError(f"Unknown division '{division}'")

    categories = config.CATEGORIES_BY_DIVISION[division]
    external_brands = EXTERNAL_BRANDS_BY_DIVISION[division]
    private_label_brand = PRIVATE_LABEL_BRAND_BY_DIVISION[division]

    discontinued_rate = rng.uniform(*DISCONTINUED_RATE_RANGE)

    records: list[dict] = []
    for _ in range(count):
        category = str(rng.choice(categories))
        is_private_label = bool(rng.random() < config.PRIVATE_LABEL_SHARE)
        brand = private_label_brand if is_private_label else str(rng.choice(external_brands))

        tier = _assign_price_tier(rng)
        list_price = _generate_list_price(division, tier, rng)
        unit_cost = _generate_unit_cost(division, list_price, rng)
        launch_date_value = _generate_launch_date(rng)
        is_active = bool(rng.random() >= discontinued_rate)
        sku_name = _generate_sku_name(division, category, rng)

        records.append({
            "sku_name": sku_name,
            "division": division,
            "category": category,
            "brand": brand,
            "list_price": list_price,
            "unit_cost": unit_cost,
            "launch_date": launch_date_value.isoformat(),
            "is_private_label": is_private_label,
            "is_active": is_active,
            "division_price_tier": tier,
        })

    logger.info(
        "Generated %d records for division '%s' (discontinued rate: %.2f%%)",
        len(records), division, discontinued_rate * 100,
    )
    return records


def generate_dim_product() -> pd.DataFrame:
    """
    Generate the complete dim_product table: 4,200 SKUs distributed across
    the four Meridian divisions per config.DIVISION_SKU_SHARE.

    Returns:
        pd.DataFrame: 4,200 rows with columns in the exact Phase 3A order:
        product_key, sku_name, division, category, brand, list_price,
        unit_cost, launch_date, is_private_label, is_active, division_price_tier.

    Raises:
        ValueError: If the resulting row count does not match the approved
            count of 4200 (config.ROW_COUNTS["dim_product"]).
    """
    logger.info("Generating dim_product")
    rng = np.random.default_rng(config.RANDOM_SEED)
    Faker.seed(config.RANDOM_SEED)

    total_skus = config.ROW_COUNTS["dim_product"]
    division_counts = _allocate_counts(total_skus, config.DIVISION_SKU_SHARE)
    logger.info("Division SKU allocation: %s", division_counts)

    all_records: list[dict] = []
    for division, count in division_counts.items():
        all_records.extend(_generate_division_records(division, count, rng))

    for product_key, record in enumerate(all_records, start=1):
        record["product_key"] = product_key

    column_order = [
        "product_key", "sku_name", "division", "category", "brand",
        "list_price", "unit_cost", "launch_date", "is_private_label",
        "is_active", "division_price_tier",
    ]
    dim_product = pd.DataFrame.from_records(all_records)[column_order]

    expected_rows = total_skus
    if len(dim_product) != expected_rows:
        raise ValueError(
            f"dim_product generated {len(dim_product)} rows, expected exactly "
            f"{expected_rows} per the Phase 3A approved design."
        )

    logger.info("dim_product generation complete: %d rows", len(dim_product))
    return dim_product


def validate_dim_product(dim_product: pd.DataFrame) -> None:
    """
    Run structural validation on the generated dim_product table before export.

    Args:
        dim_product: The DataFrame produced by generate_dim_product().

    Returns:
        None. Raises on the first failed check.

    Raises:
        ValueError: If any validation rule fails.
    """
    expected_rows = config.ROW_COUNTS["dim_product"]
    if len(dim_product) != expected_rows:
        raise ValueError(f"Row count mismatch: expected {expected_rows}, got {len(dim_product)}")

    if dim_product["product_key"].duplicated().any():
        raise ValueError("dim_product.product_key contains duplicate values; PK uniqueness violated")

    invalid_divisions = set(dim_product["division"].unique()) - set(config.DIVISIONS)
    if invalid_divisions:
        raise ValueError(f"dim_product.division contains invalid values: {invalid_divisions}")

    # Valid division/category combinations.
    invalid_combo_rows = dim_product[
        dim_product.apply(
            lambda row: row["category"] not in config.CATEGORIES_BY_DIVISION[row["division"]], axis=1
        )
    ]
    if not invalid_combo_rows.empty:
        raise ValueError(
            f"dim_product has {len(invalid_combo_rows)} row(s) with an invalid "
            f"division/category combination"
        )

    if (dim_product["unit_cost"] <= 0).any():
        raise ValueError("dim_product.unit_cost contains non-positive values")

    if (dim_product["list_price"] <= 0).any():
        raise ValueError("dim_product.list_price contains non-positive values")

    if (dim_product["unit_cost"] >= dim_product["list_price"]).any():
        raise ValueError("dim_product has rows where unit_cost >= list_price")

    min_launch = pd.Timestamp(PRE_WINDOW_LAUNCH_START)
    max_launch = pd.Timestamp(config.DATA_END_DATE)
    launch_dates = pd.to_datetime(dim_product["launch_date"])
    if (launch_dates < min_launch).any() or (launch_dates > max_launch).any():
        raise ValueError(
            f"dim_product.launch_date contains values outside [{min_launch.date()}, {max_launch.date()}]"
        )

    # Private-label logic: is_private_label True implies brand is a Meridian brand.
    meridian_brands = set(PRIVATE_LABEL_BRAND_BY_DIVISION.values())
    private_label_rows = dim_product[dim_product["is_private_label"]]
    if not private_label_rows.empty and not private_label_rows["brand"].isin(meridian_brands).all():
        raise ValueError("dim_product has is_private_label=True rows with a non-Meridian brand")

    non_private_label_rows = dim_product[~dim_product["is_private_label"]]
    if not non_private_label_rows.empty and non_private_label_rows["brand"].isin(meridian_brands).any():
        raise ValueError("dim_product has is_private_label=False rows using a Meridian private-label brand")

    valid_tiers = set(config.PRICE_TIERS)
    invalid_tiers = set(dim_product["division_price_tier"].unique()) - valid_tiers
    if invalid_tiers:
        raise ValueError(f"dim_product.division_price_tier contains invalid values: {invalid_tiers}")

    mandatory_fields = [
        "product_key", "sku_name", "division", "category", "brand", "list_price",
        "unit_cost", "launch_date", "is_private_label", "is_active", "division_price_tier",
    ]
    for field in mandatory_fields:
        if dim_product[field].isnull().any():
            raise ValueError(f"dim_product.{field} contains nulls but is a mandatory field")

    logger.info("dim_product validation passed: %d rows, all checks green", len(dim_product))


def export_dim_product(dim_product: pd.DataFrame) -> None:
    """
    Write the dim_product DataFrame to data/raw/dim_product.csv.

    Args:
        dim_product: The validated DataFrame to export.

    Returns:
        None.

    Raises:
        OSError: If the file cannot be written.
    """
    output_path = config.get_output_path("dim_product")
    try:
        dim_product.to_csv(output_path, index=False)
        logger.info("dim_product exported to %s (%d rows)", output_path, len(dim_product))
    except OSError:
        logger.exception("Failed to write dim_product to %s", output_path)
        raise


def main() -> None:
    """
    Entry point for standalone execution: generate, validate, and export
    dim_product.csv. Exits with a non-zero status code on failure.
    """
    logger.info("=== Starting dim_product generation (Phase 3B) ===")
    try:
        dim_product = generate_dim_product()
        validate_dim_product(dim_product)
        export_dim_product(dim_product)

        division_counts = dim_product["division"].value_counts().to_dict()
        tier_counts = dim_product["division_price_tier"].value_counts().to_dict()
        private_label_share = dim_product["is_private_label"].mean()
        active_share = dim_product["is_active"].mean()
        logger.info(
            "Summary: %d total rows | divisions=%s | tiers=%s | "
            "private_label=%.1f%% | active=%.1f%%",
            len(dim_product), division_counts, tier_counts,
            private_label_share * 100, active_share * 100,
        )
        logger.info("=== dim_product generation finished successfully ===")
    except Exception:
        logger.exception("dim_product generation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
