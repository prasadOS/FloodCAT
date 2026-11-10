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

## M2A-3 conservative cross-CRS remapping (2026-11-10)

Confirmed `prasadOS/FloodCAT`, fetched remote `main` at
`45d59d2a1b88e9c78bb0ad301a96b02928ab1fe2` (merged PR #2), and created
`m2a-3-cross-crs-remapping` from it. Final remote-head check returned the same
SHA. No changes were based on the previous feature branch.

### Environment and installation

Inspected the connected cloud environment and network policy: ready, current
observations, enforced package-manager/GitHub access. Neither pyproj nor Shapely
was initially installed. The user authorized this scientific milestone and
optional dependency work; the original Python 3.11.17 application environment
was retained unchanged.

Commands from the repository root:

```sh
UV_CACHE_DIR=/workspace/.floodcat-cache uv venv --python /workspace/.floodcat-venv/bin/python /workspace/work/m2a-3/venv
UV_CACHE_DIR=/workspace/.floodcat-cache uv pip install --python /workspace/work/m2a-3/venv/bin/python -r requirements.txt 'pyproj==3.7.2' 'shapely==2.1.2'
```

Both exited 0. The isolated scientific environment has 37 packages, including
Python 3.11.17, NumPy 2.4.6, pyproj 3.7.2 / PROJ 9.5.1 and Shapely 2.1.2 /
GEOS 3.13.1. `requirements-science.txt` now declares the optional NumPy/pyproj/
Shapely pipeline; install it alongside `requirements.txt` for the full test suite.
No system packages, hosted dependency changes, CLIMADA or datasets added.

### Tests and independent accuracy

- Baseline `PYTHONDONTWRITEBYTECODE=1 /workspace/.floodcat-venv/bin/python -m unittest discover -s tests -v`
  — **42 passed**, no failures/errors/skips, in **0.070 s**.
- Initial 10-test cross-CRS run exposed three errors from an overly strict
  projection round-trip guard. PROJ CEA inverse residuals were measured at
  millimetre scale; EPSG:6933 now retains native area coordinates directly and
  the domain guard uses a documented 1 cm projected residual allowance. The
  corrected 10-test run passed. Three further tests added explicit uncertainty,
  tiny missing overlap/overflow and a dense geodesic area cross-check.
- Final full scientific regression:
  `PYTHONDONTWRITEBYTECODE=1 /workspace/work/m2a-3/venv/bin/python -m unittest discover -s tests -v`
  — **55 passed**, no failures, errors or skips, in **3.675 s**. Includes all
  42 original tests and 13 cross-CRS tests. Prior full run: 55 passed in 3.792 s;
  the final run also checks convergence of the independent quadrature oracle.
- Lightweight-runtime regression with the original interpreter:
  `PYTHONDONTWRITEBYTECODE=1 /workspace/.floodcat-venv/bin/python -m unittest discover -s tests -v`
  — 55 discovered in **0.070 s**, **42 passed, 13 explicitly skipped** because
  science dependencies are absent. This is not the complete science evidence.
- Projection checks use independent exact Mollweide identities at selected
  auxiliary angles (2e-8 m coordinate tolerance), plus inverse and regional
  round-trip checks (1e-11 / 2e-11 degrees). A direct ellipsoid differential-area
  integral checks geographic rectangle area within 1e-10 relative. Native
  Mollweide Jacobian quadrature checks source physical areas within 2e-8 relative
  at -30°, 0°, 25.7° and 65°, using 100 m and 300 km cells.
- The curved 300 km fixture has quadrature area 89,623,161,267.10747 m²;
  default polygon area is 89,623,161,322.55556 m² (6.19e-10 relative difference).
  Independent clipped allocation is 60.19218571628636 from 120 units; default
  gives 60.192187692795606 and tighter 0.1 mm / 1 km refinement gives
  60.19218572400746. Absolute budget tolerance is 5e-6 units; default/tight
  agreement tolerance is 2e-6. Doubling independent quadrature from 512 to
  1,024 y panels leaves the reference unchanged at the printed precision.
- The dense geodesic cross-check gives 89,623,161,268.63834 m², agreeing with
  default footprint area to 6.02e-10 relative. It shares PROJ transformations and
  the WGS84 ellipsoid, so this is supplementary rather than independent proof
  of those ingredients. Conservation/refinement alone cannot prove geography.
- Independent hand budgets check 80 → 40 + 40 and a 20-unit clip across CRSs
  within 1e-8 units, and full-domain conservation of 52.5 people / 21,000 m²
  within 1e-10 relative. Tests also cover missing source, masked sentinels,
  valid zero, partial/absent coverage, positive tiny nodata slivers, uncertainty
  near domain/missing boundaries, touching edges, rotation/reversed axes,
  integer/float overflow, no mutation, exposure handoff and failure limits.

### Representative-grid performance

`PYTHONDONTWRITEBYTECODE=1 /workspace/work/m2a-3/venv/bin/python -m scripts.benchmark_remapping`
— exit 0. Fabricated 32×32 100 m World Mollweide grid on a 100 m lattice near
Patna → 6×6 WRI-style EPSG:4326 cells at 1/120° resolution:

- Cold map build **0.261345267 s**; two cached-map applications **0.037984678 s**.
- **1,307** intersection pairs; **5,300** footprint vertices; **5** complete
  targets and no uncertain targets (remaining cells partial or absent).
- Known population **1280.0000000000018**, built-up **256000.00000000035 m²**:
  **1.33e-15 relative** aggregate conservation error for each.
- Maximum per-source allocation residual **3.42e-12**; physical source pixel
  areas **9958.090197592835–9958.137701606182 m²**.
- Default 1 cm chord accuracy, 10 km maximum segment, 2 cm classification margin.

This is a small single-machine timing, not a large-raster throughput claim.
Footprints, edge construction and sparse pairs are in memory; unions/GEOS and
refinement cost grow with grid size, curvature and tighter tolerance. No tiling,
large-raster memory validation or global/polar/dateline coverage is provided.

### Preserved runtime and final checks

- `PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 /workspace/.floodcat-venv/bin/python /workspace/work/m2a-2/smoke_app.py`
  — exit 0. The retained temporary AppTest harness passed default Synthetic demo
  and all six sections; REAL — WRI at 0 m / 1 m (1,206.56 / 430.13 km²), three
  download controls, missing-asset warning and switch back to Synthetic demo.
  Existing Streamlit bare-context/width warnings remain. No browser download
  clicks, hosted deployment or new dashboard behavior claimed.
- `UV_CACHE_DIR=/workspace/.floodcat-cache uv pip check --python /workspace/work/m2a-3/venv/bin/python`
  — all **37** science-environment packages compatible.
- `UV_CACHE_DIR=/workspace/.floodcat-cache uv pip check --python /workspace/.floodcat-venv/bin/python`
  — all **35** original-runtime packages compatible, without installing science
  packages in that environment.
- `git diff --exit-code origin/main -- app.py requirements.txt src/floodcat/aggregation.py src/floodcat/exposure.py src/floodcat/demo.py src/floodcat/wri.py src/floodcat/wri_view.py src/floodcat/exports.py data tests/test_aggregation.py tests/test_exposure.py tests/test_demo.py tests/test_wri.py`
  — exit 0. `git diff --check` and staged whitespace checks passed.

Accuracy is empirically validated for the stated fixtures, not formally bounded
for arbitrary projections. The method is regional, uses WGS84 without datum
shifts and rejects unsupported boundaries/failed refinement. Exact real GHSL WKT,
mask semantics, source vintage, usable coverage and raster-scale performance are
still unverified. See [REMAPPING.md](REMAPPING.md) for the scientific contract,
explicit missingness/uncertainty and next single task.

## M2B-1 source verification and blocked real acquisition (2026-11-10)

Confirmed `prasadOS/FloodCAT`, fetched remote `main` at
`222577b7e213ccd6fb15b4ac5ce31f3f1311cfff` (merged PR #3), and created
`m2b-1-real-exposure-acquisition`. Final remote check returned the same main SHA.
The working branch was not based on the previous feature branch.

### Source and access evidence

- Managed cloud observations were current/ready; HTTP policy was enforced and
  restricted to package-manager/GitHub hosts. No Earth Engine credentials or
  outbound Earth Engine identity were reported in managed configuration. No
  credential files were read and no Earth Engine/provider authentication attempted.
- Six bounded direct HTTPS probes to official catalog/WorldPop/JRC websites and
  storage hosts at **2026-11-10 07:51:08 UTC** failed with proxy CONNECT
  **403 Forbidden**. No policy/proxy/TLS bypass or dataset-host fallback attempted.
  Exact URLs/outcomes are in `config/exposure_access_status.json`.
- Official Google catalog source was available independently on permitted GitHub:
  `git clone --depth 1 https://github.com/google/earthengine-catalog.git /workspace/work/m2b-1/official-catalog`
  — exit 0. Read commit `e69b2b9006b4313120b32d8a68b051732a88fbec`, including legacy
  WorldPop, R2025A v1, version table, GHSL built surface, units and SPDX definitions.
  Per-document links/checksums and verified claims are recorded in the access
  status. Catalog source hashes are not dataset hashes.
- Verified catalog distinctions: deprecated legacy WorldPop version 0.1 versus
  settlement-constrained/nationally adjusted R2025A v1; people/cell and CC BY 4.0;
  GHSL total built-up m² per 100 m cell versus NRES, producer release R2023A and
  reuse/source-acknowledgement terms. Generic GHSL `proprietary` metadata means
  non-standard license (open or closed), not a closed-data finding. Exact native
  files/WKT/masks/valid zeros, legacy model/adjustment mapping and artifact notices
  remain unverified. The pinned catalog lacks those native metadata fields.
- Revalidated WRI checksum, decoded shape/dtype/pixel support, affine and snapped
  bounds: 48×58, float32 metres, EPSG:4326,
  `(1/120,0,85,0,-1/120,25.85)`, east **85.48333333333333°E**, 3,801 bytes,
  SHA-256 **9d5c2747166f7cdecb84a7067575b311a4d4552cc2cd5ee482b924159bd91ebc**.
  1,222 valid dry zeros, 1,562 positive cells and no nodata are unchanged.

### Isolated optional packages

The original application and M2A-3 environments were retained unchanged.

```sh
UV_CACHE_DIR=/workspace/.floodcat-cache uv venv --python /workspace/.floodcat-venv/bin/python /workspace/work/m2b-1/venv
UV_CACHE_DIR=/workspace/.floodcat-cache uv pip install --python /workspace/work/m2b-1/venv/bin/python -r requirements.txt -r requirements-science.txt 'rasterio==1.4.4'
```

Both exited 0. Python **3.11.17**, Rasterio **1.4.4**, GDAL **3.10.3**,
NumPy 2.4.6, pyproj 3.7.2 / PROJ 9.5.1, Shapely 2.1.2 / GEOS 3.13.1.
The isolated environment has **42 packages**. Relative to the 37-package science
environment, new packages are Rasterio 1.4.4, affine 3.0.1, click-plugins 1.1.1.2,
cligj 0.7.2 and pyparsing 3.3.3. Requests 2.34.2 and Pillow 13.0.0 already existed
and are explicitly declared by `requirements-acquisition.txt` as direct tools.
Hosted `requirements.txt` is unchanged. No CLIMADA/Earth Engine package added.

### Exact focused and regression results

- Baseline `PYTHONDONTWRITEBYTECODE=1 /workspace/work/m2a-3/venv/bin/python -m unittest discover -s tests -v`
  — **55 passed**, no failures/errors/skips, in **3.540 s**.
- `PYTHONDONTWRITEBYTECODE=1 /workspace/work/m2b-1/venv/bin/python -m unittest discover -s tests -p test_acquisition.py -v`
  — **16 passed**, no failures/errors/skips, in **0.291 s**. Earlier 14-/15-test
  stages also passed; the final stage adds separate uint16 built-up-like window
  preservation as well as float32 population-like data. A final metadata-output
  annotation was subsequently covered by the complete run below.
- Final full suite:
  `PYTHONDONTWRITEBYTECODE=1 /workspace/work/m2b-1/venv/bin/python -m unittest discover -s tests -v`
  — **71 passed**, no failures, errors or skips, in **3.782 s**. Includes all
  **55 regressions + 16 acquisition tests**.
- Final lightweight runtime:
  `PYTHONDONTWRITEBYTECODE=1 /workspace/.floodcat-venv/bin/python -m unittest discover -s tests -v`
  — 71 discovered in **0.045 s**: **42 passed, 29 optional tests skipped**.
  This is runtime isolation evidence, not a complete scientific run.
- `PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 /workspace/.floodcat-venv/bin/python /workspace/work/m2a-2/smoke_app.py`
  — exit 0. All six synthetic sections; REAL — WRI 0 m / 1 m metrics
  (1,206.56 / 430.13 km²), three downloads, missing-asset warning and return to
  Synthetic demo passed. Existing Streamlit warnings remain. No hosted build or
  browser download clicks tested.
- `UV_CACHE_DIR=/workspace/.floodcat-cache uv pip check --python /workspace/work/m2b-1/venv/bin/python`
  — all **42** optional-environment packages compatible.
- `UV_CACHE_DIR=/workspace/.floodcat-cache uv pip check --python /workspace/.floodcat-venv/bin/python`
  — all **35** original-runtime packages compatible.
- Rasterio emitted pending-deprecation warnings for its affine `*` operations
  with affine 3.0.1; no failing assertions or numerical discrepancies occurred.

The acquisition fixtures make no real network calls. The in-memory HTTP fixture
requires exact 206/Range/Length/ETag, checks anonymous requests and cache reuse,
and rejects redirects, whole-response 200, weak/changed ETags, compression,
truncation, incorrect headers, unsupported hosts/credential URLs and byte caps.
Review tests reject unverified templates before requests/output, wrong product
or release (including silent R2025A/NRES changes), incomplete licensing/mask
review and native metadata/scaling mismatches. Metadata-only inspection is
separate from pixel/mask read permission and does not establish usable coverage.

Independent native fixtures check an exact 8×7 selection including two-cell halo,
source extent clipping, pixel budgets, preservation of raw values/dtype/nodata,
valid zero versus masked pixels, NaN, fractional-mask rejection and sum overflow.
The float32 fixture's hand-known subtotal is **1,843** (one valid zero, two masked
cells); the uint16 Mollweide surface-like fixture's is **1,110** (one valid zero,
one masked cell). Neither is actual exposure data. A separate 4,097-samples-per-edge
check contains the **actual WRI boundary** with at least 1.99 native halo cells
in a synthetic 100 m Mollweide grid. Native TIFF hashes/readback/masks and atomic
failure output are checked; the actual WorldPop/GHSL WKT remains unknown.

### Inventory and expected blocked commands

`PYTHONDONTWRITEBYTECODE=1 /workspace/work/m2b-1/venv/bin/python -m scripts.acquire_exposure_windows`
— exit 0: actual WRI reference plus candidate inventory, no network/acquisition.

The following both exited **2**, reporting unverified selection/licensing/masks
and `acquisition_published=false`, before any HTTP request or output dataset:

```sh
/workspace/work/m2b-1/venv/bin/python -m scripts.acquire_exposure_windows --source worldpop_2020_ind --review config/exposure_review_template.json --inspect
/workspace/work/m2b-1/venv/bin/python -m scripts.acquire_exposure_windows --source worldpop_2020_ind --review config/exposure_review_template.json --output /workspace/work/m2b-1/not-acquired
```

Asserted `/workspace/work/m2b-1/not-acquired` does not exist. No live source review
was marked successful, and no native source/derived dataset is committed.

`git diff --exit-code origin/main -- app.py requirements.txt src/floodcat/wri.py src/floodcat/wri_view.py src/floodcat/exposure.py src/floodcat/aggregation.py src/floodcat/remapping.py src/floodcat/demo.py src/floodcat/exports.py tests/test_wri.py tests/test_demo.py tests/test_exposure.py tests/test_aggregation.py tests/test_remapping.py data`
— exit 0; existing engines, app, requirements, tests and all assets are unchanged.
`git diff --check` and staged whitespace checks passed.

**Phase 2 is blocked and phase 3 has not run:** no real source totals, retained or
clipped contributions, conservation errors, valid-zero counts/coverage or real
threshold exposure results are available. The complete suite preserves M2A
fixture evidence without presenting it as real integration. See
[ACQUISITION.md](ACQUISITION.md) for source/licensing details, native-window
restrictions, remaining verification and the next single task.

## M2B-2 manual GitHub Actions access check (2026-11-10)

Repository confirmed as `prasadOS/FloodCAT`. `git fetch origin main` obtained
`5e9687e` (merged PR #4); branch `m2b-2-actions-data-access-check` starts there.
Read AGENTS, acquisition/source/status/evidence guidance and the existing native
acquisition/HTTP code. No application, scientific engine, acquisition, dependency
or asset changes are part of this milestone.

### Local validation

- Baseline:
  `PYTHONDONTWRITEBYTECODE=1 /workspace/work/m2b-1/venv/bin/python -m unittest discover -s tests -v`
  — **71 passed**, no failures/errors/skips, **3.750 s**.
- New standard-library-only tests:
  `PYTHONDONTWRITEBYTECODE=1 /workspace/.floodcat-venv/bin/python -m unittest discover -s tests -p test_provider_access.py -v`
  — **14 passed**, no failures/errors/skips, **0.012 s**. Tests cover default
  HEAD-only plans, no guessed filenames, exact one-byte ranges, ignored/encoded/
  malformed/truncated range responses, zero body reads on failures, redirects,
  no auth/cookies, URL/credential rejection, DNS/TLS/proxy failures, shared byte
  budget, hard deadline, real HTTP parser/CONNECT cleanup and report redaction.
- The first local live diagnostic exposed a missing `flush` method on the
  bounded HTTP reader during proxy CONNECT cleanup. Fixed it and added a real
  HTTP parser/CONNECT regression fixture. Early mock-response/socket fixtures
  were also corrected before the final passing runs. No erroneous early report
  is treated as provider/network evidence.
- Final complete regression:
  `PYTHONDONTWRITEBYTECODE=1 /workspace/work/m2b-1/venv/bin/python -m unittest discover -s tests -v`
  — **85 passed**, no failures/errors/skips, **3.704 s** on Python 3.11.17
  (71 existing tests + 14 new).
- Lightweight environment:
  `PYTHONDONTWRITEBYTECODE=1 /workspace/.floodcat-venv/bin/python -m unittest discover -s tests -v`
  — **85 discovered**, **56 passed / 29 optional tests skipped**, **0.079 s**.
  New diagnostics do not require any pip dependencies.
- `/workspace/work/m2b-2/bin/actionlint .github/workflows/provider-access-check.yml`
  — exit **0**, no findings. Actionlint **1.7.7** was obtained from its official
  GitHub release in temporary tooling storage; the published archive SHA-256
  matched **023070a287cd8cccd71515fedc843f1985bf96c436b7effaecce67290e7e0757**.
  An initial Go-install attempt was unavailable (`Go: Unknown option: install`);
  the verified standalone binary provided the actual validation. No repository
  package/dependency files were changed or application packages installed.
- YAML parsed with existing PyYAML `BaseLoader`: **only workflow_dispatch**, job
  **ubuntu-latest**, **5-minute timeout**, **contents: read**, no secret references.
- Official v6 action refs were resolved with `git ls-remote --tags` and pinned:
  checkout `d23441a48e516b6c34aea4fa41551a30e30af803`, setup-python
  `ece7cb06caefa5fff74198d8649806c4678c61a1`, upload-artifact
  `b7c566a772e6b6bfb58ed0dc250532a479d7789f`. Checkout does not persist credentials.

### Local HTTP evidence is not GitHub-hosted evidence

`PYTHONDONTWRITEBYTECODE=1 /workspace/.floodcat-venv/bin/python -m scripts.check_provider_access --output /workspace/work/m2b-2/local-report`
— exit **0**, metadata report generated. All **six default HEAD requests** recorded
**proxy CONNECT 403**, no origin HTTP status and **zero body bytes read**. Optional
WorldPop/GHSL Range probes were skipped: no reviewed exact native TIFF URLs are
known or supplied. No redirects were followed and no authentication or alternate
access route attempted. The final table presentation was regenerated from these
captured observations without another provider request.

The diagnostic has a 5 s socket-operation timeout, 15 s hard per-request process
deadline, 16,385-byte consumed HTTP response cap per worker, maximum 10 requests
and maximum two discarded body bytes (only when both optional Range checks
validate exact 206/Range/Length). Wire/TLS/kernel buffering overhead is not a
measured byte count. Denials and protocol limits are outcomes, not retries.
No bodies or rasters are saved; artifacts contain JSON/Markdown metadata only.
A green diagnostic means report generation completed, not that all providers or
any raster products are available.

### GitHub execution status and manual handoff

**No GitHub-hosted run completed or is claimed.** `git ls-tree -r --name-only
origin/main .github/workflows` returned no files on the confirmed default main.
The official GitHub docs source
[`data/reusables/actions/workflow-dispatch.md`](https://github.com/github/docs/blob/main/data/reusables/actions/workflow-dispatch.md)
(blob SHA `682b9ab6b83987a010ab6c9475a927547823fc22`) states that this trigger only
receives events when the workflow is on the default branch. This new workflow
is only in an unmerged feature PR, and merging is forbidden by the task. That is
the precise current hosted-dispatch blocker; no automatic trigger, default-branch
mutation or bootstrap workaround was added.

After owner merge: **Actions → FloodCAT provider access check → Run workflow →
main → Run workflow**. Leave optional URLs blank until exact public native TIFF
identities are known. Inspect the completed summary and **provider-access-report**
artifact, including run/SHA/runner context. Retention is 14 days. Only completed
hosted-run observations can establish hosted endpoint/Range access; website HEAD
success is never raster availability or scientific source validation. See
[ACTIONS_ACCESS_CHECK.md](ACTIONS_ACCESS_CHECK.md) for the full instructions.

Existing hosted requirements, app, WRI calculations, M2A/M2B-1 source code,
original tests, acquisition review flags and datasets are unchanged. No CLIMADA,
real acquisition, source-value processing or deployment. `git diff --check`,
staged whitespace checks and the explicit unchanged-file comparison passed.

## M2C-1 actual uploaded Patna rasters (2026-11-10)

Started branch `m2c-1-validate-uploaded-rasters` from fetched remote main
`2ee214a`, after the three native uploads and merged PR #5. Read repository and
acquisition/exposure/remapping guidance. The optional M2B-1 environment was reused
unchanged; **no packages installed or upgraded** in this milestone.

### Real input evidence and export recipe

Read-only Rasterio inspection and independent SHA-256 checks found three real
little-endian BigTIFFs, no LFS pointers:

- WRI: 65×168, 13,086 bytes, EPSG:4326, float32, SHA-256
  `9983264d5f3ef2c4bebde726c9e6ab10715c2906996002e03ebe89f478f8da8c`.
- WorldPop: 644×1,672, 5,758,647 bytes, EPSG:4326, float32, SHA-256
  `1125b05a9fe37c741a7762ac5ec0d6977f73781f98d01cce7301fdb543d57fb9`.
- GHSL: 638×1,532, 1,741,467 bytes, actual WGS84 World Mollweide WKT resolving to
  ESRI:54009, float32, SHA-256
  `c4c5f4d188c58fae04d056caaedc0a9328d4d79d9d44c8b621a8b9f252432393`.

All declare nodata -9999, scale 1 / offset 0, and pixel-is-area. TIFF unit tags and
asset IDs are absent. The user supplied the export recipe during this task,
identifying exact historical WATCH T100, legacy WorldPop `IND_2020` and GHSL 2020
`built_surface`, native projection/affine export and toFloat/unmask(-9999,false).
The source operations are transcribed with explicit attribution/limitations in
`scripts/gee/export_patna_native.js`; raw hashes/units/IDs are bound in
`config/patna_upload_provenance.json`. No export task IDs or acquisition times
were provided; these remain null, not inferred from commit/processing times.
The recipe exports the 500 m buffered district **bounding rectangle**, not the
GAUL district polygon. This distinction governs all published results.

WRI's **2,030 overlapping pilot samples** (35×58) are bitwise equal: 2,030 equal,
maximum difference **0 m**. The new window starts at column 39, row 0; the pilot
overlap starts at column 0, row 13. This corroborates identity on the overlap;
full outside-overlap source identity is supported by the user-supplied recipe.

Real missingness: population 115,214 masked -9999 pixels, zero valid zeros;
GHSL 141,151 NaNs despite all-valid stored masks, 628,967 valid zeros. Availability
is stored-valid AND finite, with no raw rewriting/zero imputation. Full WKT,
affine, bounds, band/tag/value statistics and source known numeric sums are in
`data/processed_real/patna_common/validation.json`.

### Processing and numerical audit

Initial bounded feasibility check: actual 33,200-cell GHSL window to two WRI rows
built/applied in 9.666 s, peak process RSS 281,132 KiB. This supported strip
processing rather than a full million-polygon allocation. Population full-grid
feasibility completed in 1.194 s with 6,113 complete targets and exact known-source
retention at printed precision.

Full processing command (exit 0):

```sh
PYTHONDONTWRITEBYTECODE=1 /workspace/work/m2b-1/venv/bin/python -m scripts.validate_patna_uploads --output /workspace/work/m2c-1/processed
```

It reused M2A-2 population aggregation, M2A-3 physical-area maps through disjoint
row strips and M2A-1 strict-threshold exposure. Measured population time **1.065 s**;
GHSL **33 strips**, maximum **33,250 source cells**, sum of map/apply times
**269.739738 s**, maximum **9.433031 s** per strip. Peak process RSS
**318,128 KiB / 310.67 MiB**. No monolithic million-cell map or new runtime dependency.

The known population source extent is fully contained by WRI, independently
establishing expected clipping zero: **15,827,395.092694104 people** retained,
**0 balance error**. The first draft used a residual for clipping; corrected to
independent expected zero with an explicit extent guard and audited the real
source/retained equality. The spatial allocation arrays did not change.
Known GHSL source **244,426,882 m²** → retained **244,425,812.59697458 m²** + clipped
**1,069.4030445377978 m²**; balance error **1.913309097290039e-5 m²**, relative
**7.827735974188138e-14** (acceptance 1e-10 relative / 1e-6 absolute). Unknown source
values remain outside these known-subtotal conservation statements.

Audit command:

```sh
PYTHONDONTWRITEBYTECODE=1 /workspace/work/m2b-1/venv/bin/python -m scripts.validate_patna_uploads --output /workspace/work/m2c-1/processed --audit-only
```

Final exit **0**, `audit.json` **passed**. An initial real-cell comparison found
0.012514 m² default-to-0.1mm change, exceeding a provisional 0.001 m² / 1e-7
threshold. Additional 1µm checks on ten distributed/common-centre cells established
maximum default-to-1µm change **0.016614974905678537 m²** and maximum 0.1mm-to-1µm
change **0.004101151229406241 m²**. Declared sampled acceptance is max(0.1 m²,
1 ppm of target quantity) and refinement-to-refinement ≤0.01 m². The absolute
allowance is below the observed native 1 m² value quantization (all available
uploaded GHSL values checked integral). This is sampled convergence, not a global
bound or independent verification of shared PROJ/GEOS assumptions. Existing
M2A-3 analytic/quadrature tests provide the independent geometry evidence.
Independent direct real-grid threshold sums, source hashes, common-mask/readback
invariants and retained/clipped budgets all pass.

### Common domain and real exposure

Population complete: **6,113 cells**; built surface complete: **10,458 cells**;
joint complete common domain **6,113 cells / 4,730.679260130684 km²**,
**55.97985347985348%** of uploaded WRI cells. No geometrically uncertain cells in
this run. Common-domain population before threshold: **9,602,732.2571902**;
built-up **154,887,440.49699715 m²**. Known retained quantities outside common
cells remain separately reported, not redistributed.

Strict-threshold results (common domain only):

| Threshold m | Common flooded cells | Flooded km² | Estimated people | Built surface m² |
| ---: | ---: | ---: | ---: | ---: |
| >0 | 2,116 | 1,637.3100663957925 | 2,840,320.5021073623 | 32,216,343.94410771 |
| >1 | 264 | 204.14047819214085 | 438,591.0037895779 | 6,166,476.587884915 |
| >2 | 183 | 141.50462578269597 | 331,405.76219787373 | 4,659,542.437944938 |
| >5 | 55 | 42.48104781106 | 145,829.6454354833 | 2,169,140.9575118953 |

At those thresholds the full upload has 5,217 / 1,382 / 1,110 / 318 flooded cells;
**3,101 / 1,118 / 927 / 263** are excluded by joint missing coverage. These are
not complete district/upload totals. Flooded area uses the existing WRI WGS84
ellipsoid area helper, unchanged. No observed inundation, physical damage or
financial loss is inferred.

### Final regression and packaging

- Baseline `PYTHONDONTWRITEBYTECODE=1 /workspace/work/m2b-1/venv/bin/python -m unittest discover -s tests -v`
  — **85 passed**, no failures/errors/skips, **3.646 s**.
- Focused new tests:
  `PYTHONDONTWRITEBYTECODE=1 /workspace/work/m2b-1/venv/bin/python -m unittest discover -s tests -p test_patna_processing.py -v`
  — **7 passed**, no failures/errors/skips, **0.387 s** after the bundle was
  generated. Earlier pre-generation run had one explicit temporary skip; the
  committed-bundle test passes in final evidence.
- Final full suite:
  `PYTHONDONTWRITEBYTECODE=1 /workspace/work/m2b-1/venv/bin/python -m unittest discover -s tests -v`
  — **92 passed**, no failures/errors/skips, **4.269 s** (85 regressions + 7 new).
- Original lightweight runtime: same command with `/workspace/.floodcat-venv/bin/python`
  — 92 discovered, **56 passed / 36 optional tests skipped**, **0.078 s**.
- `PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 /workspace/.floodcat-venv/bin/python /workspace/work/m2a-2/smoke_app.py`
  — exit 0: all six synthetic sections, preserved WRI pilot 0/1 m metrics
  (1,206.56 / 430.13 km²), three downloads and missing-asset fallback passed.
- `UV_CACHE_DIR=/workspace/.floodcat-cache uv pip check --python /workspace/work/m2b-1/venv/bin/python`
  — all **42 installed packages compatible**; no packages changed. Existing
  Rasterio/affine pending-deprecation warnings were recorded, without failures.
- Explicit `git diff --exit-code origin/main -- app.py requirements.txt requirements-acquisition.txt requirements-science.txt src/floodcat/wri.py src/floodcat/wri_view.py src/floodcat/aggregation.py src/floodcat/remapping.py src/floodcat/exposure.py data/demo_real`
  — exit 0. Raw sources, working app, requirements and existing engines unchanged.

Checked raw/derived licenses and sizes before staging: the small derivative
retains WorldPop CC BY 4.0, JRC source-acknowledgement and WRI attribution/terms
with exact source IDs; no GAUL polygon is redistributed. `aligned_common.npz`
is **323,391 bytes**, SHA-256
`f807ca277167e027435845f00e02b239fb76d18c1020d2df58259e2db8548167`.
Validation/audit JSON and attribution notes keep the directory under 0.4 MiB.
This is a coarse-grid derivative, not additional large native copies. `git diff
--check` and staged whitespace checks passed.

Remaining limitations: user-attested export recipe without task IDs/acquisition
times or independent new source query; upstream GHSL NaN cause not established;
common-cell selection can bias regional interpretation; district boundary not
bundled; within-source-pixel exposure uniformity and whole-WRI-cell modeled
hazard assumptions remain. Smallest next step is a checksum-verified NumPy loader
and opt-in common-footprint REAL exposure panel with explicit coverage/exclusions.
See [PATNA_VALIDATION.md](PATNA_VALIDATION.md) for full findings and instructions.

During final validation remote main advanced to `7fe68c8` with an AGENTS-only
context/efficiency update. Read the new instructions and fast-forwarded the
uncommitted feature-branch base to that commit. Source rasters, engines and app
were unchanged, so the completed real processing/tests remain applicable.

Supplemental readback: inline Python loaded all three uploaded bands separately
with Pillow 13.0.0 and Rasterio 1.4.4. `np.array_equal(..., equal_nan=True)` was
**True for every sample in every file**, corroborating the recorded GHSL NaNs
and values through a second reader. This is a decoder cross-check, not independent
validation of dataset provenance or the physical projection model.

## M2C-2 · REAL common-footprint dashboard (2026-11-10)

Started from remote main `0040e09`. No data, scientific engines or dependencies
changed. New runtime files are `src/floodcat/patna.py`, `patna_view.py` and
`config/patna_dashboard_checksums.json`; routing changes are confined to `app.py`.
Documentation changes: README, PROJECT_STATUS, DEPLOYMENT and this test record.

Commands executed from repository root:

- Baseline `/workspace/work/m2b-1/venv/bin/python -m unittest discover -s tests -q`:
  **92 passed, 4.337 s**, no skips.
- Focused `PYTHONDONTWRITEBYTECODE=1 /workspace/.floodcat-venv/bin/python -m unittest discover -s tests -p test_patna_dashboard.py -v`:
  **5 passed, 1.202 s**. Includes checksum rejection for each artifact, missing
  files, failed audit, malformed JSON/object arrays/shape/masks/negative depth,
  independent hand-computed strict-threshold fixture with valid zero and missing
  exposure, real M2C-1 thresholds and Streamlit AppTest coverage/exclusion warnings.
- Full `PYTHONDONTWRITEBYTECODE=1 /workspace/work/m2b-1/venv/bin/python -m unittest discover -s tests -v`:
  **97 passed, 6.665 s**, no failures/errors/skips.
- Lightweight runtime, same full command with `/workspace/.floodcat-venv/bin/python`:
  **97 discovered: 61 passed, 36 optional science tests skipped, 1.092 s**.
- `PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 /workspace/.floodcat-venv/bin/python /workspace/work/m2a-2/smoke_app.py`:
  **exit 0**, six Synthetic sections, WRI 0/1 m metrics, three downloads,
  missing-pilot warning and return to Synthetic preserved.
- `/workspace/.floodcat-venv/bin/python -m streamlit run app.py --server.headless true --server.port 8501`:
  server starts; `curl -s http://localhost:8501/_stcore/health` returns **ok**.
  Playwright with installed `/usr/bin/chromium` loads the live app, switches to
  REAL Patna, and confirms calculated population, both Plotly charts and CSV
  controls render. Screenshot inspected. Initial bare Chromium `--dump-dom`
  could not create its default profile directory; Playwright's temporary profile
  works without package installation.

At >0 m the new loader/summary reproduces 2,840,320.5021073623 estimated people,
32,216,343.94410771 m² built surface, 1,637.3100663957925 km² / 2,116 common flooded
cells, with 3,101 excluded flooded cells. These are recalculated from arrays, not
copied from validation summaries. Coverage is 6,113/10,920 (55.98% by cell count).
No new conservation/remapping is performed; unchanged M2C-1 budgets and scientific
limitations remain applicable. The view verifies all three artifact hashes on
each render; no cache can hide replacement/corruption between renders.

Final browser follow-up caught stale Synthetic sidebar controls after mode switch.
A shared sidebar placeholder now replaces the Synthetic controls in the real
exposure view. AppTest additionally requires exactly one sidebar slider/radio.
Final rerun: **97 passed, no skips, 6.578 s** with the full science command above;
preserved-mode smoke script again exits 0. Playwright explicitly waits for one
slider after switching and confirms the stable real view (both maps/downloads).

A fresh native server session also exposed an environment-only read-only
`/home/agent/.streamlit` telemetry identity write. For the final live check a
scratch-only launcher stubs Streamlit's telemetry UUID getter and disables usage
statistics on port 8502; no application or installed package is patched and no
home directory or credentials are written. This limitation does not affect
AppTest or the scientific arrays. Bare Chromium's profile failure is likewise
avoided by Playwright's temporary profile. These are cloud smoke-harness
adaptations, not deployment changes.

## M2C-3 · two-mode interface / native-cell OSM map (2026-11-10)

Base: latest remote main `a071692`. Direct-main commit/push explicitly authorized
by the task; no force-push. No source/processed rasters, checksum pins, scientific
engines or Python requirements changed. Leaflet 1.9.4 JS/CSS/license vendored from
pinned npm URLs; JS/CSS SHA-256 match upstream SRI pins. See [UI_MAPS.md](UI_MAPS.md)
for exact display assumptions, screenshots, performance and tile-policy caveats.

Commands (repository root; Python 3.11.17):

- Baseline `PYTHONDONTWRITEBYTECODE=1 /workspace/work/m2b-1/venv/bin/python -m unittest discover -s tests -q`:
  **97 passed, 7.232 s**, no skips.
- Focused `PYTHONDONTWRITEBYTECODE=1 /workspace/.floodcat-venv/bin/python -m unittest discover -s tests -p 'test_patna_*.py' -v`:
  **17 discovered: 10 passed / 7 optional raster-pipeline skips, 1.344 s**.
  An initial run caught a stale test expectation for coverage now in a caption;
  updated the assertion, preserving the actual coverage check.
- Full `PYTHONDONTWRITEBYTECODE=1 /workspace/work/m2b-1/venv/bin/python -m unittest discover -s tests -v`:
  **102 passed, 6.298 s**, no failures/errors/skips.
- Lightweight runtime, same full command using `/workspace/.floodcat-venv/bin/python`:
  **102 discovered: 66 passed / 36 optional science skips, 1.234 s**.
- `UV_CACHE_DIR=/workspace/.floodcat-cache uv pip check --python /workspace/.floodcat-venv/bin/python`:
  **35 installed packages compatible**, no installs or upgrades.
- `FLOODCAT_URL=http://localhost:8503 FLOODCAT_SCREENSHOTS=/workspace/work/m2c-3 node tests/browser/patna_map.cjs`:
  **exit 0**, all native-bounds/first-last-cell, zoom +/−, wheel, pan, fit, layer,
  click popup, failed-tiles canvas, CSV control and desktop/mobile checks passed.
  Initial real map readiness 2,542 ms, native draws 8.6/6.2 ms desktop, 2.9 ms mobile.
  Actual initial OSM requests were blocked; deterministic smoke aborts tiles.
  Scratch telemetry adaptation for read-only home documented in UI_MAPS; no hosted
  build or successful OSM tile access is claimed.

New independent hand fixture includes depths exactly 0, 1, 2, 5 m, >5 m,
valid zero built surface, NaN and missing exposure. Expected band populations
10/20/30/40, areas 2/3/4/5, built surface 0/2/3/4 and counts 1/1/1/1 pass;
threshold >2 keeps only 30+40, >8 is empty. Real band sums reconcile all four
quantities to engine totals at 0, .25, 1, 1.5, 2, 4.75, 5, 8 m with acceptance
1e-12 relative / 1e-8 absolute. Map payloads preserve every native float value,
all 65×168 cells and mask values, and compare against independently specified
source bounds at 1e-12 degrees. Existing audit/conservation tests still pass.

AppTest visits all six modules in both exact mode options, checks real domain,
coverage/exclusion labels and pilot downloads, strict-threshold population changes
and missing/invalid artifact warnings. Existing checksum/failed audit/malformed
array rejection remains tested. Raw uploaded rasters and all existing engines
remain unchanged. Real bundle loading/summary imports no Rasterio/Shapely/pyproj.

Final publication checks: raw/processed data, scientific engines, checksum pins
and all requirements compare unchanged to `a071692`. `.gitattributes` preserves
vendored upstream bytes (including CRLF/SRI) and recognizes their line endings;
staged `git diff --check` passes. Remote main was re-fetched and still matched the
base before the normal direct-main commit/push. No history rewriting.

## M2C-4 · depth-weighted exposure screening (2026-11-10)

Base: latest fetched remote main `0e28a4f`. Direct-main implementation/commit/push
is explicitly authorized. Raw/processed data, checksum pins, conservative engines,
M2A-1 exposure calculations, Synthetic implementation and all requirements remain
unchanged. No package installed or added. New calculations are diagnostics on
verified common cells, not vulnerability/impact estimation.

Commands run from repository root with Python 3.11.17:

- Baseline `PYTHONDONTWRITEBYTECODE=1 /workspace/work/m2b-1/venv/bin/python -m unittest discover -s tests -q`:
  **102 passed, no skips, 6.955 s**.
- Focused `PYTHONDONTWRITEBYTECODE=1 /workspace/.floodcat-venv/bin/python -m unittest discover -s tests -p 'test_patna_*.py' -v`:
  **23 discovered: 16 passed / 7 optional native-science skips, 1.577 s**.
- Final screening-focused `PYTHONDONTWRITEBYTECODE=1 /workspace/.floodcat-venv/bin/python -m unittest discover -s tests -p 'test_patna_screening.py' -v`:
  **6 passed, no skips, 1.078 s**.
- Final full `PYTHONDONTWRITEBYTECODE=1 /workspace/work/m2b-1/venv/bin/python -m unittest discover -s tests -v`:
  **108 passed, no failures/errors/skips, 7.501 s**.
- Lightweight runtime, same full command with `/workspace/.floodcat-venv/bin/python`:
  **108 discovered: 72 passed / 36 optional science skips, 2.712 s**.
- `UV_CACHE_DIR=/workspace/.floodcat-cache uv pip check --python /workspace/.floodcat-venv/bin/python`:
  **35 installed packages compatible**, no dependency changes.
- Live server: scratch launcher invokes Streamlit CLI on port 8505, disables usage
  statistics and stubs only its telemetry UUID getter because the cloud home is
  read-only. No product/package patch. Browser tests deliberately abort OSM tiles,
  reusing the already-established tile-failure limitation rather than retrying
  blocked provider access.
- `FLOODCAT_URL=http://localhost:8505 FLOODCAT_SCREENSHOTS=/workspace/work/m2c-4 node tests/browser/patna_map.cjs`:
  **exit 0**, preserved native bounds/values, +/−, wheel, pan, fit, three layer
  selectors, native cell popup, failed-tiles fallback, CSV controls and mobile
  dimensions. Added assertions for the weighted layer/legend and actual top-cell
  product; incomplete native cells expose null population/products.
- `FLOODCAT_URL=http://localhost:8505 FLOODCAT_SCREENSHOTS=/workspace/work/m2c-4 node tests/browser/patna_screening.cjs`:
  **exit 0**, weighted default layer, native population/product popup, actual
  indicator and priority CSV contents including units/domain/threshold/context,
  empty >8 m selection, no incomplete rankings, mobile layout and no JS errors.
  Weighted draw 26.6 ms desktop / 4.1 ms mobile in this fresh-server run (small
  single-grid observations, not performance guarantees). Map 358 px at a 390 px
  mobile viewport, no horizontal overflow. Screenshot inspection and an explicit
  geometry assertion confirm Fit/layer-selector controls do not overlap.

Browser debugging: closed the sidebar before resizing to avoid an automatic-
collapse race in the old smoke harness; waited for the iframe before inspecting
it to avoid a streamed-render race. A long layer selector initially overlapped
Fit on mobile: labels now wrap inside a constrained panel. A fresh-server final
run avoids stale imported view code from an earlier live-development session;
CSV contents are checked from actual downloads, not button labels alone.

Independent hand fixture: depths [[0,1,2],[5,6,3]], common population
[[100,10,20],[0,missing,20]], built surface [[10,4,0],[8,missing,2]]. At >0,
expected products are **110 person-metres** and **50 m²·m**. At thresholds
1 / 2 / 3 / 5 / 8, products are **100/46, 60/46, 0/40, 0/0, 0/0**. Exact
threshold equality, flooded valid-zero population/built-up, missing and NaN depth,
overflow rejection, stable ranking ties and cell-centre coordinates pass.
Independent Python iteration over actual source arrays checks sums at >0/1/2/5/8
(absolute comparison 1e-8 person-metres / 1e-7 m²·m); native-cell map products are
validated against exact per-cell multiplication with float64 arithmetic.

Actual >0 m diagnostics: **2,923,557.7298654984 person-metres** and
**35,969,112.45142127 m²·m**, explicitly not flood volume or damage. Highest cell
row 12 / col 88: 5.435956001281738 m × 5,126.351453354646 people =
27,866.62094754255 person-metres at 85.4125°E / 25.6375°N. Fixed >1/2/5 m population
values reproduce M2C-1. Existing zero-threshold metrics, coverage/exclusions,
all six Synthetic modules, REAL Hazard/pilot/downloads/Compare, failed bundle
checks and prior conservation/remapping regressions pass unchanged.

REAL navigation tests require exactly the six requested modules, exclude Depth
severity, and verify its depth-band CSV/charts under Exposure with optional table.
UI tests enforce the non-vulnerability heading, person-metres/m²·m labels, UNDRR
references, formulas and empty-threshold behavior. See
[formulas, limitations and screenshots](DEPTH_WEIGHTED_SCREENING.md).
Hosted deployment and successful ordinary OSM basemap access are not claimed.

## M2D blocked input gate (2026-11-10)

Branch `data/patna-multiscenario`, starting `7d40099`.

- `PYTHONDONTWRITEBYTECODE=1 /workspace/work/m2b-1/venv/bin/python -m scripts.validate_multiscenario_inputs --output config/patna_multiscenario_validation.json`: expected exit **2**, 15 inputs, 14 source-identity blockers. Exact grids match; candidate common footprint 6,113.
- Same interpreter, `-m unittest discover -s tests -p test_multiscenario_inputs.py -v`: **3 passed, 0.045 s**. Actual reproducibility/blocking, renamed-identical-file identity rejection and shifted/different-CRS geometry rejection.
- Same interpreter, `-m unittest discover -s tests -v`: **111 passed, no skips, 6.787 s**. Prior audits, arithmetic, masks, conservation and AppTest regressions pass.
- No multi-scenario browser acceptance or deployment test: app is deliberately unchanged and new scenarios are not activated. No claim of completed M2D integration.

Source-selection ambiguity requires stopping under AGENTS.md. Only Historical T100 has a matching committed export recipe; matching geometry/order cannot authenticate the other filenames. See M2D_INPUT_VALIDATION.md.
