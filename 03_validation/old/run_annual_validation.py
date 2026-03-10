"""
Run dispatch validation for all 12 months of 2024.
Proves model accuracy across full year, not just spot checks.
"""

import subprocess
import pandas as pd
from pathlib import Path
import sys

# Paths
BASE = Path(__file__).parent.parent
VALIDATION_DIR = BASE.parent / 'pypsa-nza-dispatch'
CONFIG_FILE = VALIDATION_DIR / 'config' / 'dispatch_config.yaml'
RESULTS_PATH = BASE / 'results' / 'validation'

# Check paths exist
if not VALIDATION_DIR.exists():
    print(f"ERROR: pypsa-nza-dispatch not found at {VALIDATION_DIR}")
    sys.exit(1)

if not CONFIG_FILE.exists():
    print(f"ERROR: Config file not found at {CONFIG_FILE}")
    sys.exit(1)

print("="*80)
print("ANNUAL VALIDATION: 2024 BASELINE")
print("="*80)
print(f"Config: {CONFIG_FILE}")
print(f"Output: {RESULTS_PATH}")

# Create output directory
RESULTS_PATH.mkdir(parents=True, exist_ok=True)

# Month names
months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
          'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

# Results storage
results = []

# Change to validation directory to run commands
import os
original_dir = os.getcwd()
os.chdir(VALIDATION_DIR)

for month in months:
    print(f"\nValidating {month.upper()} 2024...")
    print("-"*60)
    
    # Run validation
    cmd = [
        'nza-dispatch-validate',
        '--config', str(CONFIG_FILE),
        '--year', '2024',
        '--month', month,
        '--output-dir', str(RESULTS_PATH)
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"  ? {month.upper()} complete")
        
        # Load results
        result_file = RESULTS_PATH / f'stress_test_reference_2024_{month}.csv'
        if result_file.exists():
            df = pd.read_csv(result_file)
            results.append({
                'month': month,
                'load_shed_pct': df['load_shed_fraction'].iloc[0] * 100,
                'load_shed_MWh': df['load_shed_MWh'].iloc[0],
                'total_demand_MWh': df['total_demand_MWh'].iloc[0],
                'status': 'ADEQUATE' if df['load_shed_fraction'].iloc[0] < 0.001 else 'INADEQUATE'
            })
        
    except subprocess.CalledProcessError as e:
        print(f"  ? {month.upper()} failed")
        print(f"     Error: {e.stderr if e.stderr else 'Unknown error'}")
        results.append({
            'month': month,
            'load_shed_pct': None,
            'load_shed_MWh': None,
            'total_demand_MWh': None,
            'status': 'FAILED'
        })

# Return to original directory
os.chdir(original_dir)

# Create summary
print("\n" + "="*80)
print("ANNUAL VALIDATION SUMMARY")
print("="*80)

summary_df = pd.DataFrame(results)

print(f"\n{'Month':<10}{'Load Shed %':<15}{'Energy Shed (GWh)':<20}{'Status':<12}")
print("-"*60)

for _, row in summary_df.iterrows():
    if row['load_shed_pct'] is not None:
        print(f"{row['month'].upper():<10}{row['load_shed_pct']:<15.3f}"
              f"{row['load_shed_MWh']/1000:<20.1f}{row['status']:<12}")
    else:
        print(f"{row['month'].upper():<10}{'FAILED':<15}{'FAILED':<20}{'FAILED':<12}")

# Save summary
summary_file = RESULTS_PATH / 'annual_summary_2024.csv'
summary_df.to_csv(summary_file, index=False)
print(f"\n? Summary saved: {summary_file.relative_to(BASE)}")

# Overall assessment
adequate_months = (summary_df['status'] == 'ADEQUATE').sum()
failed_months = (summary_df['status'] == 'FAILED').sum()

print(f"\nResults: {adequate_months} ADEQUATE, "
      f"{len(summary_df) - adequate_months - failed_months} INADEQUATE, "
      f"{failed_months} FAILED")

if adequate_months == 12:
    print("? 2024 baseline is ADEQUATE year-round")
elif failed_months == 0:
    print(f"? {12 - adequate_months} months show inadequacy")
else:
    print(f"? {failed_months} months failed validation")

print("="*80)