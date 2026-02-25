"""
Fixed header spacing - no overlaps.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pypsa

baseline_results = pd.read_csv(r"C:\Users\Public\Documents\Thesis\analysis\dispatch_results\stress_test_reference_2030_baseline.csv")
upgraded_results = pd.read_csv(r"C:\Users\Public\Documents\Thesis\analysis\dispatch_results\stress_test_reference_2030_upgraded.csv")

baseline = pypsa.Network()
baseline.import_from_csv_folder(r"C:\Users\Public\Documents\Thesis\analysis\dispatch_data\cases\reference\2030\baseline_2030")
upgraded = pypsa.Network()
upgraded.import_from_csv_folder(r"C:\Users\Public\Documents\Thesis\analysis\dispatch_data\cases\reference\2030\upgraded_2030")

# Create figure with proper margins
fig, axes = plt.subplots(3, 1, figsize=(16, 22))
plt.subplots_adjust(hspace=0.6, top=0.93, bottom=0.05)

# PLOT 1: Capacity Additions
ax1 = axes[0]

baseline_gens = baseline.generators.groupby('carrier').p_nom.sum()
upgraded_gens = upgraded.generators.groupby('carrier').p_nom.sum()
additions = upgraded_gens - baseline_gens.reindex(upgraded_gens.index, fill_value=0)
additions = additions[additions > 0].sort_values(ascending=False)

colors_tech = {'gas': 'coral', 'wind': 'skyblue', 'solar': 'gold', 'battery': 'purple'}

x_pos = np.arange(len(additions))
bars = ax1.bar(x_pos, additions.values, 
               color=[colors_tech.get(tech, 'gray') for tech in additions.index],
               alpha=0.8, edgecolor='black', linewidth=3, width=0.6)

ax1.set_xticks(x_pos)
ax1.set_xticklabels([tech.replace('_', ' ').title() for tech in additions.index], 
                     fontsize=18, fontweight='bold')
ax1.set_ylabel('Capacity Added (MW)', fontsize=19, fontweight='bold')
ax1.set_title('New Generation Capacity Required for 2030 Adequacy', 
             fontsize=20, fontweight='bold', pad=20)
ax1.grid(True, alpha=0.3, axis='y')
ax1.tick_params(axis='y', labelsize=16)

for bar, val in zip(bars, additions.values):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height + 50,
            f'{val:.0f} MW', ha='center', va='bottom', 
            fontsize=17, fontweight='bold')

total = additions.sum()
ax1.text(0.98, 0.95, f'Total: {total:,.0f} MW', 
        transform=ax1.transAxes, ha='right', va='top',
        fontsize=18, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.7', facecolor='lightyellow', 
                 edgecolor='black', linewidth=3))

# PLOT 2: Investment
ax2 = axes[1]

tech_costs = {
    'Gas': (2000, 2400),
    'Wind': (550, 1375),
    'Solar': (200, 360),
    'Battery': (200, 300),
}

techs = list(tech_costs.keys())
capacities = [tech_costs[t][0] for t in techs]
costs = [tech_costs[t][1] for t in techs]

x = np.arange(len(techs))
width = 0.35

ax2_cost = ax2.twinx()

bars1 = ax2.bar(x - width/2, capacities, width, label='Capacity (MW)',
                color='steelblue', alpha=0.8, edgecolor='darkblue', linewidth=3)
bars2 = ax2_cost.bar(x + width/2, costs, width, label='Cost ($M NZD)',
                     color='coral', alpha=0.8, edgecolor='darkred', linewidth=3)

ax2.set_xlabel('Technology', fontsize=18, fontweight='bold')
ax2.set_ylabel('Capacity (MW)', fontsize=17, fontweight='bold', color='steelblue')
ax2_cost.set_ylabel('Cost ($M NZD)', fontsize=17, fontweight='bold', color='coral')
ax2.set_title('Investment by Technology', fontsize=20, fontweight='bold', pad=20)
ax2.set_xticks(x)
ax2.set_xticklabels(techs, fontsize=18, fontweight='bold')
ax2.tick_params(axis='y', labelcolor='steelblue', labelsize=15)
ax2_cost.tick_params(axis='y', labelcolor='coral', labelsize=15)
ax2.grid(True, alpha=0.3, axis='y')

total_cost = sum(costs)
ax2.text(0.5, 0.95, f'Total Investment: ${total_cost:,.0f}M NZD',
        transform=ax2.transAxes, ha='center', va='top',
        fontsize=18, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.7', facecolor='yellow', 
                 edgecolor='black', linewidth=3))

# PLOT 3: Statistics Table
ax3 = axes[2]
ax3.axis('off')

stats_data = [
    ['Metric', 'Baseline 2030', 'Upgraded 2030', 'Change'],
    ['', '', '', ''],
    ['Load Shedding (%)', '5.96', '0.00', '-5.96'],
    ['Energy Shed (GWh)', '593.2', '0.0', '-593.2'],
    ['System Status', 'INADEQUATE', 'ADEQUATE', 'FIXED'],
    ['', '', '', ''],
    ['Total Generation (MW)', '7,478', '10,428', '+2,950'],
    ['Number of Generators', '65', '80', '+15'],
    ['', '', '', ''],
    ['Peak Demand (MW)', '7,827', '7,827', '0'],
    ['Annual Demand (GWh)', '9,953', '9,953', '0'],
]

table = ax3.table(cellText=stats_data, loc='center', cellLoc='center',
                 colWidths=[0.35, 0.25, 0.25, 0.15])
table.auto_set_font_size(False)
table.set_fontsize(15)
table.scale(1, 3.5)

for i in range(4):
    table[(0, i)].set_facecolor('#4472C4')
    table[(0, i)].set_text_props(weight='bold', color='white', size=17)

for i in [1, 5, 8]:
    for j in range(4):
        table[(i, j)].set_facecolor('#E7E6E6')

table[(2, 3)].set_facecolor('#C6E0B4')
table[(2, 3)].set_text_props(weight='bold')
table[(3, 3)].set_facecolor('#C6E0B4')
table[(4, 1)].set_text_props(weight='bold', color='red', size=16)
table[(4, 2)].set_text_props(weight='bold', color='green', size=16)
table[(4, 3)].set_text_props(weight='bold', color='green', size=16)
table[(6, 3)].set_facecolor('#FFF2CC')
table[(7, 3)].set_facecolor('#FFF2CC')

ax3.set_title('System Performance Metrics', fontsize=20, fontweight='bold', pad=30)

# Main title with proper y position
fig.suptitle('2030 Adequacy Analysis: Baseline vs. Upgraded System', 
            fontsize=22, fontweight='bold', y=0.98)

plt.savefig('2030_final_figure.png', dpi=300, bbox_inches='tight')
print("\nSaved: 2030_final_figure.png")
print("Fixed: top=0.93, suptitle y=0.98")
plt.close()