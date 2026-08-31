#!/usr/bin/env python3
"""
=====================================================================
Insight360 Executive BI Platform
run_all.py — Master Pipeline Orchestration Script
=====================================================================
Runs the complete end-to-end Insight360 pipeline in a single command:

  Stage 1: Dimension Generation
  Stage 2: Fact Generation (strict dependency order)
  Stage 3: Dataset Quality Audit
  Stage 4: PostgreSQL Ingestion (optional, via --load-db)

Usage:
  python run_all.py                  # full generation + validation
  python run_all.py --skip-gen       # validation (+ optional load) only
  python run_all.py --load-db        # full pipeline + DB load
  python run_all.py --skip-gen --load-db   # validate existing CSVs, then load
=====================================================================
"""

import sys
import argparse
import subprocess
import time
from pathlib import Path
from datetime import datetime

# =====================================================================
# CONFIGURATION
# =====================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
PYTHON_EXE = sys.executable

STAGE_1_DIMENSIONS = [
    "generate_dates.py",
    "generate_stores.py",
    "generate_products.py",
    "generate_customers.py",
]

STAGE_2_FACTS = [
    "generate_sales.py",
    "generate_returns.py",
    "generate_inventory.py",
    "generate_staffing.py",
]

STAGE_3_VALIDATION = [
    "validate_dataset.py",
]

STAGE_4_DB_LOAD = [
    "load_data.py",
]

TOTAL_TRACKED_STEPS = (
    len(STAGE_1_DIMENSIONS) + len(STAGE_2_FACTS) + len(STAGE_3_VALIDATION)
)

# =====================================================================
# CONSOLE STYLING HELPERS
# =====================================================================

LINE_WIDTH = 74


def hr(char: str = "=") -> str:
    return char * LINE_WIDTH


def print_banner(text: str, char: str = "="):
    print(hr(char))
    padding = max((LINE_WIDTH - len(text)) // 2, 0)
    print(" " * padding + text)
    print(hr(char))


def print_stage_header(stage_num: int, stage_name: str):
    print()
    print(hr("-"))
    print(f"STAGE {stage_num}: {stage_name}")
    print(hr("-"))


def format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    rem_secs = seconds % 60
    return f"{minutes}m {rem_secs:.1f}s"


def print_result_line(step_counter: str, script_name: str, status: str, elapsed: float):
    tag = "[PASS]" if status == "PASS" else "[FAIL]"
    print(f"  {step_counter} {tag} {script_name} ({format_duration(elapsed)})")


# =====================================================================
# EXECUTION ENGINE
# =====================================================================

class PipelineError(Exception):
    """Raised when a pipeline stage fails, halting execution."""
    pass


def run_script(script_name: str, step_counter: str) -> float:
    """
    Run a single Python script as a subprocess, streaming its output
    live to the console. Returns elapsed time in seconds. Raises
    PipelineError on any non-zero exit code or missing script.
    """
    script_path = SCRIPT_DIR / script_name

    if not script_path.exists():
        print(f"  {step_counter} [FAIL] {script_name} (not found at {script_path})")
        raise PipelineError(f"Script not found: {script_path}")

    print(f"  {step_counter} [RUN ] {script_name} ...")
    start = time.time()

    try:
        result = subprocess.run(
            [PYTHON_EXE, str(script_path)],
            cwd=str(SCRIPT_DIR),
            check=False,
        )
    except Exception as e:
        elapsed = time.time() - start
        print_result_line(step_counter, script_name, "FAIL", elapsed)
        raise PipelineError(f"Exception while running {script_name}: {e}") from e

    elapsed = time.time() - start

    if result.returncode != 0:
        print_result_line(step_counter, script_name, "FAIL", elapsed)
        raise PipelineError(
            f"{script_name} exited with non-zero status code {result.returncode}"
        )

    print_result_line(step_counter, script_name, "PASS", elapsed)
    return elapsed


def run_stage(stage_num: int, stage_name: str, scripts: list, step_offset: int, total_steps: int, timings: dict) -> int:
    """Run all scripts in a stage sequentially. Returns updated step counter."""
    print_stage_header(stage_num, stage_name)

    step = step_offset
    for script_name in scripts:
        step += 1
        step_counter = f"[{step}/{total_steps}]"
        elapsed = run_script(script_name, step_counter)
        timings[script_name] = elapsed

    return step


# =====================================================================
# MAIN ORCHESTRATION
# =====================================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="Insight360 Executive BI Platform — Master Pipeline Orchestrator"
    )
    parser.add_argument(
        "--skip-gen",
        action="store_true",
        help="Skip CSV generation (Stages 1-2) and jump straight to validation (and optional DB load).",
    )
    parser.add_argument(
        "--load-db",
        action="store_true",
        help="Run load_data.py (Stage 4) after successful dataset validation.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    pipeline_start = time.time()
    timings = {}
    stage_timings = {}

    print_banner("INSIGHT360 EXECUTIVE BI PLATFORM")
    print_banner("Master Pipeline Orchestrator — run_all.py", char="-")
    print(f"  Started at : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Script dir : {SCRIPT_DIR}")
    print(f"  Skip-gen   : {args.skip_gen}")
    print(f"  Load-db    : {args.load_db}")

    total_steps = TOTAL_TRACKED_STEPS + (1 if args.load_db else 0)
    step_counter = 0

    try:
        # -------------------------------------------------------------
        # STAGE 1 + 2: Generation (unless --skip-gen)
        # -------------------------------------------------------------
        if not args.skip_gen:
            stage_start = time.time()
            step_counter = run_stage(
                1, "Dimension Generation", STAGE_1_DIMENSIONS,
                step_counter, total_steps, timings,
            )
            stage_timings["Stage 1: Dimension Generation"] = time.time() - stage_start

            stage_start = time.time()
            step_counter = run_stage(
                2, "Fact Generation (Strict Dependency Order)", STAGE_2_FACTS,
                step_counter, total_steps, timings,
            )
            stage_timings["Stage 2: Fact Generation"] = time.time() - stage_start
        else:
            print()
            print(hr("-"))
            print("STAGE 1 & 2: SKIPPED (--skip-gen flag provided)")
            print(hr("-"))

        # -------------------------------------------------------------
        # STAGE 3: Dataset Quality Audit
        # -------------------------------------------------------------
        stage_start = time.time()
        step_counter = run_stage(
            3, "Dataset Quality Audit", STAGE_3_VALIDATION,
            step_counter, total_steps, timings,
        )
        stage_timings["Stage 3: Dataset Quality Audit"] = time.time() - stage_start

        # -------------------------------------------------------------
        # STAGE 4: PostgreSQL Ingestion (optional)
        # -------------------------------------------------------------
        if args.load_db:
            stage_start = time.time()
            step_counter = run_stage(
                4, "PostgreSQL Ingestion", STAGE_4_DB_LOAD,
                step_counter, total_steps, timings,
            )
            stage_timings["Stage 4: PostgreSQL Ingestion"] = time.time() - stage_start
        else:
            print()
            print(hr("-"))
            print("STAGE 4: SKIPPED (pass --load-db to run PostgreSQL ingestion)")
            print(hr("-"))

    except PipelineError as e:
        total_elapsed = time.time() - pipeline_start
        print()
        print_banner("PIPELINE HALTED — FAILURE DETECTED", char="!")
        print(f"  Reason        : {e}")
        print(f"  Elapsed before failure: {format_duration(total_elapsed)}")
        print(hr("!"))
        print_final_summary(timings, stage_timings, total_elapsed, success=False)
        sys.exit(1)
    except KeyboardInterrupt:
        total_elapsed = time.time() - pipeline_start
        print()
        print_banner("PIPELINE INTERRUPTED BY USER", char="!")
        print(f"  Elapsed before interruption: {format_duration(total_elapsed)}")
        print_final_summary(timings, stage_timings, total_elapsed, success=False)
        sys.exit(130)

    total_elapsed = time.time() - pipeline_start
    print()
    print_banner("PIPELINE COMPLETED SUCCESSFULLY")
    print_final_summary(timings, stage_timings, total_elapsed, success=True)
    sys.exit(0)


def print_final_summary(timings: dict, stage_timings: dict, total_elapsed: float, success: bool):
    print()
    print(hr("-"))
    print("EXECUTION SUMMARY")
    print(hr("-"))

    if timings:
        print(f"  {'Script':<32}{'Status':<10}{'Time':>12}")
        print("  " + "-" * (LINE_WIDTH - 2))
        for script_name, elapsed in timings.items():
            print(f"  {script_name:<32}{'PASS':<10}{format_duration(elapsed):>12}")

    if stage_timings:
        print()
        print(f"  {'Stage':<48}{'Time':>12}")
        print("  " + "-" * (LINE_WIDTH - 2))
        for stage_name, elapsed in stage_timings.items():
            print(f"  {stage_name:<48}{format_duration(elapsed):>12}")

    print()
    print(hr("-"))
    print(f"  TOTAL PIPELINE RUNTIME: {format_duration(total_elapsed)}")
    print(f"  FINISHED AT           : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  RESULT                 : {'SUCCESS' if success else 'FAILED'}")
    print(hr("="))


if __name__ == "__main__":
    main()
