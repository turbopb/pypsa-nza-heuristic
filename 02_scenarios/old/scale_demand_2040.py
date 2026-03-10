"""
Create 2040 baseline network with validation checks.
"""

import pandas as pd
from pathlib import Path
import shutil

# MBIE demand growth factor for 2040 (from 2024 base)
GROWTH_FACTOR_2040 = 1.37818853974122

print("="*80)
print("CREATING 2040 BASELINE NETWORK WITH VALIDATION")
print("="*80)

# Paths
source_2035_upgraded = Path(r"C:\Users\Public\Documents\Thesis\analysis\pypsa-nza-heuristic\data\networks\2035\upgraded_tx")
source_2024_baseline = Path(r"C:\Users\Public\Documents\Thesis\analysis\pypsa-nza-heuristic\data\networks\2024\baseline")
target_2040_baseline = Path(r"C:\Users\Public\Documents\Thesis\analysis\pypsa-nza-heuristic\data\networks\2040\baseline")

# Validation Step 1: Verify source directories exist
print("\nValidation Step 1: Checking source directories...")
assert source_2035_upgraded.exists(), f"ERROR: 2035 upgraded network not found at {source_2035_upgraded}"
assert source_2024_baseline.exists(), f"ERROR: 2024 baseline not found at {source_2024_baseline}"
print("  OK - Source directories exist")

# Copy 2035 upgraded network structure
print("\nStep 2: Copy 2035 upgraded network structure...")
target_2040_baseline.parent.mkdir(parents=True, exist_ok=True)
if target_2040_baseline.exists():
    shutil.rmtree(target_2040_baseline)
shutil.copytree(source_2035_upgraded, target_2040_baseline)
print(f"  OK - Copied generation capacity from 2035 upgraded")

# Validation Step 2: Verify generators were copied
gens_2040 = pd.read_csv(target_2040_baseline / "generators.csv")
print(f"\nValidation Step 2: Checking generator count...")
print(f"  Generators in 2040 baseline: {len(gens_2040)}")
assert len(gens_2040) >= 95, f"ERROR: Expected >= 95 generators, got {len(gens_2040)}"
print("  OK - Generator count verified")

# Load 2024 BASELINE demand
print("\nStep 3: Load 2024 baseline demand...")
loads_2024_file = source_2024_baseline / "loads-p_set.csv"
loads_2024 = pd.read_csv(loads_2024_file, index_col=0)

peak_2024 = loads_2024.sum(axis=1).max()
energy_2024 = loads_2024.sum().sum() / 1000

print(f"  2024 baseline demand:")
print(f"    Peak: {peak_2024:.0f} MW")
print(f"    Total energy: {energy_2024:.0f} GWh")

# Validation Step 3: Verify 2024 baseline values
print(f"\nValidation Step 3: Checking 2024 baseline values...")
assert 6800 < peak_2024 < 6950, f"ERROR: 2024 peak {peak_2024:.0f} MW outside expected range (6800-6950 MW)"
assert 7600 < energy_2024 < 7800, f"ERROR: 2024 energy {energy_2024:.0f} GWh outside expected range (7600-7800 GWh)"
print("  OK - 2024 baseline values verified")

# Scale to 2040
print(f"\nStep 4: Scale to 2040 demand (factor: {GROWTH_FACTOR_2040:.4f})...")
loads_2040 = loads_2024 * GROWTH_FACTOR_2040

peak_2040 = loads_2040.sum(axis=1).max()
energy_2040 = loads_2040.sum().sum() / 1000
increase_mw = peak_2040 - peak_2024

print(f"  2040 projected demand:")
print(f"    Peak: {peak_2040:.0f} MW")
print(f"    Total energy: {energy_2040:.0f} GWh")
print(f"    Increase from 2024: {increase_mw:.0f} MW (+{(GROWTH_FACTOR_2040-1)*100:.1f}%)")

# Validation Step 4: Verify scaling calculation
print(f"\nValidation Step 4: Verifying scaling calculation...")
expected_peak = peak_2024 * GROWTH_FACTOR_2040
assert abs(peak_2040 - expected_peak) < 1, f"ERROR: Scaling error - expected {expected_peak:.0f}, got {peak_2040:.0f}"
print(f"  OK - Scaling verified (expected {expected_peak:.0f}, got {peak_2040:.0f})")

# Save scaled loads
loads_2040_file = target_2040_baseline / "loads-p_set.csv"
loads_2040.to_csv(loads_2040_file)
print(f"\n  OK - Saved 2040 demand")

# Final validation summary
print("\n" + "="*80)
print("2040 BASELINE NETWORK CREATED - ALL CHECKS PASSED")
print("="*80)
print(f"\nThis network has:")
print(f"  - 2040 projected demand: {peak_2040:.0f} MW peak")
print(f"  - 2035 upgraded generation: {len(gens_2040)} generators")
print(f"  - 2035 transmission upgrades included")
print(f"\nDemand trajectory:")
print(f"  2024: {peak_2024:.0f} MW")
print(f"  2030: 7827 MW (+950 MW)")
print(f"  2035: 8560 MW (+733 MW)")
print(f"  2040: {peak_2040:.0f} MW (+{peak_2040-8560:.0f} MW)")
print(f"\nNext: Run validation to check if 2035 capacity is adequate for 2040 demand")
print("="*80)