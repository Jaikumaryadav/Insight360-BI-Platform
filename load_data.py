#!/usr/bin/env python3
"""
=====================================================================
Insight360 Executive BI Platform
Phase 4 — Data Engineering: load_data.py
=====================================================================
High-performance loader for all 8 processed CSV files into the
PostgreSQL `insight360` schema created by schema_ddl.sql.

Uses PostgreSQL's native COPY command (via psycopg2) for bulk
ingestion — the fastest available method for large fact tables
such as fact_sales (~4.2M rows) and fact_inventory_snapshot (~970K
rows), avoiding row-by-row INSERT overhead and memory blowups.
=====================================================================
"""

import os
import sys
import csv
import time
import logging
from io import StringIO
from pathlib import Path

import psycopg2
from psycopg2 import sql, OperationalError, Error as Psycopg2Error

# =====================================================================
# CONFIGURATION
# =====================================================================

DB_CONFIG = {
    "host": os.getenv("PGHOST", "127.0.0.1"),
    "port": os.getenv("PGPORT", "5432"),
    "dbname": os.getenv("PGDATABASE", "insight360_db"),  # Updated to insight360_db
    "user": os.getenv("PGUSER", "postgres"),
    "password": os.getenv("PGPASSWORD", "madhu"),  # Set your password
}
SCHEMA_NAME = os.getenv("PG_SCHEMA", "insight360")

# Directory containing the processed CSV files (override via env var)
DATA_DIR = Path(os.getenv("INSIGHT360_DATA_DIR", "."))

# COPY batch size (rows buffered before flushing to DB) — tune per RAM
COPY_BATCH_ROWS = int(os.getenv("COPY_BATCH_ROWS", "200_000".replace("_", "")))

# Load order respects FK dependencies: dimensions first, then facts
LOAD_PLAN = [
    {"csv": "dim_date.csv", "table": "dim_date"},
    {"csv": "dim_store.csv", "table": "dim_store"},
    {"csv": "dim_product.csv", "table": "dim_product"},
    {"csv": "dim_customer.csv", "table": "dim_customer"},
    {"csv": "fact_sales.csv", "table": "fact_sales"},
    {"csv": "fact_returns.csv", "table": "fact_returns"},
    {"csv": "fact_inventory_snapshot.csv", "table": "fact_inventory_snapshot"},
    {"csv": "fact_staffing.csv", "table": "fact_staffing"},
]

# =====================================================================
# LOGGING
# =====================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("load_data.log", mode="a"),
    ],
)
log = logging.getLogger("insight360.load_data")


# =====================================================================
# DATABASE CONNECTION
# =====================================================================

def get_connection():
    """Establish a PostgreSQL connection with clear error handling."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        log.info(
            "Connected to database '%s' on %s:%s as user '%s'",
            DB_CONFIG["dbname"], DB_CONFIG["host"], DB_CONFIG["port"], DB_CONFIG["user"],
        )
        return conn
    except OperationalError as e:
        log.error("Failed to connect to PostgreSQL: %s", e)
        sys.exit(1)


# =====================================================================
# HELPERS
# =====================================================================

def count_csv_rows(csv_path: Path) -> int:
    """Count data rows in a CSV file (excludes header)."""
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header is None:
            return 0
        return sum(1 for _ in reader)


def get_csv_columns(csv_path: Path) -> list:
    """Return the header/column names from a CSV file, in order."""
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header is None:
            raise ValueError(f"CSV file '{csv_path}' is empty (no header row).")
        return [col.strip() for col in header]


def truncate_table(conn, table: str):
    """Truncate target table before load (idempotent re-runs)."""
    with conn.cursor() as cur:
        cur.execute(
            sql.SQL("TRUNCATE TABLE {}.{} CASCADE;").format(
                sql.Identifier(SCHEMA_NAME), sql.Identifier(table)
            )
        )
    conn.commit()
    log.info("  Truncated %s.%s before load", SCHEMA_NAME, table)


def get_db_row_count(conn, table: str) -> int:
    """Return current row count for a table."""
    with conn.cursor() as cur:
        cur.execute(
            sql.SQL("SELECT COUNT(*) FROM {}.{};").format(
                sql.Identifier(SCHEMA_NAME), sql.Identifier(table)
            )
        )
        return cur.fetchone()[0]


# =====================================================================
# CORE LOAD FUNCTION — bulk COPY with chunked buffering
# =====================================================================

def copy_csv_to_table(conn, csv_path: Path, table: str) -> int:
    """
    Bulk-load a CSV file into a PostgreSQL table using COPY, streamed
    in memory-bounded chunks via StringIO buffers. Returns rows loaded.
    """
    columns = get_csv_columns(csv_path)
    copy_sql = sql.SQL(
        "COPY {}.{} ({}) FROM STDIN WITH (FORMAT csv, HEADER false, NULL '')"
    ).format(
        sql.Identifier(SCHEMA_NAME),
        sql.Identifier(table),
        sql.SQL(", ").join(sql.Identifier(c) for c in columns),
    )

    rows_loaded = 0
    buffer = StringIO()
    writer = csv.writer(buffer)
    buffered_rows = 0

    with conn.cursor() as cur:
        with open(csv_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            next(reader, None)  # skip header

            for row in reader:
                writer.writerow(row)
                buffered_rows += 1

                if buffered_rows >= COPY_BATCH_ROWS:
                    buffer.seek(0)
                    cur.copy_expert(copy_sql, buffer)
                    rows_loaded += buffered_rows
                    log.info("    ...%s rows streamed so far", f"{rows_loaded:,}")
                    buffer = StringIO()
                    writer = csv.writer(buffer)
                    buffered_rows = 0

            # flush remaining rows
            if buffered_rows > 0:
                buffer.seek(0)
                cur.copy_expert(copy_sql, buffer)
                rows_loaded += buffered_rows

    conn.commit()
    return rows_loaded


# =====================================================================
# MAIN ORCHESTRATION
# =====================================================================

def load_table(conn, csv_filename: str, table: str) -> dict:
    """Load a single CSV into its target table with logging & verification."""
    csv_path = DATA_DIR / csv_filename

    log.info("-" * 70)
    log.info("Loading %s -> %s.%s", csv_filename, SCHEMA_NAME, table)

    if not csv_path.exists():
        log.error("  CSV file not found: %s (skipping table)", csv_path)
        return {"table": table, "status": "MISSING", "csv_rows": 0, "db_rows": 0, "elapsed": 0.0}

    expected_rows = count_csv_rows(csv_path)
    log.info("  Source CSV row count: %s", f"{expected_rows:,}")

    start = time.time()
    try:
        truncate_table(conn, table)
        loaded = copy_csv_to_table(conn, csv_path, table)
        elapsed = time.time() - start
    except Psycopg2Error as e:
        conn.rollback()
        elapsed = time.time() - start
        log.error("  ERROR loading %s: %s", table, e)
        log.error("  Transaction rolled back for %s (elapsed %.2fs)", table, elapsed)
        return {
            "table": table, "status": "FAILED", "csv_rows": expected_rows,
            "db_rows": 0, "elapsed": elapsed,
        }

    db_rows = get_db_row_count(conn, table)
    status = "OK" if db_rows == expected_rows else "MISMATCH"

    log.info(
        "  Finished %s: %s rows loaded in %.2fs (%.0f rows/sec)",
        table, f"{loaded:,}", elapsed, loaded / elapsed if elapsed > 0 else loaded,
    )
    log.info(
        "  Verification -> CSV rows: %s | DB rows: %s | Status: %s",
        f"{expected_rows:,}", f"{db_rows:,}", status,
    )

    return {
        "table": table, "status": status, "csv_rows": expected_rows,
        "db_rows": db_rows, "elapsed": elapsed,
    }


def print_summary(results: list):
    """Print a final summary table of the full load run."""
    log.info("=" * 70)
    log.info("LOAD SUMMARY")
    log.info("=" * 70)
    header = f"{'Table':<28}{'Status':<12}{'CSV Rows':>14}{'DB Rows':>14}{'Time (s)':>10}"
    log.info(header)
    log.info("-" * len(header))

    total_rows = 0
    total_time = 0.0
    all_ok = True

    for r in results:
        log.info(
            f"{r['table']:<28}{r['status']:<12}{r['csv_rows']:>14,}{r['db_rows']:>14,}{r['elapsed']:>10.2f}"
        )
        total_rows += r["db_rows"]
        total_time += r["elapsed"]
        if r["status"] != "OK":
            all_ok = False

    log.info("-" * len(header))
    log.info(f"TOTAL{'':<23}{'':<12}{'':>14}{total_rows:>14,}{total_time:>10.2f}")
    log.info("=" * 70)

    if all_ok:
        log.info("ALL TABLES LOADED SUCCESSFULLY — row counts match CSV sources.")
    else:
        log.warning("ONE OR MORE TABLES FAILED OR HAVE ROW COUNT MISMATCHES.")
        log.warning("Review the log above and re-run failed tables as needed.")


def main():
    log.info("=" * 70)
    log.info("Insight360 Phase 4 — Data Load Starting")
    log.info("Data directory: %s", DATA_DIR.resolve())
    log.info("Target schema : %s", SCHEMA_NAME)
    log.info("=" * 70)

    if not DATA_DIR.exists():
        log.error("Data directory does not exist: %s", DATA_DIR.resolve())
        sys.exit(1)

    conn = get_connection()
    results = []
    run_start = time.time()

    try:
        for entry in LOAD_PLAN:
            result = load_table(conn, entry["csv"], entry["table"])
            results.append(result)
    finally:
        conn.close()
        log.info("Database connection closed.")

    run_elapsed = time.time() - run_start
    print_summary(results)
    log.info("Total run time: %.2fs", run_elapsed)

    if any(r["status"] not in ("OK",) for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
