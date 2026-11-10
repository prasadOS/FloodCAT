# FloodCAT M1B deployment manifest

Prepared 2026-11-10. Publication requires owner approval. The ZIP is a portable file snapshot of the M1B package.

## Repository layout

| Files | Role |
| --- | --- |
| `app.py`, `requirements.txt`, `.streamlit/config.toml`, `src/floodcat/*.py` | Runtime entry point, five pinned direct dependencies, theme and application modules |
| `data/demo_real/patna_wri_watch_t100.tif`, `data/demo_real/patna_wri_watch_t100.json` | Optional as a pair. Required for REAL — WRI. Synthetic mode needs neither. |
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

Choose the approved GitHub repository and branch, set the entry point to `app.py`, and select Python 3.11 in Advanced settings. The root `requirements.txt` pins Streamlit, NumPy, pandas, Plotly, and Pillow to the tested local versions. No secrets or OS packages are required by the app. Include the two WRI files together to enable real mode. When either is absent, real mode shows a missing-data warning and the synthetic demo remains selectable. [Community Cloud deployment](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy) · [Dependency setup](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies)

After approval, confirm the first hosted build and inspect the real map, attribution and downloads. The current smoke evidence is from Windows.
