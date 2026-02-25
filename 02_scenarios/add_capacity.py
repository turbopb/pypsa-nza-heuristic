"""
Add heuristic capacity to 2030 network.

Based on shortfall analysis:
- Wind: 626 MW (50%)
- Solar: 250 MW (20%)
- Gas: 250 MW (20%)
- Battery: 125 MW (10%)
Total: 1,251 MW
"""

import pandas as pd
from pathlib import Path
import shutil

# Heuristic additions based on analysis
ADDITIONS = {
# Wind additions (550 MW total) - distributed
    'wind': [
        ('WKM', 180),  
        ('WVY', 140),  
        ('GOR', 140),  
        ('TWC', 90),   
    ],
    # Solar additions (200 MW total)
    'solar_pv': [
        ('WAI', 70),   
        ('MTO', 70),   
        ('EDG', 60),   
    ],
# Gas peaking (1575 MW total - WITH RESERVE MARGIN) - near demand centers
# Gas peaking (2000 MW total - SUBSTANTIAL MARGIN) - near demand centers
    'gas': [
        ('OTA', 600),  # Auckland region
        ('HWA', 500),  # Huntly region
        ('SFD', 300),  # Stratford region
        ('TAB', 300),  # Taranaki region
        ('GLN', 300),  # Glenbrook region
    ],
    # Battery storage (200 MW total - INCREASED) - strategic locations
    'battery': [
        ('BEN', 75),   # Benmore (increased)
        ('HAY', 75),   # Haywards (increased)
        ('OTA', 50),   # Otahuhu (increased)
    ],
}

print("\n" + "="*60)
print("ADDING HEURISTIC CAPACITY TO 2030 NETWORK")
print("="*60)

# Paths
baseline_dir = Path(r"C:\Users\Public\Documents\Thesis\analysis\dispatch_network_builder\networks\2030\baseline_2030")
upgraded_dir = Path(r"C:\Users\Public\Documents\Thesis\analysis\dispatch_network_builder\networks\2030\upgraded_2030")

# Copy baseline to upgraded
print(f"\nCopying baseline to upgraded directory...")
if upgraded_dir.exists():
    shutil.rmtree(upgraded_dir)
shutil.copytree(baseline_dir, upgraded_dir)
print(f"? Copied to: {upgraded_dir}")

# Load network files
gen_file = upgraded_dir / "generators.csv"
gen_p_max_pu_file = upgraded_dir / "generators-p_max_pu.csv"

gens = pd.read_csv(gen_file)
gen_p_max_pu = pd.read_csv(gen_p_max_pu_file, index_col=0)

# Add generators
print("\nAdding generators:")
new_generators = []
added_by_type = {}

for carrier, locations in ADDITIONS.items():
    added_by_type[carrier] = {'count': 0, 'total_mw': 0}
    
    for bus, p_nom in locations:
        gen_name = f"NEW_{carrier}_{bus}_{int(p_nom)}"
        
        # Determine p_max_pu and marginal cost
        if carrier == 'wind':
            p_max_pu = 0.40  # 40% capacity factor
            marginal_cost = 0.0
        elif carrier == 'solar_pv':
            p_max_pu = 0.25  # 25% capacity factor
            marginal_cost = 0.0
        elif carrier == 'gas':
            p_max_pu = 0.9999  # Nearly full availability
            marginal_cost = 150.0
        elif carrier == 'battery':
            p_max_pu = 0.9999  # Full availability
            marginal_cost = 0.0  # Storage, not generation
            carrier = 'battery_storage'  # Rename for clarity
        
        # Add to generators.csv
        new_gen = {
            'name': gen_name,
            'bus': bus,
            'control': 'PQ',
            'type': '',
            'p_nom': p_nom,
            'p_max_pu': p_max_pu,
            'carrier': carrier,
            'marginal_cost': marginal_cost
        }
        new_generators.append(new_gen)
        
        # Add to time-series
        gen_p_max_pu[gen_name] = p_max_pu
        
        # Track totals
        added_by_type[carrier if carrier != 'battery_storage' else 'battery']['count'] += 1
        added_by_type[carrier if carrier != 'battery_storage' else 'battery']['total_mw'] += p_nom
        
        print(f"  ? {gen_name}: {p_nom} MW at {bus}")

# Append new generators
gens = pd.concat([gens, pd.DataFrame(new_generators)], ignore_index=True)

# Save
gens.to_csv(gen_file, index=False)
gen_p_max_pu.to_csv(gen_p_max_pu_file)

print("\n" + "="*60)
print("SUMMARY OF ADDITIONS")
print("="*60)

total_added = 0
for carrier, stats in added_by_type.items():
    if stats['count'] > 0:
        print(f"{carrier.upper()}: {stats['count']} generators, {stats['total_mw']} MW")
        total_added += stats['total_mw']

print(f"\nTOTAL ADDED: {total_added} MW")
print(f"Target was: 1,252 MW")
print(f"Difference: {total_added - 1252} MW")

print(f"\n? Upgraded network saved to: {upgraded_dir}")
print("\nNext: Copy to dispatch_data and run validation")