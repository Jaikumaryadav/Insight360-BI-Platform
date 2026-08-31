"""
generate_dates.py
==================
Generates dim_date.csv — the shared calendar dimension for Insight360.

Implements the Phase 3A approved schema (Section 2.1) exactly:
    date_key, fiscal_year, fiscal_quarter, fiscal_month_number, month_name,
    week_of_year, day_of_week, is_weekend, is_festive_period,
    festive_period_name, is_prior_year_baseline

Grain: 1 row per calendar day, 730 rows total (2 fiscal years), spanning
DATA_START_DATE -> DATA_END_DATE as fixed in config.py.

This module makes no business-rule decisions of its own — every parameter
(fiscal year boundaries, festive windows) is sourced from config.py, which
in turn encodes the Phase 3A approved design. No redesign occurs here.
"""

from __future__ import annotations

import sys
from datetime import date, timedelta

import pandas as pd

import config

logger = config.get_logger(__name__)


def _expand_festive_windows(start_date: date, end_date: date) -> dict[date, str]:
    """
    Expand config.FESTIVE_WINDOWS into a concrete date -> festive_name map
    covering every calendar year touched by [start_date, end_date].

    Handles year-wrapping windows (e.g., "Year-End New Year Sale", which
    runs Dec 24 -> Jan 2) by splitting them across the two calendar years
    they straddle.

    Args:
        start_date: Inclusive lower bound of the generation window.
        end_date: Inclusive upper bound of the generation window.

    Returns:
        dict[date, str]: Mapping of each festive calendar date to the name
        of the festive window it belongs to. Dates outside any festive
        window are simply absent from the dict (checked via .get()).

    Raises:
        ValueError: If start_date is after end_date.
    """
    if start_date > end_date:
        raise ValueError(
            f"start_date ({start_date}) must not be after end_date ({end_date})"
        )

    festive_map: dict[date, str] = {}
    years_covered = range(start_date.year, end_date.year + 1)

    for window in config.FESTIVE_WINDOWS:
        name = window["name"]
        for year in years_covered:
            try:
                if not window["wraps_year"]:
                    window_start = date(year, window["start_month"], window["start_day"])
                    window_end = date(year, window["end_month"], window["end_day"])
                    _fill_range(festive_map, window_start, window_end, name, start_date, end_date)
                else:
                    # Year-wrapping window: split into a "start-side" segment
                    # (Dec of `year`) and an "end-side" segment (Jan of year+1).
                    start_side_begin = date(year, window["start_month"], window["start_day"])
                    start_side_end = date(year, 12, 31)
                    _fill_range(festive_map, start_side_begin, start_side_end, name, start_date, end_date)

                    end_side_begin = date(year + 1, 1, 1)
                    end_side_end = date(year + 1, window["end_month"], window["end_day"])
                    _fill_range(festive_map, end_side_begin, end_side_end, name, start_date, end_date)
            except ValueError as exc:
                # Guards against invalid calendar dates (e.g., Feb 30 typos
                # in config) surfacing as a clear, traceable error rather
                # than a silent skip.
                logger.error("Invalid festive window definition for '%s' in %d: %s", name, year, exc)
                raise

    return festive_map


def _fill_range(
    festive_map: dict[date, str],
    range_start: date,
    range_end: date,
    name: str,
    bound_start: date,
    bound_end: date,
) -> None:
    """
    Populate festive_map with `name` for every date in [range_start, range_end],
    clipped to [bound_start, bound_end] so windows near the edge of the
    overall generation window don't spill outside it.

    Args:
        festive_map: The dict being built up (mutated in place).
        range_start: Start of this specific festive segment.
        range_end: End of this specific festive segment.
        name: Festive period name to assign.
        bound_start: Overall generation window lower bound.
        bound_end: Overall generation window upper bound.

    Returns:
        None. Mutates festive_map in place.
    """
    clipped_start = max(range_start, bound_start)
    clipped_end = min(range_end, bound_end)
    if clipped_start > clipped_end:
        return  # Segment falls entirely outside the generation window.

    current = clipped_start
    while current <= clipped_end:
        festive_map[current] = name
        current += timedelta(days=1)


def _resolve_fiscal_year(day: date) -> int:
    """
    Determine which Meridian fiscal year a calendar date belongs to.

    Meridian's fiscal year runs April -> March, so any date from
    April 1 of year Y through March 31 of year Y+1 belongs to fiscal
    year label (Y+1), matching config.CURRENT_FISCAL_YEAR_LABEL /
    config.PRIOR_FISCAL_YEAR_LABEL conventions.

    Args:
        day: The calendar date to classify.

    Returns:
        int: The fiscal year label (e.g., 2025 or 2026).

    Raises:
        ValueError: If the date falls outside the two configured fiscal
            years, which would indicate a config/date-range mismatch.
    """
    if config.PRIOR_FISCAL_YEAR_START <= day <= config.PRIOR_FISCAL_YEAR_END:
        return config.PRIOR_FISCAL_YEAR_LABEL
    if config.CURRENT_FISCAL_YEAR_START <= day <= config.CURRENT_FISCAL_YEAR_END:
        return config.CURRENT_FISCAL_YEAR_LABEL

    raise ValueError(
        f"Date {day} does not fall within either configured fiscal year "
        f"({config.PRIOR_FISCAL_YEAR_START}..{config.PRIOR_FISCAL_YEAR_END} or "
        f"{config.CURRENT_FISCAL_YEAR_START}..{config.CURRENT_FISCAL_YEAR_END})"
    )


def _fiscal_month_number(day: date, fiscal_year_start_month: int = config.FISCAL_YEAR_START_MONTH) -> int:
    """
    Convert a calendar month into a fiscal-year-relative month number
    (1-12), where fiscal month 1 corresponds to fiscal_year_start_month.

    Args:
        day: The calendar date to convert.
        fiscal_year_start_month: The calendar month (1-12) that fiscal
            month 1 aligns to. Defaults to config's April start.

    Returns:
        int: Fiscal month number in the range 1-12.
    """
    return ((day.month - fiscal_year_start_month) % 12) + 1


def _fiscal_quarter(fiscal_month_number: int) -> str:
    """
    Map a fiscal month number (1-12) to its fiscal quarter label.

    Args:
        fiscal_month_number: Fiscal-year-relative month, 1-12.

    Returns:
        str: One of "Q1", "Q2", "Q3", "Q4".

    Raises:
        ValueError: If fiscal_month_number is outside 1-12.
    """
    if not 1 <= fiscal_month_number <= 12:
        raise ValueError(f"fiscal_month_number must be 1-12, got {fiscal_month_number}")
    return f"Q{((fiscal_month_number - 1) // 3) + 1}"


def generate_dim_date(
    start_date: date = config.DATA_START_DATE,
    end_date: date = config.DATA_END_DATE,
) -> pd.DataFrame:
    """
    Generate the complete dim_date table for the given date range.

    Args:
        start_date: Inclusive first calendar date to generate. Defaults to
            the Phase 3A-approved prior fiscal year start.
        end_date: Inclusive last calendar date to generate. Defaults to
            the Phase 3A-approved current fiscal year end.

    Returns:
        pd.DataFrame: One row per calendar day with all columns specified
        in Phase 3A Section 2.1, ready for CSV export.

    Raises:
        ValueError: If the resulting row count does not match the approved
            count of 730 (config.ROW_COUNTS["dim_date"]), which would
            indicate a start/end date misconfiguration.
    """
    logger.info("Generating dim_date from %s to %s", start_date, end_date)

    festive_map = _expand_festive_windows(start_date, end_date)

    records: list[dict] = []
    current_date = start_date

    try:
        while current_date <= end_date:
            fiscal_year = _resolve_fiscal_year(current_date)
            fiscal_month_number = _fiscal_month_number(current_date)
            fiscal_quarter = _fiscal_quarter(fiscal_month_number)
            is_festive = current_date in festive_map
            festive_name = festive_map.get(current_date)  # None when not festive

            records.append({
                "date_key": current_date.isoformat(),
                "fiscal_year": fiscal_year,
                "fiscal_quarter": fiscal_quarter,
                "fiscal_month_number": fiscal_month_number,
                "month_name": current_date.strftime("%B"),
                "week_of_year": current_date.isocalendar()[1],
                "day_of_week": current_date.strftime("%A"),
                "is_weekend": current_date.weekday() >= 5,  # Saturday=5, Sunday=6
                "is_festive_period": is_festive,
                "festive_period_name": festive_name,
                "is_prior_year_baseline": fiscal_year == config.PRIOR_FISCAL_YEAR_LABEL,
            })
            current_date += timedelta(days=1)
    except ValueError:
        logger.exception("Failed while generating dim_date at date %s", current_date)
        raise

    dim_date = pd.DataFrame.from_records(records)

    expected_rows = config.ROW_COUNTS["dim_date"]
    if len(dim_date) != expected_rows:
        raise ValueError(
            f"dim_date generated {len(dim_date)} rows, expected exactly "
            f"{expected_rows} per the Phase 3A approved design. Check "
            f"config.DATA_START_DATE / config.DATA_END_DATE."
        )

    logger.info("dim_date generation complete: %d rows", len(dim_date))
    return dim_date


def validate_dim_date(dim_date: pd.DataFrame) -> None:
    """
    Run lightweight structural validation on the generated dim_date table
    before export, checking the rules that matter most for downstream
    fact-table foreign-key integrity.

    Args:
        dim_date: The DataFrame produced by generate_dim_date().

    Returns:
        None. Raises on the first failed check.

    Raises:
        ValueError: If any validation rule fails (duplicate keys, wrong row
            count, unexpected nulls in non-nullable columns, etc.).
    """
    expected_rows = config.ROW_COUNTS["dim_date"]

    if len(dim_date) != expected_rows:
        raise ValueError(f"Row count mismatch: expected {expected_rows}, got {len(dim_date)}")

    if dim_date["date_key"].duplicated().any():
        raise ValueError("dim_date.date_key contains duplicate values; PK uniqueness violated")

    non_nullable_columns = [
        "date_key", "fiscal_year", "fiscal_quarter", "fiscal_month_number",
        "month_name", "week_of_year", "day_of_week", "is_weekend", "is_festive_period",
        "is_prior_year_baseline",
    ]
    for column in non_nullable_columns:
        if dim_date[column].isnull().any():
            raise ValueError(f"dim_date.{column} contains nulls but is defined as non-nullable")

    # festive_period_name must be null exactly when is_festive_period is False,
    # and non-null exactly when it is True (Phase 3A validation rule, Section 2.1).
    mismatch = dim_date["is_festive_period"] != dim_date["festive_period_name"].notna()
    if mismatch.any():
        raise ValueError(
            "dim_date.festive_period_name nullability is inconsistent with "
            "is_festive_period for at least one row"
        )

    valid_fiscal_years = {config.PRIOR_FISCAL_YEAR_LABEL, config.CURRENT_FISCAL_YEAR_LABEL}
    if not set(dim_date["fiscal_year"].unique()).issubset(valid_fiscal_years):
        raise ValueError(f"dim_date.fiscal_year contains values outside {valid_fiscal_years}")

    logger.info("dim_date validation passed: %d rows, all checks green", len(dim_date))


def export_dim_date(dim_date: pd.DataFrame) -> None:
    """
    Write the dim_date DataFrame to data/raw/dim_date.csv.

    Args:
        dim_date: The validated DataFrame to export.

    Returns:
        None.

    Raises:
        OSError: If the file cannot be written (e.g., permissions, disk full).
    """
    output_path = config.get_output_path("dim_date")
    try:
        dim_date.to_csv(output_path, index=False)
        logger.info("dim_date exported to %s (%d rows)", output_path, len(dim_date))
    except OSError:
        logger.exception("Failed to write dim_date to %s", output_path)
        raise


def main() -> None:
    """
    Entry point for standalone execution: generate, validate, and export
    dim_date.csv. Exits with a non-zero status code on failure so that a
    future main.py orchestrator (Phase 3B, later module) can detect and
    halt the pipeline on error.
    """
    logger.info("=== Starting dim_date generation (Phase 3B) ===")
    try:
        dim_date = generate_dim_date()
        validate_dim_date(dim_date)
        export_dim_date(dim_date)

        festive_rows = int(dim_date["is_festive_period"].sum())
        weekend_rows = int(dim_date["is_weekend"].sum())
        logger.info(
            "Summary: %d total rows | %d festive days | %d weekend days | fiscal years present: %s",
            len(dim_date), festive_rows, weekend_rows,
            sorted(dim_date["fiscal_year"].unique().tolist()),
        )
        logger.info("=== dim_date generation finished successfully ===")
    except Exception:
        logger.exception("dim_date generation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
