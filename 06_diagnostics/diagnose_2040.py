"""
diagnose_2040.py

Diagnostic for 2040 inadequate months.

Run from repo root:
    python diagnose_2040.py
"""

import yaml
from pypsa_nza_dispatch.network import (
    load_base_network,
    fix_all_capacities,
    add_load_shedding_generators,
)

CONFIG_PATH = (
    r"C:\Users\Public\Documents\Thesis\analysis"
    r"\pypsa-nza-dispatch\config\dispatch_config.yaml"
)

OUTPUT_PATH = r"C:\Users\Public\Documents\Thesis\analysis\pypsa-nza-heuristic\diagnose_2040_results.txt"

MONTHS = ['may', 'jun', 'jul', 'aug', 'sep']

with open(CONFIG_PATH) as f:
    config = yaml.safe_load(f)

lines_out = []

for month in MONTHS:
    print(f"Running {month}...")
    n = load_base_network(config, year=2040, month=month)
    n = fix_all_capacities(n, verbose=False)
    n = add_load_shedding_generators(n, verbose=False)
    n.optimize(solver_name='highs', solver_options={'log_to_console': False})

    shed_gens = [g for g in n.generators.index if g.startswith('load_shed_')]
    shed = n.generators_t.p[shed_gens].sum()
    shed = shed[shed > 0.01]

    line_loading = n.lines_t.p0.abs().max() / n.lines.s_nom
    congested = line_loading[line_loading > 0.95].sort_values(ascending=False).head(15)

    lines_out.append(f"\n=== {month.upper()} ===")
    lines_out.append("Shedding buses:")
    for bus, mwh in shed.sort_values(ascending=False).items():
        lines_out.append(f"  {bus}: {mwh:.1f} MWh")
    lines_out.append("Top congested lines (bus0->bus1, s_nom):")
    for line_name, loading in congested.items():
        b0 = n.lines.at[line_name, 'bus0']
        b1 = n.lines.at[line_name, 'bus1']
        s  = n.lines.at[line_name, 's_nom']
        lines_out.append(f"  {line_name:8s}  {b0}->{b1}  s_nom={s:.0f} MVA  loading={loading:.3f}")

with open(OUTPUT_PATH, "w") as f:
    f.write("\n".join(lines_out))

print(f"\nDone. Results written to: {OUTPUT_PATH}")
