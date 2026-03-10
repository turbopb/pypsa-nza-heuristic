"""
Quick validation of 2035 baseline network.
Uses July (winter peak) as representative month.
"""

import subprocess
from pathlib import Path
import pandas as pd
import yaml

BASE = Path(__file__).parent.parent
VALIDATION_DIR = BASE.parent / 'pypsa-nza-dispatch'
CONFIG_FILE = VALIDATION_DIR / 'config' / 'dispatch_config.yaml'
RESULTS_PATH = BASE / 'results' / 'validation'
NETWORK_2035 = BASE / 'data' / 'networks' / '2035' / 'baseline'

print("="*80)
print("VALIDATING 2035 BASELINE NETWORK")
print("="*80)

print("\nUpdating config with 2035 network path...")
with open(CONFIG_FILE, 'r') as f:
    config = yaml.safe_load(f)

if 'networks' not in config:
    config['networks'] = {}
if 'reference' not in config['networks']:
    config['networks']['reference'] = {}

config['networks']['reference']['2035'] = str(NETWORK_2035)

temp_config = VALIDATION_DIR / 'config' / 'dispatch_config_2035.yaml'
with open(temp_config, 'w') as f:
    yaml.dump(config, f)

print(f"  OK - Using network: {NETWORK_2035}")

RESULTS_PATH.mkdir(parents=True, exist_ok=True)

import os
os.chdir(VALIDATION_DIR)

cmd = [
    'nza-dispatch-validate',
    '--config', str(temp_config),
    '--year', '2035',
    '--month', 'jul',
    '--output-dir', str(RESULTS_PATH)
]

print("\nRunning validation (July 2035)...")
print("This may take 30-60 seconds...")

# Run without check=True to see the error
result = subprocess.run(cmd, capture_output=True, text=True)

print("\nSTDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print(f"\nReturn code: {result.returncode}")

if result.returncode == 0:
    result_file = RESULTS_PATH / 'stress_test_reference_2035_jul.csv'
    if result_file.exists():
        df = pd.read_csv(result_file)
        
        print("\n" + "="*80)
        print("2035 BASELINE VALIDATION RESULTS")
        print("="*80)
        print(f"\nLoad shedding: {df['load_shed_fraction'].iloc[0] * 100:.2f}%")
        print(f"Energy shed: {df['load_shed_MWh'].iloc[0]/1000:.1f} GWh")
        print(f"Total demand: {df['total_demand_MWh'].iloc[0]/1000:.0f} GWh")
        
        if df['load_shed_fraction'].iloc[0] < 0.001:
            print(f"Status: ADEQUATE")
        else:
            print(f"Status: INADEQUATE")
            
        print("="*80)

os.chdir(BASE)

if temp_config.exists():
    temp_config.unlink()