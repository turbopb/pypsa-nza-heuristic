"""
plot_adequacy_results.py

Composite adequacy validation figure for all planning horizons.

For each year (2024, 2030, 2035, 2040), produces a row of 3 panels:
  Panel 1: Load shed % by month before additions (coloured by bottleneck type)
  Panel 2: Load shed % by month after final iteration
  Panel 3: Congested lines + max line loading % before vs after (dual axis)

Output: results/validation/adequacy_results.png

Run from repo root:
    python plot_adequacy_results.py
"""

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

RESULTS_DIR = Path(
    r"C:\Users\Public\Documents\Thesis\analysis\pypsa-nza-heuristic\results\validation"
)

OUTPUT_PATH = RESULTS_DIR / "adequacy_results.png"

# ---------------------------------------------------------------------------
# Data sources: (year, before_csv, after_csv or None)
# ---------------------------------------------------------------------------

DATASETS = [
    (2024, "annual_summary_2024.csv",     None),
    (2030, "annual_summary_2030.csv",     "additions_2030_iter03.csv"),
    (2035, "annual_summary_2035.csv",     "additions_2035_iter01.csv"),
    (2040, "annual_summary_2040.csv",     "additions_2040_iter01.csv"),
]

MONTHS_ORDER = ["jan","feb","mar","apr","may","jun",
                "jul","aug","sep","oct","nov","dec"]
MONTH_LABELS = ["J","F","M","A","M","J","J","A","S","O","N","D"]

ADEQUACY_THRESHOLD = 0.01  # %

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------

BOTTLENECK_COLOURS = {
    "ADEQUATE":     "#2ecc71",
    "GENERATION":   "#e74c3c",
    "TRANSMISSION": "#3498db",
    "MIXED":        "#e67e22",
}

BEFORE_LINE_COLOUR = "#c0392b"
AFTER_LINE_COLOUR  = "#27ae60"
LOAD_COLOUR        = "#2c3e50"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_csv(results_dir: Path, filename: str) -> pd.DataFrame:
    path = results_dir / filename
    df = pd.read_csv(path)
    df["month"] = df["month"].str.lower()
    df = df.set_index("month").reindex(MONTHS_ORDER)
    return df


def month_colours(df: pd.DataFrame) -> list:
    return [BOTTLENECK_COLOURS.get(b, "#95a5a6")
            for b in df["bottleneck"].fillna("ADEQUATE")]


def shed_values(df: pd.DataFrame) -> np.ndarray:
    return df["load_shed_pct"].fillna(0).values


def congested_values(df: pd.DataFrame) -> np.ndarray:
    return df["congested_lines"].fillna(0).values


def max_loading_values(df: pd.DataFrame) -> np.ndarray:
    return df["max_line_loading_pct"].fillna(0).values


# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------

def make_figure(datasets, results_dir: Path) -> plt.Figure:
    n_years = len(datasets)
    fig, axes = plt.subplots(
        n_years, 3,
        figsize=(16, 4.2 * n_years),
        gridspec_kw={"wspace": 0.38, "hspace": 0.52}
    )

    x = np.arange(len(MONTHS_ORDER))
    bar_w = 0.38

    for row, (year, before_file, after_file) in enumerate(datasets):
        ax1, ax2, ax3 = axes[row]

        df_before = load_csv(results_dir, before_file)
        df_after  = load_csv(results_dir, after_file) if after_file else None

        colours_before = month_colours(df_before)
        shed_before    = shed_values(df_before)
        cong_before    = congested_values(df_before)
        load_before    = max_loading_values(df_before)

        # --- Panel 1: load shed before ---
        bars = ax1.bar(x, shed_before, color=colours_before,
                       edgecolor="white", linewidth=0.4, zorder=3)
        ax1.axhline(ADEQUACY_THRESHOLD, color="#7f8c8d", linewidth=1.0,
                    linestyle="--", label=f"Threshold ({ADEQUACY_THRESHOLD}%)", zorder=4)
        ax1.set_xticks(x)
        ax1.set_xticklabels(MONTH_LABELS, fontsize=8)
        ax1.set_ylabel("Load shed (%)", fontsize=8)
        ax1.set_title(f"{year}  |  Before additions", fontsize=9, fontweight="bold")
        ax1.yaxis.grid(True, linestyle=":", alpha=0.5, zorder=0)
        ax1.set_axisbelow(True)
        max_shed = max(shed_before.max(), 0.02)
        ax1.set_ylim(0, max_shed * 1.20)

        # bottleneck legend (row 0 only)
        if row == 0:
            handles = [mpatches.Patch(color=c, label=l)
                       for l, c in BOTTLENECK_COLOURS.items()]
            ax1.legend(handles=handles, fontsize=6.5, loc="upper right",
                       framealpha=0.85, ncol=2)

        # --- Panel 2: load shed after (or baseline note) ---
        if df_after is not None:
            colours_after = month_colours(df_after)
            shed_after    = shed_values(df_after)
            bars2 = ax2.bar(x, shed_after, color=colours_after,
                            edgecolor="white", linewidth=0.4, zorder=3)
            ax2.axhline(ADEQUACY_THRESHOLD, color="#7f8c8d", linewidth=1.0,
                        linestyle="--", zorder=4)
            ax2.set_ylim(0, max(shed_after.max() * 1.20, ADEQUACY_THRESHOLD * 2))
            ax2.set_title(f"{year}  |  After additions", fontsize=9, fontweight="bold")
        else:
            ax2.text(0.5, 0.5,
                     "2024 baseline:\nno iterations applied.\nUsed as source for\n2030 network.",
                     ha="center", va="center", fontsize=9,
                     transform=ax2.transAxes,
                     bbox=dict(boxstyle="round,pad=0.5", facecolor="#ecf0f1", alpha=0.8))
            ax2.set_title(f"{year}  |  Baseline (no additions)", fontsize=9, fontweight="bold")
            ax2.set_xticks(x)
            ax2.set_xticklabels(MONTH_LABELS, fontsize=8)

        ax2.set_xticks(x)
        ax2.set_xticklabels(MONTH_LABELS, fontsize=8)
        ax2.set_ylabel("Load shed (%)", fontsize=8)
        ax2.yaxis.grid(True, linestyle=":", alpha=0.5, zorder=0)
        ax2.set_axisbelow(True)

        # --- Panel 3: congested lines + max line loading before vs after ---
        ax3b = ax3.twinx()

        # grouped bars: congested lines
        offset = bar_w / 2
        ax3.bar(x - offset, cong_before, width=bar_w,
                color=BEFORE_LINE_COLOUR, alpha=0.75, label="Congested lines (before)", zorder=3)

        if df_after is not None:
            cong_after = congested_values(df_after)
            load_after = max_loading_values(df_after)
            ax3.bar(x + offset, cong_after, width=bar_w,
                    color=AFTER_LINE_COLOUR, alpha=0.75, label="Congested lines (after)", zorder=3)
            ax3b.plot(x, load_after, color=AFTER_LINE_COLOUR, marker="o",
                      markersize=3.5, linewidth=1.2, linestyle="-",
                      label="Max loading % (after)", zorder=5)

        ax3b.plot(x, load_before, color=BEFORE_LINE_COLOUR, marker="s",
                  markersize=3.5, linewidth=1.2, linestyle="--",
                  label="Max loading % (before)", zorder=5)
        ax3b.axhline(100, color="#95a5a6", linewidth=0.8, linestyle=":", zorder=2)

        ax3.set_xticks(x)
        ax3.set_xticklabels(MONTH_LABELS, fontsize=8)
        ax3.set_ylabel("Congested lines (count)", fontsize=8)
        ax3b.set_ylabel("Max line loading (%)", fontsize=8)
        ax3.set_title(f"{year}  |  Transmission stress", fontsize=9, fontweight="bold")
        ax3.yaxis.grid(True, linestyle=":", alpha=0.4, zorder=0)
        ax3.set_axisbelow(True)
        ax3.set_ylim(bottom=0)
        ax3b.set_ylim(0, 115)

        # combined legend for panel 3
        h1, l1 = ax3.get_legend_handles_labels()
        h2, l2 = ax3b.get_legend_handles_labels()
        ax3.legend(h1 + h2, l1 + l2, fontsize=6, loc="upper right", framealpha=0.85)

    fig.suptitle(
        "NZ Electricity System — Adequacy Validation by Planning Horizon",
        fontsize=13, fontweight="bold", y=1.01
    )

    return fig


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    fig = make_figure(DATASETS, RESULTS_DIR)
    fig.savefig(OUTPUT_PATH, dpi=180, bbox_inches="tight")
    print(f"Saved: {OUTPUT_PATH}")
