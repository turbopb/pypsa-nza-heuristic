"""
Simple static network map - NO dragging, just good positioning.
"""

import matplotlib
matplotlib.use('Agg')  # Non-interactive - just save file
import matplotlib.pyplot as plt
import pypsa

n = pypsa.Network()
n.import_from_csv_folder(r"C:\Users\Public\Documents\Thesis\analysis\dispatch_data\cases\reference\2030\baseline_2030")

bus_coords = n.buses[['x', 'y']]

fig, ax = plt.subplots(figsize=(14, 18))

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
        ax.plot([x0,x1], [y0,y1], 'red', lw=10, zorder=10)
        mx, my = (x0+x1)/2, (y0+y1)/2
        ax.text(mx-50000, my, 'HVDC\n1200 MW', fontsize=16, fontweight='bold',
               color='red', bbox=dict(boxstyle='round,pad=0.6', fc='yellow', 
               ec='red', lw=3), ha='center', zorder=12)

# Buses
ax.scatter(bus_coords['x'], bus_coords['y'], s=30, c='black', zorder=20, 
          alpha=0.7, edgecolors='white', lw=1)

# Major labels - FIXED GOOD POSITIONS
labels = [
    ('OTA', 'Otahuhu', 60000, -20000),
    ('HWA', 'Huntly', -60000, 0),
    ('WKM', 'Whakamaru', 60000, 0),
    ('HAY', 'Haywards', 60000, -20000),
    ('BEN', 'Benmore', -60000, -20000),
    ('TWZ', 'Tiwai Pt', 0, 30000),
]

for bus, label, dx, dy in labels:
    if bus in bus_coords.index:
        x, y = bus_coords.loc[bus, ['x', 'y']]
        ax.scatter(x, y, s=200, c='red', marker='s', zorder=25, 
                  edgecolors='yellow', lw=3)
        ax.text(x+dx, y+dy, label, fontsize=14, fontweight='bold', color='darkred',
               bbox=dict(boxstyle='round,pad=0.5', fc='yellow', ec='darkred', lw=2.5),
               ha='center', zorder=26)

ax.set_xlabel('Longitude', fontsize=18, fontweight='bold')
ax.set_ylabel('Latitude', fontsize=18, fontweight='bold')
ax.set_title('New Zealand Transmission Network - 2030', fontsize=20, fontweight='bold', pad=20)
ax.grid(True, alpha=0.3)
ax.set_aspect('equal')
ax.tick_params(labelsize=14)

from matplotlib.lines import Line2D
ax.legend(handles=[
    Line2D([0],[0], color='darkblue', lw=6, label='220 kV'),
    Line2D([0],[0], color='royalblue', lw=4, label='110 kV'),
    Line2D([0],[0], color='lightsteelblue', lw=2.5, label='66 kV'),
    Line2D([0],[0], color='red', lw=8, label='HVDC 1200 MW'),
], loc='upper left', fontsize=14, framealpha=0.95)

plt.tight_layout()
plt.savefig('2030_network_thesis.png', dpi=200, bbox_inches='tight')
print("? Saved: 2030_network_thesis.png")
plt.close()