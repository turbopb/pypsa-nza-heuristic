"""
Validate 2035 at BASE demand (no stress test scaling).
"""

import pypsa
import pandas as pd
from pathlib import Path

NETWORK_DIR = Path(r"C:\Users\Public\Documents\Thesis\analysis\pypsa-nza-heuristic\data\networks\2035\upgraded_tx")

print("="*80)
print("VALIDATING 2035 AT BASE DEMAND (NO SCALING)")
print("="*80)

print(f"\nLoading network...")
network = pypsa.Network(str(NETWORK_DIR))

print(f"  Buses: {len(network.buses)}")
print(f"  Lines: {len(network.lines)}")
print(f"  Generators: {len(network.generators)}")

# Add load shedding
print("\nAdding load shedding generators...")
for bus in network.buses.index:
    network.add("Generator",
                f"load_shedding_{bus}",
                bus=bus,
                p_nom=10000,
                marginal_cost=10000,
                carrier="load_shedding")

print(f"\nRunning optimization at BASE 2035 demand...")
network.optimize(solver_name='highs')

# Calculate load shedding
load_shed_gens = [g for g in network.generators.index if 'load_shedding' in g]
total_shed_mwh = network.generators_t.p[load_shed_gens].sum().sum()
total_demand_mwh = network.loads_t.p_set.sum().sum()
shed_fraction = total_shed_mwh / total_demand_mwh

print(f"\n" + "="*80)
print("RESULTS AT BASE 2035 DEMAND")
print("="*80)
print(f"\nLoad shedding: {shed_fraction * 100:.3f}%")
print(f"Energy shed: {total_shed_mwh/1000:.1f} GWh")
print(f"Total demand: {total_demand_mwh/1000:.0f} GWh")

if shed_fraction < 0.001:
    print(f"\nStatus: ADEQUATE for base 2035 demand!")
else:
    print(f"\nStatus: INADEQUATE even at base demand")
    
print("="*80)