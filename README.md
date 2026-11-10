# FloodCAT

FloodCAT is a Streamlit application for regional flood-hazard and physical exposure screening. **M1B** is the current verified milestone.

- **Synthetic demo** opens by default. It provides six sections with five illustrative depth scenarios, hypothetical population and built-up exposure, and CSV and JSON exports.
- **REAL — WRI** shows modeled riverine flood depth for one historical WATCH 100-year return-period tile near Patna. It reports thresholded flooded area and cell counts and provides GeoTIFF, source manifest, and summary CSV downloads. The view reads the bundled files locally without Earth Engine credentials. If either file is missing, it shows a warning and Synthetic demo remains selectable.

WRI depths support regional screening. Real population and built-up exposure, future scenarios, and local hydraulic validation remain outside M1B.

## Run locally

Clone the repository or extract the ZIP into a new folder. Open a terminal at the project root and activate an environment with Python 3.11 and the packages in `requirements.txt`.

```sh
python -m pip check
python -m unittest discover -s tests -v
python -m streamlit run app.py
```

Open [the local app](http://localhost:8501) and choose **Data mode → REAL — WRI** in the sidebar. At a threshold of 0 m, the summary reports 1,206.56 km² across 1,562 cells. Hover over a cell to inspect its depth. At 1 m, the flooded area drops to 430.13 km². The threshold changes the metrics, while the map displays all valid depths. Expand **Source and acquisition metadata** for the provenance. Press **Ctrl+C** in the terminal to stop the app.

## Deployment target

See the [deployment manifest](docs/DEPLOYMENT.md) for the publication file list, WRI redistribution terms, and Cloud settings.

After verifying the app locally, review the files before publishing. In [Streamlit Community Cloud](https://share.streamlit.io), choose the GitHub repo, branch, `app.py` entrypoint and a supported Python 3.11 runtime if offered. The platform installs `requirements.txt`. Include the approved compact GeoTIFF and manifest together to enable the real view, and verify the data-mode labels and download controls. Keep employer/client data and Earth Engine credentials local.

See [project status](docs/PROJECT_STATUS.md) for the verified milestones and pending work, and [data sources](docs/DATA_SOURCES.md) for source and raster details.
