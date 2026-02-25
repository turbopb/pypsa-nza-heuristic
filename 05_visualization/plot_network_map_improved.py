"""
Improved network map with clearly visible lines and HVDC link.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
import pypsa

print("Loading baseline network...")

# Load BASELINE network for comparison
n = pypsa.Network()
network_path = r"C:\Users\Public\Documents\Thesis\analysis\dispatch_data\cases\reference\2030\baseline_2030"
n.import_from_csv_folder(network_path)

print("Optimizing dispatch...")
n.optimize(solver_name='highs')

# Calculate AC line loadings
line_loading = (n.lines_t.p0.abs().max() / n.lines.s_nom * 100)

# Calculate HVDC link loading
link_loading = {}
if len(n.links) > 0:
    for link in n.links.index:
        loading = (n.links_t.p0[link].abs().max() / n.links.loc[link, 'p_nom'] * 100)
        link_loading[link] = loading
        print(f"HVDC Link {link}: {loading:.1f}% loading")

print(f"\nAC Lines >95%: {(line_loading > 95).sum()}")
print(f"AC Lines at 100%: {(line_loading >= 100).sum()}")

# Get bus coordinates
bus_coords = n.buses[['x', 'y']].copy()

# ============================================================
# Create comprehensive figure
# ============================================================

fig = plt.figure(figsize=(20, 12))
gs = fig.add_gridspec(2, 2, hspace=0.25, wspace=0.25)

# ============================================================
# PLOT 1: All lines with clear visibility (top left)
# ============================================================
ax1 = fig.add_subplot(gs[0, 0])

# Plot ALL AC lines first in light gray
for line_name in n.lines.index:
    bus0 = n.lines.loc[line_name, 'bus0']
    bus1 = n.lines.loc[line_name, 'bus1']
    
    if bus0 in bus_coords.index and bus1 in bus_coords.index:
        x0, y0 = bus_coords.loc[bus0, 'x'], bus_coords.loc[bus0, 'y']
        x1, y1 = bus_coords.loc[bus1, 'x'], bus_coords.loc[bus1, 'y']
        
        loading = line_loading[line_name] if line_name in line_loading.index else 0
        s_nom = n.lines.loc[line_name, 's_nom']
        
        # Determine color based on loading
        if loading >= 100:
            color = 'red'
            width = 4.0
            alpha = 1.0
            zorder = 10
        elif loading >= 95:
            color = 'orange'
            width = 3.5
            alpha = 0.9
            zorder = 9
        elif loading >= 80:
            color = 'gold'
            width = 2.5
            alpha = 0.7
            zorder = 5
        elif loading >= 60:
            color = 'yellow'
            width = 2.0
            alpha = 0.6
            zorder = 4
        elif loading >= 40:
            color = 'lightgreen'
            width = 1.5
            alpha = 0.5
            zorder = 3
        else:
            color = 'green'
            width = 1.5
            alpha = 0.4
            zorder = 2
        
        # Make thicker based on capacity
        if s_nom >= 1000:
            width *= 1.5
        
        ax1.plot([x0, x1], [y0, y1], color=color, linewidth=width, 
                alpha=alpha, zorder=zorder, solid_capstyle='round')

# Plot HVDC link
if len(n.links) > 0:
    for link in n.links.index:
        bus0 = n.links.loc[link, 'bus0']
        bus1 = n.links.loc[link, 'bus1']
        
        if bus0 in bus_coords.index and bus1 in bus_coords.index:
            x0, y0 = bus_coords.loc[bus0, 'x'], bus_coords.loc[bus0, 'y']
            x1, y1 = bus_coords.loc[bus1, 'x'], bus_coords.loc[bus1, 'y']
            
            loading = link_loading.get(link, 0)
            
            if loading >= 95:
                color = 'purple'
            elif loading >= 80:
                color = 'magenta'
            else:
                color = 'blue'
            
            # Dashed line for HVDC
            ax1.plot([x0, x1], [y0, y1], color=color, linewidth=5, 
                    linestyle='--', alpha=0.9, zorder=15,
                    label=f'HVDC: {loading:.1f}%')
            
            # Add arrow to show direction
            mid_x, mid_y = (x0 + x1) / 2, (y0 + y1) / 2
            dx, dy = x1 - x0, y1 - y0
            ax1.arrow(mid_x - dx*0.05, mid_y - dy*0.05, dx*0.1, dy*0.1,
                     head_width=15000, head_length=20000, fc=color, ec=color,
                     linewidth=2, zorder=16)

# Plot buses
ax1.scatter(bus_coords['x'], bus_coords['y'], s=80, c='black', 
           zorder=20, alpha=0.8, edgecolors='white', linewidth=1.5)

# Formatting
ax1.set_xlabel('Longitude', fontsize=12, fontweight='bold')
ax1.set_ylabel('Latitude', fontsize=12, fontweight='bold')
ax1.set_title('Full Network: All Transmission Lines (2030 Baseline)', 
             fontsize=13, fontweight='bold')
ax1.grid(True, alpha=0.3, linestyle='--')
ax1.set_aspect('equal')
ax1.legend(fontsize=10, loc='upper left')

# ============================================================
# PLOT 2: Only congested lines (top right)
# ============================================================
ax2 = fig.add_subplot(gs[0, 1])

# Plot all lines faint
for line_name in n.lines.index:
    bus0 = n.lines.loc[line_name, 'bus0']
    bus1 = n.lines.loc[line_name, 'bus1']
    
    if bus0 in bus_coords.index and bus1 in bus_coords.index:
        x0, y0 = bus_coords.loc[bus0, 'x'], bus_coords.loc[bus0, 'y']
        x1, y1 = bus_coords.loc[bus1, 'x'], bus_coords.loc[bus1, 'y']
        ax2.plot([x0, x1], [y0, y1], 'lightgray', linewidth=0.5, alpha=0.3, zorder=1)

# Highlight only congested lines (>95%)
congested_count = 0
critical_count = 0

for line_name in n.lines.index:
    loading = line_loading[line_name] if line_name in line_loading.index else 0
    
    if loading > 95:
        bus0 = n.lines.loc[line_name, 'bus0']
        bus1 = n.lines.loc[line_name, 'bus1']
        
        if bus0 in bus_coords.index and bus1 in bus_coords.index:
            x0, y0 = bus_coords.loc[bus0, 'x'], bus_coords.loc[bus0, 'y']
            x1, y1 = bus_coords.loc[bus1, 'x'], bus_coords.loc[bus1, 'y']
            s_nom = n.lines.loc[line_name, 's_nom']
            
            if loading >= 100:
                color = 'red'
                width = 5.0
                critical_count += 1
            else:
                color = 'orange'
                width = 4.0
            
            congested_count += 1
            
            ax2.plot([x0, x1], [y0, y1], color=color, linewidth=width, 
                    alpha=0.9, zorder=5, solid_capstyle='round')
            
            # Label the line
            mid_x, mid_y = (x0 + x1) / 2, (y0 + y1) / 2
            ax2.text(mid_x, mid_y, f'{loading:.0f}%', fontsize=7, 
                    ha='center', va='center',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white', 
                             alpha=0.7, edgecolor=color))

# Plot HVDC
if len(n.links) > 0:
    for link in n.links.index:
        bus0 = n.links.loc[link, 'bus0']
        bus1 = n.links.loc[link, 'bus1']
        
        if bus0 in bus_coords.index and bus1 in bus_coords.index:
            x0, y0 = bus_coords.loc[bus0, 'x'], bus_coords.loc[bus0, 'y']
            x1, y1 = bus_coords.loc[bus1, 'x'], bus_coords.loc[bus1, 'y']
            
            loading = link_loading.get(link, 0)
            color = 'purple' if loading >= 80 else 'blue'
            
            ax2.plot([x0, x1], [y0, y1], color=color, linewidth=5, 
                    linestyle='--', alpha=0.9, zorder=15)
            
            # Label HVDC
            mid_x, mid_y = (x0 + x1) / 2, (y0 + y1) / 2
            ax2.text(mid_x, mid_y, f'HVDC\n{loading:.0f}%', fontsize=9, 
                    ha='center', va='center', fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', 
                             alpha=0.8, edgecolor='purple', linewidth=2))

# Plot buses
ax2.scatter(bus_coords['x'], bus_coords['y'], s=80, c='black', 
           zorder=20, alpha=0.8, edgecolors='white', linewidth=1.5)

# Formatting
ax2.set_xlabel('Longitude', fontsize=12, fontweight='bold')
ax2.set_ylabel('Latitude', fontsize=12, fontweight='bold')
ax2.set_title(f'Congested Corridors: {critical_count} at 100%, {congested_count} total >95%', 
             fontsize=13, fontweight='bold', color='red')
ax2.grid(True, alpha=0.3, linestyle='--')
ax2.set_aspect('equal')

# ============================================================
# PLOT 3: North Island detail (bottom left)
# ============================================================
ax3 = fig.add_subplot(gs[1, 0])

# Focus on North Island
north_lats = bus_coords['y'] > -40
north_buses = bus_coords[north_lats]

# Plot all NI lines
for line_name in n.lines.index:
    bus0 = n.lines.loc[line_name, 'bus0']
    bus1 = n.lines.loc[line_name, 'bus1']
    
    if bus0 in north_buses.index or bus1 in north_buses.index:
        if bus0 in bus_coords.index and bus1 in bus_coords.index:
            x0, y0 = bus_coords.loc[bus0, 'x'], bus_coords.loc[bus0, 'y']
            x1, y1 = bus_coords.loc[bus1, 'x'], bus_coords.loc[bus1, 'y']
            
            loading = line_loading[line_name] if line_name in line_loading.index else 0
            s_nom = n.lines.loc[line_name, 's_nom']
            
            if loading >= 100:
                color = 'red'
                width = 6.0
                alpha = 1.0
            elif loading >= 95:
                color = 'orange'
                width = 5.0
                alpha = 0.9
            elif loading >= 80:
                color = 'gold'
                width = 3.5
                alpha = 0.7
            elif loading >= 60:
                color = 'yellow'
                width = 2.5
                alpha = 0.6
            else:
                color = 'lightgreen'
                width = 2.0
                alpha = 0.5
            
            if s_nom >= 1000:
                width *= 1.3
            
            ax3.plot([x0, x1], [y0, y1], color=color, linewidth=width, 
                    alpha=alpha, solid_capstyle='round')

# Plot HVDC in North Island region
if len(n.links) > 0:
    for link in n.links.index:
        bus0 = n.links.loc[link, 'bus0']
        bus1 = n.links.loc[link, 'bus1']
        
        if bus0 in bus_coords.index and bus1 in bus_coords.index:
            x0, y0 = bus_coords.loc[bus0, 'x'], bus_coords.loc[bus0, 'y']
            x1, y1 = bus_coords.loc[bus1, 'x'], bus_coords.loc[bus1, 'y']
            
            loading = link_loading.get(link, 0)
            color = 'purple' if loading >= 80 else 'blue'
            
            ax3.plot([x0, x1], [y0, y1], color=color, linewidth=6, 
                    linestyle='--', alpha=0.9, zorder=15)

# Plot buses with labels
for bus_name in north_buses.index:
    x, y = bus_coords.loc[bus_name, ['x', 'y']]
    ax3.scatter(x, y, s=120, c='black', zorder=20, 
               edgecolors='white', linewidth=2)
    
    # Label major buses
    major_buses = ['OTA', 'HWA', 'HLY', 'WKM', 'PAK', 'HAY', 'BPE', 'TKU', 
                   'WEL', 'BEN', 'TWZ', 'ROX', 'ISL', 'OHU', 'MDN']
    if bus_name in major_buses:
        ax3.annotate(bus_name, (x, y), xytext=(4, 4), textcoords='offset points',
                    fontsize=10, fontweight='bold', 
                    bbox=dict(boxstyle='round,pad=0.4', facecolor='yellow', 
                             alpha=0.9, edgecolor='black', linewidth=1.5))

# Formatting
ax3.set_xlabel('Longitude', fontsize=12, fontweight='bold')
ax3.set_ylabel('Latitude', fontsize=12, fontweight='bold')
ax3.set_title('North Island Detail: Major Buses and Critical Lines', 
             fontsize=13, fontweight='bold')
ax3.grid(True, alpha=0.3, linestyle='--')
ax3.set_aspect('equal')

# ============================================================
# PLOT 4: South Island detail (bottom right)
# ============================================================
ax4 = fig.add_subplot(gs[1, 1])

# Focus on South Island
south_lats = bus_coords['y'] <= -40
south_buses = bus_coords[south_lats]

# Plot all SI lines
for line_name in n.lines.index:
    bus0 = n.lines.loc[line_name, 'bus0']
    bus1 = n.lines.loc[line_name, 'bus1']
    
    if bus0 in south_buses.index or bus1 in south_buses.index:
        if bus0 in bus_coords.index and bus1 in bus_coords.index:
            x0, y0 = bus_coords.loc[bus0, 'x'], bus_coords.loc[bus0, 'y']
            x1, y1 = bus_coords.loc[bus1, 'x'], bus_coords.loc[bus1, 'y']
            
            loading = line_loading[line_name] if line_name in line_loading.index else 0
            s_nom = n.lines.loc[line_name, 's_nom']
            
            if loading >= 100:
                color = 'red'
                width = 6.0
            elif loading >= 95:
                color = 'orange'
                width = 5.0
            elif loading >= 80:
                color = 'gold'
                width = 3.5
            else:
                color = 'lightgreen'
                width = 2.5
            
            if s_nom >= 1000:
                width *= 1.3
            
            ax4.plot([x0, x1], [y0, y1], color=color, linewidth=width, 
                    alpha=0.8, solid_capstyle='round')

# Plot buses with labels
for bus_name in south_buses.index:
    x, y = bus_coords.loc[bus_name, ['x', 'y']]
    ax4.scatter(x, y, s=120, c='black', zorder=20, 
               edgecolors='white', linewidth=2)
    
    # Label major SI buses
    major_si_buses = ['BEN', 'ISL', 'TWZ', 'ROX', 'LIV', 'CYD', 'INV', 'TIM']
    if bus_name in major_si_buses:
        ax4.annotate(bus_name, (x, y), xytext=(4, 4), textcoords='offset points',
                    fontsize=10, fontweight='bold', 
                    bbox=dict(boxstyle='round,pad=0.4', facecolor='lightblue', 
                             alpha=0.9, edgecolor='black', linewidth=1.5))

# Formatting
ax4.set_xlabel('Longitude', fontsize=12, fontweight='bold')
ax4.set_ylabel('Latitude', fontsize=12, fontweight='bold')
ax4.set_title('South Island Detail: Hydro-Dominated Generation', 
             fontsize=13, fontweight='bold')
ax4.grid(True, alpha=0.3, linestyle='--')
ax4.set_aspect('equal')

# Overall title
fig.suptitle('2030 Baseline: Complete Transmission Network Analysis', 
            fontsize=17, fontweight='bold', y=0.995)

# Add legend
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], color='red', linewidth=4, label='100% Loading (Critical)'),
    Line2D([0], [0], color='orange', linewidth=4, label='95-100% (Severe)'),
    Line2D([0], [0], color='gold', linewidth=3, label='80-95% (High)'),
    Line2D([0], [0], color='yellow', linewidth=2, label='60-80% (Moderate)'),
    Line2D([0], [0], color='lightgreen', linewidth=2, label='40-60% (Normal)'),
    Line2D([0], [0], color='green', linewidth=2, label='<40% (Low)'),
    Line2D([0], [0], color='purple', linewidth=4, linestyle='--', label='HVDC Link'),
]
fig.legend(handles=legend_elements, loc='lower center', ncol=7, 
          fontsize=11, bbox_to_anchor=(0.5, -0.02))

plt.tight_layout(rect=[0, 0.02, 1, 0.995])
plt.savefig('2030_network_comprehensive.png', dpi=300, bbox_inches='tight')
print("\n? Comprehensive network map saved!")

plt.close()
print("Done!")