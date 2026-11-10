# FloodCAT project status

## Current engine milestone · M2A-2 (2026-11-10)

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
Changes are prepared for a PR targeting `main`; merging is outside this task.

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
