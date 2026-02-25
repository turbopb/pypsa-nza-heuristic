"""
Useful comparison plots showing what actually changed.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pypsa

# Load validation results
baseline_results = pd.read_csv(r"C:\Users\Public\Documents\Thesis\analysis\dispatch_results\stress_test_reference_2030_baseline.csv")
upgraded_results = pd.read_csv(r"C:\Users\Public\Documents\Thesis\analysis\dispatch_results\stress_test_reference_2030_upgraded.csv")

# Load networks for generator counts
baseline = pypsa.Network()
baseline.import_from_csv_folder(r"C:\Users\Public\Documents\Thesis\analysis\dispatch_data\cases\reference\2030\baseline_2030")
upgraded = pypsa.Network()
upgraded.import_from_csv_folder(r"C:\Users\Public\Documents\Thesis\analysis\dispatch_data\cases\reference\2030\upgraded_2030")

fig = plt.figure(figsize=(16, 10))
gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)

# ============================================================
# Plot 1: Load Shedding Comparison (TOP LEFT)
# ============================================================
ax1 = fig.add_subplot(gs[0, 0])

scenarios = ['Baseline\n2030', 'Upgraded\n2030']
shedding_pct = [baseline_results['load_shed_fraction'].iloc[0]*100,
                upgraded_results['load_shed_fraction'].iloc[0]*100]
colors = ['red', 'green']

bars = ax1.bar(scenarios, shedding_pct, color=colors, alpha=0.7, 
              edgecolor='black', linewidth=2.5, width=0.6)

ax1.axhline(y=0.1, color='orange', linestyle='--', linewidth=2, 
           label='Adequacy Threshold (~0.1%)', alpha=0.7)

ax1.set_ylabel('Load Shedding (%)', fontsize=14, fontweight='bold')
ax1.set_title('System Adequacy Comparison', fontsize=15, fontweight='bold')
ax1.grid(True, alpha=0.3, axis='y')
ax1.legend(fontsize=11)

for bar, val in zip(bars, shedding_pct):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height + 0.2,
            f'{val:.2f}%', ha='center', va='bottom', 
            fontsize=16, fontweight='bold')

status_baseline = 'INADEQUATE' if shedding_pct[0] > 0.1 else 'ADEQUATE'
status_upgraded = 'INADEQUATE' if shedding_pct[1] > 0.1 else 'ADEQUATE'

ax1.text(0, -0.5, status_baseline, ha='center', fontsize=13, 
        fontweight='bold', color='red')
ax1.text(1, -0.5, status_upgraded, ha='center', fontsize=13, 
        fontweight='bold', color='green')

# ============================================================
# Plot 2: Generation Capacity Additions (TOP RIGHT)
# ============================================================
ax2 = fig.add_subplot(gs[0, 1])

# Count generators by type
baseline_gens = baseline.generators.groupby('carrier').p_nom.sum()
upgraded_gens = upgraded.generators.groupby('carrier').p_nom.sum()

# Calculate additions
additions = upgraded_gens - baseline_gens.reindex(upgraded_gens.index, fill_value=0)
additions = additions[additions > 0].sort_values(ascending=True)

colors_tech = {'wind': 'skyblue', 'solar': 'gold', 'gas': 'coral', 
               'battery': 'purple', 'hydro': 'steelblue'}

y_pos = np.arange(len(additions))
bars = ax2.barh(y_pos, additions.values, 
               color=[colors_tech.get(tech, 'gray') for tech in additions.index],
               alpha=0.8, edgecolor='black', linewidth=1.5)

ax2.set_yticks(y_pos)
ax2.set_yticklabels([f'{tech.capitalize()}' for tech in additions.index], 
                    fontsize=13, fontweight='bold')
ax2.set_xlabel('Capacity Added (MW)', fontsize=14, fontweight='bold')
ax2.set_title('New Generation Capacity (2030 Upgrade)', fontsize=15, fontweight='bold')
ax2.grid(True, alpha=0.3, axis='x')

for i, (bar, val) in enumerate(zip(bars, additions.values)):
    ax2.text(val + 50, i, f'{val:.0f} MW', va='center', 
            fontsize=12, fontweight='bold')

# ============================================================
# Plot 3: Statistics Table (BOTTOM LEFT)
# ============================================================
ax3 = fig.add_subplot(gs[1, 0])
ax3.axis('off')

stats_data = [
    ['Metric', 'Baseline', 'Upgraded', 'Change'],
    ['', '', '', ''],
    ['Load Shedding (%)', f'{baseline_results["load_shed_fraction"].iloc[0]*100:.2f}',
     f'{upgraded_results["load_shed_fraction"].iloc[0]*100:.2f}',
     f'{(upgraded_results["load_shed_fraction"].iloc[0] - baseline_results["load_shed_fraction"].iloc[0])*100:.2f}'],
    ['Energy Shed (GWh)', f'{baseline_results["load_shed_MWh"].iloc[0]/1000:.1f}',
     f'{upgraded_results["load_shed_MWh"].iloc[0]/1000:.1f}',
     f'{(upgraded_results["load_shed_MWh"].iloc[0] - baseline_results["load_shed_MWh"].iloc[0])/1000:.1f}'],
    ['', '', '', ''],
    ['Total Generation (MW)', f'{baseline.generators.p_nom.sum():.0f}',
     f'{upgraded.generators.p_nom.sum():.0f}',
     f'+{upgraded.generators.p_nom.sum() - baseline.generators.p_nom.sum():.0f}'],
    ['Number of Generators', f'{len(baseline.generators)}',
     f'{len(upgraded.generators)}',
     f'+{len(upgraded.generators) - len(baseline.generators)}'],
    ['', '', '', ''],
    ['Peak Demand (MW)', '7,827', '7,827', '0'],
    ['Total Demand (GWh)', f'{baseline_results["total_demand_MWh"].iloc[0]/1000:.1f}',
     f'{upgraded_results["total_demand_MWh"].iloc[0]/1000:.1f}', '0'],
]

table = ax3.table(cellText=stats_data, loc='center', cellLoc='center',
                 colWidths=[0.35, 0.25, 0.25, 0.15])
table.auto_set_font_size(False)
table.set_fontsize(12)
table.scale(1, 2.2)

for i in range(4):
    table[(0, i)].set_facecolor('#4472C4')
    table[(0, i)].set_text_props(weight='bold', color='white', size=13)

for i in [1, 4, 7]:
    for j in range(4):
        table[(i, j)].set_facecolor('#E7E6E6')

# Highlight improvements in green
table[(2, 3)].set_facecolor('#C6E0B4')  # Shedding reduction
table[(3, 3)].set_facecolor('#C6E0B4')  # Energy reduction
table[(5, 3)].set_facecolor('#FFF2CC')  # Generation addition
table[(6, 3)].set_facecolor('#FFF2CC')  # Generator count

ax3.set_title('System Performance Metrics', fontsize=15, fontweight='bold', pad=20)

# ============================================================
# Plot 4: Investment Summary (BOTTOM RIGHT)
# ============================================================
ax4 = fig.add_subplot(gs[1, 1])

# Cost estimates (from your analysis)
tech_costs = {
    'Wind': (550, 1375),      # MW, $M
    'Solar': (200, 360),
    'Gas': (2000, 2400),
    'Battery': (200, 300),
}

techs = list(tech_costs.keys())
capacities = [tech_costs[t][0] for t in techs]
costs = [tech_costs[t][1] for t in techs]

x = np.arange(len(techs))
width = 0.35

ax4_cap = ax4
ax4_cost = ax4.twinx()

bars1 = ax4_cap.bar(x - width/2, capacities, width, label='Capacity (MW)',
                    color='steelblue', alpha=0.7, edgecolor='darkblue', linewidth=2)
bars2 = ax4_cost.bar(x + width/2, costs, width, label='Cost ($M NZD)',
                     color='coral', alpha=0.7, edgecolor='darkred', linewidth=2)

ax4_cap.set_xlabel('Technology', fontsize=14, fontweight='bold')
ax4_cap.set_ylabel('Capacity (MW)', fontsize=13, fontweight='bold', color='steelblue')
ax4_cost.set_ylabel('Cost ($M NZD)', fontsize=13, fontweight='bold', color='coral')
ax4_cap.set_title('Investment by Technology', fontsize=15, fontweight='bold')
ax4_cap.set_xticks(x)
ax4_cap.set_xticklabels(techs, fontsize=13, fontweight='bold')
ax4_cap.tick_params(axis='y', labelcolor='steelblue')
ax4_cost.tick_params(axis='y', labelcolor='coral')
ax4_cap.grid(True, alpha=0.3, axis='y')

# Add total
total_cost = sum(costs)
ax4_cap.text(0.5, 0.95, f'Total Investment: ${total_cost:,.0f}M NZD',
            transform=ax4.transAxes, ha='center', va='top',
            fontsize=14, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', 
                     edgecolor='black', linewidth=2))

fig.suptitle('2030 Adequacy Analysis: Baseline vs. Upgraded System', 
            fontsize=17, fontweight='bold', y=0.98)

plt.savefig('2030_useful_comparison.png', dpi=300, bbox_inches='tight')
print("\n? Saved: 2030_useful_comparison.png")
print("\nShows:")
print("  1. Load shedding: 5.96% ? 0%")
print("  2. Capacity additions by technology")
print("  3. Complete statistics table")
print("  4. Investment breakdown (~$4.4B)")
plt.close()