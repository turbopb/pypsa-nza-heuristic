"""
Run dispatch validation for all 12 months in PARALLEL.
Much faster on multi-core systems.
"""

import subprocess
import pandas as pd
from pathlib import Path
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
import os

BASE = Path(__file__).parent.parent
VALIDATION_DIR = BASE.parent / 'pypsa-nza-dispatch'
CONFIG_FILE = VALIDATION_DIR / 'config' / 'dispatch_config.yaml'
RESULTS_PATH = BASE / 'results' / 'validation'

def validate_month(month):
    """Validate a single month (runs in separate process)."""
    original_dir = os.getcwd()
    os.chdir(VALIDATION_DIR)
    
    cmd = [
        'nza-dispatch-validate',
        '--config', str(CONFIG_FILE),
        '--year', '2024',
        '--month', month,
        '--output-dir', str(RESULTS_PATH)
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        os.chdir(original_dir)
        
        # Load results
        result_file = RESULTS_PATH / f'stress_test_reference_2024_{month}.csv'
        if result_file.exists():
            df = pd.read_csv(result_file)
            return {
                'month': month,
                'load_shed_pct': df['load_shed_fraction'].iloc[0] * 100,
                'load_shed_MWh': df['load_shed_MWh'].iloc[0],
                'total_demand_MWh': df['total_demand_MWh'].iloc[0],
                'status': 'ADEQUATE' if df['load_shed_fraction'].iloc[0] < 0.001 else 'INADEQUATE'
            }
        else:
            return {'month': month, 'status': 'FAILED'}
            
    except Exception as e:
        os.chdir(original_dir)
        return {'month': month, 'status': 'FAILED', 'error': str(e)}


def main():
    """Main function - required for Windows multiprocessing."""
    print("="*80)
    print("PARALLEL ANNUAL VALIDATION: 2024 BASELINE")
    print("="*80)
    
    RESULTS_PATH.mkdir(parents=True, exist_ok=True)
    
    months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
              'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    
    # Run in parallel (use 12 workers for 12 months)
    print(f"\nRunning 12 months in parallel on {os.cpu_count()} cores...")
    print("-"*80)
    
    results = []
    with ProcessPoolExecutor(max_workers=12) as executor:
        # Submit all months
        future_to_month = {executor.submit(validate_month, month): month for month in months}
        
        # Collect results as they complete
        for future in as_completed(future_to_month):
            month = future_to_month[future]
            try:
                result = future.result()
                results.append(result)
                status = result.get('status', 'UNKNOWN')
                print(f"  ? {month.upper()}: {status}")
            except Exception as e:
                print(f"  ? {month.upper()} failed: {e}")
                results.append({'month': month, 'status': 'FAILED'})
    
    # Sort by month order
    month_order = {m: i for i, m in enumerate(months)}
    results.sort(key=lambda x: month_order[x['month']])
    
    # Create summary
    print("\n" + "="*80)
    print("ANNUAL VALIDATION SUMMARY")
    print("="*80)
    
    summary_df = pd.DataFrame(results)
    
    print(f"\n{'Month':<10}{'Load Shed %':<15}{'Energy Shed (GWh)':<20}{'Status':<12}")
    print("-"*60)
    
    for _, row in summary_df.iterrows():
        if row.get('load_shed_pct') is not None:
            print(f"{row['month'].upper():<10}{row['load_shed_pct']:<15.3f}"
                  f"{row['load_shed_MWh']/1000:<20.1f}{row['status']:<12}")
        else:
            print(f"{row['month'].upper():<10}{'N/A':<15}{'N/A':<20}{row['status']:<12}")
    
    # Save
    summary_file = RESULTS_PATH / 'annual_summary_2024.csv'
    summary_df.to_csv(summary_file, index=False)
    print(f"\n? Summary saved: {summary_file.relative_to(BASE)}")
    
    adequate_months = (summary_df['status'] == 'ADEQUATE').sum()
    print(f"\nOverall: {adequate_months}/12 months ADEQUATE")
    print("="*80)


if __name__ == '__main__':
    main()