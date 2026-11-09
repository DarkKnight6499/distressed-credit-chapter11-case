# Distressed credit Chapter 11 case

An offline Python and Excel study of Party City Holdco's 2023 restructuring. The analytical vintage is the July 21 filed plan and disclosure supplement. Confirmation and emergence are documented separately.

The project reproduces the filed recovery table, models a separate absolute-priority allocation, bridges enterprise value to equity, and tests tranche recoveries across valuation scenarios. The model does not reproduce negotiated subscription rights, dilution or trust settlements.

Start with [strategy note](docs/strategy_note.md), [capital structure](docs/capital_structure.md), [methodology and results](docs/methodology.md), and [event timeline](docs/timeline.md). Every extracted number has a row in [source verification](docs/source_verification.md). [Case selection](docs/case_selection.md) explains scope and access limits.

## Run offline

Requires Python 3.10+ and openpyxl (`pip install -r requirements.txt`). No network request is needed to rebuild.

```powershell
$Python = 'python'
$env:PYTHONPATH = Join-Path (Get-Location) 'python'
& $Python scripts/build_outputs.py
& $Python scripts/build_docs.py
& $Python -m unittest discover -s python/tests -v
```

The commands rebuild [Excel](excel/chapter11.xlsx), CSV and JSON tables under [examples/output](examples/output/), and generated documentation. They read [case_inputs.json](data/case_inputs.json). The snapshot and its SHA-256 manifest are shipped with the project.

## Excel

Edit controls and principal amounts on `Inputs`. `Waterfall` calculates the active case, full-payment thresholds and the stated EV scenarios. `Sensitivity` calculates EV from an EBITDA factor and multiple. `Plan` preserves filed classes and projected recoveries. `Capital` distinguishes petition figures from later plan floors.

Reconciliation tolerance: absolute `1e-8`, measured in USD millions for amounts and decimal units for recovery fractions. Stored formulas and caches are checked with an independent, restricted formula evaluator. Native Excel recalculation failed in this environment because Windows COM had no logon session. Native Excel behavior and visual layout remain untested. To recalculate in a desktop session:

```powershell
powershell -File scripts/recalculate_excel.ps1
& $Python -m unittest discover -s python/tests -v
```

## Layout

| Directory | Content |
|---|---|
| `python/ch11/` | Offline allocation, reporting, workbook builder, restricted formula evaluator |
| `python/tests/` | Hand-computed unit cases, source integrity, formula reconciliation |
| `excel/` | Live-formula workbook |
| `data/` | Reviewed extracted snapshot and provenance manifest |
| `docs/` | Sources, capital structure, methodology, limitations, timeline and strategy |
| `examples/output/` | Reproducible CSV and JSON tables |
| `scripts/` | Artifact builders, optional isolated fetcher, native Excel recalculation |

## Limitations

Stylized: one pooled estate, principal-only claims, ABL before secured notes, and pari passu allocations within modeled ranks. Actual collateral pools and entity guarantees are not reconstructed.

Assumptions and estimates: midpoint base EV, sensitivity multipliers, full DIP commitment used as a claim proxy, zero cash adjustment and zero administrative reserve. These controls are not verified estate balances. The unsecured model includes only the two bond tranches.

Not verified: liquidation values, full unsecured and priority claim denominators, allowed DIP claim amounts, petition ABL split, intercompany loan balance, petition finance lease claims, final-plan recovery table and realized distributions. The EDGAR disclosure statement omits the liquidation exhibit. The Kroll docket returned HTTP 403; liquidation work stopped without estimates. See [limitations](docs/limitations.md).

This is a retrospective study, not investment advice. No claim of real-world validation is made.

## Optional acquisition

`scripts/fetch_sources.py` is the only network-capable code. It requires an identifying `SEC_USER_AGENT`, saves raw HTML under `data/raw/`, and writes `data/fetch_manifest.json`. It stops on the first acquisition failure and never replaces reviewed inputs automatically. It was not run because the shell was offline. Sources were opened with the web tool and transcribed into the snapshot. There is no runtime network access in `python/ch11/`.
