"""
Validate 2040 upgraded network - final check.
"""

import pypsa
import pandas as pd
from pathlib import Path

BASE = Path(__file__).parent.parent
NETWORK_DIR = BASE / 'data' / 'networks' / '2040' / 'upgraded'
RESULTS_DIR = BASE / 'results' / 'validation'
ANALYSIS_DIR = BASE / 'results' / 'analysis'

print("="*80)
print("VALIDATING 2040 FINAL NETWORK (WITH TRANSMISSION UPGRADES)")
print("="*80)

print(f"\nLoading network from: {NETWORK_DIR}")
network = pypsa.Network(str(NETWORK_DIR))

print(f"  Buses: {len(network.buses)}")
print(f"  Lines: {len(network.lines)}")
print(f"  Generators: {len(network.generators)}")

print("\nAdding load shedding generators...")
for bus in network.buses.index:
    network.add("Generator",
                f"load_shedding_{bus}",
                bus=bus,
                p_nom=10000,
                marginal_cost=10000,
                carrier="load_shedding")

print(f"  Total generators: {len(network.generators)}")

print("\nRunning optimization...")
network.optimize(solver_name='highs')

# Calculate adequacy
load_shed_gens = [g for g in network.generators.index if 'load_shedding' in g]
total_shed_mwh = network.generators_t.p[load_shed_gens].sum().sum()
total_demand_mwh = network.loads_t.p_set.sum().sum()
shed_fraction = total_shed_mwh / total_demand_mwh

print("\n" + "="*80)
print("ADEQUACY RESULTS")
print("="*80)
print(f"\nLoad shedding: {shed_fraction * 100:.4f}%")
print(f"Energy shed: {total_shed_mwh/1000:.2f} GWh")
print(f"Total demand: {total_demand_mwh/1000:.0f} GWh")

if shed_fraction < 0.001:
    print(f"\nStatus: ADEQUATE - Target achieved!")
else:
    print(f"\nStatus: INADEQUATE ({shed_fraction*100:.3f}%)")

# Transmission analysis
print("\n" + "="*80)
print("TRANSMISSION ANALYSIS")
print("="*80)

line_loading = []
for line_id in network.lines.index:
    s_nom = network.lines.loc[line_id, 's_nom']
    p0 = network.lines_t.p0[line_id].abs()
    max_flow = p0.max()
    loading_pct = (max_flow / s_nom) * 100 if s_nom > 0 else 0
    
    line_loading.append({
        'line_id': line_id,
        'bus0': network.lines.loc[line_id, 'bus0'],
        'bus1': network.lines.loc[line_id, 'bus1'],
        's_nom_MVA': s_nom,
        'max_flow_MW': max_flow,
        'loading_pct': loading_pct,
    })

df = pd.DataFrame(line_loading)
df = df.sort_values('loading_pct', ascending=False)

overloaded = (df['loading_pct'] >= 100).sum()
critical = ((df['loading_pct'] >= 95) & (df['loading_pct'] < 100)).sum()

print(f"\nLines at 100% loading: {overloaded}")
print(f"Lines at 95-100% loading: {critical}")
print(f"Mean loading: {df['loading_pct'].mean():.1f}%")
print(f"Max loading: {df['loading_pct'].max():.1f}%")

if overloaded > 0:
    print(f"\nRemaining overloaded lines:")
    print(df[df['loading_pct'] >= 100][['line_id', 'bus0', 'bus1', 's_nom_MVA', 'loading_pct']].head(10).to_string(index=False))
else:
    print(f"\nNo overloaded lines - transmission adequate!")

print(f"\nTop 5 loaded lines:")
print(df[['line_id', 'bus0', 'bus1', 's_nom_MVA', 'loading_pct']].head(5).to_string(index=False))

# Save results
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

results_df = pd.DataFrame([{
    'scenario': '2040_upgraded',
    'load_shed_fraction': shed_fraction,
    'load_shed_GWh': total_shed_mwh/1000,
    'total_demand_GWh': total_demand_mwh/1000,
    'overloaded_lines': overloaded,
    'critical_lines': critical,
    'mean_loading_pct': df['loading_pct'].mean(),
    'max_loading_pct': df['loading_pct'].max(),
}])

results_df.to_csv(RESULTS_DIR / 'validation_2040_final.csv', index=False)
df.to_csv(ANALYSIS_DIR / 'line_loading_2040_final.csv', index=False)

print(f"\n" + "="*80)
print("FINAL STATUS")
print("="*80)

if shed_fraction < 0.001 and overloaded == 0:
    print("SUCCESS - 2040 NETWORK FULLY ADEQUATE")
    print("  - Zero load shedding")
    print("  - No transmission bottlenecks")
elif shed_fraction < 0.001 and overloaded > 0:
    print("PARTIAL SUCCESS - Adequate but transmission constrained")
else:
    print("INADEQUATE - Further work needed")

print(f"\nResults saved to:")
print(f"  {RESULTS_DIR / 'validation_2040_final.csv'}")
print(f"  {ANALYSIS_DIR / 'line_loading_2040_final.csv'}")
print("="*80)