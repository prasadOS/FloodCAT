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

## M2A-1 cloud evidence (2026-11-10)

Prepared interpreter: `/workspace/.floodcat-venv/bin/python`, Python 3.11.17,
NumPy 2.4.6. Branch: `feature/m2a-exposure-engine` from `7c981b0`.

- `PYTHONDONTWRITEBYTECODE=1 /workspace/.floodcat-venv/bin/python -m unittest discover -s tests -v` — 22 passed, no skips, in 0.043 s. Includes all original 12 and 10 new exposure tests.
- New hand-calculated fixtures cover strict thresholds/equality, dry cells, excluded hazard nodata, valid zero, independent missing exposure and masks, overall/flooded cell coverage, missing dry exposure, entirely missing exposure, empty flooded/valid domains, fractional counts, partition conservation, invalid dimensions/shapes/types/values/thresholds, integer overflow avoidance, sum overflow rejection and input immutability.
- Inline `PYTHONDONTWRITEBYTECODE=1 /workspace/.floodcat-venv/bin/python -` with `streamlit.testing.v1.AppTest.from_file('app.py')` — all six synthetic sections passed without exceptions. REAL — WRI passed at 0 m (1,206.56 km²) and 1 m (430.13 km²), with three download controls. Existing Streamlit bare-context and `use_container_width` deprecation warnings were emitted. No browser download clicks or hosted build were tested.

These are calculation-only tests with fabricated exposure arrays, not evidence of
real WorldPop/GHSL coverage or conservative real-raster aggregation. No source
rasters acquired, packages installed, CLIMADA added, or WRI/dashboard code changed.
Prior verification left untracked Python 3.12 `__pycache__` directories; retained.

## M2A-1 final feature-branch review (2026-11-10)

Branch `feature/m2a-exposure-engine`, based on confirmed remote main `7c981b0`.
Reviewed engine validation, strict threshold semantics, independent exposure masks,
float summation, units and coverage assumptions. Added two independent tests for
positive depth outside the hazard mask and population-only missingness with a
complete built-up total. No additional scientific dependencies or app/WRI changes.

- `PYTHONDONTWRITEBYTECODE=1 /workspace/.floodcat-venv/bin/python -m unittest discover -s tests -v` — **24 passed**, no skips, in 0.067 s (12 original + 12 exposure tests).
- `UV_CACHE_DIR=/workspace/.floodcat-cache uv pip check --python /workspace/.floodcat-venv/bin/python` — all 35 installed packages compatible.
- `git diff --check` — passed. The earlier AppTest evidence above remains applicable; app and hazard sources are unchanged.

Source-to-target aggregation, real exposure pixels, browser download clicks and
hosted deployment remain unverified. Feature-branch commit/push and a PR are
authorized; main is not to be pushed or merged by this task.

## M2A-2 conservative aggregation (2026-11-10)

Repository confirmed as `prasadOS/FloodCAT`. Initial local branch `work` was at
`7c981b0`, behind the requested base; this mismatch was reported before changes.
`git fetch origin main` obtained `84a7c6396899806ea4b488e33845a10669c44ec3`, the
M2A-1 merge. New branch `m2a-2-conservative-aggregation` starts from that commit.
A final `git ls-remote origin refs/heads/main` confirmed the same remote base.

Interpreter: `/workspace/.floodcat-venv/bin/python`, Python 3.11.17, NumPy 2.4.6.
No packages installed or upgraded, real data acquired, or CLIMADA added.

- Baseline `/workspace/.floodcat-venv/bin/python -m unittest discover -s tests -v`
  — **24 passed**, no skips, in 0.055 s.
- Initial targeted aggregation run:
  `PYTHONDONTWRITEBYTECODE=1 /workspace/.floodcat-venv/bin/python -m unittest discover -s tests -p test_aggregation.py -v`
  — **16 passed**, no skips, in 0.044 s. Two further fixtures were added for
  excluded missing pixels and simultaneous clipped/missing coverage.
- Final full regression command:
  `PYTHONDONTWRITEBYTECODE=1 /workspace/.floodcat-venv/bin/python -m unittest discover -s tests -v`
  — **42 passed**, no failures, errors or skips, in **0.087 s**. Includes all
  12 M1B tests, all 12 M2A-1 tests and 18 new aggregation tests.
- Independent hand budgets check noninteger coarsening (population 21 → 8.5 +
  12.5; built-up 910 m² → 315 + 595 m²), two-axis offsets, partial source and
  target coverage, clipping without renormalization, NaN/explicit masks, valid
  zero, all-missing and absent coverage, touching boundaries, tiny missing
  overlaps, axis direction, fractional allocation and conservation. A separate
  numerical integration of the ellipsoid differential area checks WGS84 latitude
  weights. Fabricated fine-grid counts conserve 90 people onto a WRI-transform
  fixture. Other tests check input validity, integer/float overflow, immutability,
  explicit cross-CRS rejection and safe handoff to the M2A-1 engine.
- `PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 /workspace/.floodcat-venv/bin/python /workspace/work/m2a-2/smoke_app.py`
  — exit 0. The temporary AppTest harness verified default Synthetic demo and
  all six sections; REAL — WRI at 0 m (1,206.56 km²) and 1 m (430.13 km²),
  three download controls, mocked missing-asset warning and switch back to
  Synthetic demo. The first harness invocation used a relative app path, which
  AppTest resolved relative to the temporary harness; corrected to an absolute
  path before the successful run. Existing Streamlit bare-context and width
  deprecation warnings remain. No browser download clicks or hosted build tested.
- `UV_CACHE_DIR=/workspace/.floodcat-cache uv pip check --python /workspace/.floodcat-venv/bin/python`
  — all **35 installed packages compatible**. The baseline attempt to use
  `python -m pip check` found no pip module; uv performed the compatibility check
  without installing anything.
- `git diff --exit-code origin/main -- app.py src/floodcat/exposure.py src/floodcat/wri.py src/floodcat/wri_view.py src/floodcat/demo.py src/floodcat/exports.py requirements.txt data tests/test_demo.py tests/test_exposure.py tests/test_wri.py`
  — exit 0: application, existing engines, dependencies, assets and old tests
  unchanged. `git diff --check` — passed.

These are calculation-only fixtures. Shared-CRS rectilinear grids are supported;
rotation, wrapping, arbitrary polygon clipping and cross-CRS remapping are not.
Native GHSL World Mollweide pixels have not been reprojected to WRI. The method
assumes uniform exposure over physical source-pixel area and makes no observed
inundation, damage, financial-loss or real-exposure coverage claims. Complete
target values remain NaN when source coverage is partial or missing. See
[EXPOSURE.md](EXPOSURE.md) for the full contract and next task.
