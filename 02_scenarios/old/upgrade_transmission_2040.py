"""
Upgrade transmission lines for 2040 network.
"""

import pandas as pd
from pathlib import Path
import shutil

# Lines requiring upgrades (from 2040 baseline analysis)
UPGRADES = {
    'N-L28': {'from': 1000, 'to': 1500, 'reason': 'SFD-TMN Stratford-Tokaanu'},
    'N-L20': {'from': 1000, 'to': 1500, 'reason': 'WRK-THI Wairakei-Tiwai backbone'},
    'N-L82': {'from': 1000, 'to': 1500, 'reason': 'HWA-SFD Huntly-Stratford (2nd upgrade)'},
    'N-L27': {'from': 2000, 'to': 3000, 'reason': 'WKM-PAK Whakamaru-Pakuranga (major)'},
    'N-L122': {'from': 600, 'to': 1000, 'reason': 'BOB-WIR regional connector'},
}

print("="*80)
print("UPGRADING 2040 TRANSMISSION LINES")
print("="*80)

source_dir = Path(r"C:\Users\Public\Documents\Thesis\analysis\pypsa-nza-heuristic\data\networks\2040\baseline")
target_dir = Path(r"C:\Users\Public\Documents\Thesis\analysis\pypsa-nza-heuristic\data\networks\2040\upgraded")

print(f"\nCopying baseline network...")
if target_dir.exists():
    shutil.rmtree(target_dir)
shutil.copytree(source_dir, target_dir)
print(f"  OK - Copied to: {target_dir}")

lines_file = target_dir / "lines.csv"
lines = pd.read_csv(lines_file)

print(f"\nUpgrading transmission lines:")
upgraded_count = 0
for line_id, upgrade in UPGRADES.items():
    if line_id in lines['name'].values:
        old_capacity = lines.loc[lines['name'] == line_id, 's_nom'].values[0]
        lines.loc[lines['name'] == line_id, 's_nom'] = upgrade['to']
        print(f"  + {line_id}: {int(old_capacity)} -> {upgrade['to']} MVA ({upgrade['reason']})")
        upgraded_count += 1
    else:
        print(f"  ! Warning: {line_id} not found in network")

lines.to_csv(lines_file, index=False)

total_capacity_added = sum(u['to'] - u['from'] for u in UPGRADES.values())

print(f"\n" + "="*80)
print("TRANSMISSION UPGRADES COMPLETE")
print("="*80)
print(f"\nUpgraded {upgraded_count} lines")
print(f"Total capacity added: {total_capacity_added} MVA")
print(f"\nNetwork saved to: {target_dir}")
print(f"\nNext: Validate upgraded 2040 network")
print("="*80)