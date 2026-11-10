# FloodCAT project status

## Current verified milestone · M1B (2026-11-10)

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
