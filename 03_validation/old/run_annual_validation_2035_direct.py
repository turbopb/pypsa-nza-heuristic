"""
Direct PyPSA validation for 2035 (no stress test scaling).
"""

import pypsa
import pandas as pd
from pathlib import Path

BASE = Path(__file__).parent.parent
NETWORK_DIR = BASE / 'data' / 'networks' / '2035' / 'upgraded_tx'
RESULTS_DIR = BASE / 'results' / 'validation'

print("="*80)
print("2035 DIRECT ANNUAL VALIDATION (NO STRESS TEST)")
print("="*80)

print(f"\nLoading 2035 network from: {NETWORK_DIR}")
network = pypsa.Network(str(NETWORK_DIR))

print(f"  Generators: {len(network.generators)}")
print(f"  Snapshots: {len(network.snapshots)}")

# Add load shedding generators
print("\nAdding load shedding generators...")
for bus in network.buses.index:
    network.add("Generator",
                f"load_shedding_{bus}",
                bus=bus,
                p_nom=10000,
                marginal_cost=10000,
                carrier="load_shedding")

print("\nRunning optimization...")
network.optimize(solver_name='highs')

# Calculate monthly results
load_shed_gens = [g for g in network.generators.index if 'load_shedding' in g]
monthly_results = []

for month_num in range(1, 13):
    # Get hours for this month (approximate)
    month_hours = network.snapshots[network.snapshots.month == month_num]
    
    if len(month_hours) > 0:
        month_shed = network.generators_t.p.loc[month_hours, load_shed_gens].sum().sum()
        month_demand = network.loads_t.p_set.loc[month_hours].sum().sum()
        shed_fraction = month_shed / month_demand if month_demand > 0 else 0
        
        month_names = ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']
        
        monthly_results.append({
            'month': month_names[month_num-1],
            'load_shed_pct': shed_fraction * 100,
            'energy_shed_GWh': month_shed / 1000,
            'status': 'ADEQUATE' if shed_fraction < 0.001 else 'INADEQUATE'
        })
        
        print(f"  {month_names[month_num-1].upper()}: {shed_fraction*100:.3f}%")

# Save results
summary_df = pd.DataFrame(monthly_results)
summary_file = RESULTS_DIR / 'annual_summary_2035_direct.csv'
summary_df.to_csv(summary_file, index=False)

print("\n" + "="*80)
print("2035 DIRECT VALIDATION SUMMARY")
print("="*80)
adequate = (summary_df['load_shed_pct'] < 0.1).sum()
print(f"\nAdequate months: {adequate}/12")
print(f"\nResults saved to: {summary_file}")
print("="*80)