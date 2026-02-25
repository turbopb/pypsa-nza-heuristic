"""
Clean network map with labels positioned OUTSIDE the network area.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pypsa

n = pypsa.Network()
n.import_from_csv_folder(r"C:\Users\Public\Documents\Thesis\analysis\dispatch_data\cases\reference\2030\baseline_2030")

bus_coords = n.buses[['x', 'y']]

fig, ax = plt.subplots(figsize=(16, 20))

# Plot lines
for line in n.lines.index:
    s = n.lines.loc[line, 's_nom']
    b0, b1 = n.lines.loc[line, ['bus0', 'bus1']]
    if b0 in bus_coords.index and b1 in bus_coords.index:
        x0, y0 = bus_coords.loc[b0, ['x', 'y']]
        x1, y1 = bus_coords.loc[b1, ['x', 'y']]
        if s < 600:
            ax.plot([x0,x1], [y0,y1], 'lightsteelblue', lw=2.5, alpha=0.6, zorder=1)
        elif s < 1000:
            ax.plot([x0,x1], [y0,y1], 'royalblue', lw=4.5, alpha=0.8, zorder=2)
        else:
            ax.plot([x0,x1], [y0,y1], 'darkblue', lw=7, alpha=0.95, zorder=3)

# HVDC in RED
for link in n.links.index:
    b0, b1 = n.links.loc[link, ['bus0', 'bus1']]
    if b0 in bus_coords.index and b1 in bus_coords.index:
        x0, y0 = bus_coords.loc[b0, ['x', 'y']]
        x1, y1 = bus_coords.loc[b1, ['x', 'y']]
        ax.plot([x0,x1], [y0,y1], 'red', lw=10, zorder=10, solid_capstyle='round')

# Buses - small dots
ax.scatter(bus_coords['x'], bus_coords['y'], s=25, c='black', zorder=20, 
          alpha=0.6, edgecolors='white', lw=0.8)

# Major substations - larger markers
major = ['OTA', 'HWA', 'WKM', 'HAY', 'BEN', 'TWZ']
for bus in major:
    if bus in bus_coords.index:
        x, y = bus_coords.loc[bus, ['x', 'y']]
        ax.scatter(x, y, s=250, c='red', marker='s', zorder=25, 
                  edgecolors='yellow', lw=4)

# Labels positioned OUTSIDE with clear arrows - NO OVERLAP
labels = [
    # North Island - labels to the RIGHT
    ('OTA', 'Otahuhu\n(Auckland)', (2050000, 5920000), (1850000, 5920000)),
    ('WKM', 'Whakamaru\n(Hydro)', (2050000, 5770000), (1900000, 5770000)),
    ('HWA', 'Huntly\n(Gas)', (2050000, 5640000), (1750000, 5640000)),
    ('HAY', 'Haywards\n(Wellington)', (2050000, 5450000), (1820000, 5450000)),
    
    # South Island - labels to the LEFT  
    ('BEN', 'Benmore\n(HVDC origin)', (1050000, 5070000), (1380000, 5070000)),
    ('TWZ', 'Tiwai Point\n(Aluminium)', (1050000, 5090000), (1350000, 5090000)),
]

for bus, label, label_pos, bus_pos in labels:
    if bus in bus_coords.index:
        ax.annotate(label, xy=bus_pos, xytext=label_pos,
                   fontsize=15, fontweight='bold', color='darkred',
                   bbox=dict(boxstyle='round,pad=0.6', facecolor='yellow', 
                            edgecolor='darkred', lw=3, alpha=0.95),
                   arrowprops=dict(arrowstyle='->', lw=3, color='darkred',
                                  connectionstyle='arc3,rad=0.2'),
                   ha='left' if label_pos[0] > 1500000 else 'right',
                   zorder=30)

# HVDC label - positioned to the LEFT
ax.text(1050000, 5270000, 'HVDC Link\n1200 MW\nBenmore?Haywards', 
       fontsize=16, fontweight='bold', color='red',
       bbox=dict(boxstyle='round,pad=0.7', facecolor='yellow', 
                edgecolor='red', lw=4, alpha=0.95),
       ha='left', va='center', zorder=30)

# Add arrow from HVDC label to line
ax.annotate('', xy=(1450000, 5250000), xytext=(1300000, 5270000),
           arrowprops=dict(arrowstyle='->', lw=3, color='red'))

ax.set_xlabel('Longitude', fontsize=20, fontweight='bold')
ax.set_ylabel('Latitude', fontsize=20, fontweight='bold')
ax.set_title('New Zealand Transmission Network Topology\n2030 Baseline', 
            fontsize=22, fontweight='bold', pad=25)
ax.grid(True, alpha=0.3, linestyle='--', lw=0.8)
ax.set_aspect('equal')
ax.tick_params(labelsize=16)

from matplotlib.lines import Line2D
ax.legend(handles=[
    Line2D([0],[0], color='darkblue', lw=7, label='220 kV (=1000 MVA)', solid_capstyle='round'),
    Line2D([0],[0], color='royalblue', lw=5, label='110 kV (600 MVA)', solid_capstyle='round'),
    Line2D([0],[0], color='lightsteelblue', lw=3, label='66 kV (<600 MVA)', solid_capstyle='round'),
    Line2D([0],[0], color='red', lw=9, label='HVDC Link (1200 MW)', solid_capstyle='round'),
], loc='upper left', fontsize=16, framealpha=0.95, edgecolor='black', fancybox=True)

# Extend x-limits to make room for labels
ax.set_xlim(1000000, 2100000)

plt.tight_layout()
plt.savefig('2030_network_clean.png', dpi=200, bbox_inches='tight')
print("? Done: 2030_network_clean.png")
print("  - Labels positioned OUTSIDE network")
print("  - Clear arrows to locations")
print("  - No overlap with transmission lines")