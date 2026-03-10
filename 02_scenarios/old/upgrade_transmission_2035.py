"""
Upgrade overloaded transmission lines for 2035 network.
"""

import pandas as pd
from pathlib import Path
import shutil

# Lines to upgrade (identified from transmission analysis)
UPGRADES = {
    'N-L47': {'from': 1000, 'to': 1500, 'reason': 'PAK-PEN Auckland corridor'},
    'N-L22': {'from': 1000, 'to': 1500, 'reason': 'THI-WKM North Island backbone'},
    'N-L82': {'from': 600, 'to': 1000, 'reason': 'HWA-SFD Huntly-Stratford'},
}

print("="*80)
print("UPGRADING 2035 TRANSMISSION LINES")
print("="*80)

source_dir = Path(r"C:\Users\Public\Documents\Thesis\analysis\pypsa-nza-heuristic\data\networks\2035\upgraded")
target_dir = Path(r"C:\Users\Public\Documents\Thesis\analysis\pypsa-nza-heuristic\data\networks\2035\upgraded_tx")

print(f"\nCopying network...")
if target_dir.exists():
    shutil.rmtree(target_dir)
shutil.copytree(source_dir, target_dir)
print(f"  OK - Copied to: {target_dir}")

lines_file = target_dir / "lines.csv"
lines = pd.read_csv(lines_file)

print(f"\nUpgrading transmission lines:")
for line_id, upgrade in UPGRADES.items():
    if line_id in lines['name'].values:
        old_capacity = lines.loc[lines['name'] == line_id, 's_nom'].values[0]
        lines.loc[lines['name'] == line_id, 's_nom'] = upgrade['to']
        print(f"  + {line_id}: {upgrade['from']} -> {upgrade['to']} MVA ({upgrade['reason']})")
    else:
        print(f"  ! Warning: {line_id} not found")

lines.to_csv(lines_file, index=False)

print(f"\n" + "="*80)
print("TRANSMISSION UPGRADES COMPLETE")
print("="*80)
print(f"\nUpgraded {len(UPGRADES)} lines")
print(f"Total capacity added: {sum(u['to'] - u['from'] for u in UPGRADES.values())} MVA")
print(f"\nNetwork saved to: {target_dir}")
print("="*80)