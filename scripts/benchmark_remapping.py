"""Run from repository root: python -m scripts.benchmark_remapping.

Only fabricated extensive totals on a 32x32 100 m Mollweide grid near Patna;
target is a 6x6 native-resolution WRI-style EPSG:4326 grid. No data acquisition.
Timings include one cold geometry build and two applications of the cached map.
"""

import json
import math
import platform
from time import perf_counter

import numpy as np
import pyproj
import shapely

from src.floodcat.remapping import RasterGrid, WORLD_MOLLWEIDE, build_conservative_map


def main():
    x, y = pyproj.Transformer.from_crs(4326, WORLD_MOLLWEIDE, always_xy=True).transform(85.2, 25.7)
    # 100 m lattice consistent with the catalog-inspected GHSL affine origin.
    # This does not establish the exact CRS/mask of any future acquired asset.
    source = RasterGrid((32, 32), (100, 0, 100*math.floor(x/100)-1600,
                                  0, -100, 100*math.ceil(y/100)+1600), WORLD_MOLLWEIDE)
    step = 1/120
    target = RasterGrid((6, 6), (step, 0, 85.2-3*step, 0, -step, 25.7+3*step), "EPSG:4326")
    start = perf_counter()
    mapping = build_conservative_map(source, target)
    built_at = perf_counter()
    people = mapping.apply(np.full(source.shape, 1.25))
    built = mapping.apply(np.full(source.shape, 250.))
    applied_at = perf_counter()
    population_total = math.fsum(people.known_values.ravel())
    built_total = math.fsum(built.known_values.ravel())
    assert abs(population_total-1280) < 1280*1e-10
    assert abs(built_total-256000) < 256000*1e-10
    print(json.dumps({
        "python": platform.python_version(), "pyproj": pyproj.__version__,
        "proj": pyproj.proj_version_str, "shapely": shapely.__version__,
        "geos": shapely.geos_version_string,
        "source_shape": source.shape, "target_shape": target.shape,
        "build_seconds": built_at-start, "two_apply_seconds": applied_at-built_at,
        "intersection_pairs": len(mapping.source_indices),
        "footprint_vertices": mapping.footprint_vertices,
        "complete_target_cells": int(people.valid.sum()),
        "uncertain_target_cells": int(people.geometry_uncertain.sum()),
        "population_known_total": population_total, "built_known_total_m2": built_total,
        "population_relative_error": abs(population_total/1280-1),
        "built_relative_error": abs(built_total/256000-1),
        "max_source_allocation_error": float(np.max(np.abs(mapping.source_allocated_fraction-1))),
        "source_cell_area_range_m2": [float(mapping.source_area_m2.min()),
                                      float(mapping.source_area_m2.max())],
        "edge_tolerance_m": mapping.edge_tolerance_m,
        "max_segment_m": mapping.max_segment_m,
        "boundary_margin_m": mapping.boundary_margin_m,
    }, indent=2))


if __name__ == "__main__":
    main()
