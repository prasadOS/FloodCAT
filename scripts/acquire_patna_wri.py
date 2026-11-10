"""Acquire only the native-grid Patna WATCH T100 pilot via Earth Engine."""

import argparse
from datetime import datetime, timezone
import hashlib
import json

import ee

from src.floodcat import wri


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--inspect-only", action="store_true")
    args = parser.parse_args()
    paths = [wri.ASSETS / name for name in (wri.TIFF, wri.MANIFEST)]
    if not args.inspect_only and any(path.exists() for path in paths):
        parser.error("Pilot output already exists")

    ee.Initialize(project=args.project)
    asset_id = f"{wri.COLLECTION}/{wri.IMAGE}"
    depth = ee.Image(asset_id).select(wri.BAND)
    rows, cols = wri.SHAPE
    dx, _, west, _, dy, north = wri.TRANSFORM
    bounds = [west, north + rows * dy, west + cols * dx, north]
    crs = "EPSG:4326"
    native = [dx, 0, -180, 0, dy, 90]
    geometry = ee.Geometry.Rectangle(bounds, crs, False)
    mask = depth.mask().unmask(0, False)
    classes = ee.Image.cat(
        mask.eq(0).rename("masked"),
        mask.gt(0).And(mask.lt(1)).rename("fractional_mask"),
        depth.eq(0).unmask(0, False).rename("valid_zero"),
        depth.gt(0).unmask(0, False).rename("positive"),
        depth.lt(0).unmask(0, False).rename("negative"),
    )
    grid = dict(geometry=geometry, crs=crs, crsTransform=native, maxPixels=20000)
    scenario = dict(floodtype="inunriver", climatescenario="historical",
                    model="000000000WATCH", year=1980, returnperiod=100)
    findings = ee.Dictionary(dict(
        properties=depth.toDictionary(list(scenario)),
        projection=depth.projection(),
        counts=classes.reduceRegion(ee.Reducer.sum().unweighted(), **grid),
        depth_range=depth.reduceRegion(ee.Reducer.minMax().unweighted(), **grid),
    )).getInfo()
    print(json.dumps(findings, indent=2), flush=True)
    counts = findings["counts"]
    if (findings["properties"] != scenario
        or findings["projection"]["crs"] != crs
        or findings["projection"]["transform"] != native
        or any(counts[key] for key in ("fractional_mask", "masked", "negative"))
        or not counts["positive"] or not counts["valid_zero"]
        or counts["positive"] + counts["valid_zero"] != rows * cols
    ):
        raise SystemExit("Stop: source identity, grid, or mask findings require review")
    if args.inspect_only:
        return

    payload = ee.data.computePixels(dict(
        expression=depth, fileFormat="GEO_TIFF", bandIds=[wri.BAND],
        grid=dict(
            dimensions=dict(width=cols, height=rows), crsCode=crs,
            affineTransform=dict(scaleX=dx, shearX=0, translateX=west,
                                 shearY=0, scaleY=dy, translateY=north),
        ),
    ))
    values, nodata = wri.decode_tile(payload)
    summary = wri.summarize(values, nodata, 0)
    if (summary["Flooded cells"] != counts["positive"]
        or summary["Valid dry cells"] != counts["valid_zero"]
        or summary["Nodata cells"] != counts["masked"]
        or summary["Maximum valid depth (m)"] != findings["depth_range"]["inundation_depth_max"]
    ):
        raise SystemExit(f"Stop: GeoTIFF and source pixel findings differ: {summary}")
    x0, y0, x1, y1 = wri.ROI
    manifest = dict(
        asset_id=asset_id, image_id=wri.IMAGE, scenario=scenario,
        provider="World Resources Institute (WRI)",
        attribution="World Resources Institute, Aqueduct Floods Hazard Maps Version 2, via Google Earth Engine",
        source_and_terms_url=wri.SOURCE, acquired_utc=datetime.now(timezone.utc).isoformat(),
        roi_wgs84=dict(type="Polygon", coordinates=[[[x0,y0],[x1,y0],[x1,y1],[x0,y1],[x0,y0]]]),
        grid_bounds_wgs84=bounds, edge_policy="Whole native cells covering the requested box",
        band=wri.BAND, units="m", crs=crs, transform=wri.TRANSFORM,
        shape=wri.SHAPE, dtype="float32", nodata=nodata,
        source_mask=counts, source_depth_range_m=findings["depth_range"],
        valid_pixel_fraction=1.0,
        mask_interpretation="Source-valid zero is modeled dry. The pilot has no masked cells.",
        sha256=hashlib.sha256(payload).hexdigest(),
    )
    wri.ASSETS.mkdir(parents=True, exist_ok=True)
    with paths[0].open("xb") as file:
        file.write(payload)
    with paths[1].open("x", encoding="utf-8") as file:
        json.dump(manifest, file, indent=2)
        file.write("\n")
    print(json.dumps(dict(bytes=len(payload), sha256=manifest["sha256"], summary=summary), indent=2))


if __name__ == "__main__":
    main()
