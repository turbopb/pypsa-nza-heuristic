"""
Simple, clear network visualization - ONE large map.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pypsa

print("Loading network...")

n = pypsa.Network()
n.import_from_csv_folder(r"C:\Users\Public\Documents\Thesis\analysis\dispatch_data\cases\reference\2030\baseline_2030")

bus_coords = n.buses[['x', 'y']].copy()

print(f"Network: {len(n.buses)} buses, {len(n.lines)} AC lines, {len(n.links)} DC links")

# Create ONE large, clear figure
fig, ax = plt.subplots(figsize=(16, 20))

# Plot AC lines - grouped by voltage
print("Plotting AC lines...")

# First pass: 66kV lines (thin, light gray)
for line_name in n.lines.index:
    s_nom = n.lines.loc[line_name, 's_nom']
    if s_nom < 600:
        bus0 = n.lines.loc[line_name, 'bus0']
        bus1 = n.lines.loc[line_name, 'bus1']
        if bus0 in bus_coords.index and bus1 in bus_coords.index:
            x0, y0 = bus_coords.loc[bus0, 'x'], bus_coords.loc[bus0, 'y']
            x1, y1 = bus_coords.loc[bus1, 'x'], bus_coords.loc[bus1, 'y']
            ax.plot([x0, x1], [y0, y1], color='gray', linewidth=1.5, 
                   alpha=0.4, solid_capstyle='round', zorder=1)

# Second pass: 110kV lines (medium, blue)
for line_name in n.lines.index:
    s_nom = n.lines.loc[line_name, 's_nom']
    if 600 <= s_nom < 1000:
        bus0 = n.lines.loc[line_name, 'bus0']
        bus1 = n.lines.loc[line_name, 'bus1']
        if bus0 in bus_coords.index and bus1 in bus_coords.index:
            x0, y0 = bus_coords.loc[bus0, 'x'], bus_coords.loc[bus0, 'y']
            x1, y1 = bus_coords.loc[bus1, 'x'], bus_coords.loc[bus1, 'y']
            ax.plot([x0, x1], [y0, y1], color='royalblue', linewidth=3.5, 
                   alpha=0.7, solid_capstyle='round', zorder=2)

# Third pass: 220kV lines (thick, dark blue)
for line_name in n.lines.index:
    s_nom = n.lines.loc[line_name, 's_nom']
    if s_nom >= 1000:
        bus0 = n.lines.loc[line_name, 'bus0']
        bus1 = n.lines.loc[line_name, 'bus1']
        if bus0 in bus_coords.index and bus1 in bus_coords.index:
            x0, y0 = bus_coords.loc[bus0, 'x'], bus_coords.loc[bus0, 'y']
            x1, y1 = bus_coords.loc[bus1, 'x'], bus_coords.loc[bus1, 'y']
            ax.plot([x0, x1], [y0, y1], color='darkblue', linewidth=5.5, 
                   alpha=0.9, solid_capstyle='round', zorder=3)

print("Plotting HVDC link...")

# Plot HVDC link - VERY THICK PURPLE
for link in n.links.index:
    bus0 = n.links.loc[link, 'bus0']
    bus1 = n.links.loc[link, 'bus1']
    p_nom = n.links.loc[link, 'p_nom']
    
    if bus0 in bus_coords.index and bus1 in bus_coords.index:
        x0, y0 = bus_coords.loc[bus0, 'x'], bus_coords.loc[bus0, 'y']
        x1, y1 = bus_coords.loc[bus1, 'x'], bus_coords.loc[bus1, 'y']
        
        # Very thick purple line
        ax.plot([x0, x1], [y0, y1], color='purple', linewidth=8, 
               linestyle='-', alpha=1.0, zorder=10, solid_capstyle='round')
        
        # Add direction arrow
        mid_x, mid_y = (x0 + x1) / 2, (y0 + y1) / 2
        dx, dy = x1 - x0, y1 - y0
        ax.arrow(mid_x - dx*0.1, mid_y - dy*0.1, dx*0.2, dy*0.2,
                head_width=20000, head_length=25000, fc='yellow', ec='black',
                linewidth=2, zorder=11)
        
        # Label it clearly
        ax.text(mid_x + 20000, mid_y, f'HVDC\n{p_nom:.0f} MW\nBEN?HAY', 
               fontsize=14, fontweight='bold', color='purple',
               bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', 
                        alpha=0.95, edgecolor='purple', linewidth=3),
               zorder=12)

print("Plotting buses...")

# Plot buses - MUCH SMALLER
ax.scatter(bus_coords['x'], bus_coords['y'], s=25, c='black', 
          zorder=20, alpha=0.7, edgecolors='white', linewidth=0.8)

# Label only MAJOR buses
major_buses = {
    # North Island major
    'OTA': 'Otahuhu\n(Auckland)',
    'HWA': 'Huntly',
    'WKM': 'Whakamaru',
    'HAY': 'Haywards\n(Wellington)',
    'TKU': 'Tokaanu',
    'BPE': 'Brownhill Rd',
    # South Island major  
    'BEN': 'Benmore',
    'ISL': 'Islington',
    'TWZ': 'Tiwai Point',
}

for bus_name, label in major_buses.items():
    if bus_name in bus_coords.index:
        x, y = bus_coords.loc[bus_name, ['x', 'y']]
        ax.scatter(x, y, s=150, c='red', marker='s', zorder=25, 
                  edgecolors='yellow', linewidth=2)
        ax.annotate(label, (x, y), xytext=(8, 8), textcoords='offset points',
                   fontsize=11, fontweight='bold', color='darkred',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', 
                            alpha=0.95, edgecolor='darkred', linewidth=2),
                   zorder=26)

# Title and labels
ax.set_xlabel('Longitude', fontsize=14, fontweight='bold')
ax.set_ylabel('Latitude', fontsize=14, fontweight='bold')
ax.set_title('New Zealand Transmission Network\n2030 Baseline Topology', 
            fontsize=18, fontweight='bold', pad=20)
ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
ax.set_aspect('equal')

# Simple, clear legend
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], color='darkblue', linewidth=5, label='220 kV (=1000 MVA)', solid_capstyle='round'),
    Line2D([0], [0], color='royalblue', linewidth=3, label='110 kV (600 MVA)', solid_capstyle='round'),
    Line2D([0], [0], color='gray', linewidth=1.5, label='66 kV (<600 MVA)', solid_capstyle='round'),
    Line2D([0], [0], color='purple', linewidth=6, label='HVDC Link (1200 MW)', solid_capstyle='round'),
    Line2D([0], [0], marker='s', color='w', markerfacecolor='red', 
           markersize=10, label='Major Substation', markeredgecolor='yellow', markeredgewidth=2),
]
ax.legend(handles=legend_elements, loc='upper left', fontsize=12, 
         framealpha=0.95, edgecolor='black', fancybox=True)

# Add stats box
stats_text = f'''Network Statistics:
Buses: {len(n.buses)}
AC Lines: {len(n.lines)}
DC Links: {len(n.links)}

220 kV lines: {(n.lines.s_nom >= 1000).sum()}
110 kV lines: {((n.lines.s_nom >= 600) & (n.lines.s_nom < 1000)).sum()}
66 kV lines: {(n.lines.s_nom < 600).sum()}
'''

ax.text(0.99, 0.01, stats_text, transform=ax.transAxes,
       fontsize=11, verticalalignment='bottom', horizontalalignment='right',
       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9, edgecolor='black', linewidth=2),
       family='monospace')

plt.tight_layout()
plt.savefig('2030_network_clear.png', dpi=300, bbox_inches='tight')
print("\n? Clear network map saved to: 2030_network_clear.png")
plt.close()

print("\nDone! ONE large, clear map with:")
print("  - Dark blue = 220 kV (thick)")
print("  - Royal blue = 110 kV (medium)")  
print("  - Gray = 66 kV (thin)")
print("  - PURPLE = HVDC link (very thick)")
print("  - Red squares = Major substations")