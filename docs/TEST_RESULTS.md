# Test evidence

## Portable ZIP (2026-11-10)

The source package includes `tests/test_demo.py` with seven deterministic unit tests using Python's standard-library unittest.

**Not yet verified on user's Windows laptop:** application launch, browser rendering, file downloads and hosted deployment. User should execute:

```bat
conda activate citi
cd /d D:\citi
python -m unittest discover -s tests -v
python -m streamlit run app.py
```

Record exact outputs here after execution. Do not copy test results from the old inaccessible `E:\Citi` machine into this project's test record.

## M1A local evidence (2026-11-10)

Commands used the `citi` environment interpreter (Python 3.11.18, Earth Engine API 1.7.52).

- `python -B -m unittest discover -s tests -v` — seven passed.
- `python -B -m pip check` — no broken requirements found. The local Pandas 3.1.1 and Plotly 7.1.0 are outside the repository's deployment ranges.
- `python -B scripts/inspect_gee_catalog.py --project <registered-project-id>` — initial sandboxed run failed at the OAuth proxy. Network-enabled rerun exited 0 using existing credentials.
- Supplemental metadata-only Python query applied exact model filters and checked projections and footprint containment. The first invocation used invalid Earth Engine dictionary syntax. The corrected query exited 0 and confirmed one image per WRI filter and all three footprint checks.
- `git status --short --branch` — this folder is outside a Git repository. Streamlit and raster tests were outside this inspection.

## M1B local evidence (2026-11-10)

Commands used the existing `citi` interpreter.

- Read-only Python Earth Engine `reduceRegion` with unweighted sums on the source affine grid found 2,784 cells. The first request's 10,000-pixel cap was too low for the five-band reduction. The 20,000 cap passed at the same grid spacing.
- `python -B -m scripts.acquire_patna_wri --project <registered-project-id>` exited 0 after the reader was corrected to handle Earth Engine's affine matrix tag and explicitly decode its big-endian, deflated float tile. Rejected attempts did not write assets. The saved raster matched source counts and maximum depth.
- `python -B -m unittest discover -s tests -p test_wri.py -v` — 5 passed.
- `python -B -m unittest discover -s tests -v` — 12 passed.
- `python -B -m pip check` — no broken requirements found. Import and local asset-load checks passed with Pillow 13.0.0.
- `python -B -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true --browser.gatherUsageStats false` — server started. Local GET requests to `/` and `/_stcore/health` returned HTTP 200.
- Inline `python -B -` Streamlit AppTest passed all six synthetic sections, the real map element and three download controls, the 0 m and 1 m area metrics, and simulated missing and invalid assets. The initial harness used positional radio selection and was corrected to use labels. The sandbox logged a temporary-directory cleanup error after the assertions. Browser rendering and download clicks are pending visual review.

## Publication readiness (2026-11-10)

- `python -B -m unittest discover -s tests -v` — all 12 passed on Python 3.11.18. `python -B -m pip check` — no broken requirements found. All five direct pins matched installed versions, and PyPI lists Linux CPython 3.11 or platform-independent wheels.
- `python -B -m streamlit run app.py --server.address 127.0.0.1 --server.port 58202 --server.headless true --browser.gatherUsageStats false` — fresh process started. Both `/` and `/_stcore/health` returned HTTP 200. The smoke-test process was stopped afterward.
- Inline `python -B -` AppTest passed with Google project and credential environment variables removed, Earth Engine and Google auth imports disabled, and non-loopback socket connections blocked. The real view displayed 1,206.56 km² and three download controls. Hiding either asset independently produced a warning without real metrics. Switching back to the synthetic view worked.
- The first AppTest network guard also blocked Windows asyncio's loopback socket and was corrected. The sandbox reported a temporary-directory cleanup error after the passing assertions. A hosted build and browser download clicks are pending.

## Documentation refresh and publication package (2026-11-10)

The owner independently verified the initial publication archive, its SHA-256, and all 12 tests. After the documentation refresh, `python -B -m unittest discover -s tests -v` ran in the existing Python 3.11.18 environment and passed all 12 tests in 0.119 s. The app, tests, scripts, dependencies, and raster assets were unchanged.
