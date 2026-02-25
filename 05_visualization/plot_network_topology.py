"""
Plot network topology with line capacities (no optimization needed).
Shows which lines are likely to be congested based on capacity and location.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pypsa

print("Loading baseline network...")

# Load network (no optimization needed)
n = pypsa.Network()
network_path = r"C:\Users\Public\Documents\Thesis\analysis\dispatch_data\cases\reference\2030\baseline_2030"
n.import_from_csv_folder(network_path)

print(f"Network has {len(n.buses)} buses, {len(n.lines)} AC lines, {len(n.links)} DC links")

# Get bus coordinates
bus_coords = n.buses[['x', 'y']].copy()

# Get HVDC link info
print("\nHVDC Links:")
for link in n.links.index:
    bus0 = n.links.loc[link, 'bus0']
    bus1 = n.links.loc[link, 'bus1']
    p_nom = n.links.loc[link, 'p_nom']
    print(f"  {link}: {bus0}?{bus1}, {p_nom} MW")

# From validation results, we know these lines were congested
# (You can update this list from the validation output)
known_congested = ['N-L133', 'N-L111', 'N-L122', 'N-L85', 'N-L101']

# ============================================================
# Create comprehensive figure
# ============================================================

fig = plt.figure(figsize=(20, 12))
gs = fig.add_gridspec(2, 2, hspace=0.25, wspace=0.25)

# ============================================================
# PLOT 1: Full network by capacity (top left)
# ============================================================
ax1 = fig.add_subplot(gs[0, 0])

# Plot AC lines by capacity
for line_name in n.lines.index:
    bus0 = n.lines.loc[line_name, 'bus0']
    bus1 = n.lines.loc[line_name, 'bus1']
    
    if bus0 in bus_coords.index and bus1 in bus_coords.index:
        x0, y0 = bus_coords.loc[bus0, 'x'], bus_coords.loc[bus0, 'y']
        x1, y1 = bus_coords.loc[bus1, 'x'], bus_coords.loc[bus1, 'y']
        
        s_nom = n.lines.loc[line_name, 's_nom']
        
        # Color by capacity rating
        if s_nom >= 1000:
            color = 'darkblue'
            width = 4.0
            label = '=1000 MVA (220 kV)'
        elif s_nom >= 600:
            color = 'blue'
            width = 2.5
            label = '600 MVA (110 kV)'
        else:
            color = 'lightblue'
            width = 1.5
            label = '<600 MVA (66 kV)'
        
        # Highlight known congested lines
        if line_name in known_congested:
            color = 'red'
            width *= 1.5
        
        ax1.plot([x0, x1], [y0, y1], color=color, linewidth=width, 
                alpha=0.7, solid_capstyle='round')

# Plot HVDC link
for link in n.links.index:
    bus0 = n.links.loc[link, 'bus0']
    bus1 = n.links.loc[link, 'bus1']
    
    if bus0 in bus_coords.index and bus1 in bus_coords.index:
        x0, y0 = bus_coords.loc[bus0, 'x'], bus_coords.loc[bus0, 'y']
        x1, y1 = bus_coords.loc[bus1, 'x'], bus_coords.loc[bus1, 'y']
        
        p_nom = n.links.loc[link, 'p_nom']
        
        # Thick purple dashed line for HVDC
        ax1.plot([x0, x1], [y0, y1], color='purple', linewidth=6, 
                linestyle='--', alpha=0.9, zorder=15,
                label=f'HVDC: {p_nom:.0f} MW')
        
        # Add arrow
        mid_x, mid_y = (x0 + x1) / 2, (y0 + y1) / 2
        dx, dy = x1 - x0, y1 - y0
        ax1.arrow(mid_x - dx*0.05, mid_y - dy*0.05, dx*0.1, dy*0.1,
                 head_width=15000, head_length=20000, fc='purple', ec='purple',
                 linewidth=3, zorder=16)

# Plot buses
ax1.scatter(bus_coords['x'], bus_coords['y'], s=80, c='black', 
           zorder=20, alpha=0.8, edgecolors='white', linewidth=1.5)

# Formatting
ax1.set_xlabel('Longitude', fontsize=12, fontweight='bold')
ax1.set_ylabel('Latitude', fontsize=12, fontweight='bold')
ax1.set_title('Full NZ Transmission Network: Line Capacity Ratings', 
             fontsize=13, fontweight='bold')
ax1.grid(True, alpha=0.3, linestyle='--')
ax1.set_aspect('equal')
ax1.legend(fontsize=10, loc='upper left')

# ============================================================
# PLOT 2: Major corridors (top right)
# ============================================================
ax2 = fig.add_subplot(gs[0, 1])

# Define major corridors (high capacity lines connecting regions)
major_corridors = []
for line_name in n.lines.index:
    s_nom = n.lines.loc[line_name, 's_nom']
    if s_nom >= 600:  # Only 110kV and above
        bus0 = n.lines.loc[line_name, 'bus0']
        bus1 = n.lines.loc[line_name, 'bus1']
        major_corridors.append((line_name, bus0, bus1, s_nom))

# Plot faint all lines
for line_name in n.lines.index:
    bus0 = n.lines.loc[line_name, 'bus0']
    bus1 = n.lines.loc[line_name, 'bus1']
    
    if bus0 in bus_coords.index and bus1 in bus_coords.index:
        x0, y0 = bus_coords.loc[bus0, 'x'], bus_coords.loc[bus0, 'y']
        x1, y1 = bus_coords.loc[bus1, 'x'], bus_coords.loc[bus1, 'y']
        ax2.plot([x0, x1], [y0, y1], 'lightgray', linewidth=0.5, alpha=0.3)

# Highlight major corridors
for line_name, bus0, bus1, s_nom in major_corridors:
    if bus0 in bus_coords.index and bus1 in bus_coords.index:
        x0, y0 = bus_coords.loc[bus0, 'x'], bus_coords.loc[bus0, 'y']
        x1, y1 = bus_coords.loc[bus1, 'x'], bus_coords.loc[bus1, 'y']
        
        if s_nom >= 1000:
            color = 'darkgreen'
            width = 5.0
        else:
            color = 'green'
            width = 3.5
        
        # Mark known congested
        if line_name in known_congested:
            color = 'red'
        
        ax2.plot([x0, x1], [y0, y1], color=color, linewidth=width, 
                alpha=0.8, solid_capstyle='round')

# Plot HVDC
for link in n.links.index:
    bus0 = n.links.loc[link, 'bus0']
    bus1 = n.links.loc[link, 'bus1']
    
    if bus0 in bus_coords.index and bus1 in bus_coords.index:
        x0, y0 = bus_coords.loc[bus0, 'x'], bus_coords.loc[bus0, 'y']
        x1, y1 = bus_coords.loc[bus1, 'x'], bus_coords.loc[bus1, 'y']
        
        ax2.plot([x0, x1], [y0, y1], color='purple', linewidth=6, 
                linestyle='--', alpha=0.9, zorder=15)

# Plot buses
ax2.scatter(bus_coords['x'], bus_coords['y'], s=80, c='black', 
           zorder=20, alpha=0.8, edgecolors='white', linewidth=1.5)

# Formatting
ax2.set_xlabel('Longitude', fontsize=12, fontweight='bold')
ax2.set_ylabel('Latitude', fontsize=12, fontweight='bold')
ax2.set_title(f'Major Transmission Corridors: {len(major_corridors)} lines =600 MVA', 
             fontsize=13, fontweight='bold')
ax2.grid(True, alpha=0.3, linestyle='--')
ax2.set_aspect('equal')

# ============================================================
# PLOT 3: North Island with bus labels (bottom left)
# ============================================================
ax3 = fig.add_subplot(gs[1, 0])

# Focus on North Island
north_lats = bus_coords['y'] > -40
north_buses = bus_coords[north_lats]

# Plot NI lines
for line_name in n.lines.index:
    bus0 = n.lines.loc[line_name, 'bus0']
    bus1 = n.lines.loc[line_name, 'bus1']
    
    if bus0 in north_buses.index or bus1 in north_buses.index:
        if bus0 in bus_coords.index and bus1 in bus_coords.index:
            x0, y0 = bus_coords.loc[bus0, 'x'], bus_coords.loc[bus0, 'y']
            x1, y1 = bus_coords.loc[bus1, 'x'], bus_coords.loc[bus1, 'y']
            
            s_nom = n.lines.loc[line_name, 's_nom']
            
            if line_name in known_congested:
                color = 'red'
                width = 6.0
                alpha = 1.0
            elif s_nom >= 1000:
                color = 'darkblue'
                width = 4.0
                alpha = 0.8
            elif s_nom >= 600:
                color = 'blue'
                width = 2.5
                alpha = 0.7
            else:
                color = 'lightblue'
                width = 1.5
                alpha = 0.5
            
            ax3.plot([x0, x1], [y0, y1], color=color, linewidth=width, 
                    alpha=alpha, solid_capstyle='round')

# Plot HVDC
for link in n.links.index:
    bus0 = n.links.loc[link, 'bus0']
    bus1 = n.links.loc[link, 'bus1']
    
    if bus0 in bus_coords.index and bus1 in bus_coords.index:
        x0, y0 = bus_coords.loc[bus0, 'x'], bus_coords.loc[bus0, 'y']
        x1, y1 = bus_coords.loc[bus1, 'x'], bus_coords.loc[bus1, 'y']
        
        ax3.plot([x0, x1], [y0, y1], color='purple', linewidth=6, 
                linestyle='--', alpha=0.9, zorder=15)
        
        # Label HVDC endpoint
        ax3.annotate('HVDC\nfrom SI', (x1, y1), xytext=(10, 10), 
                    textcoords='offset points',
                    fontsize=10, fontweight='bold', color='purple',
                    bbox=dict(boxstyle='round,pad=0.4', facecolor='yellow', 
                             alpha=0.9, edgecolor='purple', linewidth=2))

# Plot buses with labels
for bus_name in north_buses.index:
    x, y = bus_coords.loc[bus_name, ['x', 'y']]
    ax3.scatter(x, y, s=120, c='black', zorder=20, 
               edgecolors='white', linewidth=2)
    
    # Label major buses
    major_buses = ['OTA', 'HWA', 'HLY', 'WKM', 'PAK', 'HAY', 'BPE', 'TKU', 
                   'WEL', 'TWZ', 'ROX', 'ISL', 'OHU', 'MDN', 'SFD', 'TAB']
    if bus_name in major_buses:
        ax3.annotate(bus_name, (x, y), xytext=(4, 4), textcoords='offset points',
                    fontsize=10, fontweight='bold', 
                    bbox=dict(boxstyle='round,pad=0.4', facecolor='yellow', 
                             alpha=0.9, edgecolor='black', linewidth=1.5))

# Formatting
ax3.set_xlabel('Longitude', fontsize=12, fontweight='bold')
ax3.set_ylabel('Latitude', fontsize=12, fontweight='bold')
ax3.set_title('North Island: Major Demand Centers and Generation Sites', 
             fontsize=13, fontweight='bold')
ax3.grid(True, alpha=0.3, linestyle='--')
ax3.set_aspect('equal')

# ============================================================
# PLOT 4: South Island with hydro (bottom right)
# ============================================================
ax4 = fig.add_subplot(gs[1, 1])

# Focus on South Island
south_lats = bus_coords['y'] <= -40
south_buses = bus_coords[south_lats]

# Plot SI lines
for line_name in n.lines.index:
    bus0 = n.lines.loc[line_name, 'bus0']
    bus1 = n.lines.loc[line_name, 'bus1']
    
    if bus0 in south_buses.index or bus1 in south_buses.index:
        if bus0 in bus_coords.index and bus1 in bus_coords.index:
            x0, y0 = bus_coords.loc[bus0, 'x'], bus_coords.loc[bus0, 'y']
            x1, y1 = bus_coords.loc[bus1, 'x'], bus_coords.loc[bus1, 'y']
            
            s_nom = n.lines.loc[line_name, 's_nom']
            
            if s_nom >= 1000:
                color = 'darkblue'
                width = 5.0
            elif s_nom >= 600:
                color = 'blue'
                width = 3.0
            else:
                color = 'lightblue'
                width = 1.5
            
            ax4.plot([x0, x1], [y0, y1], color=color, linewidth=width, 
                    alpha=0.8, solid_capstyle='round')

# Plot HVDC origin
for link in n.links.index:
    bus0 = n.links.loc[link, 'bus0']
    bus1 = n.links.loc[link, 'bus1']
    
    if bus0 in bus_coords.index:
        x0, y0 = bus_coords.loc[bus0, 'x'], bus_coords.loc[bus0, 'y']
        
        # Just show the start point
        ax4.scatter(x0, y0, s=300, c='purple', marker='D', 
                   zorder=25, edgecolors='yellow', linewidth=3,
                   label='HVDC Origin (Benmore)')

# Plot buses with labels
for bus_name in south_buses.index:
    x, y = bus_coords.loc[bus_name, ['x', 'y']]
    ax4.scatter(x, y, s=120, c='black', zorder=20, 
               edgecolors='white', linewidth=2)
    
    # Label major SI buses
    major_si_buses = ['BEN', 'ISL', 'TWZ', 'ROX', 'LIV', 'CYD', 'INV', 'TIM', 
                      'TKB', 'MAK', 'CML', 'ASB']
    if bus_name in major_si_buses:
        ax4.annotate(bus_name, (x, y), xytext=(4, 4), textcoords='offset points',
                    fontsize=10, fontweight='bold', 
                    bbox=dict(boxstyle='round,pad=0.4', facecolor='lightblue', 
                             alpha=0.9, edgecolor='black', linewidth=1.5))

# Formatting
ax4.set_xlabel('Longitude', fontsize=12, fontweight='bold')
ax4.set_ylabel('Latitude', fontsize=12, fontweight='bold')
ax4.set_title('South Island: Hydro Generation Network', 
             fontsize=13, fontweight='bold')
ax4.grid(True, alpha=0.3, linestyle='--')
ax4.set_aspect('equal')
ax4.legend(fontsize=10, loc='lower left')

# Overall title
fig.suptitle('New Zealand Transmission Network Topology (2030 Baseline)', 
            fontsize=17, fontweight='bold', y=0.995)

# Add legend
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], color='darkblue', linewidth=4, label='=1000 MVA (220 kV)'),
    Line2D([0], [0], color='blue', linewidth=3, label='600 MVA (110 kV)'),
    Line2D([0], [0], color='lightblue', linewidth=2, label='<600 MVA (66 kV)'),
    Line2D([0], [0], color='red', linewidth=4, label='Known Congested (from validation)'),
    Line2D([0], [0], color='purple', linewidth=5, linestyle='--', label='HVDC Link (1200 MW)'),
]
fig.legend(handles=legend_elements, loc='lower center', ncol=5, 
          fontsize=11, bbox_to_anchor=(0.5, -0.02))

plt.tight_layout(rect=[0, 0.02, 1, 0.995])
plt.savefig('2030_network_topology.png', dpi=300, bbox_inches='tight')
print("\n? Network topology map saved to: 2030_network_topology.png")

plt.close()
print("Done! All lines clearly visible with HVDC link shown.")