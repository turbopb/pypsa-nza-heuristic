"""
Calculate reserve margin for 2030 upgraded system.
"""

import pypsa
import pandas as pd

# Load 2030 upgraded network
n = pypsa.Network()
n.import_from_csv_folder(r"C:\Users\Public\Documents\Thesis\analysis\dispatch_data\cases\reference\2030\upgraded_2030")

# Calculate peak demand
peak_demand = n.loads_t.p_set.sum(axis=1).max()

# Calculate total installed capacity
total_capacity = n.generators['p_nom'].sum()

# Calculate effective capacity (accounting for availability)
effective_capacity = 0
for gen in n.generators.index:
    p_nom = n.generators.loc[gen, 'p_nom']
    carrier = n.generators.loc[gen, 'carrier']
    
    # Get p_max_pu (availability)
    if gen in n.generators_t.p_max_pu.columns:
        # Use average availability for variable sources
        p_max_pu = n.generators_t.p_max_pu[gen].mean()
    else:
        p_max_pu = n.generators.loc[gen, 'p_max_pu']
    
    effective_capacity += p_nom * p_max_pu

# Calculate reserve margins
installed_reserve = (total_capacity - peak_demand) / peak_demand * 100
effective_reserve = (effective_capacity - peak_demand) / peak_demand * 100

print("\n" + "="*60)
print("2030 UPGRADED SYSTEM - RESERVE MARGIN ANALYSIS")
print("="*60)

print(f"\nPeak Demand: {peak_demand:,.0f} MW")
print(f"\nInstalled Capacity: {total_capacity:,.0f} MW")
print(f"Effective Capacity: {effective_capacity:,.0f} MW")

print(f"\nInstalled Reserve Margin: {installed_reserve:.1f}%")
print(f"Effective Reserve Margin: {effective_reserve:.1f}%")

print("\n" + "="*60)
print("CAPACITY BREAKDOWN")
print("="*60)

# Breakdown by carrier
carriers = n.generators.groupby('carrier').agg({
    'p_nom': 'sum'
}).round(0)

print("\nInstalled capacity by type:")
for carrier, row in carriers.iterrows():
    print(f"  {carrier}: {row['p_nom']:,.0f} MW")

print("\n" + "="*60)
print("INTERPRETATION")
print("="*60)

if effective_reserve >= 15:
    status = "HEALTHY"
    comment = "Well above minimum 10-15% standard"
elif effective_reserve >= 10:
    status = "ADEQUATE"
    comment = "Meets minimum planning reserve"
elif effective_reserve >= 5:
    status = "TIGHT"
    comment = "Below recommended margin"
else:
    status = "INADEQUATE"
    comment = "Insufficient reserve"

print(f"\nStatus: {status}")
print(f"Comment: {comment}")
print(f"\nEffective reserve margin of {effective_reserve:.1f}% provides")
print(f"{effective_capacity - peak_demand:,.0f} MW cushion above peak demand")