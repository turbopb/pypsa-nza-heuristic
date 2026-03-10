"""
02_validate_year.py

Runs adequacy validation across all 12 months for a given planning year.

For each month:
  - Loads the pre-scaled network from cases/reference/{year}/{month}_{year}/
  - Fixes all capacities (dispatch-only, no expansion)
  - Adds load shedding generators
  - Runs single-scenario dispatch with scaling_factor=1.0
    (demand is already at the correct level from 01_setup_year.py)
  - Reports adequacy and diagnoses bottleneck type

Bottleneck diagnosis:
  - Generation constrained:  many buses shedding, generators at capacity,
                             line loading moderate
  - Transmission constrained: few buses shedding, lines heavily loaded,
                              spare generation exists
  - Mixed:                   both apply

Usage:
    python 03_validation\02_validate_year.py --year 2024
    python 03_validation\02_validate_year.py --year 2030

Output:
    results\validation\annual_summary_{year}.csv
    results\validation\annual_validation_{year}.log

Author: Phillippe Bruneau
"""

import argparse
import logging
from pathlib import Path
import pandas as pd
import yaml

from pypsa_nza_dispatch.network import (
    load_base_network,
    fix_all_capacities,
    add_load_shedding_generators,
)
from pypsa_nza_dispatch.validate import validate_single_scenario

# ---------------------------------------------------------------------------
# Configuration -- update if paths change
# ---------------------------------------------------------------------------

CONFIG_PATH = Path(
    r"C:\Users\Public\Documents\Thesis\analysis\pypsa-nza-dispatch\config\dispatch_config.yaml"
)

RESULTS_DIR = Path(
    r"C:\Users\Public\Documents\Thesis\analysis\pypsa-nza-heuristic\results\validation"
)

MONTHS = [
    "jan", "feb", "mar", "apr", "may", "jun",
    "jul", "aug", "sep", "oct", "nov", "dec"
]

SOLVER = "highs"

# Thresholds for bottleneck diagnosis
LINE_LOADING_THRESHOLD = 0.95
TX_SHEDDING_BUS_LIMIT  = 3


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def setup_logging(year: int, results_dir: Path) -> logging.Logger:
    results_dir.mkdir(parents=True, exist_ok=True)
    log_file = results_dir / f"annual_validation_{year}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)s  %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, mode="w"),
        ],
    )
    return logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_config(config_path: Path) -> dict:
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def diagnose_bottleneck(diag: dict) -> str:
    """
    Classify the type of capacity shortfall from dispatch diagnostics.
    Returns one of: 'ADEQUATE', 'GENERATION', 'TRANSMISSION', 'MIXED'
    """
    if diag.get("status") == "ADEQUATE":
        return "ADEQUATE"

    buses_shedding  = diag.get("buses_with_shedding", 0)
    congested_lines = diag.get("congested_lines", 0)
    gens_at_cap     = diag.get("generators_at_capacity", 0)
    max_line        = diag.get("max_line_loading", 0)

    gen_constrained = gens_at_cap > 0
    tx_constrained  = (congested_lines > 0 or max_line >= LINE_LOADING_THRESHOLD)
    localised       = (buses_shedding <= TX_SHEDDING_BUS_LIMIT)

    if gen_constrained and tx_constrained:
        return "MIXED"
    elif tx_constrained and localised and not gen_constrained:
        return "TRANSMISSION"
    elif gen_constrained and not tx_constrained:
        return "GENERATION"
    else:
        return "MIXED"


def print_month_result(log, month: str, diag: dict, bottleneck: str) -> None:
    shed_pct   = diag.get("load_shed_fraction", 0) * 100
    status     = diag.get("status", "UNKNOWN")
    max_line   = diag.get("max_line_loading", 0) * 100
    gens_cap   = diag.get("generators_at_capacity", 0)
    cong_lines = diag.get("congested_lines", 0)
    buses_shed = diag.get("buses_with_shedding", 0)
    shed_mwh   = diag.get("total_load_shed_MWh", 0)

    log.info(
        f"  {month.upper():>3}  status={status:<10}  "
        f"shed={shed_pct:6.3f}%  ({shed_mwh:>10,.0f} MWh)  "
        f"max_line={max_line:5.1f}%  "
        f"congested_lines={cong_lines:2d}  "
        f"gens_at_cap={gens_cap:2d}  "
        f"buses_shedding={buses_shed:2d}  "
        f"bottleneck={bottleneck}"
    )


# ---------------------------------------------------------------------------
# Main validation
# ---------------------------------------------------------------------------

def validate_year(year: int, config: dict, log: logging.Logger) -> pd.DataFrame:
    log.info("=" * 70)
    log.info(f"ANNUAL ADEQUACY VALIDATION -- {year}")
    log.info("=" * 70)
    log.info("Demand is pre-scaled in network files. scaling_factor=1.0")
    log.info("")

    results = []

    for month in MONTHS:
        try:
            network = load_base_network(config, year=year, month=month)
            network = fix_all_capacities(network, verbose=False)
            network = add_load_shedding_generators(network, verbose=False)

            diag = validate_single_scenario(
                network,
                scaling_factor=1.0,
                solver_name=SOLVER,
                verbose=False,
            )

            if not diag:
                log.warning(f"  {month.upper():>3}  optimisation failed -- skipping")
                continue

            bottleneck = diagnose_bottleneck(diag)
            print_month_result(log, month, diag, bottleneck)

            results.append({
                "year":                   year,
                "month":                  month,
                "status":                 diag.get("status", "UNKNOWN"),
                "bottleneck":             bottleneck,
                "total_demand_MWh":       diag.get("total_demand_MWh", 0),
                "load_shed_MWh":          diag.get("total_load_shed_MWh", 0),
                "load_shed_pct":          diag.get("load_shed_fraction", 0) * 100,
                "buses_with_shedding":    diag.get("buses_with_shedding", 0),
                "max_line_loading_pct":   diag.get("max_line_loading", 0) * 100,
                "congested_lines":        diag.get("congested_lines", 0),
                "generators_at_capacity": diag.get("generators_at_capacity", 0),
                "solve_time_s":           diag.get("solve_time_s", 0),
            })

        except FileNotFoundError as e:
            log.error(f"  {month.upper():>3}  network not found: {e}")
        except Exception as e:
            log.error(f"  {month.upper():>3}  unexpected error: {e}", exc_info=True)

    df = pd.DataFrame(results)
    if df.empty:
        log.error("No results collected. Check network paths above.")
        return df

    # Summary
    adequate   = (df["status"] == "ADEQUATE").sum()
    inadequate = (df["status"] == "INADEQUATE").sum()
    log.info("")
    log.info("=" * 70)
    log.info(f"SUMMARY {year}")
    log.info(f"  Adequate months   : {adequate}/12")
    log.info(f"  Inadequate months : {inadequate}/12")

    if inadequate > 0:
        worst = df.loc[df["load_shed_pct"].idxmax()]
        log.info(
            f"  Worst month       : {worst['month'].upper()} "
            f"({worst['load_shed_pct']:.3f}% shed)"
        )
        for btype in ["GENERATION", "TRANSMISSION", "MIXED"]:
            count = (df["bottleneck"] == btype).sum()
            if count > 0:
                months_affected = (
                    df.loc[df["bottleneck"] == btype, "month"]
                    .str.upper().tolist()
                )
                log.info(
                    f"  {btype:<15} : {count} months -- "
                    f"{', '.join(months_affected)}"
                )
        log.info("")
        log.info("  Action: edit additions YAML and run 03_apply_additions_manual.py")
    else:
        log.info("  All months adequate.")
        log.info(
            f"  Next step: run 01_setup_year.py --source-year {year} "
            f"--target-year <next_year>"
        )

    log.info("=" * 70)

    return df


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Validate adequacy for all 12 months of a planning year."
    )
    parser.add_argument(
        "--year", type=int, required=True,
        help="Planning year to validate (e.g. 2024, 2030)"
    )
    args = parser.parse_args()

    log = setup_logging(args.year, RESULTS_DIR)
    config = load_config(CONFIG_PATH)

    df = validate_year(args.year, config, log)

    if not df.empty:
        out_path = RESULTS_DIR / f"annual_summary_{args.year}.csv"
        df.to_csv(out_path, index=False)
        log.info(f"Results saved: {out_path}")


if __name__ == "__main__":
    main()
