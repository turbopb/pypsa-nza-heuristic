# -*- coding: utf-8 -*-
"""
Visualize 2024 annual validation results showing seasonal patterns.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Paths
BASE = Path(__file__).parent.parent
DATA_FILE = BASE / 'results' / 'validation' / 'annual_summary_2024.csv'
OUTPUT_PATH = BASE / 'results' / 'figures'

# Load data
df = pd.read_csv(DATA_FILE)

# Month order
month_order = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
               'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
df['month'] = pd.Categorical(df['month'], categories=month_order, ordered=True)
df = df.sort_values('month')

# Create figure
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), height_ratios=[2, 1])

# ============================================
# Plot 1: Load Shedding by Month
# ============================================

months_display = [m.upper() for m in month_order]
x = np.arange(len(months_display))

# Color code by adequacy status
colors = ['green' if status == 'ADEQUATE' else 'red' 
          for status in df['status']]

bars = ax1.bar(x, df['load_shed_pct'], color=colors, alpha=0.8, 
               edgecolor='black', linewidth=2)

# Add threshold line
ax1.axhline(y=0.1, color='orange', linestyle='--', linewidth=2.5, 
           label='0.1% Threshold (Nominal Adequacy)', alpha=0.8)

ax1.set_xlabel('Month', fontsize=16, fontweight='bold')
ax1.set_ylabel('Load Shedding (%)', fontsize=16, fontweight='bold')
ax1.set_title('2024 Baseline Network: Monthly Load Shedding\nSeasonal Adequacy Pattern', 
             fontsize=18, fontweight='bold', pad=20)
ax1.set_xticks(x)
ax1.set_xticklabels(months_display, fontsize=14, fontweight='bold')
ax1.tick_params(axis='y', labelsize=13)
ax1.grid(True, alpha=0.3, axis='y')

# Add value labels on bars
for i, (bar, val) in enumerate(zip(bars, df['load_shed_pct'])):
    if val > 0.05:  # Only label significant values
        ax1.text(bar.get_x() + bar.get_width()/2., val + 0.05,
                f'{val:.2f}%', ha='center', va='bottom', 
                fontsize=11, fontweight='bold')

# Add seasonal shading
summer_months = [10, 11, 0, 1, 2, 3]  # Nov-Apr (NZ summer)
winter_months = [4, 5, 6, 7, 8, 9]    # May-Oct (NZ winter)

ax1.axvspan(-0.5, 3.5, alpha=0.15, color='yellow', label='Summer (Adequate)')
ax1.axvspan(3.5, 9.5, alpha=0.15, color='blue', label='Winter (Stress)')
ax1.axvspan(9.5, 11.5, alpha=0.15, color='yellow')

# Custom legend
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor='green', alpha=0.8, edgecolor='black', label='Adequate (<0.1%)'),
    Patch(facecolor='red', alpha=0.8, edgecolor='black', label='Inadequate (>=0.1%)'),
    ax1.get_lines()[0],  # Threshold line
    Patch(facecolor='yellow', alpha=0.15, label='Summer Period'),
    Patch(facecolor='blue', alpha=0.15, label='Winter Period'),
]
ax1.legend(handles=legend_elements, fontsize=13, loc='upper left')

# ============================================
# Plot 2: Energy Shed by Month
# ============================================

bars2 = ax2.bar(x, df['load_shed_MWh']/1000, color=colors, alpha=0.8,
               edgecolor='black', linewidth=2)

ax2.set_xlabel('Month', fontsize=16, fontweight='bold')
ax2.set_ylabel('Energy Shed (GWh)', fontsize=16, fontweight='bold')
ax2.set_title('Total Energy Shed by Month', fontsize=17, fontweight='bold', pad=15)
ax2.set_xticks(x)
ax2.set_xticklabels(months_display, fontsize=14, fontweight='bold')
ax2.tick_params(axis='y', labelsize=13)
ax2.grid(True, alpha=0.3, axis='y')

# Add seasonal shading
ax2.axvspan(-0.5, 3.5, alpha=0.15, color='yellow')
ax2.axvspan(3.5, 9.5, alpha=0.15, color='blue')
ax2.axvspan(9.5, 11.5, alpha=0.15, color='yellow')

# Add value labels for significant energy shed
for i, (bar, val) in enumerate(zip(bars2, df['load_shed_MWh']/1000)):
    if val > 10:  # Only label >10 GWh
        ax2.text(bar.get_x() + bar.get_width()/2., val + 3,
                f'{val:.1f}', ha='center', va='bottom', 
                fontsize=11, fontweight='bold')

# Add summary text box
adequate = (df['status'] == 'ADEQUATE').sum()
total_shed = df['load_shed_MWh'].sum() / 1000

summary_text = f"Annual Summary:\n" + \
               f"  - Adequate: {adequate}/12 months\n" + \
               f"  - Inadequate: {12-adequate}/12 months\n" + \
               f"  - Total shed: {total_shed:.1f} GWh\n" + \
               f"  - Peak: August ({df.loc[df['month']=='aug', 'load_shed_MWh'].values[0]/1000:.1f} GWh)"

ax2.text(0.98, 0.97, summary_text, transform=ax2.transAxes,
        fontsize=13, verticalalignment='top', horizontalalignment='right',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9, linewidth=2),
        fontweight='bold')

plt.tight_layout()

# Save
OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
output_file = OUTPUT_PATH / 'annual_validation_2024.png'
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"\nSaved: {output_file.relative_to(BASE)}")

# Print summary
print("\n2024 Baseline Annual Validation:")
print(f"  Adequate months: {adequate}/12 ({adequate/12*100:.0f}%)")
print(f"  Winter stress: May, Jun, Aug, Sep")
print(f"  Peak shortage: August (92.4 GWh shed)")
print(f"  Total annual shortage: {total_shed:.1f} GWh")

plt.close()