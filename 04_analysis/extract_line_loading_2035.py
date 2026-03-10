"""
Extract transmission line loading for 2035 upgraded network.
"""

import pypsa
import pandas as pd
from pathlib import Path

BASE = Path(__file__).parent.parent
NETWORK_DIR = BASE / 'data' / 'networks' / '2035' / 'upgraded'
OUTPUT_FILE = BASE / 'results' / 'analysis' / 'line_loading_2035_upgraded.csv'

print("="*80)
print("EXTRACTING 2035 UPGRADED TRANSMISSION LINE LOADING")
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
status = network.optimize(solver_name='highs')

print(f"  Optimization complete")
print(f"  Objective: {network.objective:,.0f}")

# Check load shedding
load_shed_gens = [g for g in network.generators.index if 'load_shedding' in g]
total_shed = network.generators_t.p[load_shed_gens].sum().sum()
print(f"  Load shed: {total_shed/1000:.1f} GWh")

print("\nExtracting line loading...")
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
        'length_km': network.lines.loc[line_id, 'length']
    })

df = pd.DataFrame(line_loading)
df = df.sort_values('loading_pct', ascending=False)

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUTPUT_FILE, index=False)

overloaded = (df['loading_pct'] >= 100).sum()
critical = ((df['loading_pct'] >= 95) & (df['loading_pct'] < 100)).sum()

print(f"\nTransmission analysis:")
print(f"  Lines at 100% loading: {overloaded}")
print(f"  Lines at 95-100% loading: {critical}")
print(f"  Mean loading: {df['loading_pct'].mean():.1f}%")
print(f"  Max loading: {df['loading_pct'].max():.1f}%")

if overloaded > 0:
    print(f"\n  DIAGNOSIS: TRANSMISSION BOTTLENECK")
    print(f"  {overloaded} lines are overloaded - need transmission upgrades")
else:
    print(f"\n  DIAGNOSIS: GENERATION BOTTLENECK")
    print(f"  No transmission overload - need more generation capacity")

print(f"\nTop 10 loaded lines:")
print(df[['line_id', 'bus0', 'bus1', 's_nom_MVA', 'loading_pct']].head(10).to_string(index=False))

print(f"\nSaved to: {OUTPUT_FILE.relative_to(BASE)}")
print("="*80)