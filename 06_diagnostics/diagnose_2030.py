"""
diagnose_2030.py

Runs a proper diagnostic on all inadequate 2030 months.
Calls fix_all_capacities before optimising so results are reliable.

Results written to: diagnose_2030_results.txt

Run from repo root:
    python diagnose_2030.py
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

OUTPUT_PATH = r"C:\Users\Public\Documents\Thesis\analysis\pypsa-nza-heuristic\diagnose_2030_results.txt"

MONTHS = ['jan', 'feb', 'mar', 'may', 'jun', 'aug', 'sep']

with open(CONFIG_PATH) as f:
    config = yaml.safe_load(f)

lines_out = []

for month in MONTHS:
    print(f"Running {month}...")
    n = load_base_network(config, year=2030, month=month)
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
    lines_out.append("Top congested lines:")
    lines_out.append(congested.to_string())

with open(OUTPUT_PATH, "w") as f:
    f.write("\n".join(lines_out))

print(f"\nDone. Results written to: {OUTPUT_PATH}")
