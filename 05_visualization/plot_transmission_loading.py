"""
Plot transmission line loading for 2030 baseline and upgraded systems.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pypsa

print("Loading networks and analyzing transmission...")

# Load both networks
baseline = pypsa.Network()
baseline.import_from_csv_folder(r"C:\Users\Public\Documents\Thesis\analysis\dispatch_data\cases\reference\2030\baseline_2030")

upgraded = pypsa.Network()
upgraded.import_from_csv_folder(r"C:\Users\Public\Documents\Thesis\analysis\dispatch_data\cases\reference\2030\upgraded_2030")

# Run optimization for both (needed to get line loadings)
print("Running baseline optimization...")
baseline.optimize(solver_name='highs')

print("Running upgraded optimization...")
upgraded.optimize(solver_name='highs')

# Calculate line loadings
baseline_loading = (baseline.lines_t.p0.abs().max() / baseline.lines.s_nom * 100).sort_values(ascending=False)
upgraded_loading = (upgraded.lines_t.p0.abs().max() / upgraded.lines.s_nom * 100).sort_values(ascending=False)

# Get top congested lines
n_top = 30
top_lines = baseline_loading.head(n_top).index

# Count congested lines
baseline_congested = (baseline_loading > 95).sum()
upgraded_congested = (upgraded_loading > 95).sum()

print(f"\nBaseline: {baseline_congested} lines >95% loaded")
print(f"Upgraded: {upgraded_congested} lines >95% loaded")

# Create figure with subplots
fig = plt.figure(figsize=(16, 10))
gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)

# ============================================================
# Plot 1: Histogram of all line loadings (top left)
# ============================================================
ax1 = fig.add_subplot(gs[0, 0])

bins = np.linspace(0, 105, 22)
ax1.hist(baseline_loading, bins=bins, alpha=0.6, label='Baseline', 
         color='red', edgecolor='darkred', linewidth=1.5)
ax1.hist(upgraded_loading, bins=bins, alpha=0.6, label='Upgraded', 
         color='blue', edgecolor='darkblue', linewidth=1.5)

ax1.axvline(x=95, color='orange', linestyle='--', linewidth=2, 
           label='95% Threshold', alpha=0.8)
ax1.axvline(x=100, color='red', linestyle='--', linewidth=2, 
           label='100% Capacity', alpha=0.8)

ax1.set_xlabel('Line Loading (%)', fontsize=12, fontweight='bold')
ax1.set_ylabel('Number of Lines', fontsize=12, fontweight='bold')
ax1.set_title('Distribution of Transmission Line Loading', fontsize=13, fontweight='bold')
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)

# ============================================================
# Plot 2: Top 30 congested lines (top right)
# ============================================================
ax2 = fig.add_subplot(gs[0, 1])

x = np.arange(n_top)
width = 0.35

baseline_top = baseline_loading[top_lines].values
upgraded_top = upgraded_loading[top_lines].values

bars1 = ax2.barh(x - width/2, baseline_top, width, label='Baseline', 
                 color='red', alpha=0.7, edgecolor='darkred', linewidth=1)
bars2 = ax2.barh(x + width/2, upgraded_top, width, label='Upgraded', 
                 color='blue', alpha=0.7, edgecolor='darkblue', linewidth=1)

ax2.axvline(x=95, color='orange', linestyle='--', linewidth=2, alpha=0.7)
ax2.axvline(x=100, color='red', linestyle='--', linewidth=2, alpha=0.7)

ax2.set_yticks(x)
ax2.set_yticklabels(top_lines, fontsize=8)
ax2.set_xlabel('Loading (%)', fontsize=12, fontweight='bold')
ax2.set_ylabel('Line Name', fontsize=12, fontweight='bold')
ax2.set_title(f'Top {n_top} Most Congested Lines', fontsize=13, fontweight='bold')
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3, axis='x')
ax2.invert_yaxis()

# ============================================================
# Plot 3: Cumulative distribution (bottom left)
# ============================================================
ax3 = fig.add_subplot(gs[1, 0])

baseline_sorted = np.sort(baseline_loading)
upgraded_sorted = np.sort(upgraded_loading)

cumulative_baseline = np.arange(1, len(baseline_sorted) + 1) / len(baseline_sorted) * 100
cumulative_upgraded = np.arange(1, len(upgraded_sorted) + 1) / len(upgraded_sorted) * 100

ax3.plot(baseline_sorted, cumulative_baseline, 'r-', linewidth=3, 
        label='Baseline', alpha=0.8)
ax3.plot(upgraded_sorted, cumulative_upgraded, 'b-', linewidth=3, 
        label='Upgraded', alpha=0.8)

ax3.axvline(x=95, color='orange', linestyle='--', linewidth=2, 
           label='95% Threshold', alpha=0.7)
ax3.axvline(x=100, color='red', linestyle='--', linewidth=2, 
           label='100% Capacity', alpha=0.7)

ax3.set_xlabel('Line Loading (%)', fontsize=12, fontweight='bold')
ax3.set_ylabel('Cumulative Percentage of Lines (%)', fontsize=12, fontweight='bold')
ax3.set_title('Cumulative Distribution of Line Loading', fontsize=13, fontweight='bold')
ax3.legend(fontsize=10)
ax3.grid(True, alpha=0.3)
ax3.set_xlim(0, 105)

# ============================================================
# Plot 4: Summary statistics table (bottom right)
# ============================================================
ax4 = fig.add_subplot(gs[1, 1])
ax4.axis('off')

# Calculate statistics
stats_data = [
    ['Metric', 'Baseline', 'Upgraded', 'Change'],
    ['', '', '', ''],
    ['Total Lines', f'{len(baseline_loading)}', f'{len(upgraded_loading)}', '---'],
    ['Lines >95%', f'{baseline_congested}', f'{upgraded_congested}', 
     f'{upgraded_congested - baseline_congested:+d}'],
    ['Lines at 100%', f'{(baseline_loading >= 100).sum()}', 
     f'{(upgraded_loading >= 100).sum()}', 
     f'{(upgraded_loading >= 100).sum() - (baseline_loading >= 100).sum():+d}'],
    ['', '', '', ''],
    ['Max Loading', f'{baseline_loading.max():.1f}%', 
     f'{upgraded_loading.max():.1f}%', 
     f'{upgraded_loading.max() - baseline_loading.max():+.1f}%'],
    ['Mean Loading', f'{baseline_loading.mean():.1f}%', 
     f'{upgraded_loading.mean():.1f}%', 
     f'{upgraded_loading.mean() - baseline_loading.mean():+.1f}%'],
    ['Median Loading', f'{baseline_loading.median():.1f}%', 
     f'{upgraded_loading.median():.1f}%', 
     f'{upgraded_loading.median() - baseline_loading.median():+.1f}%'],
]

table = ax4.table(cellText=stats_data, loc='center', cellLoc='center',
                 colWidths=[0.3, 0.25, 0.25, 0.2])
table.auto_set_font_size(False)
table.set_fontsize(11)
table.scale(1, 2.5)

# Style header row
for i in range(4):
    table[(0, i)].set_facecolor('#4472C4')
    table[(0, i)].set_text_props(weight='bold', color='white')

# Style data rows
for i in range(2, len(stats_data)):
    for j in range(4):
        if i == 1 or i == 5:  # Separator rows
            table[(i, j)].set_facecolor('#E7E6E6')
        elif j == 3:  # Change column
            table[(i, j)].set_facecolor('#FFF2CC')

ax4.set_title('Transmission Loading Statistics', fontsize=13, fontweight='bold', pad=20)

# Overall title
fig.suptitle('2030 Transmission Line Loading Analysis: Baseline vs. Upgraded', 
            fontsize=16, fontweight='bold', y=0.98)

plt.savefig('2030_transmission_loading.png', dpi=300, bbox_inches='tight')
print("\n? Transmission loading plot saved to: 2030_transmission_loading.png")

# Print top 10 most congested lines in baseline
print("\n" + "="*70)
print("TOP 10 MOST CONGESTED LINES (BASELINE)")
print("="*70)
for i, (line, loading) in enumerate(baseline_loading.head(10).items(), 1):
    s_nom = baseline.lines.loc[line, 's_nom']
    bus0 = baseline.lines.loc[line, 'bus0']
    bus1 = baseline.lines.loc[line, 'bus1']
    upgraded_load = upgraded_loading[line] if line in upgraded_loading.index else 0
    print(f"{i:2d}. {line:10s} ({bus0}?{bus1}): "
          f"{loading:6.2f}% ({s_nom:4.0f} MVA) ? "
          f"Upgraded: {upgraded_load:6.2f}%")

plt.close()
print("\nDone!")