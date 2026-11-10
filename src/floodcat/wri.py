"""Local validation and area calculations for the Patna WRI pilot tile."""

import hashlib
import io
import json
from pathlib import Path
import zlib

import numpy as np
from PIL import Image

COLLECTION = "WRI/Aqueduct_Flood_Hazard_Maps/V2"
IMAGE = "inunriver_historical_000000000WATCH_1980_rp00100"
BAND = "inundation_depth"
SOURCE = "https://developers.google.com/earth-engine/datasets/catalog/WRI_Aqueduct_Flood_Hazard_Maps_V2"
ROI = (85.0, 25.45, 85.48, 25.85)
STEP = 1 / 120
SHAPE = (48, 58)
TRANSFORM = (STEP, 0, 85.0, 0, -STEP, 25.85)
NODATA_FILL = -9999.0
ASSETS = Path(__file__).resolve().parents[2] / "data" / "demo_real"
TIFF = "patna_wri_watch_t100.tif"
MANIFEST = "patna_wri_watch_t100.json"


def decode_tile(payload):
    """Read and verify the fixed north-up, pixel-is-area pilot GeoTIFF."""
    with Image.open(io.BytesIO(payload)) as image:
        if image.format != "TIFF" or image.n_frames != 1 or image.mode != "F":
            raise ValueError("Expected a single-band float32 TIFF")
        tags = image.tag_v2
        if tags.get(258) != (32,) or tags.get(339) != (3,):
            raise ValueError("Expected 32-bit floating-point depth samples")
        directory = tags.get(34735, ())
        keys = {
            key: value
            for key, location, count, value in zip(
                directory[4::4], directory[5::4], directory[6::4], directory[7::4]
            )
            if location == 0 and count == 1
        }
        if keys.get(2048) != 4326 or keys.get(1025, 1) != 1:
            raise ValueError("Expected EPSG:4326 with pixel-is-area coordinates")
        scale = tags.get(33550, ())
        tiepoint = tags.get(33922, ())
        matrix = tags.get(34264)
        if matrix is not None and len(matrix) == 16 and not scale and not tiepoint:
            if tuple(matrix[12:]) != (0, 0, 0, 1):
                raise ValueError("Expected an affine GeoTIFF transformation")
            transform = tuple(matrix[i] for i in (0, 1, 3, 4, 5, 7))
        elif matrix is None and len(scale) == 3 and len(tiepoint) == 6:
            x, y, _, lon, lat, _ = tiepoint
            dx, dy, _ = scale
            transform = (dx, 0, lon - x * dx, 0, -dy, lat + y * dy)
        else:
            raise ValueError("Expected a GeoTIFF affine matrix or scale and tiepoint tags")
        if payload[:2] == b"MM" and tags.get(259) in (8, 32946):
            # Pillow/libtiff can decode Earth Engine's big-endian float tile with
            # reversed sample bytes. Read the single deflated tile explicitly.
            offsets, lengths = tags.get(324, ()), tags.get(325, ())
            width, height = tags.get(322, 0), tags.get(323, 0)
            if (len(offsets) != 1 or len(lengths) != 1 or tags.get(317, 1) != 1
                or not image.width <= width <= 256 or not image.height <= height <= 256
            ):
                raise ValueError("Unsupported Earth Engine TIFF tile encoding")
            offset, length = offsets[0], lengths[0]
            samples = zlib.decompress(payload[offset:offset + length])
            depth = np.frombuffer(samples, dtype=">f4").reshape(height, width)
            depth = depth[:image.height, :image.width].astype(np.float32)
        else:
            depth = np.array(image)
        if depth.shape != SHAPE or not np.allclose(transform, TRANSFORM, rtol=0, atol=1e-10):
            raise ValueError("Raster shape or grid alignment differs from the Patna pilot")
        raw_nodata = tags.get(42113)
        nodata = None if raw_nodata is None else float(raw_nodata.rstrip("\x00"))
        if nodata not in (None, NODATA_FILL):
            raise ValueError("Unexpected GeoTIFF nodata value")
    return depth, nodata


def pixel_areas_km2(transform, rows):
    """Integrate WGS84 ellipsoid area between each pair of latitude parallels."""
    dx, _, _, _, dy, top = transform
    latitude_edges = np.deg2rad(top + dy * np.arange(rows + 1))
    sin_lat = np.sin(latitude_edges)
    a = 6378137.0
    flattening = 1 / 298.257223563
    e2 = flattening * (2 - flattening)
    e = np.sqrt(e2)
    integral = sin_lat / (1 - e2 * sin_lat**2) + np.arctanh(e * sin_lat) / e
    return a**2 * (1 - e2) / 2 * abs(np.deg2rad(dx)) * np.abs(np.diff(integral)) / 1e6


def summarize(depth, nodata, threshold, transform=TRANSFORM):
    valid = np.isfinite(depth) & (depth != nodata)
    wet = valid & (depth > threshold)
    areas = pixel_areas_km2(transform, depth.shape[0])
    return {
        "Threshold (m)": float(threshold),
        "Flooded area (km²)": float(wet.sum(axis=1) @ areas),
        "Flooded cells": int(wet.sum()),
        "Valid dry cells": int(np.count_nonzero(valid & (depth == 0))),
        "Nodata cells": int(depth.size - valid.sum()),
        "Maximum valid depth (m)": float(depth[valid].max()) if valid.any() else None,
    }


def load_pilot(directory=ASSETS):
    manifest_bytes = (directory / MANIFEST).read_bytes()
    manifest = json.loads(manifest_bytes)
    payload = (directory / TIFF).read_bytes()
    if manifest["asset_id"] != f"{COLLECTION}/{IMAGE}" or manifest["band"] != BAND:
        raise ValueError("Unexpected WRI source asset or band")
    if manifest["sha256"] != hashlib.sha256(payload).hexdigest():
        raise ValueError("GeoTIFF checksum does not match the source manifest")
    depth, nodata = decode_tile(payload)
    if manifest["nodata"] != nodata or manifest["units"] != "m":
        raise ValueError("Depth units or nodata differ from the source manifest")
    counts = manifest["source_mask"]
    summary = summarize(depth, nodata, 0)
    if (summary["Flooded cells"], summary["Valid dry cells"], summary["Nodata cells"]) != (
        counts["positive"], counts["valid_zero"], counts["masked"]
    ) or sum((counts["positive"], counts["valid_zero"], counts["masked"])) != depth.size:
        raise ValueError("Local pixel counts differ from the source mask findings")
    if summary["Maximum valid depth (m)"] != manifest["source_depth_range_m"]["inundation_depth_max"]:
        raise ValueError("Local maximum depth differs from the source")
    return depth, nodata, manifest, payload, manifest_bytes
