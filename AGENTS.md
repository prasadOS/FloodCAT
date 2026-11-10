# FloodCAT development instructions

## Scope
FloodCAT is a Python/Streamlit application for regional physical flood-hazard and exposure screening. **M1B** is the current verified milestone. Preserve the default **Synthetic demo** and the separate **REAL — WRI** historical Patna WATCH T100 hazard view. Keep synthetic exposure separate from real hazard.

Keep claims within the evidence. Treat WRI depths as modeled screening data and population and built-up overlays as exposure. Avoid claims of observed inundation, calibrated hydraulics, or physical damage. Financial loss, AAL/PML, insurance and credit are outside scope. Label RCP/CMIP5 and SSP/CMIP6 distinctly.

## Resume from a clone

1. Inspect `git status --short --branch`, [README.md](README.md), [project status](docs/PROJECT_STATUS.md), [decisions](docs/DECISIONS.md), [data sources](docs/DATA_SOURCES.md), and [test evidence](docs/TEST_RESULTS.md). Review the affected source and tests before editing.
2. Work from the repository root with Python 3.11 and the dependencies in `requirements.txt`. Use repository-relative paths with `pathlib`.
3. Run `python -m unittest discover -s tests -v` and, for app changes, `python -m streamlit run app.py`. Check both modes and missing-asset behavior when relevant.
4. Make one verifiable change at a time and add deterministic tests for scientific behavior changes. Record the exact commands and outcomes, distinguish prior reports from new evidence, and hand over modified files, Git state, and the next single task.

Coordinate ownership so only one agent edits the checkout at a time. Preserve existing work. Obtain owner approval before package installations or upgrades, data acquisition, destructive cleanup, commits, pushes, or deployment.

## Data and deployment

For real rasters, verify the exact source asset and scenario, units, CRS, native grid, pixel areas, mask semantics, valid dry zero, attribution, redistribution terms, and SHA-256. Stop if source selection or mask semantics are ambiguous. When adding exposure, test count conservation and document grid and edge handling.

Keep Earth Engine access in local acquisition scripts. Use authorized credentials and an explicitly provided project ID. Keep credentials, local environment exports, confidential data, and large raw datasets out of Git. Cloud runs from compact, redistributable local files with provenance. Follow the [deployment manifest](docs/DEPLOYMENT.md).

Use [project status](docs/PROJECT_STATUS.md) to determine what has been verified and what awaits approval. Catalog matches and footprints alone establish neither usable pixel coverage nor completed integrations.
