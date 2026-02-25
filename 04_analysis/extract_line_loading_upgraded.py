"""
Extract transmission line loading from 2030 UPGRADED scenario.
Compare to baseline to see impact of generation additions.
"""

import pypsa
import pandas as pd
import sys
from pathlib import Path

# Paths
BASE = Path(__file__).parent.parent
NETWORK_PATH = BASE / 'data' / 'networks' / '2030' / 'upgraded'
OUTPUT_PATH = BASE / 'results' / 'analysis'

print("="*80)
print("TRANSMISSION LINE LOADING ANALYSIS - 2030 UPGRADED")
print("="*80)

# Load network
print(f"\nLoading network from: {NETWORK_PATH}")
n = pypsa.Network()
n.import_from_csv_folder(str(NETWORK_PATH))

print(f"Network loaded: {len(n.buses)} buses, {len(n.lines)} AC lines, {len(n.links)} DC links")

print("\nRunning dispatch optimization...")
print("(This may take 30-60 seconds...)")

try:
    for bus in n.buses.index:
        gen_name = f'load_shed_{bus}'
        n.add('Generator', gen_name,
              bus=bus,
              p_nom=10000,
              marginal_cost=10000,
              carrier='load_shedding')
    
    n.optimize(solver_name='highs', solver_options={'time_limit': 300})
    print("? Optimization complete")
    
except Exception as e:
    print(f"\n? Optimization failed: {e}")
    sys.exit(1)

# Extract line loading
print("\nExtracting line loading data...")

line_data = []
for line in n.lines.index:
    max_flow = n.lines_t.p0[line].abs().max()
    s_nom = n.lines.loc[line, 's_nom']
    loading_pct = (max_flow / s_nom * 100) if s_nom > 0 else 0
    
    line_data.append({
        'line': line,
        'bus0': n.lines.loc[line, 'bus0'],
        'bus1': n.lines.loc[line, 'bus1'],
        'capacity_MVA': s_nom,
        'max_flow_MW': max_flow,
        'loading_pct': loading_pct,
        'length_km': n.lines.loc[line, 'length'],
    })

df = pd.DataFrame(line_data).sort_values('loading_pct', ascending=False)

# Save
output_file = OUTPUT_PATH / 'line_loading_2030_upgraded.csv'
df.to_csv(output_file, index=False)
print(f"? Saved to: {output_file.relative_to(BASE)}")

# Statistics
print("\n" + "="*80)
print("SUMMARY STATISTICS")
print("="*80)

total = len(df)
lines_100 = (df['loading_pct'] >= 100).sum()
lines_95 = (df['loading_pct'] >= 95).sum()
lines_80 = ((df['loading_pct'] >= 80) & (df['loading_pct'] < 95)).sum()

print(f"\nTotal AC lines: {total}")
print(f"Lines =100%: {lines_100} ({lines_100/total*100:.1f}%)")
print(f"Lines =95%: {lines_95} ({lines_95/total*100:.1f}%)")
print(f"Lines 80-95%: {lines_80} ({lines_80/total*100:.1f}%)")
print(f"\nMean: {df['loading_pct'].mean():.1f}%")
print(f"Median: {df['loading_pct'].median():.1f}%")
print(f"Max: {df['loading_pct'].max():.1f}%")

# Top 20
print("\n" + "="*80)
print("TOP 20 MOST LOADED LINES")
print("="*80)
print(f"\n{'Rank':<6}{'Line':<12}{'From':<8}{'To':<8}{'Loading':<10}")
print("-"*60)

for i, row in df.head(20).iterrows():
    print(f"{df.index.get_loc(i)+1:<6}{row['line']:<12}{row['bus0']:<8}{row['bus1']:<8}{row['loading_pct']:<10.1f}%")

# Load baseline for comparison
baseline_file = OUTPUT_PATH / 'line_loading_2030_baseline.csv'
if baseline_file.exists():
    print("\n" + "="*80)
    print("COMPARISON: BASELINE vs. UPGRADED")
    print("="*80)
    
    df_base = pd.read_csv(baseline_file)
    
    print(f"\n{'Metric':<25}{'Baseline':<15}{'Upgraded':<15}{'Change':<10}")
    print("-"*65)
    print(f"{'Lines =100%':<25}{(df_base['loading_pct'] >= 100).sum():<15}{lines_100:<15}{lines_100 - (df_base['loading_pct'] >= 100).sum():<+10}")
    print(f"{'Lines =95%':<25}{(df_base['loading_pct'] >= 95).sum():<15}{lines_95:<15}{lines_95 - (df_base['loading_pct'] >= 95).sum():<+10}")
    print(f"{'Mean loading (%)':<25}{df_base['loading_pct'].mean():<15.1f}{df['loading_pct'].mean():<15.1f}{df['loading_pct'].mean() - df_base['loading_pct'].mean():<+10.1f}")

print("\n" + "="*80)
print("DONE")
print("="*80)