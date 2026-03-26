"""
plot_capacity_additions.py

Capacity additions figure across all planning horizons.

For each year (2030, 2035, 2040), produces a row of 4 panels:
  Panel 1: Generation capacity before additions (by carrier) vs peak demand
  Panel 2: Generation capacity after additions (baseline + added) vs peak demand
  Panel 3: Transmission stress before additions (congested lines + max loading)
  Panel 4: Transmission stress after additions (congested lines + max loading)

Data sources:
  - generators.csv from network CSV folders  --> capacity (month-invariant)
  - loads-p_set.csv from network CSV folders --> peak demand per month
  - annual_summary_{year}.csv               --> before tx metrics
  - additions_{year}_iter{N}.csv            --> after tx metrics

  Baseline for year Y = network CSVs from year Y-1 (since 01_setup_year.py
  copies the final Y-1 state into Y before scaling demand). Final state for
  year Y = network CSVs from year Y (after all iterations).

Run from repo root:
    python plot_capacity_additions.py
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.ticker import MaxNLocator
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

CASES_ROOT = Path(
    r"C:\Users\Public\Documents\Thesis\analysis\dispatch_data\cases\reference"
)

RESULTS_DIR = Path(
    r"C:\Users\Public\Documents\Thesis\analysis\pypsa-nza-heuristic\results\validation"
)

OUTPUT_PATH = RESULTS_DIR / "capacity_additions.png"

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# (planning_year, baseline_year, after_tx_csv)
# baseline_year network CSVs = state before any additions for planning_year
# planning_year network CSVs = state after all iterations for planning_year
YEAR_CONFIG = [
    (2030, 2024, "additions_2030_iter03.csv"),
    (2035, 2030, "additions_2035_iter01.csv"),
    (2040, 2035, "additions_2040_iter01.csv"),
]

MONTHS_ORDER = ["jan", "feb", "mar", "apr", "may", "jun",
                "jul", "aug", "sep", "oct", "nov", "dec"]
MONTH_LABELS = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]

ADEQUACY_THRESHOLD = 0.01  # %

# Carrier display order and colours
CARRIER_COLOURS = {
    "hydro":      "#3498db",
    "geothermal": "#e74c3c",
    "wind":       "#2ecc71",
    "gas":        "#e67e22",
    "solar_pv":   "#f1c40f",
    "diesel":     "#7f8c8d",
}
CARRIER_ORDER = ["hydro", "geothermal", "wind", "gas", "solar_pv", "diesel"]

BEFORE_COLOUR = "#c0392b"
AFTER_COLOUR  = "#27ae60"

# ---------------------------------------------------------------------------
# Data reading
# ---------------------------------------------------------------------------

def read_capacity_by_carrier(year: int) -> pd.Series:
    """
    Read generators.csv from jan_{year} and return total p_nom by carrier.
    Month is irrelevant -- capacity is the same across all 12 monthly networks.
    """
    path = CASES_ROOT / str(year) / f"jan_{year}" / "generators.csv"
    df = pd.read_csv(path, usecols=["carrier", "p_nom"])
    return df.groupby("carrier")["p_nom"].sum()


def read_annual_peak_demand(year: int) -> float:
    """
    Read loads-p_set.csv from each month and return the highest
    hourly total system load found across the full year (MW).
    """
    annual_peak = 0.0
    for month in MONTHS_ORDER:
        path = CASES_ROOT / str(year) / f"{month}_{year}" / "loads-p_set.csv"
        if not path.exists():
            continue
        df = pd.read_csv(path, index_col=0)
        # Sum all load buses per timestep, take monthly peak
        monthly_peak = df.sum(axis=1).max()
        if monthly_peak > annual_peak:
            annual_peak = monthly_peak
    return annual_peak


def read_tx_metrics(csv_path: Path) -> pd.DataFrame:
    """Read a validation results CSV and reindex to canonical month order."""
    df = pd.read_csv(csv_path)
    df["month"] = df["month"].str.lower()
    return df.set_index("month").reindex(MONTHS_ORDER)


# ---------------------------------------------------------------------------
# Panel: generation capacity
# ---------------------------------------------------------------------------

def plot_generation_panel(
    ax,
    cap_baseline: pd.Series,
    cap_added: pd.Series,
    peak_demand: float,
    title: str,
    is_first_row: bool,
):
    """
    Horizontal stacked bar chart, one bar per carrier.
      cap_baseline : MW already installed (solid bar)
      cap_added    : MW added this iteration (hatched segment on top, same colour)
      peak_demand  : vertical dashed line showing annual system peak (MW)
    """
    # Build ordered list of all carriers that have any capacity
    all_carriers = CARRIER_ORDER + [
        c for c in cap_baseline.index.union(cap_added.index)
        if c not in CARRIER_ORDER
    ]
    # Filter to carriers with non-zero presence
    carriers = [
        c for c in all_carriers
        if cap_baseline.get(c, 0) > 0 or cap_added.get(c, 0) > 0
    ]

    y         = np.arange(len(carriers))
    bar_h     = 0.55
    baseline  = np.array([cap_baseline.get(c, 0) for c in carriers])
    added     = np.array([cap_added.get(c, 0)    for c in carriers])
    colours   = [CARRIER_COLOURS.get(c, "#95a5a6") for c in carriers]

    # Baseline bars
    ax.barh(y, baseline, height=bar_h, color=colours,
            edgecolor="white", linewidth=0.4, zorder=3)

    # Added capacity: same colour, lighter + hatched
    ax.barh(y, added, height=bar_h, left=baseline,
            color=colours, alpha=0.45, edgecolor="white",
            linewidth=0.4, hatch="///", zorder=3)

    # Peak demand reference line
    ax.axvline(peak_demand, color="#2c3e50", linewidth=1.4,
               linestyle="--", zorder=5,
               label=f"Annual peak demand\n({peak_demand:,.0f} MW)")

    ax.set_yticks(y)
    ax.set_yticklabels(carriers, fontsize=7)
    ax.set_xlabel("Installed capacity (MW)", fontsize=8)
    ax.set_title(title, fontsize=9, fontweight="bold")
    ax.xaxis.grid(True, linestyle=":", alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.set_xlim(left=0)

    if is_first_row:
        carrier_patches = [
            mpatches.Patch(color=CARRIER_COLOURS.get(c, "#95a5a6"), label=c)
            for c in carriers
        ]
        added_patch = mpatches.Patch(
            facecolor="#aaaaaa", alpha=0.45, hatch="///",
            edgecolor="grey", label="Added this horizon"
        )
        demand_line = plt.Line2D(
            [0], [0], color="#2c3e50", linewidth=1.4,
            linestyle="--", label="Annual peak demand"
        )
        ax.legend(
            handles=carrier_patches + [added_patch, demand_line],
            fontsize=6, loc="lower right", framealpha=0.85, ncol=1
        )


# ---------------------------------------------------------------------------
# Panel: transmission stress
# ---------------------------------------------------------------------------

def plot_tx_panel(
    ax,
    df: pd.DataFrame,
    title: str,
    colour: str,
    is_first_row: bool,
):
    """
    Vertical bars: congested line count per month.
    Dashed line (right axis): max line loading %.
    """
    ax2 = ax.twinx()

    x       = np.arange(len(MONTHS_ORDER))
    cong    = df["congested_lines"].fillna(0).values
    maxload = df["max_line_loading_pct"].fillna(0).values

    ax.bar(x, cong, width=0.65, color=colour, alpha=0.75,
           label="Congested lines", zorder=3)
    ax2.plot(x, maxload, color=colour, marker="s", markersize=3.5,
             linewidth=1.2, linestyle="--", label="Max loading %", zorder=5)
    ax2.axhline(100, color="#95a5a6", linewidth=0.8, linestyle=":", zorder=2)
    ax.axhline(ADEQUACY_THRESHOLD, color="#7f8c8d", linewidth=0,
               linestyle="")  # invisible, keeps spacing consistent

    ax.set_xticks(x)
    ax.set_xticklabels(MONTH_LABELS, fontsize=8)
    ax.set_ylabel("Congested lines (count)", fontsize=8)
    ax2.set_ylabel("Max line loading (%)", fontsize=8)
    ax.set_title(title, fontsize=9, fontweight="bold")
    ax.yaxis.grid(True, linestyle=":", alpha=0.4, zorder=0)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax2.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_axisbelow(True)
    ax.set_ylim(bottom=0)
    ax2.set_ylim(0, 115)

    if is_first_row:
        h1, l1 = ax.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        ax.legend(h1 + h2, l1 + l2, fontsize=6.5,
                  loc="upper right", framealpha=0.85)


# ---------------------------------------------------------------------------
# Main figure
# ---------------------------------------------------------------------------

def make_figure(year_config, results_dir: Path) -> plt.Figure:
    n_rows = len(year_config)

    fig, axes = plt.subplots(
        n_rows, 4,
        figsize=(20, 4.8 * n_rows),
        gridspec_kw={"wspace": 0.50, "hspace": 0.55}
    )

    for row, (year, baseline_year, after_csv) in enumerate(year_config):
        ax_gb, ax_ga, ax_tb, ax_ta = axes[row]
        is_first = (row == 0)

        # --- Generation capacity ---
        cap_baseline = read_capacity_by_carrier(baseline_year)
        cap_final    = read_capacity_by_carrier(year)

        # Added = final - baseline, clipped to zero (no carrier should shrink)
        all_carriers = cap_final.index.union(cap_baseline.index)
        cap_added = (
            cap_final.reindex(all_carriers, fill_value=0)
            - cap_baseline.reindex(all_carriers, fill_value=0)
        ).clip(lower=0)

        peak_demand = read_annual_peak_demand(year)

        # --- Transmission metrics ---
        df_before_tx = read_tx_metrics(results_dir / f"annual_summary_{year}.csv")
        df_after_tx  = read_tx_metrics(results_dir / after_csv)

        # --- Plot ---
        plot_generation_panel(
            ax_gb, cap_baseline, pd.Series(dtype=float), peak_demand,
            f"{year}  |  Generation — before\n(base: {baseline_year} network)",
            is_first
        )
        plot_generation_panel(
            ax_ga, cap_baseline, cap_added, peak_demand,
            f"{year}  |  Generation — after\n(baseline + additions)",
            is_first_row=False
        )
        plot_tx_panel(
            ax_tb, df_before_tx,
            f"{year}  |  Transmission — before",
            BEFORE_COLOUR, is_first
        )
        plot_tx_panel(
            ax_ta, df_after_tx,
            f"{year}  |  Transmission — after",
            AFTER_COLOUR, is_first_row=False
        )

    # Column headers
    col_titles = [
        "Generation capacity — before additions",
        "Generation capacity — after additions",
        "Transmission stress — before additions",
        "Transmission stress — after additions",
    ]
    for ax, ctitle in zip(axes[0], col_titles):
        ax.annotate(
            ctitle, xy=(0.5, 1.18), xycoords="axes fraction",
            ha="center", fontsize=9, fontstyle="italic", color="#555555"
        )

    fig.suptitle(
        "NZ Electricity System \u2014 Capacity Additions by Planning Horizon",
        fontsize=13, fontweight="bold", y=1.02
    )

    return fig


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    fig = make_figure(YEAR_CONFIG, RESULTS_DIR)
    fig.savefig(OUTPUT_PATH, dpi=180, bbox_inches="tight")
    print(f"Saved: {OUTPUT_PATH}")
