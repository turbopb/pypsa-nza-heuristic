"""
Validate 2035 upgraded network with capacity additions.
"""

import subprocess
from pathlib import Path
import pandas as pd
import shutil

BASE = Path(__file__).parent.parent
VALIDATION_DIR = BASE.parent / 'pypsa-nza-dispatch'
RESULTS_PATH = BASE / 'results' / 'validation'
NETWORK_2035_UPGRADED = BASE / 'data' / 'networks' / '2035' / 'upgraded'
TARGET = Path(r"C:\Users\Public\Documents\Thesis\analysis\dispatch_data\cases\reference\2035\jul_2035")

print("="*80)
print("VALIDATING 2035 UPGRADED NETWORK")
print("="*80)

print("\nStep 1: Copy upgraded network to validation location...")
if TARGET.exists():
    shutil.rmtree(TARGET)
shutil.copytree(NETWORK_2035_UPGRADED, TARGET)
print(f"  OK - Copied from: {NETWORK_2035_UPGRADED}")

print("\nStep 2: Run validation...")

import os
os.chdir(VALIDATION_DIR)

cmd = [
    'nza-dispatch-validate',
    '--config', 'config/dispatch_config.yaml',
    '--year', '2035',
    '--month', 'jul',
    '--output-dir', str(RESULTS_PATH)
]

print("  Running (this may take 30-60 seconds)...")

result = subprocess.run(cmd, capture_output=True, text=True)

print("\n" + "="*80)
print("VALIDATION OUTPUT:")
print("="*80)
print(result.stdout)

if result.stderr:
    print("\nERRORS/WARNINGS:")
    print(result.stderr[:2000])  # First 2000 chars

if result.returncode == 0:
    result_file = RESULTS_PATH / 'stress_test_reference_2035_jul.csv'
    if result_file.exists():
        df = pd.read_csv(result_file)
        
        print("\n" + "="*80)
        print("2035 UPGRADED VALIDATION RESULTS")
        print("="*80)
        print(f"\nLoad shedding: {df['load_shed_fraction'].iloc[0] * 100:.3f}%")
        print(f"Energy shed: {df['load_shed_MWh'].iloc[0]/1000:.1f} GWh")
        print(f"Total demand: {df['total_demand_MWh'].iloc[0]/1000:.0f} GWh")
        
        if df['load_shed_fraction'].iloc[0] < 0.001:
            print(f"\nStatus: ADEQUATE")
        else:
            print(f"\nStatus: INADEQUATE")
            
        print("="*80)
else:
    print(f"\nValidation FAILED with return code: {result.returncode}")

os.chdir(BASE)