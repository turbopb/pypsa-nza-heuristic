"""
Run annual validation for 2040 upgraded network (all 12 months).
"""

import subprocess
import pandas as pd
from pathlib import Path
import shutil

BASE = Path(__file__).parent.parent
VALIDATION_DIR = BASE.parent / 'pypsa-nza-dispatch'
NETWORK_2040 = BASE / 'data' / 'networks' / '2040' / 'upgraded'
RESULTS_DIR = BASE / 'results' / 'validation'
DISPATCH_BASE = Path(r"C:\Users\Public\Documents\Thesis\analysis\dispatch_data\cases\reference\2040")

MONTHS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

print("="*80)
print("2040 ANNUAL VALIDATION (12 MONTHS)")
print("="*80)

RESULTS_DIR.mkdir(parents=True, exist_ok=True)

results = []

for month in MONTHS:
    print(f"\nValidating {month.upper()} 2040...")
    
    target = DISPATCH_BASE / f"{month}_2040"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(NETWORK_2040, target)
    
    import os
    os.chdir(VALIDATION_DIR)
    
    cmd = [
        'nza-dispatch-validate',
        '--config', 'config/dispatch_config.yaml',
        '--year', '2040',
        '--month', month,
        '--output-dir', str(RESULTS_DIR)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    result_file = RESULTS_DIR / f'stress_test_reference_2040_{month}.csv'
    if result_file.exists():
        df = pd.read_csv(result_file)
        shed_pct = df['load_shed_fraction'].iloc[0] * 100
        shed_gwh = df['load_shed_MWh'].iloc[0] / 1000
        status = 'ADEQUATE' if shed_pct < 0.1 else 'INADEQUATE'
        
        results.append({
            'month': month,
            'load_shed_pct': shed_pct,
            'energy_shed_GWh': shed_gwh,
            'status': status
        })
        
        print(f"  {status}: {shed_pct:.3f}% ({shed_gwh:.1f} GWh)")
    else:
        print(f"  ERROR: Result file not found")
        results.append({
            'month': month,
            'load_shed_pct': None,
            'energy_shed_GWh': None,
            'status': 'ERROR'
        })
    
    os.chdir(BASE)

summary_df = pd.DataFrame(results)
summary_file = RESULTS_DIR / 'annual_summary_2040.csv'
summary_df.to_csv(summary_file, index=False)

print("\n" + "="*80)
print("2040 ANNUAL SUMMARY")
print("="*80)
adequate = (summary_df['load_shed_pct'] < 0.1).sum()
print(f"\nAdequate months: {adequate}/12")
print(f"Inadequate months: {12-adequate}/12")
print(f"\nResults saved to: {summary_file}")
print("="*80)