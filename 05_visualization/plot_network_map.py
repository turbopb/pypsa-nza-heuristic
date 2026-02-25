"""
Plot geographic network map with transmission line loading.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
import pypsa
from matplotlib.patches import FancyBboxPatch
from matplotlib.collections import LineCollection

print("Loading network and running optimization...")

# Load network (use upgraded 2030 as example)
n = pypsa.Network()
network_path = r"C:\Users\Public\Documents\Thesis\analysis\dispatch_data\cases\reference\2030\baseline_2030"
n.import_from_csv_folder(network_path)

print("Optimizing dispatch...")
n.optimize(solver_name='highs')

# Calculate line loadings
line_loading = (n.lines_t.p0.abs().max() / n.lines.s_nom * 100)

print(f"Lines loaded >95%: {(line_loading > 95).sum()}")
print(f"Lines at 100%: {(line_loading >= 100).sum()}")

# Get bus coordinates
bus_coords = n.buses[['x', 'y']].copy()

# Create figure with two subplots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))

# ============================================================
# LEFT PLOT: Network with line loading
# ============================================================

# Create line segments for plotting
segments = []
line_colors = []
line_widths = []

for line_name in n.lines.index:
    bus0 = n.lines.loc[line_name, 'bus0']
    bus1 = n.lines.loc[line_name, 'bus1']
    
    if bus0 in bus_coords.index and bus1 in bus_coords.index:
        x0, y0 = bus_coords.loc[bus0, 'x'], bus_coords.loc[bus0, 'y']
        x1, y1 = bus_coords.loc[bus1, 'x'], bus_coords.loc[bus1, 'y']
        
        segments.append([(x0, y0), (x1, y1)])
        
        # Get loading percentage
        loading = line_loading[line_name] if line_name in line_loading.index else 0
        line_colors.append(loading)
        
        # Line width based on capacity
        s_nom = n.lines.loc[line_name, 's_nom']
        if s_nom >= 1000:
            width = 3.0
        elif s_nom >= 600:
            width = 2.0
        else:
            width = 1.0
        line_widths.append(width)

# Create colormap
cmap = plt.cm.RdYlGn_r  # Red-Yellow-Green reversed (green=low, red=high)
norm = mcolors.Normalize(vmin=0, vmax=100)

# Plot lines
lc = LineCollection(segments, linewidths=line_widths, cmap=cmap, norm=norm, alpha=0.8)
lc.set_array(np.array(line_colors))
ax1.add_collection(lc)

# Plot buses
bus_sizes = 50
ax1.scatter(bus_coords['x'], bus_coords['y'], s=bus_sizes, c='black', 
           zorder=5, alpha=0.6, edgecolors='white', linewidth=0.5)

# Add colorbar
cbar1 = plt.colorbar(lc, ax=ax1, fraction=0.046, pad=0.04)
cbar1.set_label('Line Loading (%)', fontsize=12, fontweight='bold')

# Formatting
ax1.set_xlabel('Longitude', fontsize=12, fontweight='bold')
ax1.set_ylabel('Latitude', fontsize=12, fontweight='bold')
ax1.set_title('NZ Transmission Network: Line Loading by Corridor', 
             fontsize=14, fontweight='bold')
ax1.grid(True, alpha=0.3, linestyle='--')
ax1.set_aspect('equal')

# Add legend for line widths
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], color='gray', linewidth=3, label='=1000 MVA (220 kV)'),
    Line2D([0], [0], color='gray', linewidth=2, label='600 MVA (110 kV)'),
    Line2D([0], [0], color='gray', linewidth=1, label='<600 MVA (66 kV)')
]
ax1.legend(handles=legend_elements, loc='upper left', fontsize=10)

# ============================================================
# RIGHT PLOT: Congested corridors highlighted
# ============================================================

# Plot all lines in gray first
for seg in segments:
    ax2.plot([seg[0][0], seg[1][0]], [seg[0][1], seg[1][1]], 
            'gray', linewidth=0.5, alpha=0.3, zorder=1)

# Highlight congested lines (>95%)
congested_segments = []
congested_colors = []
congested_widths = []

for i, line_name in enumerate(n.lines.index):
    loading = line_colors[i]
    if loading > 95:
        congested_segments.append(segments[i])
        congested_colors.append(loading)
        congested_widths.append(line_widths[i] * 2)  # Thicker for visibility

if congested_segments:
    lc_congested = LineCollection(congested_segments, linewidths=congested_widths, 
                                  cmap=cmap, norm=norm, alpha=0.9, zorder=3)
    lc_congested.set_array(np.array(congested_colors))
    ax2.add_collection(lc_congested)

# Plot buses
ax2.scatter(bus_coords['x'], bus_coords['y'], s=bus_sizes, c='black', 
           zorder=5, alpha=0.6, edgecolors='white', linewidth=0.5)

# Add colorbar
cbar2 = plt.colorbar(lc_congested if congested_segments else lc, ax=ax2, 
                     fraction=0.046, pad=0.04)
cbar2.set_label('Line Loading (%)', fontsize=12, fontweight='bold')

# Formatting
ax2.set_xlabel('Longitude', fontsize=12, fontweight='bold')
ax2.set_ylabel('Latitude', fontsize=12, fontweight='bold')
ax2.set_title(f'Congested Corridors (>{95}% Loading): {len(congested_segments)} Lines', 
             fontsize=14, fontweight='bold')
ax2.grid(True, alpha=0.3, linestyle='--')
ax2.set_aspect('equal')

# Add annotation
textstr = f'Baseline 2030:\n{(line_loading > 95).sum()} lines >95%\n{(line_loading >= 100).sum()} lines at 100%'
props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
ax2.text(0.02, 0.98, textstr, transform=ax2.transAxes, fontsize=11,
        verticalalignment='top', bbox=props)

# Overall title
fig.suptitle('2030 Transmission System: Geographic Loading Analysis', 
            fontsize=16, fontweight='bold')

plt.tight_layout()
plt.savefig('2030_network_map.png', dpi=300, bbox_inches='tight')
print("\n? Network map saved to: 2030_network_map.png")

# ============================================================
# Create detailed regional zoom
# ============================================================

fig2, ax3 = plt.subplots(figsize=(14, 10))

# Focus on North Island (where most congestion is)
north_island_buses = bus_coords[(bus_coords['y'] > -40)]

# Plot lines in North Island region
for i, line_name in enumerate(n.lines.index):
    bus0 = n.lines.loc[line_name, 'bus0']
    bus1 = n.lines.loc[line_name, 'bus1']
    
    if bus0 in north_island_buses.index or bus1 in north_island_buses.index:
        seg = segments[i]
        loading = line_colors[i]
        width = line_widths[i]
        
        # Color based on loading
        if loading >= 100:
            color = 'red'
            alpha = 0.9
            width *= 2
        elif loading >= 95:
            color = 'orange'
            alpha = 0.8
            width *= 1.5
        elif loading >= 80:
            color = 'yellow'
            alpha = 0.6
        else:
            color = 'green'
            alpha = 0.4
        
        ax3.plot([seg[0][0], seg[1][0]], [seg[0][1], seg[1][1]], 
                color=color, linewidth=width, alpha=alpha, zorder=2)

# Plot buses with labels for major nodes
for bus_name in north_island_buses.index:
    x, y = bus_coords.loc[bus_name, ['x', 'y']]
    ax3.scatter(x, y, s=100, c='black', zorder=5, 
               edgecolors='white', linewidth=1)
    
    # Label major buses
    if bus_name in ['OTA', 'HWA', 'HLY', 'WKM', 'PAK', 'HAY', 'BPE', 'TKU', 'WEL']:
        ax3.annotate(bus_name, (x, y), xytext=(3, 3), textcoords='offset points',
                    fontsize=9, fontweight='bold', 
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))

# Formatting
ax3.set_xlabel('Longitude', fontsize=12, fontweight='bold')
ax3.set_ylabel('Latitude', fontsize=12, fontweight='bold')
ax3.set_title('North Island Transmission: Critical Congestion Points', 
             fontsize=14, fontweight='bold')
ax3.grid(True, alpha=0.3, linestyle='--')
ax3.set_aspect('equal')

# Legend
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor='red', alpha=0.9, label='100% Loading (Critical)'),
    Patch(facecolor='orange', alpha=0.8, label='95-100% Loading (Severe)'),
    Patch(facecolor='yellow', alpha=0.6, label='80-95% Loading (High)'),
    Patch(facecolor='green', alpha=0.4, label='<80% Loading (Normal)')
]
ax3.legend(handles=legend_elements, loc='upper right', fontsize=11)

plt.tight_layout()
plt.savefig('2030_network_north_island.png', dpi=300, bbox_inches='tight')
print("? North Island zoom saved to: 2030_network_north_island.png")

# ============================================================
# Print top congested corridors with geography
# ============================================================

print("\n" + "="*80)
print("TOP 15 CONGESTED TRANSMISSION CORRIDORS")
print("="*80)
print(f"{'Rank':<5} {'Line':<10} {'Corridor':<30} {'Capacity':<10} {'Loading':<10}")
print("-"*80)

top_lines = line_loading.sort_values(ascending=False).head(15)
for rank, (line_name, loading) in enumerate(top_lines.items(), 1):
    bus0 = n.lines.loc[line_name, 'bus0']
    bus1 = n.lines.loc[line_name, 'bus1']
    s_nom = n.lines.loc[line_name, 's_nom']
    corridor = f"{bus0}?{bus1}"
    
    print(f"{rank:<5} {line_name:<10} {corridor:<30} {s_nom:<10.0f} {loading:<10.1f}%")

plt.close('all')
print("\nDone! Created 2 network maps.")