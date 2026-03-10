"""
03_apply_additions_manual.py

Applies user-specified generation and transmission additions to a planning
year network, then reruns adequacy validation across all 12 months.

Additions are specified in a YAML file. The script applies identical
additions to all 12 monthly network directories for the target year,
then reports the updated adequacy.

Usage:
    python 02_scenarios\03_apply_additions_manual.py --year 2030 --additions 02_scenarios\additions\additions_2030_iter01.yaml --iteration 1

Additions YAML format:
    year: 2030
    notes: "First iteration -- add gas peakers and upgrade South Island corridor"

    generators:
      - name: OTA_gas_1        # Must be unique across network
        bus: OTA               # Must match an existing bus name
        p_nom: 300             # MW
        carrier: gas
        marginal_cost: 80      # $/MWh
        efficiency: 0.4        # optional, default 1.0

      - name: HAY_wind_1
        bus: HAY
        p_nom: 150
        carrier: wind
        marginal_cost: 0
        p_max_pu: 0.35         # optional capacity factor

    lines:
      - name: HAY_BEN_upgrade   # Label for logging only
        existing_line: HAY_BEN  # Must match existing line name in network
        add_s_nom: 400          # MVA to add to existing s_nom

Author: Phillippe Bruneau
"""

import argparse
import logging
from pathlib import Path
import pandas as pd
import pypsa
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

LINE_LOADING_THRESHOLD = 0.95
TX_SHEDDING_BUS_LIMIT  = 3


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def setup_logging(year: int, iteration: int, results_dir: Path) -> logging.Logger:
    results_dir.mkdir(parents=True, exist_ok=True)
    log_file = results_dir / f"additions_{year}_iter{iteration:02d}.log"
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


def load_additions(additions_path: Path) -> dict:
    with open(additions_path, "r") as f:
        return yaml.safe_load(f)


def get_cases_root(config: dict) -> Path:
    return Path(config["paths"]["root"]) / "cases" / "reference"


def get_month_dir(cases_root: Path, year: int, month: str) -> Path:
    return cases_root / str(year) / f"{month}_{year}"


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


def apply_additions_to_network(
    network: pypsa.Network,
    additions: dict,
    log: logging.Logger
) -> pypsa.Network:
    """
    Apply generator and line additions to a PyPSA network object.
    Returns the modified network.
    """
    # --- Generators ---
    for gen in additions.get("generators", []):
        name = gen["name"]

        if name in network.generators.index:
            log.warning(f"    Generator '{name}' already exists -- skipping.")
            continue

        carrier = gen.get("carrier", "gas")
        if carrier not in network.carriers.index:
            network.add("Carrier", carrier)

        kwargs = {
            "bus":              gen["bus"],
            "p_nom":            gen["p_nom"],
            "carrier":          carrier,
            "marginal_cost":    gen.get("marginal_cost", 0.0),
            "efficiency":       gen.get("efficiency", 1.0),
            "p_min_pu":         gen.get("p_min_pu", 0.0),
            "p_max_pu":         gen.get("p_max_pu", 1.0),
            "p_nom_extendable": False,
        }

        network.add("Generator", name, **kwargs)
        log.info(
            f"    + Generator: {name}  bus={gen['bus']}  "
            f"p_nom={gen['p_nom']} MW  carrier={carrier}  "
            f"mc={gen.get('marginal_cost', 0):.0f} $/MWh"
        )

    # --- Lines ---
    for line_spec in additions.get("lines", []):
        existing_name = line_spec["existing_line"]
        add_s_nom     = line_spec["add_s_nom"]

        if existing_name not in network.lines.index:
            log.warning(
                f"    Line '{existing_name}' not found in network -- skipping."
            )
            continue

        old_s_nom = network.lines.at[existing_name, "s_nom"]
        new_s_nom = old_s_nom + add_s_nom
        network.lines.at[existing_name, "s_nom"] = new_s_nom
        log.info(
            f"    + Line: {existing_name}  "
            f"{old_s_nom:.0f} -> {new_s_nom:.0f} MVA  (+{add_s_nom:.0f} MVA)"
        )

    return network


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def apply_and_validate(
    year: int,
    additions: dict,
    config: dict,
    iteration: int,
    log: logging.Logger
) -> pd.DataFrame:

    cases_root = get_cases_root(config)

    log.info("=" * 70)
    log.info(f"APPLYING ADDITIONS -- {year}  (iteration {iteration:02d})")
    if "notes" in additions:
        log.info(f"Notes: {additions['notes']}")
    log.info("=" * 70)

    n_gens  = len(additions.get("generators", []))
    n_lines = len(additions.get("lines", []))
    log.info(f"Additions: {n_gens} generator(s), {n_lines} line upgrade(s)")
    log.info("")

    results = []

    for month in MONTHS:
        month_dir = get_month_dir(cases_root, year, month)

        if not month_dir.exists():
            log.warning(f"  {month.upper():>3}  directory not found -- skipping")
            continue

        try:
            log.info(f"  {month.upper():>3}  applying additions...")

            # Load current network for this month
            network = load_base_network(config, year=year, month=month)

            # Apply additions
            network = apply_additions_to_network(network, additions, log)

            # Write updated network back to CSV so it persists for next iteration
            network.export_to_csv_folder(str(month_dir))

            # Validate
            network = fix_all_capacities(network, verbose=False)
            network = add_load_shedding_generators(network, verbose=False)

            diag = validate_single_scenario(
                network,
                scaling_factor=1.0,
                solver_name=SOLVER,
                verbose=False,
            )

            if not diag:
                log.warning(f"  {month.upper():>3}  optimisation failed")
                continue

            bottleneck = diagnose_bottleneck(diag)
            shed_pct   = diag.get("load_shed_fraction", 0) * 100
            status     = diag.get("status", "UNKNOWN")

            log.info(
                f"  {month.upper():>3}  status={status:<10}  "
                f"shed={shed_pct:6.3f}%  "
                f"({diag.get('total_load_shed_MWh', 0):>10,.0f} MWh)  "
                f"max_line={diag.get('max_line_loading', 0)*100:5.1f}%  "
                f"congested={diag.get('congested_lines', 0):2d}  "
                f"gens_at_cap={diag.get('generators_at_capacity', 0):2d}  "
                f"bottleneck={bottleneck}"
            )

            results.append({
                "year":                   year,
                "month":                  month,
                "iteration":              iteration,
                "status":                 status,
                "bottleneck":             bottleneck,
                "total_demand_MWh":       diag.get("total_demand_MWh", 0),
                "load_shed_MWh":          diag.get("total_load_shed_MWh", 0),
                "load_shed_pct":          shed_pct,
                "buses_with_shedding":    diag.get("buses_with_shedding", 0),
                "max_line_loading_pct":   diag.get("max_line_loading", 0) * 100,
                "congested_lines":        diag.get("congested_lines", 0),
                "generators_at_capacity": diag.get("generators_at_capacity", 0),
                "solve_time_s":           diag.get("solve_time_s", 0),
            })

        except Exception as e:
            log.error(f"  {month.upper():>3}  error: {e}", exc_info=True)

    df = pd.DataFrame(results)
    if df.empty:
        return df

    # Summary
    adequate   = (df["status"] == "ADEQUATE").sum()
    inadequate = (df["status"] == "INADEQUATE").sum()
    log.info("")
    log.info("=" * 70)
    log.info(f"SUMMARY after iteration {iteration:02d}")
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
        log.info(
            f"  Network still inadequate. Create a new additions YAML and "
            f"run again with --iteration {iteration + 1}"
        )
    else:
        log.info("  All months adequate.")
        log.info(
            f"  Network is ready. Next step: run 01_setup_year.py "
            f"--source-year {year} --target-year <next_year>"
        )

    log.info("=" * 70)

    return df


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Apply capacity additions to a planning year and revalidate."
    )
    parser.add_argument(
        "--year", type=int, required=True,
        help="Planning year to modify (e.g. 2030)"
    )
    parser.add_argument(
        "--additions", type=str, required=True,
        help="Path to additions YAML file"
    )
    parser.add_argument(
        "--iteration", type=int, default=1,
        help="Iteration number for tracking (default: 1). Increment each run."
    )
    args = parser.parse_args()

    log = setup_logging(args.year, args.iteration, RESULTS_DIR)
    config = load_config(CONFIG_PATH)

    additions_path = Path(args.additions)
    if not additions_path.exists():
        print(f"Additions file not found: {additions_path}")
        return

    additions = load_additions(additions_path)

    df = apply_and_validate(args.year, additions, config, args.iteration, log)

    if not df.empty:
        out_path = RESULTS_DIR / f"additions_{args.year}_iter{args.iteration:02d}.csv"
        df.to_csv(out_path, index=False)
        log.info(f"Results saved: {out_path}")


if __name__ == "__main__":
    main()
