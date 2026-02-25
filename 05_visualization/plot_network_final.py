"""
Final clear network visualization with large text and visible lines.
"""

import matplotlib
matplotlib.use('TkAgg')  # Interactive backend for draggable annotations
import matplotlib.pyplot as plt
import numpy as np
import pypsa

print("Loading network...")

n = pypsa.Network()
n.import_from_csv_folder(r"C:\Users\Public\Documents\Thesis\analysis\dispatch_data\cases\reference\2030\baseline_2030")

bus_coords = n.buses[['x', 'y']].copy()

print(f"Network: {len(n.buses)} buses, {len(n.lines)} AC lines, {len(n.links)} DC links")

# Create ONE large, clear figure
fig, ax = plt.subplots(figsize=(18, 24))

# Plot AC lines - ALL THICKER NOW
print("Plotting AC lines...")

# First pass: 66kV lines (THICKER - now visible)
for line_name in n.lines.index:
    s_nom = n.lines.loc[line_name, 's_nom']
    if s_nom < 600:
        bus0 = n.lines.loc[line_name, 'bus0']
        bus1 = n.lines.loc[line_name, 'bus1']
        if bus0 in bus_coords.index and bus1 in bus_coords.index:
            x0, y0 = bus_coords.loc[bus0, 'x'], bus_coords.loc[bus0, 'y']
            x1, y1 = bus_coords.loc[bus1, 'x'], bus_coords.loc[bus1, 'y']
            ax.plot([x0, x1], [y0, y1], color='lightsteelblue', linewidth=2.5, 
                   alpha=0.6, solid_capstyle='round', zorder=1)

# Second pass: 110kV lines (THICKER)
for line_name in n.lines.index:
    s_nom = n.lines.loc[line_name, 's_nom']
    if 600 <= s_nom < 1000:
        bus0 = n.lines.loc[line_name, 'bus0']
        bus1 = n.lines.loc[line_name, 'bus1']
        if bus0 in bus_coords.index and bus1 in bus_coords.index:
            x0, y0 = bus_coords.loc[bus0, 'x'], bus_coords.loc[bus0, 'y']
            x1, y1 = bus_coords.loc[bus1, 'x'], bus_coords.loc[bus1, 'y']
            ax.plot([x0, x1], [y0, y1], color='royalblue', linewidth=4.5, 
                   alpha=0.8, solid_capstyle='round', zorder=2)

# Third pass: 220kV lines (VERY THICK)
for line_name in n.lines.index:
    s_nom = n.lines.loc[line_name, 's_nom']
    if s_nom >= 1000:
        bus0 = n.lines.loc[line_name, 'bus0']
        bus1 = n.lines.loc[line_name, 'bus1']
        if bus0 in bus_coords.index and bus1 in bus_coords.index:
            x0, y0 = bus_coords.loc[bus0, 'x'], bus_coords.loc[bus0, 'y']
            x1, y1 = bus_coords.loc[bus1, 'x'], bus_coords.loc[bus1, 'y']
            ax.plot([x0, x1], [y0, y1], color='darkblue', linewidth=7, 
                   alpha=0.95, solid_capstyle='round', zorder=3)

print("Plotting HVDC link in RED...")

# Plot HVDC link - VERY THICK RED
annotations = []  # Store annotations for draggability

for link in n.links.index:
    bus0 = n.links.loc[link, 'bus0']
    bus1 = n.links.loc[link, 'bus1']
    p_nom = n.links.loc[link, 'p_nom']
    
    if bus0 in bus_coords.index and bus1 in bus_coords.index:
        x0, y0 = bus_coords.loc[bus0, 'x'], bus_coords.loc[bus0, 'y']
        x1, y1 = bus_coords.loc[bus1, 'x'], bus_coords.loc[bus1, 'y']
        
        # Very thick RED line
        ax.plot([x0, x1], [y0, y1], color='red', linewidth=10, 
               linestyle='-', alpha=1.0, zorder=10, solid_capstyle='round')
        
        # Add direction arrow
        mid_x, mid_y = (x0 + x1) / 2, (y0 + y1) / 2
        dx, dy = x1 - x0, y1 - y0
        ax.arrow(mid_x - dx*0.1, mid_y - dy*0.1, dx*0.2, dy*0.2,
                head_width=20000, head_length=25000, fc='yellow', ec='black',
                linewidth=3, zorder=11)
        
        # Label it clearly - LARGER TEXT
        ann = ax.text(mid_x + 20000, mid_y, f'HVDC\n{p_nom:.0f} MW\nBEN?HAY', 
               fontsize=18, fontweight='bold', color='red',
               bbox=dict(boxstyle='round,pad=0.6', facecolor='yellow', 
                        alpha=0.95, edgecolor='red', linewidth=3),
               zorder=12)
        annotations.append(ann)

print("Plotting buses...")

# Plot buses - small
ax.scatter(bus_coords['x'], bus_coords['y'], s=30, c='black', 
          zorder=20, alpha=0.7, edgecolors='white', linewidth=1)

# Label only MAJOR buses - LARGER TEXT
major_buses = {
    'OTA': 'Otahuhu\n(Auckland)',
    'HWA': 'Huntly',
    'WKM': 'Whakamaru',
    'HAY': 'Haywards\n(Wellington)',
    'TKU': 'Tokaanu',
    'BPE': 'Brownhill Rd',
    'BEN': 'Benmore',
    'ISL': 'Islington',
    'TWZ': 'Tiwai Point',
}

for bus_name, label in major_buses.items():
    if bus_name in bus_coords.index:
        x, y = bus_coords.loc[bus_name, ['x', 'y']]
        ax.scatter(x, y, s=200, c='red', marker='s', zorder=25, 
                  edgecolors='yellow', linewidth=3)
        ann = ax.annotate(label, (x, y), xytext=(10, 10), textcoords='offset points',
                   fontsize=16, fontweight='bold', color='darkred',
                   bbox=dict(boxstyle='round,pad=0.6', facecolor='yellow', 
                            alpha=0.95, edgecolor='darkred', linewidth=2.5),
                   zorder=26)
        annotations.append(ann)

# MUCH LARGER axis labels and title
ax.set_xlabel('Longitude', fontsize=20, fontweight='bold')
ax.set_ylabel('Latitude', fontsize=20, fontweight='bold')
ax.set_title('New Zealand Transmission Network\n2030 Baseline Topology', 
            fontsize=24, fontweight='bold', pad=25)
ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
ax.set_aspect('equal')

# LARGER tick labels
ax.tick_params(axis='both', which='major', labelsize=16)

# LARGER legend
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], color='darkblue', linewidth=6, label='220 kV (=1000 MVA)', solid_capstyle='round'),
    Line2D([0], [0], color='royalblue', linewidth=4, label='110 kV (600 MVA)', solid_capstyle='round'),
    Line2D([0], [0], color='lightsteelblue', linewidth=2.5, label='66 kV (<600 MVA)', solid_capstyle='round'),
    Line2D([0], [0], color='red', linewidth=8, label='HVDC Link (1200 MW)', solid_capstyle='round'),
    Line2D([0], [0], marker='s', color='w', markerfacecolor='red', 
           markersize=12, label='Major Substation', markeredgecolor='yellow', markeredgewidth=2),
]
ax.legend(handles=legend_elements, loc='upper left', fontsize=16, 
         framealpha=0.95, edgecolor='black', fancybox=True)

# LARGER stats box
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
       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9, edgecolor='black', linewidth=2.5),
       family='monospace')

# Make annotations draggable
class DraggableAnnotation:
    def __init__(self, annotation):
        self.annotation = annotation
        self.press = None
        
    def connect(self):
        self.cidpress = self.annotation.figure.canvas.mpl_connect('button_press_event', self.on_press)
        self.cidrelease = self.annotation.figure.canvas.mpl_connect('button_release_event', self.on_release)
        self.cidmotion = self.annotation.figure.canvas.mpl_connect('motion_notify_event', self.on_motion)
        
    def on_press(self, event):
        if event.inaxes != self.annotation.axes: return
        contains, attrd = self.annotation.contains(event)
        if not contains: return
        self.press = (self.annotation.xy, (event.xdata, event.ydata))
        
    def on_motion(self, event):
        if self.press is None: return
        if event.inaxes != self.annotation.axes: return
        xy0, (xpress, ypress) = self.press
        dx = event.xdata - xpress
        dy = event.ydata - ypress
        self.annotation.set_position((xy0[0] + dx, xy0[1] + dy))
        self.annotation.figure.canvas.draw()
        
    def on_release(self, event):
        self.press = None
        self.annotation.figure.canvas.draw()

# Enable dragging for all annotations
for ann in annotations:
    da = DraggableAnnotation(ann)
    da.connect()

print("\n" + "="*70)
print("INTERACTIVE MODE")
print("="*70)
print("You can now DRAG the yellow annotation boxes to better positions!")
print("Click and drag any yellow box to move it.")
print("Close the window when you're happy with the layout.")
print("="*70)

plt.tight_layout()

# Save initial version
plt.savefig('2030_network_final.png', dpi=300, bbox_inches='tight')
print("\n? Network map saved to: 2030_network_final.png")

# Show interactive plot
plt.show()

print("\nDone! Improvements:")
print("  ? MUCH LARGER text (18-24pt)")
print("  ? RED HVDC link (very visible)")
print("  ? Thicker 66kV lines (now visible)")
print("  ? DRAGGABLE annotations (reposition in interactive window)")
print("  ? Larger tick labels (16pt)")