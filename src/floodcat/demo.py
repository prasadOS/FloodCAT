"""Deterministic, explicitly synthetic 1-km-ish flood/exposure grid.

No WRI, WorldPop or GHSL data are bundled. All demo arrays are hypothetical.
These utilities can later be replaced by validated raster-ingest functions.
"""
from dataclasses import dataclass
import numpy as np

SCENARIOS = (
    ("Historical | T25", "Historical", 25, "Synthetic"),
    ("Historical | T100", "Historical", 100, "Synthetic"),
    ("Historical | T500", "Historical", 500, "Synthetic"),
    ("Future RCP4.5 2050 | T100", "RCP4.5 / 2050", 100, "Synthetic"),
    ("Future RCP8.5 2050 | T100", "RCP8.5 / 2050", 100, "Synthetic"),
)
SCENARIO_NAMES = tuple(s[0] for s in SCENARIOS)
LAT_MIN, LAT_MAX = 25.45, 25.85
LON_MIN, LON_MAX = 85.00, 85.48
ROWS, COLS = 42, 48

@dataclass(frozen=True)
class DemoData:
    lat: np.ndarray
    lon: np.ndarray
    area_km2: np.ndarray
    people: np.ndarray
    builtup_km2: np.ndarray
    depths: dict


def cell_areas_km2(lat_edges, lon_edges):
    """Spherical Earth cell area; returns (lat,lon) area matrix in km²."""
    radius_km = 6371.0088
    lat_band = np.abs(np.diff(np.sin(np.radians(lat_edges))))
    lon_band = np.abs(np.diff(np.radians(lon_edges)))
    return radius_km ** 2 * np.outer(lat_band, lon_band)


def make_demo_data():
    lat_edges = np.linspace(LAT_MIN, LAT_MAX, ROWS + 1)
    lon_edges = np.linspace(LON_MIN, LON_MAX, COLS + 1)
    lat = (lat_edges[:-1] + lat_edges[1:]) / 2
    lon = (lon_edges[:-1] + lon_edges[1:]) / 2
    yy, xx = np.meshgrid(lat, lon, indexing="ij")
    area = cell_areas_km2(lat_edges, lon_edges)
    # Stylized east-west river channel with floodplain; not a physical hydraulic simulation.
    river = 25.65 + 0.028 * np.sin((xx - 85.0) * 12.0)
    distance = np.abs(yy - river)
    terrain = 0.010 * np.cos((xx - 85.0) * 19) + 0.006 * np.sin((yy - 25.45) * 29)
    effective_distance = np.maximum(0, distance + terrain)
    def depth(width, peak):
        return np.maximum(0.0, (1.0 - effective_distance / width)) ** 1.4 * peak
    d25 = depth(0.052, 2.2)
    d100 = np.maximum(d25, depth(0.073, 3.8))
    d500 = np.maximum(d100, depth(0.098, 5.0))
    d45 = np.maximum(d25, depth(0.084, 4.0))
    d85 = np.maximum(d45, depth(0.103, 5.4))
    # Synthetic settlement concentrations; counts and built-up area per cell.
    town1 = np.exp(-(((xx - 85.15) / 0.105) ** 2 + ((yy - 25.61) / 0.070) ** 2))
    town2 = np.exp(-(((xx - 85.33) / 0.072) ** 2 + ((yy - 25.71) / 0.046) ** 2))
    pattern = 0.12 + 1.55 * town1 + 1.2 * town2
    people = np.rint(1700 * pattern).astype(np.int64)
    builtup = np.minimum(area * 0.75, area * (0.03 + 0.43 * np.minimum(pattern / 2.5, 1)))
    return DemoData(lat=lat, lon=lon, area_km2=area, people=people,
                    builtup_km2=builtup, depths=dict(zip(SCENARIO_NAMES, (d25,d100,d500,d45,d85))))


def summarize(data, scenario, threshold=0.0):
    """Flooded means depth > threshold (strict), not >=."""
    d = data.depths[scenario]
    wet = np.isfinite(d) & (d > threshold)
    return {
        "Scenario": scenario,
        "Threshold (m)": float(threshold),
        "Inundated area (km²)": float(np.sum(data.area_km2[wet])),
        "Exposed people (synthetic)": int(np.sum(data.people[wet])),
        "Exposed built-up (km²)": float(np.sum(data.builtup_km2[wet])),
        "Max depth (m)": float(np.max(d[wet])) if np.any(wet) else 0.0,
        "Flooded cells": int(np.count_nonzero(wet)),
    }


def severity(data, scenario, threshold=0):
    d = data.depths[scenario]
    bands = [("0–1 m",0,1), ("1–2 m",1,2), ("2–5 m",2,5), (">5 m",5,np.inf)]
    rows=[]
    for label,lo,hi in bands:
        mask = (d > max(lo, threshold)) & (d <= hi) if lo==0 else (d > max(lo, threshold)) & (d <= hi)
        rows.append({"Depth band":label, "Area (km²)":float(data.area_km2[mask].sum()),
                     "People (synthetic)":int(data.people[mask].sum())})
    return rows
