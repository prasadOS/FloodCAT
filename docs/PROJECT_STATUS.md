# FloodCAT project status

## Current milestone · M2D — merged multi-scenario dashboard

PR #8 was merged into `main` at `c7d33ea1cf6aff3b72e7645b03e9920c53567536`.
M2D implementation and GitHub integration are complete; live Streamlit deployment
has not been independently verified.

The user supplied exact source-selection/export evidence after the initial gate
stopped. Fifteen user-attested, hash-bound source selections are compatible with
the official catalog schema; completed-task identities/live per-asset properties
are not independently authenticated. All native grids match exactly; independent
Pillow decoding matches all processed arrays. Reuse of audited extensive exposure
requires no remapping. Fixed all-scenario common footprint remains 6,113 cells.

All REAL selectors/modules/exports and genuine multi-scenario Compare are wired,
with fixed 2020 exposure and explicit CMIP5/RCP terminology. Historical T100
benchmarks, original audits/raw files and dependencies are unchanged. Compact
products and checksum loader fail closed. See [full scenario findings](M2D.md).
Source attestation limitations remain scientific qualifications, not a pending
GitHub integration. Completed GEE tasks/live per-asset properties and observational
calibration or independent flood-impact validation have not been independently
verified. Next task: verify the live Streamlit application; no live deployment
claim follows from the merge.

## Historical M2D attempt — resolved missing-recipe blocker (2026-11-10)

This records the initial state, not a current integration blocker. On
`data/patna-multiscenario` at `7d40099`, 15 rasters passed native geometry/numeric
checks, but 14 had no matching export recipe/source-selection provenance.
Only Historical T100 was then identified by the committed M2C-1 recipe, so
scenario activation stopped. The subsequently supplied user-attested recipes
resolved that missing-evidence gate; the completed implementation is now merged.
See [source evidence and remaining qualifications](M2D_INPUT_VALIDATION.md).
The common footprint remained 6,113 cells; raw data, the original audited bundle
and hosted dependencies were preserved.

## Previous milestone · M2C-4 — depth-weighted exposure screening (2026-11-10)

Started from freshly fetched remote main `0e28a4f`. User authorized tested commits
and normal pushes directly to main. REAL navigation is exactly Overview, Hazard,
Exposure, Vulnerability, Compare, Data & methods. Synthetic remains unchanged.
Depth-band charts/CSV live under Exposure; detailed numerical tables are optional.

Vulnerability is explicitly **depth-weighted exposure screening, not a validated
vulnerability model**. It shows fixed >1/2/5 m population totals and selected-depth
products in person-metres and m²·m (not flood volume/building damage). A selectable
sequential orange/red native-cell layer and Top 10 complete flooded raster-cell
ranking expose the same products. Coordinates are cell centres, not community
rankings. No coefficients, damage ratios, casualty estimates or annualized impacts
are inferred. Formulas and UNDRR/impact-methodology references are documented.

At >0 m, Σ(population × depth) = 2,923,557.7298654984 person-metres and
Σ(built_surface_m² × depth) = 35,969,112.45142127 m²·m. Existing 0 m exposure,
55.98% coverage and 3,101 excluded flooded cells are unchanged. Missing cells stay
unavailable. Source rasters, processed bundle/checksums, remapping/conservation
engines and hosted requirements are unchanged. No packages added.

See [screening definitions/evidence](DEPTH_WEIGHTED_SCREENING.md) and
[test results](TEST_RESULTS.md). No new scientific blocker for this qualified
screening; actual vulnerability, neighborhood-level risk and genuine impacts
remain unmodeled. OSM access was previously blocked in this cloud; deterministic
browser tests deliberately abort tiles and verify the independent overlays.
Hosted deployment and successful basemap access are not claimed. Next single
task: verify the updated six REAL modules and ordinary OSM tiles in the hosted
app, retaining the common-footprint and non-vulnerability qualifications.

## Previous milestone · M2C-3 — two-mode UI and geographic maps (2026-11-10)

Started from latest remote main `a071692`; user authorized tested commits directly
to main without force-push. Exactly two modes: Synthetic Demo (default), REAL —
Patna; all six modules are available in each. The formerly separate small WRI
pilot remains a hazard reference/download expander inside REAL — Patna.

Real results reuse the unchanged checksummed/audited arrays and M2A-1 exposure
engine. Four KPIs and compact coverage/exclusion qualification replace the large
banners. Depth bands reconcile at strict thresholds; Compare uses historical T100
thresholds only. Exact domain/source/mask/budget/uncertainty details and CSVs are
in Data & methods and expanders.

Locally bundled Leaflet 1.9.4 (BSD-2-Clause) provides OSM basemap, native-cell depth
and joint-coverage layers, scroll zoom, pan, +/−, fit and native-cell hover/click.
The canvas renderer projects geographic cell boundaries for display only; no
resampling or scientific processing is added. No Python dependencies changed.
Browser tests verify alignment, all interactions and desktop/mobile fallback.
**Actual OSM tile access is blocked by this cloud's network policy**; overlays
remain visible. Basemap success and hosted deployment are not claimed.
See [map design/evidence](UI_MAPS.md) and [test results](TEST_RESULTS.md).

Remaining scientific limitations are unchanged: partial common-cell selection,
no district-only polygon, export task metadata gaps, unknown upstream GHSL NaN
cause and sampled geometric accuracy. Next single task: verify ordinary OSM tile
loading and the two modes in the deployed Community Cloud app; avoid bulk tile
requests and review OSM policy if usage grows.

## Previous milestone · M2C-2 — first REAL exposure dashboard (2026-11-10)

Started from latest remote main `0040e09` containing merged M2C-1. Added a
third opt-in **REAL — Patna common-footprint exposure** mode. Synthetic remains
the default; the historical small WRI pilot and all processing engines are unchanged.
A separate repository manifest pins SHA-256 of all three processed artifacts.
The NumPy-only loader requires a passing audit, checks array/grid/mask/area
invariants and rejects invalid bundles with a useful warning. `allow_pickle=False`
is mandatory. No dependencies were added or hosted requirements changed.

The UI recalculates strict-threshold exposure with M2A-1, uses the existing WRI
area helper, and displays depth plus joint-coverage maps, exposure/area/counts,
prominent coverage and excluded flooded cells, attribution, limitations and two
CSV downloads. Display rounding does not affect downloaded precision.
These are complete common-cell screening estimates in the uploaded buffered
bounding rectangle, **not district totals or observed damage**. No missing value
is imputed. M2C-1 provenance uncertainties and selection bias remain; there is
no new scientific blocker for this explicitly restricted screening view.

See [test evidence](TEST_RESULTS.md). Next single task: review the feature PR
and run the three modes in the hosted app after an owner-approved deployment.
District-only analysis still requires the exact boundary and a separate validation.

## Previous milestone · M2C-1 — validated real common-footprint bundle (2026-11-10)

Started from remote main `2ee214a`; fast-forwarded the feature-branch base to
`7fe68c8` after an AGENTS-only update arrived during validation.
All three uploads are genuine readable BigTIFFs, not LFS pointers. The new WRI
65×168 grid matches all 2,030 pilot-overlap values exactly. User-supplied native
Earth Engine export operations identify exact bands/assets and bind source hashes;
WorldPop units are people/cell and GHSL total built surface is m²/cell.

Population has 115,214 masked pixels and no valid zeros; GHSL has 141,151 NaNs
although its stored mask is all-valid. Missingness is retained, never zero-filled.
Bounded strips reuse M2A-3 on actual Mollweide WKT; M2A-2 handles population and
M2A-1 computes strict-threshold exposure. All existing engines/app are unchanged.

The complete common domain is 6,113 WRI cells / 4,730.679 km², or 55.98% of the
uploaded grid. At >0 m it contains 2,840,320.502 estimated people and
32,216,343.944 m² built-up exposure. It excludes 3,101 of the upload's 5,217
flooded cells. These are bounding-rectangle common-cell metrics, not district
or whole-upload totals. The supplied recipe exports a buffered rectangle; the
GAUL district polygon is not bundled.

Known-source conservation balances: population exact at printed precision,
built-up relative error 7.83e-14. Processing uses at most 33,250 source cells per
strip, 33 strips / 269.74 s mapping time, 310.67 MiB peak RSS. Sampled real-data
refinement and independent threshold/readback audits pass. The compact NPZ is
323,391 bytes with source/derived SHA-256 and coverage/budget/provenance records.
See [full findings](PATNA_VALIDATION.md) and [test evidence](TEST_RESULTS.md).

The former next step, checksum-verified loading and an opt-in exposure panel,
is implemented in M2C-2 above. District-only
metrics require the exact polygon. Task IDs/times and the upstream NaN cause
remain unverified; no damage/financial model or new dependencies were added.

## Previous milestone · M2B-2 — manual Actions access diagnostic (2026-11-10)

Branch `m2b-2-actions-data-access-check` starts from freshly fetched remote `main`
`5e9687e`, containing merged PR #4. Added a Python 3.11, Ubuntu GitHub-hosted
`workflow_dispatch` workflow with no automatic triggers, provider credentials,
application dependencies or raster acquisition. Six fixed official endpoints
receive HEAD requests; optional exact approved TIFF URLs receive one-byte Range
checks, with no redirects/retries and strict byte/time limits. Metadata-only
reports distinguish origin status, proxy failures and untested raster availability.

All 85 tests pass in the complete optional environment (71 regressions + 14 new),
with no skips. `actionlint` and YAML trigger/permissions checks pass. The local
Codex probe records six proxy CONNECT 403 failures, zero body bytes read and no
Range test because no reviewed native TIFF URLs are known. Existing app,
requirements, scientific/acquisition engines and assets are unchanged.

**GitHub-hosted provider access remains unverified.** GitHub requires a
`workflow_dispatch` file on the default branch; no workflow existed on main at
the start, and this task leaves the new workflow in an unmerged PR. No hosted
run has completed. PR #5 was merged (`93114a9`); no hosted-provider access result is inferred from that merge. Manual handoff was Actions → FloodCAT
provider access check → Run workflow and review its artifact; successful website
access alone cannot establish raster availability. See [manual instructions and
limits](ACTIONS_ACCESS_CHECK.md) and [exact validation evidence](TEST_RESULTS.md).

## Previous milestone · M2B-1 — acquisition prepared, real access blocked (2026-11-10)

Branch `m2b-1-real-exposure-acquisition` starts from freshly fetched remote `main`
`222577b`, containing merged PR #3. The exact bundled WRI native footprint,
48×58 shape, EPSG:4326 affine and SHA-256 were independently rechecked.

Verified current product/units/version/licensing statements in Google's official
Earth Engine catalog source at pinned commit `e69b2b9`: legacy WorldPop is
deprecated; R2025A v1 is a distinct constrained/nationally adjusted release;
GHSL R2023A total `built_surface` is m² per 100 m cell, with reuse/source
acknowledgement terms. Direct producer sites and raster hosts were denied by the
cloud proxy (CONNECT 403). No Earth Engine credentials are configured. The exact
legacy public file/model mapping, native WKT, masks/valid zeros and real coverage
remain unverified. Catalog licensing is not a completed per-artifact review.

No exposure rasters acquired, aligned products created or real exposure totals
calculated. Added anonymous bounded Range access, two-stage metadata/mask review,
native-window extraction with a halo, exact metadata/mask preservation and
provenance/checksum reporting. Checked-in review templates cannot acquire data.
Optional Rasterio tools are isolated in `requirements-acquisition.txt`; the hosted
requirements, dashboard, WRI calculations and all M2A engines are unchanged.

Full optional-environment suite: **71 passed**, no skips (55 regressions + 16 new).
The unchanged application environment passes its 42 applicable tests and Streamlit
smoke checks; 29 optional tests skip there. See [source evidence and route](ACQUISITION.md),
[access status](../config/exposure_access_status.json) and [exact test results](TEST_RESULTS.md).

Next single task: resolve permitted producer access and exact native file/variant,
WKT and mask evidence, then perform bounded acquisition within the existing task
authorization. Phase 3 and a production REAL exposure dashboard remain unstarted.
M2B-1 was merged into `main` in PR #4 (`5e9687e`). Producer/raster access and real integration remain unverified.

## Previous engine milestone · M2A-3 (2026-11-10)

Branch `m2a-3-cross-crs-remapping` starts from freshly fetched remote `main`
`45d59d2`, which contains merged PR #2. Added reusable sparse physical-area
remapping between regional WGS84 CRSs, especially World Mollweide to EPSG:4326.
PROJ transforms adaptively densified pixel boundaries; GEOS intersects them in
ellipsoidal equal-area coordinates. Complete, partial, nodata, zero and boundary
uncertainty remain explicit, without redistribution or imputation.

The optional scientific requirements are NumPy, pyproj 3.7.2 and Shapely 2.1.2.
The hosted requirements, dashboard, M2A-1 exposure and M2A-2 aggregation sources,
original tests and bundled assets are unchanged. No real rasters acquired or
CLIMADA/vulnerability added. See [method, accuracy and limits](REMAPPING.md) and
[exact test evidence](TEST_RESULTS.md).

The full scientific suite has 55 passing tests (42 regressions + 13 new), with no
skips. The 32×32 100 m to 6×6 WRI-style fixture built in 0.261 s and applied twice
in 0.038 s; known totals conserved within 1.33e-15 relative error. Source area and
clipped budgets were checked independently of polygon area, with analytic
projection controls and a separate geodesic-area cross-check.

Validation is calculation-only and regional: empirical edge accuracy is not a
universal projection error bound, global/polar/dateline grids and datum shifts
are unsupported, and memory scaling remains unvalidated for large rasters.
Next single task: verify exact candidate source metadata and design a bounded
acquisition/processing plan before separately authorized raster acquisition.
M2A-3 was merged into `main` in PR #3 (`222577b`). Its source-verification next task is recorded above.

## Previous engine milestone · M2A-2 (2026-11-10)

Started branch `m2a-2-conservative-aggregation` from freshly fetched remote `main`
`84a7c63` (the M2A-1 merge), rather than the previous feature branch. Added an
independent NumPy area-overlap method for extensive population counts and built-up
m², with WGS84 ellipsoid or caller-verified shared equal-area coordinates. Offset
grids, resolution differences, target-extent clipping, source nodata and area
coverage are explicit. Partial target totals are NaN with a completeness mask;
known subtotals remain available without imputation or renormalization.

All 42 unit tests pass on Python 3.11.17: 18 new aggregation tests plus all 24
regressions. See [assumptions and API](EXPOSURE.md) and [exact evidence](TEST_RESULTS.md).
The M1B dashboard, WRI calculations, M2A-1 engine, dependencies and bundled assets
are unchanged. No real exposure data acquired, packages installed or CLIMADA added.

This is shared-CRS aggregation, not a completed native GHSL-to-WRI integration.
Cross-CRS grids are explicitly rejected. Next single task: validate conservative
cross-CRS remapping on in-memory fixtures before real GHSL acquisition/integration.
M2A-2 was merged into `main` in PR #2 (`45d59d2`). Its next task, cross-CRS remapping, is recorded above.

## Previous engine milestone · M2A-1 (2026-11-10)

Implemented an independent NumPy exposure engine on branch `feature/m2a-exposure-engine`. It accepts already aligned population counts and GHSL built-up m², uses strict valid-depth thresholds, preserves zero, and reports missing exposure and cell coverage separately for both measures. Complete totals remain unknown when flooded exposure is missing. All 24 unit tests pass in the prepared Python 3.11.17 environment, including the original 12 M1B tests. See [engine assumptions and API contract](EXPOSURE.md) and [test evidence](TEST_RESULTS.md).

No real exposure data were acquired or integrated. The application remains the M1B dashboard and REAL — WRI remains hazard-only. No WRI calculations or dependencies changed. M2A-1 was merged into `main` in PR #1 (`84a7c63`). Its original next task, M2A-2 aggregation, is recorded above. Deployment remains separate.

## Preserved application baseline · M1B (2026-11-10)

FloodCAT provides two local Streamlit modes. **Synthetic demo** is the default and retains the six illustrative sections. **REAL — WRI** is a hazard-only view backed by one genuine native-grid Patna historical WATCH T100 GeoTIFF. It displays modeled flood depth, thresholded area and counts, source metadata, and downloads. The GeoTIFF and JSON manifest are the only bundled real data assets.

Both app modes passed local smoke checks. The real view also passed with Earth Engine authentication disabled, and the complete suite has 12 passing tests. The owner independently verified the initial publication archive, SHA-256, and all 12 tests. See [test evidence](TEST_RESULTS.md) and [data sources](DATA_SOURCES.md).

The refreshed publication package is ready for owner review before GitHub upload and the first Community Cloud build. M1C has not started. Additional WRI scenarios and WorldPop/GHSL exposure remain outside the current implementation.

## Historical record · M0 portable reconstruction (2026-11-10)

- Initial source workspace: `D:\citi`, Conda environment `citi`, Python 3.11.18 reported working.
- User reported installed Streamlit, Pandas, NumPy and Plotly and a successful import check.
- The M0 archive contained only the synthetic six-module app, illustrative scenario and exposure models, seven tests, and deployment notes. It contained no source rasters.
- The M0 handover called for local extraction, testing and UI review before any publication. Those instructions described the starter phase.

## Earlier system, not restored
An agent's 2026-11-09 report described five WRI hazard configurations, WorldPop/GHSL exposure, CLIMADA arithmetic check and 50 passing tests on `E:\Citi`. These claims refer to the **previous inaccessible laptop**, and should not be displayed as this reconstruction's output.

## M1A (2026-11-10)

Live Earth Engine catalog inspection identified five exact WRI matches and both 2020 exposure assets. At that stage, the app used synthetic grids only. M1B subsequently checked the source mask and wet/dry coverage, then acquired the Patna historical WATCH T100 tile.

## Publication readiness (2026-11-10)

The first local publication snapshot pinned the tested runtime dependencies and documented the WRI redistribution terms. The refreshed snapshot includes a portable agent handover. See the [deployment manifest](DEPLOYMENT.md).
