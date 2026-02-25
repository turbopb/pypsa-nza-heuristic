"""
Network visualization with WORKING draggable annotations.
Uses matplotlib's built-in DraggableAnnotation.
"""

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np
import pypsa

print("Loading network...")

n = pypsa.Network()
n.import_from_csv_folder(r"C:\Users\Public\Documents\Thesis\analysis\dispatch_data\cases\reference\2030\baseline_2030")

bus_coords = n.buses[['x', 'y']].copy()

# Create figure
fig, ax = plt.subplots(figsize=(18, 24))

# Plot AC lines
for line_name in n.lines.index:
    s_nom = n.lines.loc[line_name, 's_nom']
    bus0 = n.lines.loc[line_name, 'bus0']
    bus1 = n.lines.loc[line_name, 'bus1']
    
    if bus0 in bus_coords.index and bus1 in bus_coords.index:
        x0, y0 = bus_coords.loc[bus0, 'x'], bus_coords.loc[bus0, 'y']
        x1, y1 = bus_coords.loc[bus1, 'x'], bus_coords.loc[bus1, 'y']
        
        if s_nom < 600:
            ax.plot([x0, x1], [y0, y1], color='lightsteelblue', linewidth=2.5, 
                   alpha=0.6, solid_capstyle='round', zorder=1)
        elif 600 <= s_nom < 1000:
            ax.plot([x0, x1], [y0, y1], color='royalblue', linewidth=4.5, 
                   alpha=0.8, solid_capstyle='round', zorder=2)
        else:
            ax.plot([x0, x1], [y0, y1], color='darkblue', linewidth=7, 
                   alpha=0.95, solid_capstyle='round', zorder=3)

# Plot HVDC in RED
for link in n.links.index:
    bus0 = n.links.loc[link, 'bus0']
    bus1 = n.links.loc[link, 'bus1']
    p_nom = n.links.loc[link, 'p_nom']
    
    if bus0 in bus_coords.index and bus1 in bus_coords.index:
        x0, y0 = bus_coords.loc[bus0, 'x'], bus_coords.loc[bus0, 'y']
        x1, y1 = bus_coords.loc[bus1, 'x'], bus_coords.loc[bus1, 'y']
        
        ax.plot([x0, x1], [y0, y1], color='red', linewidth=10, 
               alpha=1.0, zorder=10, solid_capstyle='round')
        
        mid_x, mid_y = (x0 + x1) / 2, (y0 + y1) / 2
        dx, dy = x1 - x0, y1 - y0
        ax.arrow(mid_x - dx*0.1, mid_y - dy*0.1, dx*0.2, dy*0.2,
                head_width=20000, head_length=25000, fc='yellow', ec='black',
                linewidth=3, zorder=11)

# Plot buses
ax.scatter(bus_coords['x'], bus_coords['y'], s=30, c='black', 
          zorder=20, alpha=0.7, edgecolors='white', linewidth=1)

# Create annotations with better initial positions
major_buses = {
    'OTA': ('Otahuhu\n(Auckland)', 30000, 10000),
    'HWA': ('Huntly', -40000, -10000),
    'WKM': ('Whakamaru', 40000, 0),
    'HAY': ('Haywards\n(Wellington)', -50000, 10000),
    'TKU': ('Tokaanu', 30000, 15000),
    'BPE': ('Brownhill Rd', 40000, -10000),
    'BEN': ('Benmore', -30000, 20000),
    'ISL': ('Islington', 30000, -15000),
    'TWZ': ('Tiwai Point', -35000, 15000),
}

draggable_anns = []

for bus_name, (label, offset_x, offset_y) in major_buses.items():
    if bus_name in bus_coords.index:
        x, y = bus_coords.loc[bus_name, ['x', 'y']]
        ax.scatter(x, y, s=200, c='red', marker='s', zorder=25, 
                  edgecolors='yellow', linewidth=3)
        
        ann = ax.annotate(label, xy=(x, y), xytext=(offset_x, offset_y), 
                   textcoords='offset points',
                   fontsize=16, fontweight='bold', color='darkred',
                   bbox=dict(boxstyle='round,pad=0.6', facecolor='yellow', 
                            alpha=0.95, edgecolor='darkred', linewidth=2.5),
                   arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.3',
                                  color='darkred', lw=2),
                   zorder=26)
        draggable_anns.append(ann)

# HVDC annotation
for link in n.links.index:
    bus0 = n.links.loc[link, 'bus0']
    bus1 = n.links.loc[link, 'bus1']
    p_nom = n.links.loc[link, 'p_nom']
    
    if bus0 in bus_coords.index and bus1 in bus_coords.index:
        x0, y0 = bus_coords.loc[bus0, 'x'], bus_coords.loc[bus0, 'y']
        x1, y1 = bus_coords.loc[bus1, 'x'], bus_coords.loc[bus1, 'y']
        mid_x, mid_y = (x0 + x1) / 2, (y0 + y1) / 2
        
        ann = ax.annotate(f'HVDC\n{p_nom:.0f} MW\nBEN?HAY',
                   xy=(mid_x, mid_y), xytext=(50000, 0), textcoords='offset points',
                   fontsize=18, fontweight='bold', color='red',
                   bbox=dict(boxstyle='round,pad=0.6', facecolor='yellow', 
                            alpha=0.95, edgecolor='red', linewidth=3),
                   arrowprops=dict(arrowstyle='->', color='red', lw=3),
                   zorder=12)
        draggable_anns.append(ann)

# Labels and formatting
ax.set_xlabel('Longitude', fontsize=20, fontweight='bold')
ax.set_ylabel('Latitude', fontsize=20, fontweight='bold')
ax.set_title('New Zealand Transmission Network - 2030 Baseline\n(DRAG YELLOW BOXES TO REPOSITION)', 
            fontsize=24, fontweight='bold', pad=25, color='red')
ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
ax.set_aspect('equal')
ax.tick_params(axis='both', which='major', labelsize=16)

# Legend
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], color='darkblue', linewidth=6, label='220 kV (=1000 MVA)'),
    Line2D([0], [0], color='royalblue', linewidth=4, label='110 kV (600 MVA)'),
    Line2D([0], [0], color='lightsteelblue', linewidth=2.5, label='66 kV (<600 MVA)'),
    Line2D([0], [0], color='red', linewidth=8, label='HVDC Link (1200 MW)'),
    Line2D([0], [0], marker='s', color='w', markerfacecolor='red', 
           markersize=12, label='Major Substation'),
]
ax.legend(handles=legend_elements, loc='upper left', fontsize=16, 
         framealpha=0.95, edgecolor='black')

# Stats box
stats_text = f'''Network Statistics:
Buses: {len(n.buses)}
AC Lines: {len(n.lines)}
DC Links: {len(n.links)}

220 kV: {(n.lines.s_nom >= 1000).sum()}
110 kV: {((n.lines.s_nom >= 600) & (n.lines.s_nom < 1000)).sum()}
66 kV: {(n.lines.s_nom < 600).sum()}
'''

ax.text(0.99, 0.01, stats_text, transform=ax.transAxes,
       fontsize=15, verticalalignment='bottom', horizontalalignment='right',
       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9, linewidth=2.5),
       family='monospace')

# ENABLE DRAGGING using matplotlib's built-in method
print("\n" + "="*70)
print("ENABLING DRAGGABLE ANNOTATIONS...")
print("="*70)

for ann in draggable_anns:
    ann.draggable(True)  # This is matplotlib's built-in draggable!
    print(f"  ? Made '{ann.get_text().strip()}' draggable")

print("\n" + "="*70)
print("INSTRUCTIONS:")
print("  1. Click and HOLD on any YELLOW BOX")
print("  2. DRAG it to a new position")
print("  3. RELEASE to drop")
print("  4. CLOSE WINDOW when done (saves automatically)")
print("="*70)

plt.tight_layout()

# Save
plt.savefig('2030_network_draggable.png', dpi=300, bbox_inches='tight')
print("\n? Initial version saved!")

# Show interactive
plt.show()

# Save final version after user closes window
fig.savefig('2030_network_final_positioned.png', dpi=300, bbox_inches='tight')
print("? Final positioned version saved to: 2030_network_final_positioned.png")

print("\nDone!")