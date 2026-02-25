"""
customize_dispatch_network.py

Adds renewable profiles and generator availability to dispatch network.
"""

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

def load_network(config, year=2024, month='temp'):
    """Load the base network."""
    root = Path(config['paths']['root'])
    network_dir = root / config['paths']['dirpath_networks'] / str(year) / f"{month}_{year}"
    
    print(f"\nLoading network from: {network_dir}")
    n = pypsa.Network()
    n.import_from_csv_folder(str(network_dir))
    
    print(f"  Buses: {len(n.buses)}")
    print(f"  Generators: {len(n.generators)}")
    print(f"  Lines: {len(n.lines)}")
    print(f"  Loads: {len(n.loads)}")
    
    return n

def save_network(network, config, month='temp', year=2024):
    """Save customized network."""
    root = Path(config['paths']['root'])
    output_dir = root / config['paths']['dirpath_networks'] / str(year) / f"{month}_{year}"
    
    network.export_to_csv_folder(str(output_dir))
    print(f"\n✓ Customized network saved to: {output_dir}")
    
    return output_dir

def add_renewable_profiles(network, config):
    """Add time-varying availability profiles for renewables."""
    print("\n" + "="*60)
    print("ADDING RENEWABLE PROFILES")
    print("="*60)
    
    # Load solar profile from monthly file
    solar_file = Path(config['paths']['dirpath_renewables_solar']) / config['filename']['solar_dir'] / f"solar_PV_pu_{config['filename']['wind_pu'][-10:-4]}.csv"
    solar_gens = network.generators[network.generators.carrier == 'solar_pv'].index
    
    if solar_file.exists():
        solar_pu = pd.read_csv(solar_file, index_col=0, parse_dates=True)
        # Remove timezone if present
        if hasattr(solar_pu.index, 'tz') and solar_pu.index.tz is not None:
            solar_pu.index = solar_pu.index.tz_localize(None)
        else:
            solar_pu.index = pd.to_datetime(solar_pu.index, utc=True).tz_localize(None)
        solar_pu = solar_pu.reindex(network.snapshots, method='nearest')
        
        solar_profiles_added = 0
        for gen in solar_gens:
            if gen in solar_pu.columns:
                network.generators_t.p_max_pu[gen] = solar_pu[gen].values
                solar_profiles_added += 1
        
        if solar_profiles_added > 0:
            print(f"  ✓ Added solar profiles for {solar_profiles_added} generators")
        else:
            print(f"  ⚠ No matching solar columns found in {solar_file.name}")
            network.generators.loc[solar_gens, 'p_max_pu'] = 0.25
            print(f"  ✓ Using fixed 25% capacity factor for {len(solar_gens)} solar generators")
    else:
        print(f"  ⚠ Solar file not found: {solar_file}")
        if len(solar_gens) > 0:
            network.generators.loc[solar_gens, 'p_max_pu'] = 0.25
            print(f"  ✓ Using fixed 25% capacity factor for {len(solar_gens)} solar generators")
    
    # Load wind profile
    wind_file = Path(config['paths']['dirpath_renewables_wind']) / config['filename']['wind_pu']
    wind_gens = network.generators[network.generators.carrier == 'wind'].index
    
    if wind_file.exists():
        wind_pu = pd.read_csv(wind_file, index_col=0, parse_dates=True)
        # Remove timezone if present
        if hasattr(wind_pu.index, 'tz') and wind_pu.index.tz is not None:
            wind_pu.index = wind_pu.index.tz_localize(None)
        else:
            wind_pu.index = pd.to_datetime(wind_pu.index, utc=True).tz_localize(None)
        wind_pu = wind_pu.reindex(network.snapshots, method='nearest')
        
        wind_profiles_added = 0
        for gen in wind_gens:
            if gen in wind_pu.columns:
                network.generators_t.p_max_pu[gen] = wind_pu[gen].values
                wind_profiles_added += 1
        
        if wind_profiles_added > 0:
            print(f"  ✓ Added wind profiles for {wind_profiles_added} generators")
        else:
            print(f"  ⚠ No matching wind columns found")
            network.generators.loc[wind_gens, 'p_max_pu'] = 0.40
            print(f"  ✓ Using fixed 40% capacity factor for {len(wind_gens)} wind generators")
    else:
        print(f"  ⚠ Wind file not found: {wind_file}")
        if len(wind_gens) > 0:
            network.generators.loc[wind_gens, 'p_max_pu'] = 0.40
            print(f"  ✓ Using fixed 40% capacity factor for {len(wind_gens)} wind generators")
    
    return network

def set_generator_availability(network):
    """Set availability factors for non-renewable generators."""
    print("\n" + "="*60)
    print("SETTING GENERATOR AVAILABILITY")
    print("="*60)
    
    # Initialize empty DataFrame if needed
    if network.generators_t.p_max_pu.empty:
        network.generators_t.p_max_pu = pd.DataFrame(
            index=network.snapshots,
            columns=network.generators.index,
            dtype=float
        )
    
    # Add any missing generator columns
    for gen in network.generators.index:
        if gen not in network.generators_t.p_max_pu.columns:
            network.generators_t.p_max_pu[gen] = float('nan')
    
    # Availability factors by carrier type
    availability = {
        'hydro': 0.9999,       
        'geothermal': 0.95,  
        'gas': 0.9999,       # ← Changed from 1.0 (forces export)
        'diesel': 0.9999,    # ← Changed from 1.0 (forces export)
    }
    
    for carrier, factor in availability.items():
        gens = network.generators[network.generators.carrier == carrier].index
        if len(gens) > 0:
            # Set static value
            network.generators.loc[gens, 'p_max_pu'] = factor
            
            # Set time-series
            for gen in gens:
                network.generators_t.p_max_pu.loc[:, gen] = factor
            
            print(f"  ✓ Set {carrier}: {len(gens)} generators at {factor*100:.2f}% availability")
    
    return network

    
def add_costs(network, config):
    """Add marginal costs to generators."""
    print("\n" + "="*60)
    print("ADDING GENERATOR COSTS")
    print("="*60)
    
    # Simple cost estimates (NZD/MWh)
    costs = {
        'hydro': 0.0,        # Zero marginal cost
        'wind': 0.0,         # Zero marginal cost
        'solar_pv': 0.0,     # Zero marginal cost
        'geothermal': 5.0,   # Low marginal cost
        'gas': 150.0,        # Gas price dependent
        'diesel': 300.0,     # Expensive backup
    }
    
    for carrier, cost in costs.items():
        gens = network.generators[network.generators.carrier == carrier].index
        if len(gens) > 0:
            network.generators.loc[gens, 'marginal_cost'] = cost
            print(f"  ✓ Set {carrier}: {len(gens)} generators at ${cost:.0f}/MWh")
    
    return network

if __name__ == '__main__':
    print("\n" + "="*60)
    print("DISPATCH NETWORK CUSTOMIZER")
    print("="*60)
    
    # Load config
    config = load_config()
    
    # Load base network (from temp location)
    network = load_network(config, year=2024, month='temp')
    
    # IMPORTANT: Set availability FIRST
    network = set_generator_availability(network)
    
    # THEN add renewable profiles
    network = add_renewable_profiles(network, config)
    
    # Add costs
    network = add_costs(network, config)
    
    # Verification
    print("\n" + "="*60)
    print("VERIFICATION: Generators in time-series")
    print("="*60)
    print(f"Total generators: {len(network.generators)}")
    print(f"Generators with p_max_pu time-series: {len(network.generators_t.p_max_pu.columns)}")
    print(f"Missing: {set(network.generators.index) - set(network.generators_t.p_max_pu.columns)}")
    
    # Save customized network
    save_network(network, config, month='temp', year=2024)
    
    print("\n" + "="*60)
    print("✓ CUSTOMIZATION COMPLETE")
    print("="*60)
    print("\nNext step: Run dispatch validation on this network")