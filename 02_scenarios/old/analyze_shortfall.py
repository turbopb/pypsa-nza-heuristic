"""
Analyze 2030 shortfall to determine heuristic additions.
"""

import pypsa
import pandas as pd

# Load 2030 baseline network
n = pypsa.Network()
n.import_from_csv_folder(r"C:\Users\Public\Documents\Thesis\analysis\dispatch_data\cases\reference\2030\baseline_2030")

# Add load shedding to run optimization
for bus in n.buses.index:
    n.add("Generator",
          name=f"load_shed_{bus}",
          bus=bus,
          p_nom=10000,
          marginal_cost=10000,
          carrier="load_shedding")

# Optimize
print("Running optimization to identify shortfall...")
n.optimize(solver_name='highs', solver_options={'log_to_console': False})

# Analyze results
print("\n" + "="*60)
print("2030 SHORTFALL ANALYSIS")
print("="*60)

# Load shedding
load_shed_gens = [g for g in n.generators.index if g.startswith('load_shed_')]
total_shed = n.generators_t.p[load_shed_gens].sum().sum()
peak_shed = n.generators_t.p[load_shed_gens].sum(axis=1).max()

print(f"\nTotal load shed: {total_shed:.0f} MWh")
print(f"Peak load shed: {peak_shed:.0f} MW")

# Peak demand
peak_demand = n.loads_t.p_set.sum(axis=1).max()
avg_demand = n.loads_t.p_set.sum(axis=1).mean()
print(f"\nPeak demand: {peak_demand:.0f} MW")
print(f"Average demand: {avg_demand:.0f} MW")

# Current generation capacity
total_capacity = n.generators.loc[~n.generators.index.str.startswith('load_shed_'), 'p_nom'].sum()
print(f"\nCurrent total capacity: {total_capacity:.0f} MW")
print(f"Shortfall at peak: {peak_shed:.0f} MW")
print(f"Required new capacity: ~{peak_shed*1.15:.0f} MW (with 15% reserve margin)")

# Generation at capacity
real_gens = [g for g in n.generators.index if not g.startswith('load_shed_')]
gen_utilization = (n.generators_t.p[real_gens].max() / n.generators.loc[real_gens, 'p_nom']).sort_values(ascending=False)
at_capacity = gen_utilization[gen_utilization > 0.95]

print(f"\n{len(at_capacity)} generators at >95% capacity:")
print("\nBy carrier:")
for carrier in ['hydro', 'geothermal', 'gas', 'wind', 'solar_pv']:
    carrier_gens = n.generators.loc[at_capacity.index[n.generators.loc[at_capacity.index, 'carrier'] == carrier]]
    if len(carrier_gens) > 0:
        total_cap = carrier_gens['p_nom'].sum()
        print(f"  {carrier}: {len(carrier_gens)} generators, {total_cap:.0f} MW")

# Transmission loading
line_loading = (n.lines_t.p0.abs().max() / n.lines.s_nom).sort_values(ascending=False)
congested = line_loading[line_loading > 0.95]

print(f"\nCongested lines (>95%): {len(congested)}")
if len(congested) > 0:
    print("Top 5 congested:")
    for line, loading in congested.head(5).items():
        line_info = n.lines.loc[line]
        print(f"  {line}: {loading*100:.0f}% - {line_info.bus0}?{line_info.bus1} ({line_info.s_nom:.0f} MVA)")

# RECOMMENDATION
print("\n" + "="*60)
print("HEURISTIC RECOMMENDATION")
print("="*60)

required_capacity = peak_shed * 1.15  # 15% reserve margin

print(f"\nRequired new capacity: ~{required_capacity:.0f} MW")
print(f"\nSuggested mix (aligned with NZ policy):")
print(f"  Wind (50%): {required_capacity*0.5:.0f} MW - renewable target")
print(f"  Solar (20%): {required_capacity*0.2:.0f} MW - daytime peak support")
print(f"  Gas peaking (20%): {required_capacity*0.2:.0f} MW - firming capacity")
print(f"  Battery storage (10%): {required_capacity*0.1:.0f} MW - flexibility")

print(f"\nRough cost estimate (NZD):")
print(f"  Wind @ $2.5M/MW: ${required_capacity*0.5*2.5:.0f} M")
print(f"  Solar @ $1.8M/MW: ${required_capacity*0.2*1.8:.0f} M")
print(f"  Gas @ $1.2M/MW: ${required_capacity*0.2*1.2:.0f} M")
print(f"  Battery @ $1.5M/MW: ${required_capacity*0.1*1.5:.0f} M")
total_cost = (required_capacity*0.5*2.5 + required_capacity*0.2*1.8 + 
              required_capacity*0.2*1.2 + required_capacity*0.1*1.5)
print(f"  TOTAL: ~${total_cost:.0f} M")

if len(congested) > 0:
    print(f"\nNote: {len(congested)} transmission constraints also need addressing")