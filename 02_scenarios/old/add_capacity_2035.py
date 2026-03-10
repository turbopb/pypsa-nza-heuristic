"""
Add heuristic capacity to 2035 network.
Iteration 3: Final push to <0.1% adequacy
"""

import pandas as pd
from pathlib import Path
import shutil

# Heuristic additions for 2035 (iteration 3 - FINAL)
ADDITIONS = {
    # Wind additions (400 MW)
    'wind': [
        ('WKM', 120),
        ('WVY', 100),
        ('GOR', 100),
        ('TWC', 80),
    ],
    # Solar additions (200 MW)
    'solar_pv': [
        ('WAI', 80),
        ('MTO', 60),
        ('EDG', 60),
    ],
    # Gas peaking (3,000 MW - FINAL PUSH)
    'gas': [
        ('OTA', 900),   # Auckland (major increase)
        ('HWA', 750),   # Huntly
        ('SFD', 600),   # Stratford
        ('GLN', 450),   # Glenbrook
        ('TAB', 300),   # Taranaki
    ],
    # Battery storage (200 MW)
    'battery': [
        ('BEN', 75),
        ('HAY', 75),
        ('OTA', 50),
    ],
}

print("\n" + "="*80)
print("ADDING CAPACITY TO 2035 NETWORK (ITERATION 3 - FINAL)")
print("="*80)

baseline_dir = Path(r"C:\Users\Public\Documents\Thesis\analysis\pypsa-nza-heuristic\data\networks\2035\baseline")
upgraded_dir = Path(r"C:\Users\Public\Documents\Thesis\analysis\pypsa-nza-heuristic\data\networks\2035\upgraded")

print(f"\nCopying baseline to upgraded directory...")
if upgraded_dir.exists():
    shutil.rmtree(upgraded_dir)
shutil.copytree(baseline_dir, upgraded_dir)
print(f"OK - Copied to: {upgraded_dir}")

gen_file = upgraded_dir / "generators.csv"
gen_p_max_pu_file = upgraded_dir / "generators-p_max_pu.csv"

gens = pd.read_csv(gen_file)
gen_p_max_pu = pd.read_csv(gen_p_max_pu_file, index_col=0)

print("\nAdding generators:")
new_generators = []
added_by_type = {}

for carrier, locations in ADDITIONS.items():
    added_by_type[carrier] = {'count': 0, 'total_mw': 0}
    
    for bus, p_nom in locations:
        gen_name = f"NEW2035_{carrier}_{bus}_{int(p_nom)}"
        
        if carrier == 'wind':
            p_max_pu = 0.40
            marginal_cost = 0.0
        elif carrier == 'solar_pv':
            p_max_pu = 0.25
            marginal_cost = 0.0
        elif carrier == 'gas':
            p_max_pu = 0.9999
            marginal_cost = 150.0
        elif carrier == 'battery':
            p_max_pu = 0.9999
            marginal_cost = 0.0
            carrier = 'battery_storage'
        
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
        gen_p_max_pu[gen_name] = p_max_pu
        
        added_by_type[carrier if carrier != 'battery_storage' else 'battery']['count'] += 1
        added_by_type[carrier if carrier != 'battery_storage' else 'battery']['total_mw'] += p_nom
        
        print(f"  + {gen_name}: {p_nom} MW at {bus}")

gens = pd.concat([gens, pd.DataFrame(new_generators)], ignore_index=True)

gens.to_csv(gen_file, index=False)
gen_p_max_pu.to_csv(gen_p_max_pu_file)

print("\n" + "="*80)
print("SUMMARY OF ADDITIONS")
print("="*80)

total_added = 0
for carrier, stats in added_by_type.items():
    if stats['count'] > 0:
        print(f"{carrier.upper()}: {stats['count']} generators, {stats['total_mw']} MW")
        total_added += stats['total_mw']

print(f"\nTOTAL ADDED: {total_added} MW")
print(f"\nUpgraded network saved to: {upgraded_dir}")
print("="*80)