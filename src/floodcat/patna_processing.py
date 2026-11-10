"""Validate uploaded native rasters and prepare compact common-cell exposure.

Optional acquisition environment only. Source rasters are always read-only.
M2A engines are reused without changing their numerical/missingness contracts.
"""

from dataclasses import asdict
from datetime import datetime, timezone
import gc
import hashlib
import json
import math
from pathlib import Path
import time

import numpy as np
from pyproj import CRS
import rasterio
from rasterio.windows import Window, from_bounds
from rasterio.warp import transform_bounds

from .aggregation import GridSpec, AggregationResult, aggregate_extensive
from .remapping import RasterGrid, RemapResult, build_conservative_map
from .exposure import calculate_exposure
from . import wri

ROOT = Path(__file__).resolve().parents[2]
FILENAMES = {"hazard": "FloodCAT_Patna_WRI_Historical_T100.tif",
             "population": "FloodCAT_Patna_WorldPop_2020.tif",
             "built_surface": "FloodCAT_Patna_GHSL_BuiltSurface_2020.tif"}


def check_provenance(provenance):
    if sha256(ROOT/provenance["recipe_path"]) != provenance["recipe_sha256"]:
        raise ValueError("Export recipe changed; revalidate source provenance")
    expected = {"hazard": (wri.COLLECTION+"/"+wri.IMAGE, "m"),
                "population": ("WorldPop/GP/100m/pop/IND_2020", "people/cell"),
                "built_surface": ("JRC/GHSL/P2023A/GHS_BUILT_S/2020", "m2/cell")}
    for key, (asset, units) in expected.items():
        if provenance["sources"][key]["asset_id"] != asset or provenance["sources"][key]["units"] != units:
            raise ValueError("Source identity/units require explicit recipe verification")


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024*1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inventory(path):
    path = Path(path)
    with path.open("rb") as stream:
        signature = stream.read(256)
    if signature.startswith(b"version https://git-lfs.github.com/spec/v1"):
        raise ValueError(f"{path.name} is an LFS pointer, not raster bytes")
    if signature[:4] not in (b"II*\0", b"MM\0*", b"II+\0", b"MM\0+"):
        raise ValueError(f"{path.name} is not TIFF/BigTIFF")
    with rasterio.open(path) as ds:
        if ds.driver != "GTiff" or ds.count != 1 or ds.crs is None:
            raise ValueError("Expected one georeferenced real band")
        values, mask = ds.read(1), ds.read_masks(1)
        if not np.isin(mask, [0, 255]).all():
            raise ValueError("Fractional masks need separate interpretation")
        available = (mask == 255) & np.isfinite(values)
        if np.any(available & (values < 0)) or np.any((mask == 255) & np.isinf(values)):
            raise ValueError("Valid quantities must be finite/nonnegative; NaN is unavailable")
        if ds.scales != (1.,) or ds.offsets != (0.,) or ds.tags().get("AREA_OR_POINT", "Area") != "Area":
            raise ValueError("Packed or point-sampled data are unsupported")
        info = {"filename": path.name, "bytes": path.stat().st_size, "sha256": sha256(path),
                "format": "BigTIFF" if signature[:4] in (b"II+\0", b"MM\0+") else "TIFF",
                "shape": list(ds.shape), "bands": ds.count, "crs": ds.crs.to_string(), "crs_wkt": ds.crs.to_wkt(),
                "transform": list(ds.transform)[:6], "bounds": list(ds.bounds), "dtype": ds.dtypes[0],
                "nodata": "NaN" if ds.nodata is not None and math.isnan(ds.nodata) else ds.nodata,
                "mask_flags": [f.name for f in ds.mask_flag_enums[0]], "tags": ds.tags(),
                "band_tags": ds.tags(1), "band_description": ds.descriptions[0], "stored_unit": ds.units[0],
                "scales": list(ds.scales), "offsets": list(ds.offsets),
                "pixels": int(values.size), "declared_mask_invalid": int((mask == 0).sum()),
                "nan_pixels": int(np.isnan(values).sum()), "infinite_pixels": int(np.isinf(values).sum()),
                "available_pixels": int(available.sum()), "unavailable_pixels": int((~available).sum()),
                "valid_zero": int(np.count_nonzero(available & (values == 0))),
                "valid_positive": int(np.count_nonzero(available & (values > 0))),
                "minimum": float(values[available].min()), "maximum": float(values[available].max()),
                "known_numeric_sum": math.fsum(float(v) for v in values[available]),
                "native_array_bytes": int(values.nbytes+mask.nbytes)}
    return info, values, available


def pilot_overlap(depth, grid):
    pilot, _, manifest, *_ = wri.load_pilot()
    a, b, left, d, e, top = grid.transform
    if b or d or not CRS(grid.crs).equals(CRS(4326), ignore_axis_order=True):
        raise ValueError("WRI target must be north-up WGS84")
    if not np.allclose([a, e], [wri.STEP, -wri.STEP], rtol=0, atol=1e-12):
        raise ValueError("Uploaded WRI resolution differs from verified pilot")
    col_offset, row_offset = (85-left)/a, (25.85-top)/e
    if abs(col_offset-round(col_offset)) > 1e-8 or abs(row_offset-round(row_offset)) > 1e-8:
        raise ValueError("WRI pilot and uploaded grid are not aligned")
    co, ro = round(col_offset), round(row_offset)
    pr0, pc0 = max(0, -ro), max(0, -co)
    pr1, pc1 = min(pilot.shape[0], depth.shape[0]-ro), min(pilot.shape[1], depth.shape[1]-co)
    if pr1 <= pr0 or pc1 <= pc0:
        raise ValueError("No pilot overlap to check source identity")
    expected = pilot[pr0:pr1, pc0:pc1]
    actual = depth[pr0+ro:pr1+ro, pc0+co:pc1+co]
    delta = np.abs(actual.astype(float)-expected)
    return {"cells": int(expected.size), "shape": list(expected.shape),
            "equal_cells": int(np.count_nonzero(actual == expected)),
            "max_absolute_difference_m": float(delta.max()), "bitwise_equal_values": bool(np.array_equal(actual, expected)),
            "pilot_sha256": manifest["sha256"], "uploaded_window_col_row": [pc0+co, pr0+ro],
            "pilot_window_col_row": [pc0, pr0]}


def remap_strips(values, available, source_grid, target_grid, *, tile_rows=2,
                 max_source_cells=60000, progress=None):
    """Bounded source-window adapter around the unchanged M2A-3 engine.

    Disjoint target row strips; native source windows have two-cell halos.
    Source allocation fractions accumulate across strips for clipping budgets.
    Native coordinates are never snapped, reprojected by interpolation or filled.
    """
    if tile_rows < 1 or max_source_cells < 1:
        raise ValueError("Positive tile rows and source-cell cap required")
    if values.shape != source_grid.shape or available.shape != values.shape:
        raise ValueError("Source arrays/grid must match")
    if available.dtype != bool:
        raise ValueError("Availability must be boolean")
    st = rasterio.Affine(*source_grid.transform)
    tt = rasterio.Affine(*target_grid.transform)
    out_shape = target_grid.shape
    out = {"values": np.full(out_shape, np.nan), "known_values": np.zeros(out_shape),
           "valid": np.zeros(out_shape, dtype=bool), "source_coverage_fraction": np.zeros(out_shape),
           "valid_coverage_fraction": np.zeros(out_shape), "geometry_uncertain": np.zeros(out_shape, dtype=bool)}
    allocated = np.zeros(values.shape)
    timings, largest, row = [], 0, 0
    while row < out_shape[0]:
        height = min(tile_rows, out_shape[0]-row)
        while True:
            target_window = Window(0, row, out_shape[1], height)
            bounds = rasterio.windows.bounds(target_window, tt)
            projected = transform_bounds(target_grid.crs, source_grid.crs, *bounds, densify_pts=128)
            fraction = from_bounds(*projected, transform=st)
            c0, r0 = max(0, math.floor(fraction.col_off)-2), max(0, math.floor(fraction.row_off)-2)
            c1 = min(values.shape[1], math.ceil(fraction.col_off+fraction.width)+2)
            r1 = min(values.shape[0], math.ceil(fraction.row_off+fraction.height)+2)
            count = max(0, c1-c0)*max(0, r1-r0)
            if count <= max_source_cells:
                break
            if height == 1:
                raise ValueError("Even one target row exceeds source-cell cap; use a smaller target extent")
            height = max(1, height//2)
        start = time.perf_counter()
        if count:
            sw = Window(c0, r0, c1-c0, r1-r0)
            sg = RasterGrid((r1-r0, c1-c0), tuple(rasterio.windows.transform(sw, st))[:6], source_grid.crs)
            tg = RasterGrid((height, out_shape[1]), tuple(rasterio.windows.transform(target_window, tt))[:6], target_grid.crs)
            mapping = build_conservative_map(sg, tg)
            result = mapping.apply(values[r0:r1, c0:c1], source_valid=available[r0:r1, c0:c1])
            for name in out:
                out[name][row:row+height] = getattr(result, name)
            allocated[r0:r1, c0:c1] += mapping.source_allocated_fraction.reshape(sg.shape)
            del mapping, result
        largest = max(largest, count)
        timings.append(time.perf_counter()-start)
        row += height
        if progress:
            progress({"target_rows_done": row, "target_rows": out_shape[0], "source_cells": count,
                      "strip_seconds": round(timings[-1], 3)})
        gc.collect()
    if allocated.max() > 1+1e-8:
        raise ValueError("Strip overlap/source allocation exceeds numerical tolerance")
    return RemapResult(**out), allocated, {"strips": len(timings), "max_source_cells": largest,
                                          "strip_seconds_sum": math.fsum(timings), "max_strip_seconds": max(timings)}


def budget(values, available, retained, allocated=None):
    source = math.fsum(float(v) for v in values[available])
    kept = math.fsum(float(v) for v in retained.ravel())
    if allocated is None:
        # Independent expected zero, not the residual (which would be tautological).
        # Caller must verify complete containment of this source's extent.
        clipped = 0.
    else:
        clipped = math.fsum(float(v)*(1-min(1., float(f))) for v, f in zip(values[available], allocated[available]))
    error = kept+clipped-source
    if abs(error) > max(1e-6, abs(source)*1e-10):
        raise ValueError("Known-source conservation budget failed")
    return {"known_source_total": source, "known_retained_in_wri_extent": kept,
            "known_clipped_outside_wri_extent": clipped, "balance_error": error,
            "relative_balance_error": abs(error)/source if source else 0.,
            "unknown_source_pixels_excluded": int((~available).sum())}


def prepare(output, *, source_directory=ROOT/"data/demo_real", tile_rows=2, progress=None):
    output = Path(output)
    if output.exists():
        raise ValueError("Output directory already exists; refuse to replace evidence")
    provenance = json.loads((ROOT/"config/patna_upload_provenance.json").read_text())
    check_provenance(provenance)
    records, arrays, available = {}, {}, {}
    for key, name in FILENAMES.items():
        info, values, mask = inventory(Path(source_directory)/name)
        if info["sha256"] != provenance["sources"][key]["sha256"]:
            raise ValueError("Uploaded source checksum changed: revalidate provenance first")
        if info["band_description"] != provenance["sources"][key]["band"]:
            raise ValueError("Unexpected source band")
        records[key], arrays[key], available[key] = info, values, mask
    h = records["hazard"]
    grid = RasterGrid(tuple(h["shape"]), tuple(h["transform"]), h["crs_wkt"])
    overlap = pilot_overlap(arrays["hazard"], grid)
    if not overlap["bitwise_equal_values"]:
        raise ValueError("WRI overlap differs from verified historical WATCH T100")
    if not CRS(records["population"]["crs_wkt"]).equals(CRS(4326), ignore_axis_order=True):
        raise ValueError("Population must use its verified native WGS84 grid")
    pw, ps, pe, pn = records["population"]["bounds"]
    hw, hs, he, hn = h["bounds"]
    if not (hw <= pw <= pe <= he and hs <= ps <= pn <= hn):
        raise ValueError("Population clipping requires an explicit allocation budget; source is not fully contained")
    t = time.perf_counter()
    population = aggregate_extensive(arrays["population"],
        GridSpec(tuple(records["population"]["shape"]), tuple(records["population"]["transform"])),
        GridSpec(grid.shape, grid.transform), source_valid=available["population"])
    pop_seconds = time.perf_counter()-t
    built, allocation, timing = remap_strips(arrays["built_surface"], available["built_surface"],
        RasterGrid(tuple(records["built_surface"]["shape"]), tuple(records["built_surface"]["transform"]),
                   records["built_surface"]["crs_wkt"]), grid, tile_rows=tile_rows, progress=progress)
    common = available["hazard"] & population.valid & built.valid
    if not common.any():
        raise ValueError("No complete common WRI cells; exposure is unavailable")
    summaries = []
    area = wri.pixel_areas_km2(grid.transform, grid.shape[0])[:, None]*np.ones(grid.shape)
    for threshold in (0., 1., 2., 5.):
        result = calculate_exposure(arrays["hazard"], common, population.values, built.values, threshold,
                                    population_valid=population.valid, built_surface_valid=built.valid)
        summaries.append({"threshold_m": threshold, "flooded_area_km2": math.fsum(area[common & (arrays["hazard"] > threshold)]),
                          **asdict(result)})
    pop_budget = budget(arrays["population"], available["population"], population.known_values)
    built_budget = budget(arrays["built_surface"], available["built_surface"], built.known_values, allocation)
    for measure, totals, result in (("population", pop_budget, population), ("built_surface_m2", built_budget, built)):
        total_common = math.fsum(float(v) for v in result.values[common])
        totals["known_total_on_common_complete_cells"] = total_common
        totals["known_retained_outside_common_cells"] = totals["known_retained_in_wri_extent"]-total_common
    output.mkdir(parents=True)
    artifact = output/"aligned_common.npz"
    np.savez_compressed(artifact, depth_m=arrays["hazard"], valid_depth=available["hazard"], common_valid=common,
        population_count=population.values, population_known=population.known_values, population_valid=population.valid,
        population_source_coverage=population.source_coverage_fraction, population_available_coverage=population.valid_coverage_fraction,
        built_surface_m2=built.values, built_known_m2=built.known_values, built_valid=built.valid,
        built_source_coverage=built.source_coverage_fraction, built_available_coverage=built.valid_coverage_fraction,
        built_geometry_uncertain=built.geometry_uncertain)
    try:
        import resource, sys
        peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss if sys.platform.startswith("linux") else None
    except ImportError:
        peak_rss = None
    report = {"schema_version": 1, "created_utc": datetime.now(timezone.utc).isoformat(), "sources": records,
              "provenance": provenance, "pilot_overlap": overlap, "target_grid": asdict(grid),
              "domain": "Complete common WRI cells in the uploaded buffered bounding rectangle, NOT Patna district polygon",
              "common_cells": int(common.sum()), "common_area_km2": math.fsum(area[common]),
              "hazard_valid_cells": int(available["hazard"].sum()),
              "population_complete_cells": int(population.valid.sum()), "built_complete_cells": int(built.valid.sum()),
              "built_uncertain_cells": int(built.geometry_uncertain.sum()),
              "budgets": {"population": pop_budget, "built_surface_m2": built_budget}, "exposure": summaries,
              "performance": {"population_seconds": pop_seconds, "built": timing,
                              "peak_process_rss_kib_linux": peak_rss},
              "processed_artifact": {"path": artifact.name, "bytes": artifact.stat().st_size, "sha256": sha256(artifact)},
              "limitations": ["Export recipe is user-supplied, not independently re-run; task IDs/times unavailable",
                "GHSL stored mask is all-valid but NaNs are unavailable; no imputation",
                "Whole target cells with any missing or uncertain source coverage are excluded from common domain",
                "Not district-only statistics; the GAUL polygon is not bundled",
                "Uniform source-pixel exposure per physical area; exposure is not observed damage",
                "Geometric accuracy controls are empirical; 1 cm edge tolerance, 2 cm classification margin"]}
    (output/"validation.json").write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
    return report


def audit_bundle(output):
    """Cheap independent readback/budget checks and tighter real-cell geometry.

    Does not repeat full remapping. The threshold oracle directly sums selected
    cells without calling calculate_exposure. The geometric refinement is a
    convergence check, not an independent validation of projection assumptions.
    """
    output = Path(output)
    report = json.loads((output/"validation.json").read_text())
    check_provenance(report["provenance"])
    if sha256(output/"aligned_common.npz") != report["processed_artifact"]["sha256"]:
        raise ValueError("Processed bundle checksum mismatch")
    for key, info in report["sources"].items():
        if sha256(ROOT/"data/demo_real"/info["filename"]) != info["sha256"]:
            raise ValueError("Source bytes changed")
    with np.load(output/"aligned_common.npz", allow_pickle=False) as data:
        common = data["common_valid"]
        if np.any(common & ~(data["population_valid"] & data["built_valid"] & data["valid_depth"])):
            raise ValueError("Common mask contains unavailable cells")
        coverage = {"hazard_valid_cells":int(data["valid_depth"].sum()),"common_cells":int(common.sum()),
                    "excluded_cells_without_population":int((data["valid_depth"] & ~data["population_valid"]).sum()),
                    "excluded_cells_without_built_surface":int((data["valid_depth"] & ~data["built_valid"]).sum()),
                    "thresholds":[]}
        for row in report["exposure"]:
            wet = common & (data["depth_m"] > row["threshold_m"])
            all_wet = data["valid_depth"] & (data["depth_m"] > row["threshold_m"])
            coverage["thresholds"].append({"threshold_m":row["threshold_m"],
                "full_uploaded_hazard_flooded_cells":int(all_wet.sum()),"common_flooded_cells":int(wet.sum()),
                "excluded_flooded_cells":int((all_wet & ~common).sum()),
                "missing_population_flooded_cells":int((all_wet & ~data["population_valid"]).sum()),
                "missing_built_surface_flooded_cells":int((all_wet & ~data["built_valid"]).sum())})
            for name, key in (("population_count", "population"), ("built_surface_m2", "built_surface_m2")):
                total = math.fsum(float(v) for v in data[name][wet])
                if abs(total-row[key]["total_exposed"]) > max(1e-7, total*1e-12):
                    raise ValueError("Independent threshold sum differs")
        for name, totals in report["budgets"].items():
            key = "population_known" if name == "population" else "built_known_m2"
            kept = math.fsum(float(v) for v in data[key].ravel())
            if abs(kept-totals["known_retained_in_wri_extent"]) > max(1e-6, kept*1e-12):
                raise ValueError("Retained subtotal differs from stored array")
            residual = kept+totals["known_clipped_outside_wri_extent"]-totals["known_source_total"]
            if abs(residual) > max(1e-6, abs(totals["known_source_total"])*1e-10):
                raise ValueError("Conservation audit failed")
        pw,ps,pe,pn = report["sources"]["population"]["bounds"]
        hw,hs,he,hn = report["sources"]["hazard"]["bounds"]
        if not (hw <= pw <= pe <= he and hs <= ps <= pn <= hn):
            raise ValueError("Population expected-zero clipping is not geometrically established")
        if report["budgets"]["population"]["known_clipped_outside_wri_extent"] != 0:
            raise ValueError("Population full-source containment must have zero clipping")
        cells = np.argwhere(common)
        centre = np.asarray(common.shape)/2
        indices = sorted(set(np.linspace(0,len(cells)-1,9,dtype=int).tolist()+
                             [int(np.argmin(np.sum((cells-centre)**2,axis=1)))]))
        samples = [(int(cells[i,0]),int(cells[i,1]),float(data["built_surface_m2"][tuple(cells[i])])) for i in indices]
    h = report["sources"]["hazard"]
    tt = rasterio.Affine(*h["transform"])
    refinements = []
    with rasterio.open(ROOT/"data/demo_real"/FILENAMES["built_surface"]) as ds:
        for row, col, baseline in samples:
            target_window = Window(col,row,1,1)
            native = transform_bounds(h["crs_wkt"], ds.crs, *rasterio.windows.bounds(target_window, tt), densify_pts=128)
            f = from_bounds(*native, transform=ds.transform)
            c0, r0 = max(0, math.floor(f.col_off)-2), max(0, math.floor(f.row_off)-2)
            c1, r1 = min(ds.width, math.ceil(f.col_off+f.width)+2), min(ds.height, math.ceil(f.row_off+f.height)+2)
            sw = Window(c0, r0, c1-c0, r1-r0)
            values = ds.read(1, window=sw)
            amounts = []
            for tolerance in (.0001,.000001):
                m = build_conservative_map(RasterGrid(values.shape, tuple(ds.window_transform(sw))[:6], ds.crs.to_wkt()),
                    RasterGrid((1,1), tuple(rasterio.windows.transform(target_window,tt))[:6], h["crs_wkt"]),
                    edge_tolerance_m=tolerance, max_segment_m=1000)
                result = m.apply(values, source_valid=(ds.read_masks(1,window=sw)==255)&np.isfinite(values))
                if not result.valid[0,0]:
                    raise ValueError("Refined common cell is incomplete")
                amounts.append(float(result.values[0,0]))
            # 0.1 m² is below the source's 1 m² quantization. Relative tolerance
            # is 1 ppm for larger built-up totals. This is sampled convergence,
            # not a global error bound; independent geometry tests remain in M2A-3.
            if abs(amounts[1]-baseline) > max(.1, abs(baseline)*1e-6) or abs(amounts[1]-amounts[0]) > .01:
                raise ValueError("Real-cell refinement audit exceeds 0.1 m²/1 ppm or 0.01 m² convergence tolerance")
            refinements.append({"wri_row_col":[row,col],"default_built_m2":baseline,
                "refined_0_1mm_built_m2":amounts[0],"refined_1um_built_m2":amounts[1],
                "default_to_1um_absolute_difference_m2":abs(baseline-amounts[1]),
                "refinement_absolute_difference_m2":abs(amounts[0]-amounts[1])})
    import sys, pyproj, shapely
    audit = {"status": "passed", "ready_for": "Opt-in common-rectangle screening dashboard; not district-only metrics",
             "independent_threshold_sums": "passed", "source_checksums": "passed", "known_source_budgets": "passed",
             "coverage":coverage,
             "software":{"python":sys.version.split()[0],"numpy":np.__version__,"rasterio":rasterio.__version__,
                "gdal":rasterio.__gdal_version__,"pyproj":pyproj.__version__,"proj":pyproj.proj_version_str,
                "shapely":shapely.__version__,"geos":shapely.geos_version_string},
             "geometry_refinement": {"samples":refinements,
                "default_tolerance_m":.01,"refined_tolerances_m":[.0001,.000001],
                "absolute_acceptance_m2":.1,"relative_acceptance":1e-6,
                "note": "Sampled convergence only, shares PROJ/GEOS physical-area model; not a global accuracy bound"}}
    (output/"audit.json").write_text(json.dumps(audit,indent=2)+"\n")
    return audit
