"""
Extract transmission line loading from 2030 baseline scenario.
Identifies congested lines that may require upgrades.
"""

import pypsa
import pandas as pd
import sys
from pathlib import Path

# Paths relative to heuristic_planning directory
BASE = Path(__file__).parent.parent
NETWORK_PATH = BASE / 'data' / 'networks' / '2030' / 'baseline'
OUTPUT_PATH = BASE / 'results' / 'analysis'

print("="*80)
print("TRANSMISSION LINE LOADING ANALYSIS - 2030 BASELINE")
print("="*80)

# Load network
print(f"\nLoading network from: {NETWORK_PATH}")
n = pypsa.Network()
n.import_from_csv_folder(str(NETWORK_PATH))

print(f"Network loaded: {len(n.buses)} buses, {len(n.lines)} AC lines, {len(n.links)} DC links")

# We need to run optimization to get line flows
print("\nRunning dispatch optimization to calculate line flows...")
print("(This may take 30-60 seconds...)")

try:
    # Add load shedding generators at all buses (for adequacy validation)
    for bus in n.buses.index:
        gen_name = f'load_shed_{bus}'
        n.add('Generator', gen_name,
              bus=bus,
              p_nom=10000,  # 10 GW (effectively unlimited)
              marginal_cost=10000,  # Very expensive (penalty)
              carrier='load_shedding')
    
    # Run optimization
    n.optimize(solver_name='highs', 
               solver_options={'time_limit': 300})  # 5 min timeout
    
    print("? Optimization complete")
    
except Exception as e:
    print(f"\n? Optimization failed: {e}")
    print("\nNote: This may happen if network has issues.")
    print("We can still analyze line capacities (static analysis).")
    sys.exit(1)

# Extract line loading
print("\nExtracting line loading data...")

# Calculate loading for each line
line_data = []

for line in n.lines.index:
    # Get maximum absolute power flow across all timesteps
    max_flow = n.lines_t.p0[line].abs().max()
    
    # Get line capacity
    s_nom = n.lines.loc[line, 's_nom']
    
    # Calculate loading percentage
    loading_pct = (max_flow / s_nom * 100) if s_nom > 0 else 0
    
    # Get bus connections
    bus0 = n.lines.loc[line, 'bus0']
    bus1 = n.lines.loc[line, 'bus1']
    length = n.lines.loc[line, 'length']
    
    line_data.append({
        'line': line,
        'bus0': bus0,
        'bus1': bus1,
        'capacity_MVA': s_nom,
        'max_flow_MW': max_flow,
        'loading_pct': loading_pct,
        'length_km': length,
    })

# Create DataFrame
df = pd.DataFrame(line_data)
df = df.sort_values('loading_pct', ascending=False)

# Save to CSV
output_file = OUTPUT_PATH / 'line_loading_2030_baseline.csv'
output_file.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(output_file, index=False)

print(f"? Saved line loading data to: {output_file.relative_to(BASE)}")

# Print summary statistics
print("\n" + "="*80)
print("SUMMARY STATISTICS")
print("="*80)

total_lines = len(df)
lines_95_plus = (df['loading_pct'] >= 95).sum()
lines_100 = (df['loading_pct'] >= 100).sum()
lines_80_95 = ((df['loading_pct'] >= 80) & (df['loading_pct'] < 95)).sum()

print(f"\nTotal AC lines: {total_lines}")
print(f"Lines =100% loading: {lines_100} ({lines_100/total_lines*100:.1f}%)")
print(f"Lines =95% loading: {lines_95_plus} ({lines_95_plus/total_lines*100:.1f}%)")
print(f"Lines 80-95% loading: {lines_80_95} ({lines_80_95/total_lines*100:.1f}%)")

print(f"\nMean loading: {df['loading_pct'].mean():.1f}%")
print(f"Median loading: {df['loading_pct'].median():.1f}%")
print(f"Max loading: {df['loading_pct'].max():.1f}%")

# Print top congested lines
print("\n" + "="*80)
print("TOP 20 MOST CONGESTED TRANSMISSION LINES")
print("="*80)
print(f"\n{'Rank':<6}{'Line':<12}{'From':<8}{'To':<8}{'Capacity':<12}{'Max Flow':<12}{'Loading':<10}")
print("-"*80)

for i, row in df.head(20).iterrows():
    print(f"{df.index.get_loc(i)+1:<6}{row['line']:<12}{row['bus0']:<8}{row['bus1']:<8}"
          f"{row['capacity_MVA']:<12.0f}{row['max_flow_MW']:<12.0f}{row['loading_pct']:<10.1f}%")

# Identify critical corridors (=95%)
if lines_95_plus > 0:
    print("\n" + "="*80)
    print(f"CRITICAL CORRIDORS (=95% LOADING) - {lines_95_plus} LINES")
    print("="*80)
    
    critical = df[df['loading_pct'] >= 95]
    
    for i, row in critical.iterrows():
        status = "OVERLOADED" if row['loading_pct'] >= 100 else "CRITICAL"
        print(f"\n{row['line']}: {row['bus0']} ? {row['bus1']}")
        print(f"  Capacity: {row['capacity_MVA']:.0f} MVA")
        print(f"  Max Flow: {row['max_flow_MW']:.0f} MW")
        print(f"  Loading: {row['loading_pct']:.1f}% [{status}]")
        print(f"  Length: {row['length_km']:.1f} km")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
print(f"\nDetailed data saved to: {output_file.relative_to(BASE)}")
print("\nNext steps:")
print("  1. Review critical corridors list above")
print("  2. Consider transmission upgrades vs. localized generation")
print("  3. Use this data for 2035 planning iteration")
print("="*80)