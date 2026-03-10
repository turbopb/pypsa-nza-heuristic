# pypsa-nza-heuristic: Capacity Expansion Validation Framework

## Overview

`pypsa-nza-heuristic` is a heuristic capacity expansion and adequacy validation framework for the New Zealand electricity system, built on top of [PyPSA](https://pypsa.org/) and the `pypsa-nza-dispatch` validation tool. It supports sequential planning horizon analysis from a 2024 baseline through to 2040, applying MBIE demand growth projections and iteratively adding generation and transmission capacity until all planning years meet a defined adequacy threshold.

The framework is designed to support PhD research into the role of flexible hydrogen production in the New Zealand electricity system, with Tiwai Point as the primary case study site.

---

## Repository Structure

```
pypsa-nza-heuristic/
├── 02_scenarios/
│   ├── 01_setup_year.py              # Copy and scale a source year to a target year
│   ├── 03_apply_additions_manual.py  # Apply capacity additions and revalidate
│   └── additions/                    # YAML files specifying capacity additions
│       ├── additions_2030_iter01.yaml
│       ├── additions_2030_iter02.yaml
│       ├── additions_2030_iter03.yaml
│       ├── additions_2035_iter01.yaml
│       └── additions_2040_iter01.yaml
├── 03_validation/
│   └── 02_validate_year.py           # Validate adequacy across all 12 months
├── results/
│   └── validation/                   # CSV and log outputs
└── diagnose_{year}.py                # Diagnostic scripts (run as needed)
```

---

## Dependencies

- Python 3.11
- PyPSA 1.0.7 (conda environment: `pypsa-nza-dispatch`)
- `pypsa-nza-dispatch` package (separate repository, must be installed)
- pandas, PyYAML, linopy, HiGHS solver

Activate the environment before running any script:

```powershell
conda activate pypsa-nza-dispatch
```

---

## Workflow

The workflow proceeds sequentially through four planning horizons: 2024, 2030, 2035, and 2040. Each year is derived from the previous, with demand scaled by MBIE growth factors. Capacity additions are applied iteratively until all twelve months meet the adequacy threshold.

### Adequacy Threshold

A month is considered adequate when load shedding is at or below **0.01% of total demand**. This corresponds to the criterion used in New Zealand electricity planning practice.

### Demand Scaling

Demand is scaled using absolute MBIE reference scenario growth factors. The year-on-year multiplier applied at setup time is:

```
factor = MBIE_absolute[target_year] / MBIE_absolute[source_year]
```

| Transition | Multiplier |
|---|---|
| 2024 -> 2030 | 1.13816 |
| 2030 -> 2035 | 1.09357 |
| 2035 -> 2040 | 1.10725 |

Demand is pre-scaled into `loads-p_set.csv` at setup time. All subsequent validation and dispatch runs use `scaling_factor=1.0`.

---

## Step-by-Step Calling Sequence

### Step 1 -- Validate the 2024 Baseline

```powershell
python 03_validation\02_validate_year.py --year 2024
```

This validates all twelve months of the 2024 network as-is. The 2024 network is the permanent source of truth and is never modified. Any inadequacies in 2024 are noted but not corrected at this stage (see Known Issues).

Output: `results\validation\annual_summary_2024.csv`

---

### Step 2 -- Set Up the 2030 Network

```powershell
python 02_scenarios\01_setup_year.py --source-year 2024 --target-year 2030
```

This copies all twelve monthly network directories from 2024 to 2030 and scales `loads-p_set.csv` by the 2024->2030 MBIE factor. The script will refuse to run if the target directory already exists.

---

### Step 3 -- Validate the 2030 Network

```powershell
python 03_validation\02_validate_year.py --year 2030
```

Output: `results\validation\annual_summary_2030.csv`

---

### Step 4 -- Apply Capacity Additions and Revalidate

```powershell
python 02_scenarios\03_apply_additions_manual.py ^
    --year 2030 ^
    --additions 02_scenarios\additions\additions_2030_iter01.yaml ^
    --iteration 1
```

This reads the additions YAML, applies generator and line upgrades to all twelve monthly network directories (writing the changes back to CSV so they persist), then reruns adequacy validation. Increment `--iteration` on each run.

Output: `results\validation\additions_2030_iter01.csv`

Repeat Steps 3-4 (with increasing iteration numbers) until all twelve months are adequate.

---

### Step 5 -- Repeat for 2035 and 2040

Once 2030 is adequate:

```powershell
python 02_scenarios\01_setup_year.py --source-year 2030 --target-year 2035
python 03_validation\02_validate_year.py --year 2035
# iterate additions as needed
python 02_scenarios\01_setup_year.py --source-year 2035 --target-year 2040
python 03_validation\02_validate_year.py --year 2040
# iterate additions as needed
```

---

## Capacity Addition YAML Format

Additions are specified in YAML files. Each file applies to one year and one iteration. Additions are cumulative -- each iteration's changes are written into the network CSV files, so subsequent iterations build on top of previous ones.

```yaml
year: 2030
notes: "Brief description of this iteration"

generators:
  - name: OTA_gas_01       # Must be unique across the network
    bus: OTA               # Must match an existing bus name
    p_nom: 300             # Installed capacity in MW
    carrier: gas
    marginal_cost: 80      # $/MWh
    efficiency: 0.4        # Optional, default 1.0
    p_max_pu: 1.0          # Optional capacity factor, default 1.0

lines:
  - name: S-L3_upgrade     # Label for logging only
    existing_line: S-L3    # Must match an existing line name in the network
    add_s_nom: 600         # MVA to add to the existing thermal rating
```

---

## Bottleneck Diagnosis

After each validation run, inadequate months are classified by bottleneck type:

| Type | Description |
|---|---|
| `GENERATION` | Many buses shedding across the network, most generators at capacity, lines not saturated |
| `TRANSMISSION` | Few buses shedding, one or more lines at 100% loading, spare generation available |
| `MIXED` | Both generation shortage and transmission congestion contributing |
| `ADEQUATE` | Load shedding at or below the 0.01% threshold |

### Diagnostic Script

When the summary output alone is insufficient to identify the specific bottleneck, run a detailed diagnostic:

```powershell
python diagnose_{year}.py
```

This loads each inadequate month with `fix_all_capacities()` called before optimisation (critical -- without this, generators remain extendable and the results are not representative of a fixed-capacity dispatch). It reports shedding by bus and congested lines with their bus connections and thermal ratings.

Output: `diagnose_{year}_results.txt`

---

## Rationale and Method for Capacity Modification

### Why heuristic iteration rather than linear optimisation?

A standard capacity expansion model (LOPF with extendable assets) would solve for the least-cost combination of generation and transmission additions in a single optimisation. This approach was not used here for two reasons:

1. **Computational cost**: solving a full expansion model over 8760 hourly snapshots for all four years simultaneously is prohibitive without dedicated HPC resources.
2. **Transparency**: the heuristic approach makes each addition explicit and traceable, which is important for thesis documentation and for understanding which specific infrastructure decisions drive adequacy outcomes.

### Generation additions

New generators are added as dispatchable thermal plant (gas) at buses where shedding is observed. The bus location is chosen to be electrically close to the shedding load, subject to the constraint that the bus has an existing gas or thermal connection in the network. Marginal costs are set in the range $80--90/MWh, consistent with open-cycle gas turbine peaking plant.

Capacity is sized based on the magnitude of shedding observed in the worst month, with a margin applied. Additions are only made when the diagnostic indicates a generation bottleneck (many buses shedding, most generators at capacity); if shedding is localised to one or two buses with congested lines nearby, a transmission upgrade is preferred.

### Transmission upgrades

Line upgrades are applied by adding MVA capacity to an existing line's `s_nom` parameter. This represents the addition of a parallel circuit on an existing corridor, which is the most common form of transmission augmentation in practice. The increment used is 600 MVA, corresponding to one additional 220 kV double-circuit line.

Lines are prioritised for upgrade based on their loading factor in the diagnostic output. Lines at or above 100% loading in multiple months are upgraded first. Lines near 100% in only one month are upgraded if they are clearly the binding constraint isolating a shedding bus.

The diagnostic is always run with `fix_all_capacities()` applied before the solver. Without this step, extendable generators absorb the capacity shortfall and lines appear to operate within limits, masking the true bottleneck.

---

## Known Issues and Planned Corrections

The following issues were identified during validation and must be corrected before results are considered final. All four planning years will need to be regenerated once the 2024 base network is corrected.

1. **S-L3 (INV->TWI)**: The Tiwai Point feed is a double-circuit line but is currently modelled as a single circuit (600 MVA). The correct rating is approximately 1200 MVA. This caused large spurious shedding at TWI in the 2030 validation, which was compensated by a transmission upgrade addition.

2. **220 kV lines**: A number of 220 kV lines in the network are rated at 600 MVA (single circuit) but should be double circuit (1200 MVA). The full line list needs to be audited against Transpower published data.

3. **S-L68 / S-L69**: These lines near the HVDC corridor carry an unusual rating of 1000 MVA. This should be verified against source data.

4. **2024 baseline inadequacy**: Eight of twelve months in 2024 are currently inadequate. This is partly attributable to the underrated lines above, and partly because 2024 was a stressed year in practice (Transpower employed demand response measures including ripple control). The baseline should be re-evaluated after line rating corrections.

---

## Ideas for Automation

The current workflow is manual: the user inspects the validation summary, runs the diagnostic script, writes an additions YAML, and reruns. The following approaches could automate this loop.

### 1. Rule-based automatic iteration

A script reads the validation CSV after each run and applies a fixed decision rule:

- If a month has a GENERATION bottleneck: add N MW of gas at the bus with the highest shedding.
- If a month has a TRANSMISSION bottleneck: upgrade the most loaded line by 600 MVA.
- If MIXED: do both.
- Repeat until all months are adequate or a maximum iteration count is reached.

This is straightforward to implement and would handle most cases. The main risk is oscillation, where adding generation in one area shifts the bottleneck to a different transmission constraint. A damping factor (adding less than the full apparent shortfall each iteration) can mitigate this.

### 2. Shadow price-guided additions

After each dispatch run, the shadow prices (dual variables) on line and generator capacity constraints identify exactly which constraints are binding and by how much. PyPSA returns these via `n.lines_t.mu_lower` / `mu_upper` and the generator marginal prices. Additions can be sized proportional to the shadow price, concentrating investment where it has the highest impact on adequacy.

### 3. Snakemake pipeline

The setup, validation, and addition steps map naturally onto a Snakemake DAG. Each year's adequacy CSV would be a Snakemake target, with rules for setup, validation, and each iteration. This would allow the full four-year workflow to be re-executed with a single `snakemake` command after any change to the base network.

### 4. Convergence criterion and automatic termination

Rather than checking the summary manually, the addition script could accept a `--auto` flag that loops internally until all months are adequate, writing a new additions YAML for each iteration and logging all decisions. A maximum iteration guard prevents infinite loops in pathological cases.

---

## Results Summary

| Year | Initial adequate months | Iterations required | Final adequate months |
|---|---|---|---|
| 2024 | 4/12 | 0 (baseline) | 4/12 |
| 2030 | 0/12 | 3 | 12/12 |
| 2035 | 10/12 | 1 | 12/12 |
| 2040 | 7/12 | 1 | 12/12 |

Note: 2035 MAY shows 0.001% shedding after iter01, which is within the 0.01% threshold.

---

## Authors

Phillippe Bruneau  
PhD Candidate, University of Canterbury  
