# FloodCAT

FloodCAT is a Streamlit application for regional flood-hazard and physical exposure screening. The interface has exactly two modes, each with **Overview, Hazard, Exposure, Depth severity, Compare, Data & methods**.

- **Synthetic Demo** is the default: deterministic, hypothetical hazard and exposure with illustrative scenarios, charts and CSV exports.
- **REAL — Patna** uses the unchanged audited M2C-1/M2C-2 common-footprint bundle. A strict depth threshold recalculates estimated people, built-up surface, flooded area/cells and excluded flooded cells. The Leaflet map overlays native WRI cells on OpenStreetMap, with selectable depth/coverage layers, zoom, pan, fit and native-cell hover/click. Missing tile access leaves the scientific layers usable. The verified small WRI pilot remains in Hazard and Data & methods as a reference with its original GeoTIFF, manifest and summary downloads.

**REAL metrics cover complete common WRI cells in the uploaded buffered bounding rectangle, not all of Patna district.** Coverage and exclusions remain visible on every real results page. These are modeled screening estimates, not observed impacts, measured damage or monetary loss. Depth-band totals reconcile to the selected strict threshold; Compare uses actual T100 thresholds, not invented climate scenarios.

The checksum loader pins all three processed artifacts, requires a passing audit and uses NumPy `allow_pickle=False`. Missing, changed or malformed artifacts display a warning instead of exposure results. No raw rasters or heavy geospatial packages are loaded by the new map. Hosted Python requirements remain unchanged; a pinned local Leaflet 1.9.4 distribution (BSD-2-Clause) adds no Python dependency or map token. [UI/map details, screenshots and limitations](docs/UI_MAPS.md).

Optional scientific processing remains isolated in `requirements-science.txt` and `requirements-acquisition.txt`; see [aggregation](docs/EXPOSURE.md) and [remapping](docs/REMAPPING.md).

**M2B-1:** official source-catalog facts and a tested bounded acquisition/validation route are documented in [ACQUISITION.md](docs/ACQUISITION.md). Direct producer acquisition was blocked in that milestone. M2C-1 subsequently validates user-uploaded exports below; this is distinct from a successful provider download. Optional tools use `requirements-acquisition.txt`.

**M2B-2:** a [manual GitHub Actions provider-access diagnostic](docs/ACTIONS_ACCESS_CHECK.md) is available for review. It runs only via `workflow_dispatch`, saves bounded HTTP metadata, and does not acquire rasters. GitHub-hosted access remains unverified until a real manual run is reviewed.

**M2C-1:** [uploaded real Patna rasters are validated](docs/PATNA_VALIDATION.md), with a compact audited common-cell exposure bundle. Metrics apply to complete cells in the export bounding rectangle, **not the district polygon or whole upload**. The verified bundle powers REAL — Patna.

- **REAL — Patna common-footprint exposure** loads checksum-pinned `aligned_common.npz`, `validation.json` and passing `audit.json` using NumPy with `allow_pickle=False`. It shows historical T100 depth and joint-coverage maps, a strict depth threshold, estimated population and built-up exposure, common flooded area/cells, excluded flooded cells and current/comparison CSV downloads. Metrics cover complete common WRI cells in the uploaded buffered bounding rectangle, **not all of Patna district**. Missing/changed/malformed artifacts disable this view with a warning. No raw-raster reads or heavy geospatial dependencies run in Streamlit.

## Run locally

Clone the repository or extract the ZIP into a new folder. Open a terminal at the project root and activate an environment with Python 3.11 and the packages in `requirements.txt`.

```sh
python -m pip check
python -m unittest discover -s tests -v
python -m streamlit run app.py
```

Open [the local app](http://localhost:8501), then choose **REAL — Patna** and a module in the sidebar. At >0 m, the common-footprint view reports 2,840,321 estimated people, 32.216 km² built surface, 1,637.31 km² flooded area and 2,116 flooded cells, with 55.98% joint cell coverage and 3,101 excluded flooded cells. Values are calculated from arrays, not hardcoded. At >1 m, estimated exposed people drop to 438,591. Expand Export summaries for CSVs, or Data & methods for provenance and conservation. In Hazard, expand the small pilot reference to retain the original 1,206.56 km² (>0 m) / 430.13 km² (>1 m) hazard comparison and source downloads. Press **Ctrl+C** to stop.

## Deployment target

See the [deployment manifest](docs/DEPLOYMENT.md) for the publication file list, WRI redistribution terms, and Cloud settings.

After verifying the app locally, review the files before publishing. In [Streamlit Community Cloud](https://share.streamlit.io), choose the GitHub repo, branch, `app.py` entrypoint and a supported Python 3.11 runtime if offered. The platform installs `requirements.txt`. Include the approved compact GeoTIFF and manifest together to enable the real view, and verify the data-mode labels and download controls. Keep employer/client data and Earth Engine credentials local.

See [project status](docs/PROJECT_STATUS.md) for the verified milestones and pending work, and [data sources](docs/DATA_SOURCES.md) for source and raster details.
