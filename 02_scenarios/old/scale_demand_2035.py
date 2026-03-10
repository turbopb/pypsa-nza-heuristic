"""
Create 2035 baseline network.
Demand: 2024 baseline scaled by 1.2447 (MBIE reference scenario)
Generation: 2030 upgraded capacity
"""

import pandas as pd
from pathlib import Path
import shutil

GROWTH_FACTOR_2035 = 1.2446826863832408

print("="*80)
print("CREATING 2035 BASELINE NETWORK")
print("="*80)

source_2030_upgraded = Path(r"C:\Users\Public\Documents\Thesis\analysis\pypsa-nza-heuristic\data\networks\2030\upgraded")
source_2024_baseline = Path(r"C:\Users\Public\Documents\Thesis\analysis\pypsa-nza-heuristic\data\networks\2024\baseline")
target_2035_baseline = Path(r"C:\Users\Public\Documents\Thesis\analysis\pypsa-nza-heuristic\data\networks\2035\baseline")

print("\nStep 1: Copy 2030 upgraded network structure...")
target_2035_baseline.parent.mkdir(parents=True, exist_ok=True)
if target_2035_baseline.exists():
    shutil.rmtree(target_2035_baseline)
shutil.copytree(source_2030_upgraded, target_2035_baseline)
print("  OK - Copied generation capacity from 2030 upgraded")

print("\nStep 2: Load 2024 baseline demand...")
loads_2024_file = source_2024_baseline / "loads-p_set.csv"
loads_2024 = pd.read_csv(loads_2024_file, index_col=0)

# FIXED: System peak = sum across all buses at each timestep, then max
peak_2024 = loads_2024.sum(axis=1).max()
energy_2024 = loads_2024.sum().sum() / 1000

print(f"  2024 baseline demand:")
print(f"    Peak: {peak_2024:.0f} MW")
print(f"    Total energy: {energy_2024:.0f} GWh")

print(f"\nStep 3: Scale to 2035 demand (factor: {GROWTH_FACTOR_2035:.4f})...")
loads_2035 = loads_2024 * GROWTH_FACTOR_2035

# FIXED: System peak calculation
peak_2035 = loads_2035.sum(axis=1).max()
energy_2035 = loads_2035.sum().sum() / 1000
increase_mw = peak_2035 - peak_2024

print(f"  2035 projected demand:")
print(f"    Peak: {peak_2035:.0f} MW")
print(f"    Total energy: {energy_2035:.0f} GWh")
print(f"    Increase from 2024: {increase_mw:.0f} MW (+{(GROWTH_FACTOR_2035-1)*100:.1f}%)")

loads_2035_file = target_2035_baseline / "loads-p_set.csv"
loads_2035.to_csv(loads_2035_file)
print(f"\n  OK - Saved 2035 demand")

# Calculate 2030 peak for comparison
peak_2030 = 7827  # We know this from previous work

print("\n" + "="*80)
print("2035 BASELINE NETWORK CREATED")
print("="*80)
print(f"\nThis network has:")
print(f"  - 2035 projected demand: {peak_2035:.0f} MW peak")
print(f"  - 2030 upgraded generation: 10,428 MW installed")
print(f"  - No additional capacity for 2030 to 2035 growth")
print(f"\nDemand trajectory:")
print(f"  2024: {peak_2024:.0f} MW")
print(f"  2030: {peak_2030:.0f} MW (+{peak_2030-peak_2024:.0f} MW)")
print(f"  2035: {peak_2035:.0f} MW (+{peak_2035-peak_2030:.0f} MW from 2030)")
print(f"\nNext: Run validation to check if 2030 capacity is adequate for 2035 demand")
print("="*80)