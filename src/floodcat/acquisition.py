"""Verified, bounded native exposure windows; optional offline scientific tools.

No acquisition is permitted from the checked-in unverified source candidates.
See docs/ACQUISITION.md for review requirements and the current network blocker.
"""

from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import tempfile

import numpy as np
from pyproj import CRS
from pyproj.exceptions import CRSError
import rasterio
from rasterio.warp import transform_bounds
from rasterio.windows import Window, from_bounds

from . import wri
from .http_range import AcquisitionBlocked, HTTPRangeSource, public_url

SOURCES = {
    "worldpop_2020_ind": {
        "product_id": "WorldPop/GP/100m/pop/IND_2020", "epoch": 2020,
        "release": "legacy catalog 0.1", "band": "population", "units": "people/cell",
        "provider": "WorldPop", "allowed_hosts": ("data.worldpop.org",),
        "catalog_url": "https://developers.google.com/earth-engine/datasets/catalog/WorldPop_GP_100m_pop",
    },
    "ghsl_2020_built_surface": {
        "product_id": "JRC/GHSL/P2023A/GHS_BUILT_S/2020", "epoch": 2020,
        "release": "R2023A", "band": "built_surface", "units": "m2/cell",
        "provider": "European Commission Joint Research Centre", "allowed_hosts": ("jeodpp.jrc.ec.europa.eu",),
        "catalog_url": "https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_BUILT_S",
    },
}


def wri_reference():
    """Verify the bundled raster, checksum and exact snapped footprint first."""
    depth, nodata, manifest, payload, _ = wri.load_pilot()
    if (manifest["crs"] != "EPSG:4326" or tuple(manifest["shape"]) != depth.shape or
            not np.allclose(manifest["transform"], wri.TRANSFORM, rtol=0, atol=1e-12)):
        raise AcquisitionBlocked("WRI manifest grid differs from the decoded native grid")
    a, _, left, _, e, top = wri.TRANSFORM
    bounds = [left, top+e*depth.shape[0], left+a*depth.shape[1], top]
    if not np.allclose(bounds, manifest["grid_bounds_wgs84"], rtol=0, atol=1e-12):
        raise AcquisitionBlocked("WRI manifest bounds differ from native pixel support")
    return {"asset_id": manifest["asset_id"], "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload), "shape": list(depth.shape), "crs": manifest["crs"],
            "transform": list(wri.TRANSFORM), "bounds_wgs84": bounds,
            "dtype": str(depth.dtype), "nodata": nodata,
            "hazard_counts": {"valid_zero": int(np.count_nonzero(depth == 0)),
                              "positive": int(np.count_nonzero(depth > 0))}}


def verify_review(source_key, review, *, metadata_only=False):
    """Require explicit provider evidence, not catalog-footprint assumptions.

    Human evidence review is necessary; this validator cannot prove a declaration
    true. It prevents accidental acquisition from the blocked template or a silent
    change to R2025A/nonresidential GHSL. Actual raster metadata is checked too.
    """
    if source_key not in SOURCES:
        raise AcquisitionBlocked("Unknown source; product selection must be reviewed explicitly")
    spec = SOURCES[source_key]
    flag = "metadata_access_verified" if metadata_only else "verified"
    if not isinstance(review, dict) or review.get(flag) is not True:
        raise AcquisitionBlocked("Source selection, licensing and mask semantics remain unverified")
    for name in ("product_id", "epoch", "release", "band", "units"):
        if review.get(name) != spec[name]:
            raise AcquisitionBlocked(f"Reviewed {name} does not match the selected product")
    for name in ("verified_utc", "documentation_url", "product_evidence", "license_name", "license_url",
                 "attribution", "license_evidence", "variant_evidence"):
        if not isinstance(review.get(name), str) or not review[name].strip():
            raise AcquisitionBlocked(f"Missing reviewed evidence: {name}")
    try:
        timestamp = datetime.fromisoformat(review["verified_utc"])
    except ValueError as error:
        raise AcquisitionBlocked("A dated review is required") from error
    if timestamp.utcoffset() is None:
        raise AcquisitionBlocked("Review timestamp must include a timezone")
    if review.get("acquisition_permitted") is not True:
        raise AcquisitionBlocked("Source access permission must be established")
    if source_key == "worldpop_2020_ind" and review.get("population_adjustment") not in ("unadjusted", "UN_adjusted"):
        raise AcquisitionBlocked("Match the legacy image to a documented adjustment/model variant first")
    url = public_url(review.get("source_url"), spec["allowed_hosts"])
    if not url.lower().endswith((".tif", ".tiff")):
        raise AcquisitionBlocked("Only a reviewed single-band public GeoTIFF is supported, not an archive")
    if metadata_only:
        return spec
    if type(review.get("redistribution_permitted")) is not bool:
        raise AcquisitionBlocked("Acquisition permission and an explicit redistribution decision are required")
    for name in ("mask_evidence", "zero_evidence", "dtype", "crs_wkt"):
        if not isinstance(review.get(name), str) or not review[name].strip():
            raise AcquisitionBlocked(f"Missing reviewed evidence: {name}")
    try:
        crs = CRS.from_wkt(review["crs_wkt"])
    except CRSError as error:
        raise AcquisitionBlocked("Actual source CRS WKT is required") from error
    if (review.get("pixel_support") != "area" or review.get("mask_storage") != "internal_or_nodata" or
            review.get("zero_semantics") != "valid_unless_masked"):
        raise AcquisitionBlocked("Pixel support, stored masks and valid-zero semantics must be established")
    resolution = np.asarray(review.get("resolution_native"))
    if resolution.shape != (2,) or resolution.dtype.kind not in "iuf" or not np.all(np.isfinite(resolution) & (resolution > 0)):
        raise AcquisitionBlocked("Actual native pixel resolution is required")
    flags = review.get("mask_flags")
    if not isinstance(flags, list) or not flags or any(f not in ("all_valid", "nodata", "per_dataset") for f in flags):
        raise AcquisitionBlocked("Actual binary mask storage flags must be reviewed")
    if "nodata" not in review:
        raise AcquisitionBlocked("Declare source nodata explicitly (null, a number, or NaN string)")
    nodata = review["nodata"]
    if nodata is not None and nodata != "NaN" and (
            isinstance(nodata, bool) or not isinstance(nodata, (int, float)) or not math.isfinite(nodata)):
        raise AcquisitionBlocked("Nodata must be null, a finite number, or the NaN string")
    if source_key == "worldpop_2020_ind" and not crs.equals(CRS(4326), ignore_axis_order=True):
        raise AcquisitionBlocked("Legacy WorldPop candidate must have its verified WGS84 native grid")
    if source_key == "ghsl_2020_built_surface":
        if (not crs.is_projected or crs.coordinate_operation.method_name != "Mollweide" or
                not np.allclose(resolution, [100, 100], rtol=0, atol=1e-8) or
                any(abs(a.unit_conversion_factor-1) > 1e-12 for a in crs.axis_info)):
            raise AcquisitionBlocked("GHSL must be actual 100 m World Mollweide, not a fixture assumption")
    return spec


def inspect_source(source_key, review, *, max_bytes=2*1024**2):
    """Read bounded native metadata after product/license access review only.

    No exposure samples or mask pixels are read. This supplies actual WKT,
    nodata and stored-mask flags for the subsequent scientific semantics review;
    stored metadata alone does not prove source-valid coverage or valid zeros.
    """
    spec = verify_review(source_key, review, metadata_only=True)
    remote = HTTPRangeSource(review["source_url"], spec["allowed_hosts"], max_bytes=max_bytes)
    try:
        with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR"):
            with rasterio.open(remote.url, opener=remote.opener) as dataset:
                nodata = dataset.nodata
                result = {"mode": "metadata_only_no_pixel_or_mask_read", "source_key": source_key,
                          "shape": list(dataset.shape), "count": dataset.count, "driver": dataset.driver,
                          "dtype": list(dataset.dtypes), "crs_wkt": dataset.crs.to_wkt() if dataset.crs else None,
                          "transform": list(dataset.transform)[:6], "resolution_native": list(dataset.res),
                          "nodata": "NaN" if nodata is not None and math.isnan(nodata) else nodata,
                          "mask_flags": [[f.name for f in flags] for flags in dataset.mask_flag_enums],
                          "scales": list(dataset.scales), "offsets": list(dataset.offsets),
                          "units": list(dataset.units), "descriptions": list(dataset.descriptions),
                          "area_or_point": dataset.tags().get("AREA_OR_POINT"),
                          "sidecar_discovery": "disabled; metadata describes only the reviewed GeoTIFF object",
                          "source_url": remote.url, "source_etag": remote.etag,
                          "source_size_bytes": remote.size, "http_payload_bytes": remote.transferred_bytes,
                          "coverage_and_mask_semantics": "unverified"}
        return result
    finally:
        remote.close()


def validate_raster(dataset, review):
    """Check actual native metadata before reading exposure pixels."""
    if dataset.driver != "GTiff" or dataset.count != 1 or dataset.crs is None:
        raise AcquisitionBlocked("Expected the reviewed single-band native GeoTIFF")
    if not CRS(dataset.crs.to_wkt()).equals(CRS.from_wkt(review["crs_wkt"]), ignore_axis_order=True):
        raise AcquisitionBlocked("Actual source CRS differs from reviewed WKT")
    t = dataset.transform
    if t.b != 0 or t.d != 0 or t.a <= 0 or t.e >= 0:
        raise AcquisitionBlocked("This acquisition route requires the native north-up source grid")
    if not np.allclose([t.a, -t.e], review["resolution_native"], rtol=0, atol=1e-10):
        raise AcquisitionBlocked("Source resolution differs from review")
    if dataset.dtypes[0] != review["dtype"] or np.dtype(dataset.dtypes[0]).kind not in "iuf":
        raise AcquisitionBlocked("Source dtype differs from review or is not real numeric")
    expected = review["nodata"]
    actual = dataset.nodata
    if expected == "NaN":
        same_nodata = actual is not None and math.isnan(actual)
    else:
        same_nodata = actual == expected
    if not same_nodata:
        raise AcquisitionBlocked("Actual nodata differs from reviewed semantics")
    if sorted(flag.name for flag in dataset.mask_flag_enums[0]) != sorted(review["mask_flags"]):
        raise AcquisitionBlocked("Actual mask storage differs from review")
    if dataset.scales != (1.,) or dataset.offsets != (0.,):
        raise AcquisitionBlocked("Packed/scaled exposure needs a separately reviewed conversion")
    if dataset.tags().get("AREA_OR_POINT", "Area").lower() != "area":
        raise AcquisitionBlocked("Point-sampled source is not a pixel-is-area exposure grid")


def plan_window(dataset, reference, *, halo_cells=2, max_pixels=1_000_000):
    """Select native cells around a densified target envelope, without resampling.

    transform_bounds densifies each WRI edge with 128 points; a two-source-cell
    halo absorbs rounding and edge curvature for the verified regional grids.
    This selects an envelope, not physical overlap weights or usable coverage.
    """
    if isinstance(halo_cells, bool) or not isinstance(halo_cells, int) or halo_cells < 2:
        raise AcquisitionBlocked("At least two native halo cells are required")
    if isinstance(max_pixels, bool) or not isinstance(max_pixels, int) or max_pixels <= 0:
        raise AcquisitionBlocked("Native pixel budget must be a positive integer")
    native = transform_bounds(reference["crs"], dataset.crs, *reference["bounds_wgs84"], densify_pts=128)
    if not np.isfinite(native).all():
        raise AcquisitionBlocked("Target footprint cannot be transformed into the native source CRS")
    fractional = from_bounds(*native, transform=dataset.transform)
    c0, r0 = math.floor(fractional.col_off)-halo_cells, math.floor(fractional.row_off)-halo_cells
    c1 = math.ceil(fractional.col_off+fractional.width)+halo_cells
    r1 = math.ceil(fractional.row_off+fractional.height)+halo_cells
    cc0, rr0, cc1, rr1 = max(c0, 0), max(r0, 0), min(c1, dataset.width), min(r1, dataset.height)
    if cc1 <= cc0 or rr1 <= rr0:
        raise AcquisitionBlocked("No native source pixels overlap the requested footprint envelope")
    if (cc1-cc0)*(rr1-rr0) > max_pixels:
        raise AcquisitionBlocked("Native window exceeds pixel budget; no country/tile download fallback")
    window = Window(cc0, rr0, cc1-cc0, rr1-rr0)
    b = dataset.bounds
    return window, {"window_col_row_width_height": list(window.flatten()),
                    "requested_col_row_width_height": [c0, r0, c1-c0, r1-r0],
                    "halo_cells": halo_cells, "transformed_wri_envelope": list(native),
                    "source_extent_clipped": (cc0, rr0, cc1, rr1) != (c0, r0, c1, r1),
                    "wri_envelope_inside_source_extent": b.left <= native[0] and b.bottom <= native[1]
                        and b.right >= native[2] and b.top >= native[3]}


def pixel_summary(values, mask):
    if values.shape != mask.shape or mask.dtype != np.uint8 or not np.isin(mask, [0, 255]).all():
        raise AcquisitionBlocked("Expected exact binary RFC15 validity mask")
    declared = mask == 255
    if np.any(declared & ((values < 0) | np.isinf(values))):
        raise AcquisitionBlocked("Source declares negative/infinite exposure valid")
    known = declared & np.isfinite(values)
    try:
        total = math.fsum(float(v) for v in values[known])
    except OverflowError as error:
        raise AcquisitionBlocked("Known source-window total exceeds finite range") from error
    if not math.isfinite(total):
        raise AcquisitionBlocked("Known source-window total exceeds finite range")
    return {"pixels": int(values.size), "known_pixels": int(known.sum()),
            "valid_zero": int(np.count_nonzero(known & (values == 0))),
            "valid_positive": int(np.count_nonzero(known & (values > 0))),
            "masked_pixels": int(np.count_nonzero(~declared)),
            "declared_valid_nan": int(np.count_nonzero(declared & np.isnan(values))),
            "known_window_total": total, "known_window_fraction": float(known.mean())}


def acquire_window(source_key, review, output_directory, *, reference=None, max_bytes=32*1024**2,
                   max_pixels=1_000_000):
    """Acquire one native source window after verified anonymous public access.

    No credentials or Earth Engine fallback. Every remote request is bounded;
    no output dataset is published on failure. Data stay separate from future
    WRI-aligned products and must pass a separate redistribution/size review.
    """
    spec = verify_review(source_key, review)  # No network before verification.
    reference = wri_reference() if reference is None else reference
    output = Path(output_directory)
    if output.exists():
        raise AcquisitionBlocked("Output directory exists; refusing to replace acquisition evidence")
    remote = HTTPRangeSource(review["source_url"], spec["allowed_hosts"], max_bytes=max_bytes)
    try:
        with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_TIFF_INTERNAL_MASK=True):
            with rasterio.open(remote.url, opener=remote.opener) as dataset:
                validate_raster(dataset, review)
                window, plan = plan_window(dataset, reference, max_pixels=max_pixels)
                values = dataset.read(1, window=window)  # Base/native samples; no out_shape or interpolation.
                mask = dataset.read_masks(1, window=window)
                summary = pixel_summary(values, mask)
                transform = dataset.window_transform(window)
                profile = {"driver": "GTiff", "count": 1, "height": values.shape[0], "width": values.shape[1],
                           "dtype": values.dtype, "crs": dataset.crs, "transform": transform,
                           "nodata": dataset.nodata, "compress": "deflate"}
                metadata = {"full_source_shape": list(dataset.shape), "shape": list(values.shape),
                            "crs_wkt": dataset.crs.to_wkt(), "transform": list(transform)[:6],
                            "full_source_transform": list(dataset.transform)[:6], "dtype": str(values.dtype),
                            "nodata": "NaN" if dataset.nodata is not None and math.isnan(dataset.nodata) else dataset.nodata,
                            "source_mask_flags": [flag.name for flag in dataset.mask_flag_enums[0]],
                            "window_mask_storage": "internal_binary_RFC15",
                            "scales": list(dataset.scales), "offsets": list(dataset.offsets),
                            "band_description": dataset.descriptions[0], "stored_unit": dataset.units[0]}
                tags, band_tags = dataset.tags(), dataset.tags(1)
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".exposure-window-", dir=output.parent) as temporary:
            stage = Path(temporary)
            raster = stage / "source_window.tif"
            with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):
                with rasterio.open(raster, "w", **profile) as target:
                    target.write(values, 1)
                    target.write_mask(mask)
                    target.update_tags(**tags)
                    target.update_tags(1, **band_tags)
                    target.set_band_description(1, metadata["band_description"] or review["band"])
                    if metadata["stored_unit"] is not None:
                        target.set_band_unit(1, metadata["stored_unit"])
            manifest = {"schema_version": 1, "kind": "native_source_window", "source_key": source_key,
                        "product": {k: v for k, v in spec.items() if k != "allowed_hosts"},
                        "acquired_utc": datetime.now(timezone.utc).isoformat(), "review": review,
                        "wri_reference": reference, "native_raster": metadata, "window_plan": plan,
                        "pixels": summary, "units": spec["units"],
                        "source_object": {"url": remote.url, "size_bytes": remote.size, "etag": remote.etag,
                                          "last_modified": remote.last_modified, "full_object_sha256": None},
                        "http_payload_bytes": remote.transferred_bytes, "max_payload_bytes": max_bytes,
                        "window_file": {"path": raster.name, "bytes": raster.stat().st_size,
                                        "sha256": hashlib.sha256(raster.read_bytes()).hexdigest()},
                        "resampling": "none", "integration_status": "not_run",
                        "note": "Native samples re-encoded as a cropped TIFF; not a byte-identical original object or WRI-aligned product"}
            (stage / "manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False)+"\n")
            # Rename a complete staging directory, retaining originals on failures.
            stage.rename(output)
        return manifest
    finally:
        remote.close()
