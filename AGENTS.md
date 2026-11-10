# FloodCAT development instructions

## Scope
FloodCAT is a Python/Streamlit application for regional physical flood-hazard and exposure screening. **M2C-3** consolidates the interface into **Synthetic Demo** (default) and **REAL — Patna**, each with six modules. Preserve verified common-footprint data and the historical small WRI pilot reference/downloads inside REAL — Patna. Keep hypothetical and real exposure distinct.

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
## Codex efficiency and context management

- Prioritize the smallest correct, testable implementation that satisfies the current milestone.
- Inspect the relevant repository paths before reading large documents. Read only the documentation and source files needed for the task.
- Treat current `main`, verified tests and source manifests as authoritative. Do not repeatedly rediscover established project facts.
- Reuse existing modules, dependencies and test utilities whenever appropriate. Avoid speculative refactoring, unnecessary abstractions and unrelated changes.
- Start with focused tests for modified components. Run the relevant regression suite before completing a pull request. Do not skip essential scientific validation to save tokens.
- Avoid repeating unsuccessful commands or blocked network requests without a concrete reason to expect a different result.
- Keep status messages and final reports concise. Report changed files, actual test results, blockers, scientific limitations and the PR link.
- If a task becomes substantially broader than the approved milestone, stop and report the proposed next milestone instead of expanding the work automatically.
- Never sacrifice numerical correctness, provenance, mask handling, conservation checks or data safety for efficiency.
