"""CSV/JSON export utilities with honest metadata."""
import io
import json
import csv

def table_csv(rows):
    if not rows:
        return b""
    f=io.StringIO(newline="")
    writer=csv.DictWriter(f,fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return f.getvalue().encode('utf-8-sig')

def metadata_json(scenario, threshold):
    return json.dumps({
        "product":"FloodCAT demonstration", "dataset_type":"SYNTHETIC / hypothetical",
        "source":"Deterministic equations in src/floodcat/demo.py; no downloaded rasters",
        "scenario_label":scenario, "threshold_m":threshold,
        "depth_units":"metres (synthetic)",
        "exposure_units":"people per cell and km2 built-up per cell (synthetic)",
        "warning":"NOT WRI/WorldPop/GHSL; not observed, calibrated, or suitable for decisions",
    },indent=2).encode('utf-8')
