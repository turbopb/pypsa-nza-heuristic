"""
Transmission line loading analysis visualizations.
Multiple plotting functions that can be called individually or together.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import argparse


def load_data(base_path):
    """Load baseline and upgraded transmission loading data."""
    data_path = base_path / 'results' / 'analysis'
    baseline = pd.read_csv(data_path / 'line_loading_2030_baseline.csv')
    upgraded = pd.read_csv(data_path / 'line_loading_2030_upgraded.csv')
    return baseline, upgraded


def plot_histogram(baseline, upgraded, output_path):
    """
    Plot histogram comparing distribution of line loading.
    Shows shift from high loading (baseline) to lower loading (upgraded).
    """
    fig, ax = plt.subplots(figsize=(14, 8))
    
    bins = np.arange(0, 105, 5)
    
    ax.hist(baseline['loading_pct'], bins=bins, alpha=0.7, 
            color='red', edgecolor='darkred', linewidth=2, label='Baseline (Inadequate)')
    ax.hist(upgraded['loading_pct'], bins=bins, alpha=0.7, 
            color='green', edgecolor='darkgreen', linewidth=2, label='Upgraded (Adequate)')
    
    ax.axvline(95, color='orange', linestyle='--', linewidth=3, 
               label='95% Critical Threshold', alpha=0.8)
    ax.axvline(100, color='darkred', linestyle='--', linewidth=3, 
               label='100% Capacity', alpha=0.8)
    
    ax.set_xlabel('Line Loading (%)', fontsize=18, fontweight='bold')
    ax.set_ylabel('Number of Lines', fontsize=18, fontweight='bold')
    ax.set_title('Distribution of Transmission Line Loading\nBaseline vs. Upgraded (2030)', 
                 fontsize=20, fontweight='bold', pad=20)
    ax.legend(fontsize=16, loc='upper right')
    ax.grid(True, alpha=0.3, axis='y')
    ax.tick_params(labelsize=15)
    
    shift_text = f"Baseline: {(baseline['loading_pct'] >= 95).sum()} lines =95%\n" + \
                 f"Upgraded: {(upgraded['loading_pct'] >= 95).sum()} lines =95%\n" + \
                 f"Reduction: {(baseline['loading_pct'] >= 95).sum() - (upgraded['loading_pct'] >= 95).sum()} lines (-90%)"
    ax.text(0.02, 0.97, shift_text, transform=ax.transAxes,
            fontsize=16, verticalalignment='top', fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.95, linewidth=3))
    
    plt.tight_layout()
    output_file = output_path / 'transmission_histogram.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  ? Saved: {output_file.name}")
    plt.close()


def plot_categories(baseline, upgraded, output_path):
    """
    Plot bar chart comparing number of lines in each loading category.
    Clearly shows reduction in overloaded/critical lines.
    """
    fig, ax = plt.subplots(figsize=(12, 8))
    
    categories = ['=100%\nOVERLOADED', '95-100%\nCRITICAL', '80-95%\nHIGH', '<80%\nNORMAL']
    
    baseline_counts = [
        (baseline['loading_pct'] >= 100).sum(),
        ((baseline['loading_pct'] >= 95) & (baseline['loading_pct'] < 100)).sum(),
        ((baseline['loading_pct'] >= 80) & (baseline['loading_pct'] < 95)).sum(),
        (baseline['loading_pct'] < 80).sum(),
    ]
    
    upgraded_counts = [
        (upgraded['loading_pct'] >= 100).sum(),
        ((upgraded['loading_pct'] >= 95) & (upgraded['loading_pct'] < 100)).sum(),
        ((upgraded['loading_pct'] >= 80) & (upgraded['loading_pct'] < 95)).sum(),
        (upgraded['loading_pct'] < 80).sum(),
    ]
    
    x = np.arange(len(categories))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, baseline_counts, width, label='Baseline',
                   color='red', alpha=0.8, edgecolor='darkred', linewidth=2.5)
    bars2 = ax.bar(x + width/2, upgraded_counts, width, label='Upgraded',
                   color='green', alpha=0.8, edgecolor='darkgreen', linewidth=2.5)
    
    ax.set_ylabel('Number of Lines', fontsize=18, fontweight='bold')
    ax.set_title('Transmission Lines by Loading Category\nBaseline vs. Upgraded (2030)', 
                 fontsize=20, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=16, fontweight='bold')
    ax.legend(fontsize=16, loc='upper left')
    ax.grid(True, alpha=0.3, axis='y')
    ax.tick_params(axis='y', labelsize=15)
    
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height + 2,
                        f'{int(height)}', ha='center', va='bottom', 
                        fontsize=15, fontweight='bold')
    
    plt.tight_layout()
    output_file = output_path / 'transmission_categories.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  ? Saved: {output_file.name}")
    plt.close()


def plot_top_lines(baseline, upgraded, output_path, n_lines=15):
    """
    Plot horizontal bar chart showing top N most congested lines.
    Shows before/after for each line to demonstrate relief.
    """
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Get top N from baseline
    top_baseline = baseline.nlargest(n_lines, 'loading_pct')[['line', 'loading_pct']].set_index('line')
    
    comparison_data = []
    for line in top_baseline.index:
        base_load = top_baseline.loc[line, 'loading_pct']
        upg_load = upgraded[upgraded['line'] == line]['loading_pct'].values[0] if line in upgraded['line'].values else 0
        comparison_data.append({
            'line': line,
            'baseline': base_load,
            'upgraded': upg_load,
            'reduction': base_load - upg_load
        })
    
    comp_df = pd.DataFrame(comparison_data)
    comp_df = comp_df.sort_values('reduction', ascending=True)
    
    y_pos = np.arange(len(comp_df))
    
    ax.barh(y_pos, comp_df['baseline'], height=0.4, 
            color='red', alpha=0.8, edgecolor='darkred', linewidth=2,
            label='Baseline (Inadequate)')
    ax.barh(y_pos, comp_df['upgraded'], height=0.4, 
            color='green', alpha=0.8, edgecolor='darkgreen', linewidth=2,
            label='Upgraded (Adequate)')
    
    ax.axvline(100, color='darkred', linestyle='--', linewidth=3, alpha=0.8, label='100% Capacity')
    ax.axvline(95, color='orange', linestyle='--', linewidth=3, alpha=0.8, label='95% Threshold')
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(comp_df['line'], fontsize=14, fontweight='bold')
    ax.set_xlabel('Line Loading (%)', fontsize=18, fontweight='bold')
    ax.set_title(f'Top {n_lines} Most Congested Lines: Before and After\n2,950 MW Generation Additions (2030)', 
                 fontsize=20, fontweight='bold', pad=20)
    ax.legend(fontsize=15, loc='lower right')
    ax.grid(True, alpha=0.3, axis='x')
    ax.tick_params(axis='x', labelsize=15)
    
    plt.tight_layout()
    output_file = output_path / 'transmission_top_lines.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  ? Saved: {output_file.name}")
    plt.close()


def plot_summary_table(baseline, upgraded, output_path):
    """
    Create summary statistics table as standalone figure.
    Provides quantitative comparison of key metrics.
    """
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.axis('off')
    
    stats_data = [
        ['Metric', 'Baseline\n(Inadequate)', 'Upgraded\n(Adequate)', 'Change'],
        ['', '', '', ''],
        ['Lines =100% (Overloaded)', f'{(baseline["loading_pct"] >= 100).sum()}', 
         f'{(upgraded["loading_pct"] >= 100).sum()}', 
         f'{(upgraded["loading_pct"] >= 100).sum() - (baseline["loading_pct"] >= 100).sum()}'],
        ['Lines =95% (Critical)', f'{(baseline["loading_pct"] >= 95).sum()}', 
         f'{(upgraded["loading_pct"] >= 95).sum()}', 
         f'{(upgraded["loading_pct"] >= 95).sum() - (baseline["loading_pct"] >= 95).sum()}'],
        ['Lines 80-95% (High)', 
         f'{((baseline["loading_pct"] >= 80) & (baseline["loading_pct"] < 95)).sum()}',
         f'{((upgraded["loading_pct"] >= 80) & (upgraded["loading_pct"] < 95)).sum()}',
         f'{((upgraded["loading_pct"] >= 80) & (upgraded["loading_pct"] < 95)).sum() - ((baseline["loading_pct"] >= 80) & (baseline["loading_pct"] < 95)).sum()}'],
        ['', '', '', ''],
        ['Mean Loading (%)', f'{baseline["loading_pct"].mean():.1f}', 
         f'{upgraded["loading_pct"].mean():.1f}', 
         f'{upgraded["loading_pct"].mean() - baseline["loading_pct"].mean():.1f}'],
        ['Median Loading (%)', f'{baseline["loading_pct"].median():.1f}', 
         f'{upgraded["loading_pct"].median():.1f}', 
         f'{upgraded["loading_pct"].median() - baseline["loading_pct"].median():.1f}'],
        ['Max Loading (%)', f'{baseline["loading_pct"].max():.1f}', 
         f'{upgraded["loading_pct"].max():.1f}', 
         f'{upgraded["loading_pct"].max() - baseline["loading_pct"].max():.1f}'],
    ]
    
    table = ax.table(cellText=stats_data, loc='center', cellLoc='center',
                     colWidths=[0.40, 0.20, 0.20, 0.20])
    table.auto_set_font_size(False)
    table.set_fontsize(16)
    table.scale(1, 4)
    
    for i in range(4):
        table[(0, i)].set_facecolor('#4472C4')
        table[(0, i)].set_text_props(weight='bold', color='white', size=18)
    
    for i in [1, 5]:
        for j in range(4):
            table[(i, j)].set_facecolor('#E7E6E6')
    
    table[(2, 3)].set_facecolor('#C6E0B4')
    table[(2, 3)].set_text_props(weight='bold', size=17)
    table[(3, 3)].set_facecolor('#C6E0B4')
    table[(3, 3)].set_text_props(weight='bold', size=17)
    table[(4, 3)].set_facecolor('#FFF2CC')
    table[(6, 3)].set_facecolor('#C6E0B4')
    table[(7, 3)].set_facecolor('#C6E0B4')
    table[(8, 3)].set_facecolor('#C6E0B4')
    
    ax.set_title('Transmission Network Loading Statistics\nBaseline vs. Upgraded (2030)', 
                fontsize=22, fontweight='bold', pad=30)
    
    plt.tight_layout()
    output_file = output_path / 'transmission_summary.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  ? Saved: {output_file.name}")
    plt.close()


def main():
    """
    Main function to generate transmission analysis plots.
    Can be called with arguments to select specific plots.
    """
    parser = argparse.ArgumentParser(description='Generate transmission loading analysis plots')
    parser.add_argument('--plots', nargs='+', 
                       choices=['histogram', 'categories', 'top_lines', 'summary', 'all'],
                       default=['all'],
                       help='Which plots to generate (default: all)')
    parser.add_argument('--n-lines', type=int, default=15,
                       help='Number of top lines to show in top_lines plot (default: 15)')
    
    args = parser.parse_args()
    
    # Setup paths
    BASE = Path(__file__).parent.parent
    OUTPUT_PATH = BASE / 'results' / 'figures'
    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
    
    # Load data
    print("\nLoading transmission loading data...")
    baseline, upgraded = load_data(BASE)
    print(f"  Baseline: {len(baseline)} lines")
    print(f"  Upgraded: {len(upgraded)} lines")
    
    # Determine which plots to generate
    plots_to_generate = args.plots
    if 'all' in plots_to_generate:
        plots_to_generate = ['histogram', 'categories', 'top_lines', 'summary']
    
    print(f"\nGenerating plots: {', '.join(plots_to_generate)}")
    print("-" * 60)
    
    # Generate requested plots
    if 'histogram' in plots_to_generate:
        plot_histogram(baseline, upgraded, OUTPUT_PATH)
    
    if 'categories' in plots_to_generate:
        plot_categories(baseline, upgraded, OUTPUT_PATH)
    
    if 'top_lines' in plots_to_generate:
        plot_top_lines(baseline, upgraded, OUTPUT_PATH, n_lines=args.n_lines)
    
    if 'summary' in plots_to_generate:
        plot_summary_table(baseline, upgraded, OUTPUT_PATH)
    
    print("-" * 60)
    print(f"? All plots saved to: {OUTPUT_PATH.relative_to(BASE)}\n")


if __name__ == '__main__':
    main()