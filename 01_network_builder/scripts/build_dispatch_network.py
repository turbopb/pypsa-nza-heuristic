"""
build_dispatch_network.py

Simplified network builder for dispatch validation.
Uses fixed realistic line ratings. Completely isolated from capacity expansion.
"""

import os
import sys
from pathlib import Path
import pandas as pd
import pypsa
import yaml
import warnings
import logging

# Suppress PyPSA warnings
warnings.filterwarnings('ignore')
logging.getLogger('pypsa').setLevel(logging.ERROR)

# Configuration
CONFIG_FILE = Path(__file__).parent.parent / "config" / "dispatch_net_config.yaml"

def load_config():
    with open(CONFIG_FILE, 'r') as f:
        return yaml.safe_load(f)

def create_network(config):
    """Create base network with topology and demand."""
    print("\n" + "="*60)
    print("BUILDING DISPATCH VALIDATION NETWORK")
    print("="*60)
    
    # Create network
    n = pypsa.Network()
    
    # Set snapshots from config
    snapshots = pd.date_range(
        start=config['start_date'],
        end=config['end_date'],
        freq=config['frequency']
    )
    n.set_snapshots(snapshots)
    print(f"  Snapshots: {len(snapshots)}")
    
    # Add carriers
    carriers = ["hydro", "solar_pv", "geothermal", "gas", "diesel", "wind", "DC"]
    colors = ["blue", "yellow", "orange", "green", "brown", "cyan", "red"]
    n.add("Carrier", carriers, color=colors)
    print(f"  ✓ Added {len(carriers)} carriers")
    
    # Load and add buses
    root = Path(config['paths']['root'])
    bus_file = root / config['paths']['dirpath_static'] / config['filename']['bus_data']
    buses = pd.read_csv(bus_file)
    
    for _, row in buses.iterrows():
        n.add("Bus",
            name=row['site'],
            v_nom=row.get('volts', 220),
            x=row['X'],
            y=row['Y'],
            carrier="AC")
        
    print(f"  ✓ Added {len(buses)} buses")
    
    # Load and add lines with voltage-appropriate ratings
    line_file = root / config['paths']['dirpath_static'] / config['filename']['line_data']
    lines = pd.read_csv(line_file)
    
    # Critical corridors with higher capacity
    critical_lines = {
        'N-L27': 2000.0,  # WKM→PAK 400kV DC (Auckland feed)
    }
    
    for _, row in lines.iterrows():
        voltage = row.get('volts', 220)  # Get voltage, default to 220
        
        # Check if this is a critical line first
        if row['line'] in critical_lines:
            s_nom_fixed = critical_lines[row['line']]
        elif voltage >= 220:
            s_nom_fixed = 1000.0  # Major 220 kV lines - double circuit
        elif voltage >= 110:
            s_nom_fixed = 600.0   # 110 kV lines
        else:
            s_nom_fixed = 300.0   # 66 kV lines
            
        n.add("Line",
              name=row['line'],
              bus0=row['bus0'],
              bus1=row['bus1'],
              s_nom=s_nom_fixed,
              s_nom_extendable=False,
              length=row['length'],
              x=0.01 * row['length'],
              r=0.001 * row['length'])
    print(f"  ✓ Added {len(lines)} lines with voltage-appropriate ratings")
    
    # Load and add HVDC link with ACTUAL rating
    link_file = root / config['paths']['dirpath_static'] / config['filename']['link_data']
    links = pd.read_csv(link_file)
    
    for _, row in links.iterrows():
        # Use p_nom from file if present, otherwise use config default
        p_nom = row.get('p_nom', config['line_ratings']['hvdc_p_nom'])
        
        n.add("Link",
              name=row['link'],
              bus0=row['bus0'],
              bus1=row['bus1'],
              p_nom=p_nom,                # ACTUAL HVDC rating
              p_nom_extendable=False,     # NOT extendable
              carrier=row['carrier'],
              efficiency=0.98)            # ~2% HVDC losses
    print(f"  ✓ Added {len(links)} HVDC links (p_nom = {p_nom} MW)")
    
    # Load and add generators (dormant - will be activated by customize script)
    gen_file = root / config['paths']['dirpath_static'] / config['filename']['gen_data']
    generators = pd.read_csv(gen_file)
    
    for _, row in generators.iterrows():
        n.add("Generator",
              name=row['site'],
              bus=row['site'],
              p_nom=row['p_nom'],
              carrier=row['carrier'],
              p_max_pu=0.0,  # Dormant until customized
              p_min_pu=0.0)
    print(f"  ✓ Added {len(generators)} generators (dormant)")
    
    # Add loads from monthly demand file
    demand_path = config['paths']['dirpath_demand']
    if Path(demand_path).is_absolute():
        demand_dir = Path(demand_path)
    else:
        demand_dir = root / demand_path

    # Determine month number from start_date
    start_date = pd.to_datetime(config['start_date'])
    month_num = start_date.strftime('%Y%m')
    
    # Load monthly demand file
    demand_file = demand_dir / f"{month_num}_d_MW.csv"
    print(f"  Loading demand from: {demand_file}")

    if demand_file.exists():
        demand_data = pd.read_csv(demand_file, index_col=0, parse_dates=True)
        demand_data = demand_data.reindex(n.snapshots, method='nearest')
        
        loads_added = 0
        for bus in n.buses.index:
            if bus in demand_data.columns:
                n.add("Load",
                    name=bus,
                    bus=bus,
                    p_set=demand_data[bus].values)
                loads_added += 1
        
        print(f"  ✓ Added {loads_added} loads with time-series demand")
    else:
        print(f"  ✗ Demand file not found: {demand_file}")
        loads_added = 0    

    return n

def save_network(network, config, month='apr', year=2024):
    """Save network to CSV folder."""
    root = Path(config['paths']['root'])
    output_dir = root / config['paths']['dirpath_networks'] / str(year) / f"{month}_{year}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    network.export_to_csv_folder(str(output_dir))
    print(f"\n✓ Network saved to: {output_dir}")
    
    return output_dir

if __name__ == '__main__':
    print("\nDISPATCH NETWORK BUILDER")
    print("Isolated from capacity expansion - fixed realistic line ratings\n")
    
    # Load config
    config = load_config()
    
    # Build network
    network = create_network(config)
    
    # Save network (output folder name doesn't matter - we'll rename when copying)
    save_network(network, config, month='temp', year=2024)
    
    print("\n" + "="*60)
    print("✓ NETWORK BUILD COMPLETE")
    print("="*60)
    print("\nNext step: Run customize_dispatch_network.py to add profiles")