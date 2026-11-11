# FloodCAT deployment manifest

Updated for M2C-3 on 2026-11-10. Git publication for this task is owner-authorized; hosted deployment has not been verified. Earlier ZIP references describe the historical M1B snapshot.

## Repository layout

| Files | Role |
| --- | --- |
| `app.py`, `requirements.txt`, `.streamlit/config.toml`, `src/floodcat/*.py` | Runtime entry point, five pinned direct dependencies, theme and application modules |
| `data/demo_real/patna_wri_watch_t100.tif`, `data/demo_real/patna_wri_watch_t100.json` | Optional pair for the small WRI pilot reference inside REAL — Patna. Synthetic mode needs neither. |
| `tests/test_demo.py`, `tests/test_wri.py` | Regression and raster checks |
| `scripts/inspect_gee_catalog.py`, `scripts/acquire_patna_wri.py` | Local-only acquisition tooling. The Earth Engine API is separate from Cloud requirements. |
| `config/scenarios.json`, `data/sample/README.md` | Synthetic scenario reference and sample directory description |
| `.gitignore`, `README.md`, `AGENTS.md`, `docs/DEPLOYMENT.md`, `docs/DATA_SOURCES.md`, `docs/DECISIONS.md`, `docs/PROJECT_STATUS.md`, `docs/TEST_RESULTS.md` | Publication and project documentation, including portable development instructions |

Keep `CLAUDE.md`, `START_HERE.txt`, and `docs/REAL_DATA_CODEX_TASK.md` in the local working copy. They describe workstation recovery and earlier handovers. Keep OAuth and service-account files, Streamlit secrets, environment exports and local env folders, caches, logs, temporary paths, output archives, and all other data out of the publication snapshot. Use the file list above to review the first staged tree. Ignore rules are supplemental and cannot recognize credentials stored under arbitrary names.

## Third-party data terms

The Earth Engine catalog terms for the exact WRI Aqueduct Floods Hazard Maps V2 collection permit use and distribution and request proper WRI attribution. WRI's Open Data Commitment names CC BY 4.0 as its standard data license. The catalog gives a dataset-specific distribution statement without naming a license identifier. Base publication of this exact subset on that statement and retain the provider, source links, and modification description. WRI lists the original Version 2 product separately. [Dataset-specific terms](https://developers.google.com/earth-engine/datasets/catalog/WRI_Aqueduct_Flood_Hazard_Maps_V2#terms-of-use) · [WRI Open Data Commitment](https://www.wri.org/data/open-data-commitment) · [WRI dataset listing](https://www.wri.org/data/aqueduct-floods-hazard-maps)

Attribution for the bundled file: World Resources Institute, Aqueduct Floods Hazard Maps Version 2, historical WATCH T100 riverine inundation depth, accessed via Google Earth Engine. FloodCAT extracted a native-grid Patna subset. Keep the matching source manifest beside the TIFF and retain in-app attribution and downloads. The tile is 3,801 bytes and SHA-256 is `9d5c2747166f7cdecb84a7067575b311a4d4552cc2cd5ee482b924159bd91ebc`.

FloodCAT code licensing is a separate owner decision. No source-code license file is present. Confirm publication rights before making a repository public, and choose a code license if reuse is intended.

## Community Cloud settings

Choose the approved GitHub repository and branch, set the entry point to `app.py`, and select Python 3.11 in Advanced settings. The root `requirements.txt` pins Streamlit, NumPy, pandas, Plotly, and Pillow to the tested local versions. No secrets or OS packages are required by the app. Include the compact processed artifacts and checksum manifest for REAL — Patna (below). The optional pilot needs its matching TIFF/JSON pair. Missing or invalid artifacts show warnings; Synthetic Demo remains selectable. [Community Cloud deployment](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy) · [Dependency setup](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies)

After a hosted build, inspect both modes, real map layers/OSM tiles, attribution and downloads. Current M2C-3 smoke evidence is from Linux, not a verified Community Cloud deployment.

## M2C-2 real common-footprint mode

Include `config/patna_dashboard_checksums.json` and all three unchanged files in
`data/processed_real/patna_common/` alongside application source. No raw uploaded
rasters or science dependencies are required by the new view. The loader verifies
SHA-256 on every render (under 0.4 MiB), then parses and validates the bundle.
Do not regenerate checksum pins merely to silence a failure: revalidate any new
scientific artifact and review its passing audit before updating the pins. Pins
protect against accidental corruption, not malicious repository changes.

## M2C-3 map assets and network

Ship `src/floodcat/static/native_map.html` and `src/floodcat/static/leaflet/`
(JS, CSS, license and source/hash notes). Leaflet is embedded locally: no CDN, API
key or Python package is required at runtime. Retain the BSD-2-Clause notice.
Only current-viewport OSM tiles use an external service,
`https://tile.openstreetmap.org/{z}/{x}/{y}.png`; retain visible OSM attribution
and follow its usage policy. Do not disable referrers, bypass limits, prefetch or
bulk-cache tiles. The app performs no tile downloads server-side. Scientific
layers and map controls remain usable if tile access fails; geographic context
is then limited to coordinates and the study raster. Large deployments should
review an appropriate tile service rather than assume unlimited OSM capacity.

## M2D scenario products

Include `config/patna_scenario_checksums.json` and both files in
`data/processed_real/patna_scenarios/`, in addition to the original M2C-1 bundle
and its three-file pins. The runtime does not open the 15 native rasters or import
Rasterio/pyproj/Shapely. Keep scenario validation/provenance documentation and WRI
attribution. Review source attestation limitations before integration. New artifacts
are compact WRI derivatives (~223 KiB combined), not additional raw copies.
