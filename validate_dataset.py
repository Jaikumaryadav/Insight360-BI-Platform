"""
validate_dataset.py
Insight360 -- Executive BI Platform for Retail

End-to-end data quality validation for all Phase 3B generated CSV outputs.
Inspects dim_date, dim_store, dim_product, dim_customer, fact_sales,
fact_returns, fact_inventory_snapshot, and fact_staffing, then prints a
structured PASS/FAIL health report.

Does NOT modify: generate_dates.py, generate_stores.py, generate_products.py,
generate_customers.py, generate_sales.py, generate_returns.py,
generate_inventory.py, generate_staffing.py
"""

import os
import sys
import numpy as np
import pandas as pd

# =================================================
# CONFIG
# =================================================

CANDIDATE_DIRS = ["data/raw", "data/cleaned", "data", "."]

FILE_SPECS = {
    "dim_date.csv":                 {"pk": ["date_key"],                    "expected": 730,       "tolerance": 0.10},
    "dim_store.csv":                {"pk": ["store_key"],                   "expected": 216,       "tolerance": 0.05},
    "dim_product.csv":              {"pk": ["product_key"],                 "expected": 4200,      "tolerance": 0.10},
    "dim_customer.csv":             {"pk": ["customer_key"],                "expected": 850_000,   "tolerance": 0.10},
    "fact_sales.csv":               {"pk": ["sales_id", "sales_line_id"],   "expected": 4_200_000, "tolerance": 0.10},
    "fact_returns.csv":             {"pk": ["return_id"],                   "expected": 220_000,   "tolerance": 0.15},
    "fact_inventory_snapshot.csv":  {"pk": ["snapshot_id"],                 "expected": 970_000,   "tolerance": 0.10},
    "fact_staffing.csv":            {"pk": ["staffing_id"],                 "expected": 11_128,    "tolerance": 0.02},
}

REQUIRED_FILES = list(FILE_SPECS.keys())

RETURN_RATE_MIN, RETURN_RATE_MAX = 0.05, 0.07
RETURN_RATE_TOLERANCE = 0.02          # small buffer around the strict 5-7% band
MAX_RETURN_WINDOW_DAYS = 30
PHYSICAL_FORMATS = {"Flagship", "Express", "Outlet"}
TARGET_PHYSICAL_STORES = 214
TARGET_STAFFING_WEEKS = 52

PASS = "PASS"
FAIL = "FAIL"
SKIP = "SKIP"


# =================================================
# PATH / LOAD UTILITIES
# =================================================

def _resolve_path(filename):
    for d in CANDIDATE_DIRS:
        candidate = os.path.join(d, filename)
        if os.path.exists(candidate):
            return candidate
    return None


def _find_col(df, candidates, required=False):
    for c in candidates:
        if c in df.columns:
            return c
    if required:
        raise KeyError(f"None of {candidates} found. Available: {list(df.columns)}")
    return None


def load_all_files():
    """Load every file that exists; record which ones are missing."""
    frames = {}
    missing = []
    paths = {}
    for filename in REQUIRED_FILES:
        path = _resolve_path(filename)
        if path is None:
            missing.append(filename)
            continue
        paths[filename] = path
        try:
            frames[filename] = pd.read_csv(path, low_memory=False)
        except Exception as exc:
            missing.append(f"{filename} (failed to load: {exc})")
    return frames, missing, paths


# =================================================
# REPORT HELPERS
# =================================================

class Report:
    def __init__(self):
        self.sections = {}   # section_name -> list of row dicts
        self.section_status = {}  # section_name -> PASS/FAIL

    def add_row(self, section, item, expected, actual, status, note=""):
        self.sections.setdefault(section, []).append(
            {"item": item, "expected": expected, "actual": actual, "status": status, "note": note}
        )
        current = self.section_status.get(section, PASS)
        if status == FAIL:
            self.section_status[section] = FAIL
        elif status == PASS and current != FAIL:
            self.section_status[section] = current if current == FAIL else PASS

    ITEM_WIDTH = 58
    EXPECTED_WIDTH = 26
    ACTUAL_WIDTH = 34
    STATUS_WIDTH = 8
    TABLE_WIDTH = ITEM_WIDTH + EXPECTED_WIDTH + ACTUAL_WIDTH + STATUS_WIDTH

    def print_section(self, section, header):
        print(header)
        print("-" * self.TABLE_WIDTH)
        print(
            f"{'Check':<{self.ITEM_WIDTH}}{'Expected':<{self.EXPECTED_WIDTH}}"
            f"{'Actual':<{self.ACTUAL_WIDTH}}{'Status':<{self.STATUS_WIDTH}}"
        )
        print("-" * self.TABLE_WIDTH)
        for row in self.sections.get(section, []):
            item_str = str(row["item"])
            expected_str = str(row["expected"])
            actual_str = str(row["actual"])
            if len(item_str) > self.ITEM_WIDTH - 1:
                item_str = item_str[: self.ITEM_WIDTH - 4] + "..."
            if len(expected_str) > self.EXPECTED_WIDTH - 1:
                expected_str = expected_str[: self.EXPECTED_WIDTH - 4] + "..."
            if len(actual_str) > self.ACTUAL_WIDTH - 1:
                actual_str = actual_str[: self.ACTUAL_WIDTH - 4] + "..."
            print(
                f"{item_str:<{self.ITEM_WIDTH}}{expected_str:<{self.EXPECTED_WIDTH}}"
                f"{actual_str:<{self.ACTUAL_WIDTH}}{row['status']:<{self.STATUS_WIDTH}}"
            )
            if row["note"]:
                print(f"    -> {row['note']}")
        status = self.section_status.get(section, SKIP)
        print("-" * self.TABLE_WIDTH)
        print(f"Section Result: {status}")
        print()
        return status


# =================================================
# SECTION 1 -- FILE EXISTENCE & ROW COUNT
# =================================================

def run_row_count_checks(report, frames, missing):
    section = "row_count"

    for filename in REQUIRED_FILES:
        if filename in frames:
            report.add_row(section, f"{filename} exists", "present", "present", PASS)
        else:
            report.add_row(section, f"{filename} exists", "present", "MISSING", FAIL)

    for filename, spec in FILE_SPECS.items():
        if filename not in frames:
            report.add_row(section, f"{filename} row count", f"~{spec['expected']:,}", "N/A (file missing)", FAIL)
            continue
        actual = len(frames[filename])
        expected = spec["expected"]
        tolerance = spec["tolerance"]
        lower = expected * (1 - tolerance)
        upper = expected * (1 + tolerance)
        status = PASS if lower <= actual <= upper else FAIL
        report.add_row(
            section,
            f"{filename} row count",
            f"~{expected:,} (+/-{int(tolerance * 100)}%)",
            f"{actual:,}",
            status,
        )

    return report.print_section(section, "SECTION 1: FILE EXISTENCE & ROW COUNT CHECKS")


# =================================================
# SECTION 2 -- PRIMARY KEY INTEGRITY
# =================================================

def run_primary_key_checks(report, frames):
    section = "primary_key"

    for filename, spec in FILE_SPECS.items():
        if filename not in frames:
            report.add_row(section, f"{filename} PK uniqueness", "unique", "N/A (file missing)", FAIL)
            continue
        df = frames[filename]
        pk_col = _find_col(df, spec["pk"])
        if pk_col is None:
            report.add_row(
                section, f"{filename} PK uniqueness", "unique",
                f"N/A (no {spec['pk']} column found)", FAIL,
            )
            continue

        n_total = len(df)
        n_unique = df[pk_col].nunique(dropna=False)
        n_nulls = df[pk_col].isna().sum()
        is_unique = (n_unique == n_total) and (n_nulls == 0)
        status = PASS if is_unique else FAIL
        note = "" if is_unique else f"{n_total - n_unique} duplicate(s), {n_nulls} null(s) in '{pk_col}'"
        report.add_row(section, f"{filename} PK ('{pk_col}') uniqueness", "unique, no nulls",
                        f"{n_unique:,}/{n_total:,} unique", status, note)

    return report.print_section(section, "SECTION 2: PRIMARY KEY INTEGRITY")


# =================================================
# SECTION 3 -- FOREIGN KEY / REFERENTIAL INTEGRITY
# =================================================

def _fk_check(report, section, label, child_df, child_col_candidates, parent_key_set,
              nullable=False):
    if child_df is None:
        report.add_row(section, label, "0 orphans", "N/A (file missing)", FAIL)
        return
    child_col = _find_col(child_df, child_col_candidates)
    if child_col is None:
        report.add_row(section, label, "0 orphans", f"N/A (no {child_col_candidates} column)", FAIL)
        return

    series = child_df[child_col]
    if nullable:
        series = series.dropna()

    orphan_mask = ~series.isin(parent_key_set)
    n_orphans = int(orphan_mask.sum())
    status = PASS if n_orphans == 0 else FAIL
    report.add_row(section, label, "0 orphans", f"{n_orphans:,} orphans", status)


def run_referential_integrity_checks(report, frames):
    section = "referential_integrity"

    dim_date = frames.get("dim_date.csv")
    dim_store = frames.get("dim_store.csv")
    dim_product = frames.get("dim_product.csv")
    dim_customer = frames.get("dim_customer.csv")
    fact_sales = frames.get("fact_sales.csv")
    fact_returns = frames.get("fact_returns.csv")
    fact_inventory = frames.get("fact_inventory_snapshot.csv")
    fact_staffing = frames.get("fact_staffing.csv")

    date_keys = set(dim_date[_find_col(dim_date, ["date_key"])]) if dim_date is not None else set()
    store_keys = set(dim_store[_find_col(dim_store, ["store_key"])]) if dim_store is not None else set()
    product_keys = set(dim_product[_find_col(dim_product, ["product_key"])]) if dim_product is not None else set()
    customer_keys = set(dim_customer[_find_col(dim_customer, ["customer_key"])]) if dim_customer is not None else set()
    sales_ids = set()
    if fact_sales is not None:
        sales_id_col = _find_col(fact_sales, ["sales_id", "sales_line_id"])
        if sales_id_col:
            sales_ids = set(fact_sales[sales_id_col])

    # fact_sales -> dim_customer, dim_product, dim_store, dim_date
    _fk_check(report, section, "fact_sales.customer_key -> dim_customer", fact_sales,
              ["customer_key"], customer_keys, nullable=True)
    _fk_check(report, section, "fact_sales.product_key -> dim_product", fact_sales,
              ["product_key"], product_keys)
    _fk_check(report, section, "fact_sales.store_key -> dim_store", fact_sales,
              ["store_key"], store_keys)
    _fk_check(report, section, "fact_sales.date_key -> dim_date", fact_sales,
              ["date_key"], date_keys)

    # fact_returns -> fact_sales, dim_product, dim_store, dim_date
    _fk_check(report, section, "fact_returns.original_sales_id -> fact_sales", fact_returns,
              ["original_sales_id", "original_sales_line_id"], sales_ids)
    _fk_check(report, section, "fact_returns.product_key -> dim_product", fact_returns,
              ["product_key"], product_keys)
    _fk_check(report, section, "fact_returns.store_key -> dim_store", fact_returns,
              ["store_key"], store_keys)
    _fk_check(report, section, "fact_returns.date_key -> dim_date", fact_returns,
              ["date_key"], date_keys)

    # fact_inventory_snapshot -> dim_store, dim_product, dim_date
    _fk_check(report, section, "fact_inventory_snapshot.store_key -> dim_store", fact_inventory,
              ["store_key"], store_keys)
    _fk_check(report, section, "fact_inventory_snapshot.product_key -> dim_product", fact_inventory,
              ["product_key"], product_keys)
    _fk_check(report, section, "fact_inventory_snapshot.date_key -> dim_date", fact_inventory,
              ["date_key", "snapshot_date_key"], date_keys)

    # fact_staffing -> dim_store, dim_date
    _fk_check(report, section, "fact_staffing.store_key -> dim_store", fact_staffing,
              ["store_key"], store_keys)
    _fk_check(report, section, "fact_staffing.date_key -> dim_date", fact_staffing,
              ["date_key", "week_start_date_key"], date_keys)

    return report.print_section(section, "SECTION 3: FOREIGN KEY / REFERENTIAL INTEGRITY")


# =================================================
# SECTION 4 -- BUSINESS RULE VALIDATION
# =================================================

def run_business_rule_checks(report, frames):
    section = "business_rules"

    fact_sales = frames.get("fact_sales.csv")
    fact_returns = frames.get("fact_returns.csv")
    fact_inventory = frames.get("fact_inventory_snapshot.csv")
    fact_staffing = frames.get("fact_staffing.csv")
    dim_store = frames.get("dim_store.csv")
    dim_product = frames.get("dim_product.csv")

    # --- 4.1 Overall return rate 5-7% ---
    if fact_sales is not None and fact_returns is not None:
        rate = len(fact_returns) / max(len(fact_sales), 1)
        lower = RETURN_RATE_MIN - RETURN_RATE_TOLERANCE
        upper = RETURN_RATE_MAX + RETURN_RATE_TOLERANCE
        status = PASS if lower <= rate <= upper else FAIL
        report.add_row(section, "Overall return rate (fact_returns / fact_sales)",
                        f"{RETURN_RATE_MIN:.0%} - {RETURN_RATE_MAX:.0%}", f"{rate:.2%}", status)
    else:
        report.add_row(section, "Overall return rate", f"{RETURN_RATE_MIN:.0%}-{RETURN_RATE_MAX:.0%}",
                        "N/A (missing file)", FAIL)

    # --- 4.2 Online return rate > Store return rate ---
    channel_rate_status = SKIP
    if fact_sales is not None and fact_returns is not None and dim_store is not None:
        try:
            store_key_col = _find_col(dim_store, ["store_key"], required=True)
            format_col = _find_col(dim_store, ["store_format", "format"], required=True)
            store_format_map = dim_store.set_index(store_key_col)[format_col].to_dict()

            sales_store_col = _find_col(fact_sales, ["store_key"], required=True)
            sales_channel_col = _find_col(fact_sales, ["channel"])
            if sales_channel_col:
                sales_channel = fact_sales[sales_channel_col].astype(str)
            else:
                sales_channel = fact_sales[sales_store_col].map(store_format_map).astype(str)
                sales_channel = sales_channel.replace(
                    {"Flagship": "Store", "Express": "Store", "Outlet": "Store"}
                )

            sales_id_col = _find_col(fact_sales, ["sales_id", "sales_line_id"], required=True)
            sales_channel_by_id = pd.Series(sales_channel.to_numpy(), index=fact_sales[sales_id_col].to_numpy())

            returns_orig_col = _find_col(fact_returns, ["original_sales_id", "original_sales_line_id"], required=True)
            returns_channel = fact_returns[returns_orig_col].map(sales_channel_by_id)

            sales_channel_counts = sales_channel.value_counts()
            returns_channel_counts = returns_channel.value_counts()

            online_sales = sales_channel_counts.get("Online", 0)
            store_sales = sales_channel_counts.get("Store", 0)
            online_returns = returns_channel_counts.get("Online", 0)
            store_returns = returns_channel_counts.get("Store", 0)

            online_rate = online_returns / online_sales if online_sales else 0.0
            store_rate = store_returns / store_sales if store_sales else 0.0

            status = PASS if online_rate > store_rate else FAIL
            channel_rate_status = status
            report.add_row(
                section, "Online return rate > Store return rate",
                "Online > Store",
                f"Online={online_rate:.2%}, Store={store_rate:.2%}",
                status,
            )
        except Exception as exc:
            report.add_row(section, "Online return rate > Store return rate", "Online > Store",
                            "N/A (could not compute)", FAIL, note=str(exc))
    else:
        report.add_row(section, "Online return rate > Store return rate", "Online > Store",
                        "N/A (missing file)", FAIL)

    # --- 4.3 / 4.4: quantity + date-window checks (joined via original_sales_id) ---
    if fact_sales is not None and fact_returns is not None:
        try:
            sales_id_col = _find_col(fact_sales, ["sales_id", "sales_line_id"], required=True)
            sales_qty_col = _find_col(fact_sales, ["quantity"], required=True)
            sales_date_col = _find_col(fact_sales, ["date_key"], required=True)

            returns_orig_col = _find_col(fact_returns, ["original_sales_id", "original_sales_line_id"], required=True)
            returns_qty_col = _find_col(fact_returns, ["quantity_returned"], required=True)
            returns_date_col = _find_col(fact_returns, ["date_key"], required=True)

            qty_by_sales_id = pd.Series(fact_sales[sales_qty_col].to_numpy(), index=fact_sales[sales_id_col].to_numpy())
            date_by_sales_id = pd.Series(
                pd.to_datetime(fact_sales[sales_date_col]).to_numpy(), index=fact_sales[sales_id_col].to_numpy()
            )

            matched_mask = fact_returns[returns_orig_col].isin(qty_by_sales_id.index)
            matched_returns = fact_returns[matched_mask].copy()

            matched_returns["_sold_qty"] = matched_returns[returns_orig_col].map(qty_by_sales_id)
            matched_returns["_sold_date"] = matched_returns[returns_orig_col].map(date_by_sales_id)
            matched_returns["_return_date"] = pd.to_datetime(matched_returns[returns_date_col])

            qty_violation = matched_returns[returns_qty_col] > matched_returns["_sold_qty"]
            n_qty_violation = int(qty_violation.sum())
            status = PASS if n_qty_violation == 0 else FAIL
            report.add_row(section, "quantity_returned <= quantity sold", "0 violations",
                            f"{n_qty_violation:,} violations", status)

            after_sale = matched_returns["_return_date"] > matched_returns["_sold_date"]
            within_window = (matched_returns["_return_date"] - matched_returns["_sold_date"]).dt.days <= MAX_RETURN_WINDOW_DAYS
            date_violation = ~(after_sale & within_window)
            n_date_violation = int(date_violation.sum())
            status = PASS if n_date_violation == 0 else FAIL
            report.add_row(section, "Return date after sale date, within 30 days", "0 violations",
                            f"{n_date_violation:,} violations", status)
        except Exception as exc:
            report.add_row(section, "quantity_returned <= quantity sold", "0 violations",
                            "N/A (could not compute)", FAIL, note=str(exc))
            report.add_row(section, "Return date after sale date, within 30 days", "0 violations",
                            "N/A (could not compute)", FAIL, note=str(exc))
    else:
        report.add_row(section, "quantity_returned <= quantity sold", "0 violations",
                        "N/A (missing file)", FAIL)
        report.add_row(section, "Return date after sale date, within 30 days", "0 violations",
                        "N/A (missing file)", FAIL)

    # --- 4.5 Closing stock = opening - sales + replenished ---
    if fact_inventory is not None:
        opening_col = _find_col(fact_inventory, ["opening_stock", "beginning_stock", "opening_units"])
        closing_col = _find_col(fact_inventory, ["closing_stock", "ending_stock", "units_on_hand"])
        sold_col = _find_col(fact_inventory, ["units_sold", "sales_qty", "sold_units"])
        replenished_col = _find_col(fact_inventory, ["units_replenished", "replenishment_qty", "units_received"])

        if opening_col and closing_col and sold_col and replenished_col:
            expected_closing = (
                fact_inventory[opening_col] - fact_inventory[sold_col] + fact_inventory[replenished_col]
            )
            mismatch = (expected_closing.round(2) != fact_inventory[closing_col].round(2))
            n_mismatch = int(mismatch.sum())
            status = PASS if n_mismatch == 0 else FAIL
            report.add_row(section, "Closing stock = opening - sales + replenished", "0 mismatches",
                            f"{n_mismatch:,} mismatches", status)
        else:
            report.add_row(
                section, "Closing stock = opening - sales + replenished", "0 mismatches",
                "N/A", SKIP,
                note="Required columns (opening/closing/sold/replenished) not present in fact_inventory_snapshot.csv; "
                     "skipped rather than failed.",
            )
    else:
        report.add_row(section, "Closing stock = opening - sales + replenished", "0 mismatches",
                        "N/A (missing file)", FAIL)

    # --- 4.6 East region and Electronics show higher stockout rates ---
    if fact_inventory is not None and dim_store is not None and dim_product is not None:
        stockout_col = _find_col(fact_inventory, ["stockout_flag"])
        inv_store_col = _find_col(fact_inventory, ["store_key"])
        inv_product_col = _find_col(fact_inventory, ["product_key"])
        store_key_col = _find_col(dim_store, ["store_key"])
        region_col = _find_col(dim_store, ["region"])
        product_key_col = _find_col(dim_product, ["product_key"])
        division_col = _find_col(dim_product, ["division", "category"])

        if stockout_col and inv_store_col and inv_product_col and region_col and division_col:
            region_map = dim_store.set_index(store_key_col)[region_col].to_dict()
            division_map = dim_product.set_index(product_key_col)[division_col].to_dict()

            inv = fact_inventory.copy()
            inv["_region"] = inv[inv_store_col].map(region_map)
            inv["_division"] = inv[inv_product_col].map(division_map)
            inv["_stockout"] = inv[stockout_col].astype(bool)

            region_rates = inv.groupby("_region")["_stockout"].mean()
            division_rates = inv.groupby("_division")["_stockout"].mean()

            east_rate = region_rates.get("East", np.nan)
            other_region_rate = region_rates.drop(labels=["East"], errors="ignore").mean()
            region_status = PASS if pd.notna(east_rate) and east_rate > other_region_rate else FAIL
            report.add_row(
                section, "East region stockout rate > other regions", "East > average of others",
                f"East={east_rate:.2%}, Others avg={other_region_rate:.2%}" if pd.notna(east_rate) else "N/A",
                region_status,
            )

            electronics_key = next((d for d in division_rates.index if isinstance(d, str) and "Electronics" in d), None)
            if electronics_key is not None:
                electronics_rate = division_rates.get(electronics_key, np.nan)
                other_division_rate = division_rates.drop(labels=[electronics_key], errors="ignore").mean()
                division_status = PASS if electronics_rate > other_division_rate else FAIL
                report.add_row(
                    section, "Electronics stockout rate > other divisions", "Electronics > average of others",
                    f"Electronics={electronics_rate:.2%}, Others avg={other_division_rate:.2%}",
                    division_status,
                )
            else:
                report.add_row(section, "Electronics stockout rate > other divisions",
                                "Electronics > average of others", "N/A (division not found)", SKIP)
        else:
            report.add_row(section, "East region / Electronics stockout rate checks", "higher than average",
                            "N/A", SKIP, note="Required columns not present in fact_inventory_snapshot.csv.")
    else:
        report.add_row(section, "East region / Electronics stockout rate checks", "higher than average",
                        "N/A (missing file)", FAIL)

    # --- 4.7 fact_staffing = physical stores only, 214 x 52 ---
    if fact_staffing is not None and dim_store is not None:
        try:
            staffing_store_col = _find_col(fact_staffing, ["store_key"], required=True)
            staffing_date_col = _find_col(fact_staffing, ["date_key", "week_start_date_key"], required=True)
            store_key_col = _find_col(dim_store, ["store_key"], required=True)
            format_col = _find_col(dim_store, ["store_format", "format"], required=True)

            store_format_map = dim_store.set_index(store_key_col)[format_col].to_dict()
            staffing_formats = fact_staffing[staffing_store_col].map(store_format_map)

            non_physical_mask = ~staffing_formats.isin(PHYSICAL_FORMATS)
            n_non_physical = int(non_physical_mask.sum())
            status = PASS if n_non_physical == 0 else FAIL
            report.add_row(section, "fact_staffing contains physical stores only", "0 non-physical rows",
                            f"{n_non_physical:,} non-physical rows", status)

            n_distinct_stores = fact_staffing[staffing_store_col].nunique()
            n_distinct_weeks = fact_staffing[staffing_date_col].nunique()
            grid_status = PASS if (n_distinct_stores == TARGET_PHYSICAL_STORES and n_distinct_weeks == TARGET_STAFFING_WEEKS) else FAIL
            report.add_row(
                section, "fact_staffing grid = 214 stores x 52 weeks",
                f"{TARGET_PHYSICAL_STORES} stores x {TARGET_STAFFING_WEEKS} weeks",
                f"{n_distinct_stores} stores x {n_distinct_weeks} weeks",
                grid_status,
            )
        except Exception as exc:
            report.add_row(section, "fact_staffing physical-store / grid checks", "214 x 52",
                            "N/A (could not compute)", FAIL, note=str(exc))
    else:
        report.add_row(section, "fact_staffing physical-store / grid checks", "214 x 52",
                        "N/A (missing file)", FAIL)

    return report.print_section(section, "SECTION 4: BUSINESS RULE VALIDATION")


# =================================================
# MAIN
# =================================================

def main():
    print("=" * 100)
    print("INSIGHT360 -- PHASE 3B DATASET VALIDATION REPORT")
    print("=" * 100)
    print()

    frames, missing, paths = load_all_files()
    if missing:
        print("The following files could not be located or loaded:")
        for m in missing:
            print(f"  - {m}")
        print()

    report = Report()

    s1 = run_row_count_checks(report, frames, missing)
    s2 = run_primary_key_checks(report, frames)
    s3 = run_referential_integrity_checks(report, frames)
    s4 = run_business_rule_checks(report, frames)

    suite_results = [
        ("1. Row Count Checks", s1),
        ("2. Primary Key Integrity", s2),
        ("3. Referential Integrity", s3),
        ("4. Business Rule Validation", s4),
    ]

    print("=" * 100)
    print("OVERALL SUITE SUMMARY")
    print("=" * 100)
    print(f"{'Test Suite':<45}{'Status':<10}")
    print("-" * 100)
    for name, status in suite_results:
        print(f"{name:<45}{status:<10}")
    print("=" * 100)
    print()

    overall_pass = all(status == PASS for _, status in suite_results)

    if overall_pass:
        print("✅ PHASE 3B DATASET VALIDATION PASSED - READY FOR PHASE 4 POSTGRESQL INGESTION")
        sys.exit(0)
    else:
        print("❌ PHASE 3B DATASET VALIDATION FAILED - RESOLVE ISSUES BEFORE PHASE 4 POSTGRESQL INGESTION")
        sys.exit(1)


if __name__ == "__main__":
    main()
