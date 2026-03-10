"""
01_setup_year.py

Creates a new planning year network by:
  1. Copying all 12 monthly network directories from the source year
  2. Scaling loads-p_set.csv by the year-on-year MBIE demand growth factor

The demand scaling factor is computed as:
    factor = MBIE_absolute[target_year] / MBIE_absolute[source_year]

This means each year's networks contain pre-scaled demand and the
dispatch tool is always called with scaling_factor=1.0.

Usage:
    python 01_setup_year.py --source-year 2024 --target-year 2030
    python 01_setup_year.py --source-year 2030 --target-year 2035
    python 01_setup_year.py --source-year 2035 --target-year 2040

Author: Phillippe Bruneau
"""

import argparse
import shutil
import logging
from pathlib import Path
import pandas as pd
import yaml

# ---------------------------------------------------------------------------
# Configuration -- update if paths change
# ---------------------------------------------------------------------------

CONFIG_PATH = Path(
    r"C:\Users\Public\Documents\Thesis\analysis\pypsa-nza-dispatch\config\dispatch_config.yaml"
)

MONTHS = [
    "jan", "feb", "mar", "apr", "may", "jun",
    "jul", "aug", "sep", "oct", "nov", "dec"
]

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[logging.StreamHandler()],
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_config(config_path: Path) -> dict:
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def get_mbie_factor(config: dict, year: int) -> float:
    """Return the absolute MBIE scaling factor for a given year."""
    factors = config["demand_scenarios"]["reference"]
    if year not in factors:
        raise ValueError(
            f"Year {year} not found in demand_scenarios. "
            f"Available: {sorted(factors.keys())}"
        )
    return factors[year]


def get_cases_root(config: dict) -> Path:
    """Return the root path for case directories."""
    root = Path(config["paths"]["root"])
    return root / "cases" / "reference"


def get_month_dir(cases_root: Path, year: int, month: str) -> Path:
    return cases_root / str(year) / f"{month}_{year}"


def scale_loads(month_dir: Path, factor: float) -> None:
    """
    Scale loads-p_set.csv in place by factor.
    The file has snapshots as rows and load names as columns.
    """
    loads_file = month_dir / "loads-p_set.csv"
    if not loads_file.exists():
        raise FileNotFoundError(f"loads-p_set.csv not found in {month_dir}")

    df = pd.read_csv(loads_file, index_col=0)
    df = df * factor
    df.to_csv(loads_file)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def setup_year(source_year: int, target_year: int, config: dict) -> None:
    cases_root = get_cases_root(config)

    # Compute year-on-year scaling factor
    source_factor = get_mbie_factor(config, source_year)
    target_factor = get_mbie_factor(config, target_year)
    yoy_factor = target_factor / source_factor

    log.info("=" * 60)
    log.info(f"Setting up {target_year} network from {source_year}")
    log.info(f"  MBIE factor {source_year}: {source_factor:.6f}")
    log.info(f"  MBIE factor {target_year}: {target_factor:.6f}")
    log.info(f"  Year-on-year demand scaling factor: {yoy_factor:.6f}")
    log.info("=" * 60)

    # Check source year exists
    source_year_dir = cases_root / str(source_year)
    if not source_year_dir.exists():
        raise FileNotFoundError(
            f"Source year directory not found: {source_year_dir}"
        )

    # Check target year directory does not already exist (safety check)
    target_year_dir = cases_root / str(target_year)
    if target_year_dir.exists():
        log.warning(
            f"Target directory already exists: {target_year_dir}\n"
            f"  Delete it manually if you want to regenerate from scratch."
        )
        raise FileExistsError(
            f"Target year directory already exists: {target_year_dir}. "
            f"Aborting to avoid overwriting existing work."
        )

    # Process each month
    for month in MONTHS:
        source_dir = get_month_dir(cases_root, source_year, month)
        target_dir = get_month_dir(cases_root, target_year, month)

        if not source_dir.exists():
            log.warning(f"  {month}: source directory not found -- skipping ({source_dir})")
            continue

        log.info(f"  {month}: copying {source_dir.name} -> {target_dir.name}")

        # Copy entire directory
        shutil.copytree(str(source_dir), str(target_dir))

        # Scale the demand file
        scale_loads(target_dir, yoy_factor)

        # Verify the scaling was applied
        df_source = pd.read_csv(source_dir / "loads-p_set.csv", index_col=0)
        df_target = pd.read_csv(target_dir / "loads-p_set.csv", index_col=0)
        actual_ratio = df_target.values.sum() / df_source.values.sum()
        log.info(
            f"         demand scaling verified: "
            f"{actual_ratio:.6f} (expected {yoy_factor:.6f})"
        )

    log.info("")
    log.info(f"Done. {target_year} networks written to: {target_year_dir}")
    log.info(
        f"Next step: run 02_validate_year.py --year {target_year} "
        f"to check adequacy."
    )


def main():
    parser = argparse.ArgumentParser(
        description="Create a new planning year network by copying and scaling demand."
    )
    parser.add_argument(
        "--source-year", type=int, required=True,
        help="Source year to copy from (e.g. 2024)"
    )
    parser.add_argument(
        "--target-year", type=int, required=True,
        help="Target year to create (e.g. 2030)"
    )
    args = parser.parse_args()

    config = load_config(CONFIG_PATH)
    setup_year(args.source_year, args.target_year, config)


if __name__ == "__main__":
    main()
