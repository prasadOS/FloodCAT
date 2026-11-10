"""Offline fixtures only; never substitute these values for real exposure data."""

from contextlib import redirect_stdout
import copy
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

AVAILABLE = all(importlib.util.find_spec(n) for n in ("rasterio", "pyproj", "requests"))
if AVAILABLE:
    import rasterio
    from rasterio.io import MemoryFile
    from rasterio.transform import from_origin
    from pyproj import CRS, Transformer
    from src.floodcat.acquisition import (SOURCES, acquire_window, pixel_summary, plan_window,
                                         inspect_source, validate_raster, verify_review, wri_reference)
    from src.floodcat.http_range import AcquisitionBlocked, HTTPRangeSource
    from scripts.acquire_exposure_windows import main

ROOT = Path(__file__).resolve().parents[1]


class RangeServer:
    """Deterministic in-memory HTTP fixture. No network or real provider pixels."""
    def __init__(self, payload, *, status=206, etag='"test-object"', mutate=False,
                 truncate=False, headers=None):
        self.payload, self.status, self.etag = payload, status, etag
        self.mutate, self.truncate, self.headers = mutate, truncate, headers or {}
        self.requests = []

    def get(self, url, **options):
        self.requests.append((url, options))
        first, last = map(int, re.findall(r"\d+", options["headers"]["Range"]))
        last = min(last, len(self.payload)-1)
        etag = '"changed"' if self.mutate and len(self.requests) > 1 else self.etag
        payload = self.payload[first:last+1]
        if self.truncate:
            payload = payload[:-1]

        class Response:
            status_code = self.status
            headers = {"ETag": etag, "Content-Range": f"bytes {first}-{last}/{len(self.payload)}",
                       "Content-Length": str(last-first+1), **self.headers}

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def iter_content(self, chunk_size):
                for i in range(0, len(payload), chunk_size):
                    yield payload[i:i+chunk_size]

        return Response()


def fixture_raster():
    values = np.arange(80, dtype="float32").reshape(8, 10)
    mask = np.full(values.shape, 255, dtype="uint8")
    values[1, 1], values[2, 2] = -9999, 9999
    mask[1, 1] = mask[2, 2] = 0
    with MemoryFile() as memory:
        with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):
            with memory.open(driver="GTiff", height=8, width=10, count=1, dtype="float32",
                             crs="EPSG:4326", transform=from_origin(0, 8, 1, 1), nodata=-9999) as dataset:
                dataset.write(values, 1)
                dataset.write_mask(mask)
        payload = memory.read()
    return payload, values, mask


def reviewed_fixture(source_key="worldpop_2020_ind", crs="EPSG:4326", resolution=(1, 1)):
    # Deliberately fictional reviewed fixture, never an actual provider review.
    result = {k: v for k, v in SOURCES[source_key].items()
              if k in ("product_id", "epoch", "release", "band", "units")}
    result.update(verified=True, verified_utc="2026-11-10T00:00:00+00:00",
                  source_url=f"https://{SOURCES[source_key]['allowed_hosts'][0]}/TEST_FIXTURE.tif",
                  documentation_url=SOURCES[source_key]["catalog_url"], product_evidence="test fixture only",
                  variant_evidence="test fixture only", population_adjustment="unadjusted",
                  license_name="TEST ONLY", license_url="https://example.invalid/test-license",
                  attribution="TEST FIXTURE", license_evidence="test fixture only",
                  acquisition_permitted=True, redistribution_permitted=False,
                  pixel_support="area", mask_storage="internal_or_nodata", mask_evidence="test fixture only",
                  zero_semantics="valid_unless_masked", zero_evidence="test fixture only",
                  dtype="float32", nodata=-9999, mask_flags=["per_dataset"],
                  crs_wkt=CRS(crs).to_wkt(), resolution_native=list(resolution))
    return result


@unittest.skipUnless(AVAILABLE, "Optional acquisition dependencies not installed")
class TestAcquisition(unittest.TestCase):
    def test_actual_wri_reference_exact_snapped_footprint(self):
        ref = wri_reference()
        self.assertEqual(ref["sha256"], "9d5c2747166f7cdecb84a7067575b311a4d4552cc2cd5ee482b924159bd91ebc")
        self.assertEqual(ref["shape"], [48, 58])
        self.assertEqual(ref["bytes"], 3801)
        self.assertEqual(ref["crs"], "EPSG:4326")
        np.testing.assert_allclose(ref["transform"], [1/120, 0, 85, 0, -1/120, 25.85], rtol=0, atol=1e-14)
        self.assertAlmostEqual(ref["bounds_wgs84"][2], 85+58/120)
        self.assertGreater(ref["bounds_wgs84"][2], 85.48)
        self.assertEqual(ref["hazard_counts"], {"valid_zero": 1222, "positive": 1562})

    def test_wri_manifest_grid_mismatch_is_rejected(self):
        from src.floodcat import wri
        original = wri.load_pilot()
        for name, value in [("shape", [47, 58]), ("crs", "EPSG:3857"),
                            ("grid_bounds_wgs84", [85, 25.45, 85.48, 25.85])]:
            altered = list(original)
            altered[2] = copy.deepcopy(original[2])
            altered[2][name] = value
            with patch.object(wri, "load_pilot", return_value=altered), self.assertRaises(AcquisitionBlocked):
                wri_reference()

    def test_checked_in_reviews_stop_before_network_or_output(self):
        reviews = json.loads((ROOT/"config/exposure_review_template.json").read_text())
        with tempfile.TemporaryDirectory() as temporary, patch("requests.Session.get") as request:
            for key in SOURCES:
                output = Path(temporary)/key
                with self.assertRaisesRegex(AcquisitionBlocked, "unverified"):
                    acquire_window(key, reviews[key], output)
                with self.assertRaisesRegex(AcquisitionBlocked, "unverified"):
                    inspect_source(key, reviews[key])
                self.assertFalse(output.exists())
            request.assert_not_called()

    def test_metadata_inspection_precedes_mask_review_without_acquisition(self):
        payload, _, _ = fixture_raster()
        review = {**reviewed_fixture(), "verified": False, "metadata_access_verified": True,
                  "crs_wkt": None, "mask_evidence": None, "zero_evidence": None}
        with patch("requests.Session.get", side_effect=RangeServer(payload).get):
            metadata = inspect_source("worldpop_2020_ind", review)
        self.assertEqual(metadata["mode"], "metadata_only_no_pixel_or_mask_read")
        self.assertEqual(metadata["shape"], [8, 10])
        self.assertTrue(CRS(metadata["crs_wkt"]).equals(CRS(4326), ignore_axis_order=True))
        self.assertEqual(metadata["nodata"], -9999)
        self.assertEqual(metadata["mask_flags"], [["per_dataset"]])
        self.assertNotIn("pixels", metadata)
        self.assertEqual(metadata["coverage_and_mask_semantics"], "unverified")
        with patch("requests.Session.get") as request, tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(AcquisitionBlocked):
                acquire_window("worldpop_2020_ind", review, Path(temporary)/"no-window")
            request.assert_not_called()

    def test_product_variant_license_and_crs_gates(self):
        review = reviewed_fixture()
        verify_review("worldpop_2020_ind", review)
        for change in [dict(product_id="R2025A"), dict(release="R2025A"), dict(epoch=2025),
                       dict(band="built_surface_nres"), dict(units="people/km2"),
                       dict(acquisition_permitted=False), dict(redistribution_permitted=None),
                       dict(mask_evidence=None), dict(variant_evidence=None), dict(population_adjustment=None),
                       dict(crs_wkt=CRS(3857).to_wkt()), dict(crs_wkt="invalid WKT"),
                       dict(mask_storage="external"), dict(nodata=True)]:
            with self.subTest(change=change), self.assertRaises((AcquisitionBlocked, ValueError)):
                verify_review("worldpop_2020_ind", {**review, **change})
        ghsl = reviewed_fixture("ghsl_2020_built_surface", "ESRI:54009", (100, 100))
        verify_review("ghsl_2020_built_surface", ghsl)
        for change in [dict(crs_wkt=CRS(6933).to_wkt()), dict(resolution_native=[1000, 1000])]:
            with self.assertRaises(AcquisitionBlocked):
                verify_review("ghsl_2020_built_surface", {**ghsl, **change})

    def test_exact_native_window_halo_clipping_and_budget(self):
        payload, _, _ = fixture_raster()
        with MemoryFile(payload) as memory, memory.open() as dataset:
            reference = {"crs": "EPSG:4326", "bounds_wgs84": [2, 3, 6, 6]}
            window, plan = plan_window(dataset, reference)
            self.assertEqual(tuple(window.flatten()), (0, 0, 8, 7))
            self.assertFalse(plan["source_extent_clipped"])
            self.assertTrue(plan["wri_envelope_inside_source_extent"])
            _, plan = plan_window(dataset, {**reference, "bounds_wgs84": [-1, -1, 2, 2]})
            self.assertTrue(plan["source_extent_clipped"])
            self.assertFalse(plan["wri_envelope_inside_source_extent"])
            for options in [dict(max_pixels=55), dict(halo_cells=1), dict(max_pixels=0)]:
                with self.assertRaises(AcquisitionBlocked):
                    plan_window(dataset, reference, **options)
            with self.assertRaises(AcquisitionBlocked):
                plan_window(dataset, {**reference, "bounds_wgs84": [40, 40, 41, 41]})

    def test_mollweide_window_contains_dense_actual_wri_boundary(self):
        ref = wri_reference()
        projection = Transformer.from_crs(4326, "ESRI:54009", always_xy=True)
        x, y = projection.transform(85.24, 25.65)
        transform = from_origin(100*math.floor(x/100)-40000, 100*math.ceil(y/100)+40000, 100, 100)
        with MemoryFile() as memory:
            with memory.open(driver="GTiff", height=800, width=800, count=1, dtype="uint16",
                             crs="ESRI:54009", transform=transform) as dataset:
                window, plan = plan_window(dataset, ref)
                west, south, east, north = ref["bounds_wgs84"]
                lon = np.r_[np.linspace(west,east,4097),np.linspace(west,east,4097),
                            np.full(4097,west),np.full(4097,east)]
                lat = np.r_[np.full(4097,north),np.full(4097,south),
                            np.linspace(south,north,4097),np.linspace(south,north,4097)]
                xx, yy = projection.transform(lon,lat)
                cols, rows = (xx-transform.c)/100, (transform.f-yy)/100
                self.assertGreaterEqual(cols.min()-window.col_off, 1.99)
                self.assertGreaterEqual(rows.min()-window.row_off, 1.99)
                self.assertGreaterEqual(window.col_off+window.width-cols.max(), 1.99)
                self.assertGreaterEqual(window.row_off+window.height-rows.max(), 1.99)
                self.assertFalse(plan["source_extent_clipped"])

    def test_metadata_mismatch_and_packed_values_stop(self):
        payload, _, _ = fixture_raster()
        with MemoryFile(payload) as memory, memory.open() as dataset:
            review = reviewed_fixture()
            validate_raster(dataset, review)
            for change in [dict(crs_wkt=CRS(6933).to_wkt()), dict(resolution_native=[.5,.5]),
                           dict(dtype="uint16"), dict(nodata=None), dict(mask_flags=["all_valid"])]:
                with self.assertRaises(AcquisitionBlocked):
                    validate_raster(dataset, {**review, **change})
        with MemoryFile() as memory:
            with memory.open(driver="GTiff",height=2,width=2,count=1,dtype="float32",
                             crs="EPSG:4326",transform=from_origin(0,2,1,1),nodata=-9999) as dataset:
                dataset.scales=(.5,)
                with self.assertRaises(AcquisitionBlocked):
                    validate_raster(dataset,{**reviewed_fixture(),"mask_flags":["nodata"]})

    def test_anonymous_window_roundtrip_values_mask_metadata_and_hash(self):
        payload, values, mask = fixture_raster()
        server = RangeServer(payload)
        reference = {"crs":"EPSG:4326","bounds_wgs84":[2,3,6,6],"test_fixture":True}
        with tempfile.TemporaryDirectory() as temporary, patch("requests.Session.get", side_effect=server.get):
            output = Path(temporary)/"native"
            manifest = acquire_window("worldpop_2020_ind", reviewed_fixture(), output, reference=reference)
            with rasterio.open(output/"source_window.tif") as result:
                np.testing.assert_array_equal(result.read(1),values[:7,:8])
                np.testing.assert_array_equal(result.read_masks(1),mask[:7,:8])
                self.assertEqual(result.dtypes,("float32",))
                self.assertEqual(result.transform,from_origin(0,8,1,1))
                self.assertEqual(result.nodata,-9999)
            self.assertEqual(manifest["pixels"]["known_window_total"],1843)
            self.assertEqual(manifest["pixels"]["valid_zero"],1)
            self.assertEqual(manifest["pixels"]["masked_pixels"],2)
            self.assertEqual(manifest["native_raster"]["shape"],[7,8])
            self.assertEqual(manifest["window_file"]["sha256"],hashlib.sha256((output/"source_window.tif").read_bytes()).hexdigest())
            self.assertIsNone(manifest["source_object"]["full_object_sha256"])
            self.assertEqual(manifest["resampling"],"none")
            self.assertEqual(manifest["integration_status"],"not_run")
            self.assertEqual(json.loads((output/"manifest.json").read_text()),manifest)

    def test_failed_transfer_publishes_no_window(self):
        payload, _, _ = fixture_raster()
        with tempfile.TemporaryDirectory() as temporary, patch("requests.Session.get",side_effect=RangeServer(payload,status=200).get):
            output = Path(temporary)/"not_created"
            with self.assertRaises(AcquisitionBlocked):
                acquire_window("worldpop_2020_ind",reviewed_fixture(),output)
            self.assertFalse(output.exists())

    def test_ghsl_like_uint16_window_preserves_surface_zero_and_mask(self):
        # Known Mollweide test CRS, not purported actual GHSL raster metadata.
        x, y = Transformer.from_crs(4326, "ESRI:54009", always_xy=True).transform(85.2, 25.7)
        transform = from_origin(100*math.floor(x/100), 100*math.ceil(y/100), 100, 100)
        values = np.arange(48, dtype="uint16").reshape(6, 8)
        mask = np.full(values.shape, 255, dtype="uint8")
        values[2, 2], mask[2, 2] = 65535, 0
        with MemoryFile() as memory:
            with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):
                with memory.open(driver="GTiff", height=6, width=8, count=1, dtype="uint16",
                                 crs="ESRI:54009", transform=transform) as dataset:
                    dataset.write(values, 1)
                    dataset.write_mask(mask)
                    bounds = rasterio.warp.transform_bounds(dataset.crs, "EPSG:4326", *dataset.bounds,
                                                            densify_pts=128)
            payload = memory.read()
        review = {**reviewed_fixture("ghsl_2020_built_surface", "ESRI:54009", (100, 100)),
                  "dtype": "uint16", "nodata": None}
        reference = {"crs": "EPSG:4326", "bounds_wgs84": list(bounds), "test_fixture": True}
        with tempfile.TemporaryDirectory() as temporary, patch("requests.Session.get", side_effect=RangeServer(payload).get):
            output = Path(temporary)/"built_fixture"
            manifest = acquire_window("ghsl_2020_built_surface", review, output, reference=reference)
            with rasterio.open(output/"source_window.tif") as result:
                np.testing.assert_array_equal(result.read(1), values)
                np.testing.assert_array_equal(result.read_masks(1), mask)
                self.assertEqual(result.dtypes, ("uint16",))
            self.assertEqual(manifest["units"], "m2/cell")
            self.assertEqual(manifest["pixels"]["known_window_total"], 1110)
            self.assertEqual(manifest["pixels"]["valid_zero"], 1)
            self.assertEqual(manifest["pixels"]["masked_pixels"], 1)
            self.assertTrue(manifest["window_plan"]["source_extent_clipped"])

    def test_pixel_mask_zero_nan_and_invalid_values(self):
        values=np.array([[0.,0.,np.nan,5.,99.]])
        mask=np.array([[255,0,255,255,0]],dtype="uint8")
        summary=pixel_summary(values,mask)
        self.assertEqual(summary["known_window_total"],5)
        self.assertEqual(summary["valid_zero"],1)
        self.assertEqual(summary["masked_pixels"],2)
        self.assertEqual(summary["declared_valid_nan"],1)
        for bad in [np.array([[-1.]]),np.array([[np.inf]]),np.array([[1e308,1e308]])]:
            with self.assertRaises(AcquisitionBlocked):
                pixel_summary(bad,np.full(bad.shape,255,dtype="uint8"))
        with self.assertRaises(AcquisitionBlocked):
            pixel_summary(np.array([[1.]]),np.array([[128]],dtype="uint8"))

    def test_range_cache_seek_and_anonymous_request_contract(self):
        server=RangeServer(b"0123456789")
        with patch("requests.Session.get",side_effect=server.get):
            source=HTTPRangeSource("https://data.worldpop.org/test.tif",{"data.worldpop.org"},block_size=4,max_bytes=20)
            with source.opener(source.url) as handle:
                self.assertEqual(handle.read(3),b"012")
                self.assertEqual(handle.seek(5),5)
                self.assertEqual(handle.read(),b"56789")
                handle.seek(0)
                self.assertEqual(handle.read(4),b"0123")
            self.assertEqual(source.transferred_bytes,11)
            self.assertEqual(len(server.requests),4)
            for _,options in server.requests:
                self.assertFalse(options["allow_redirects"])
                self.assertTrue(options["stream"])
                self.assertEqual(options["headers"]["Accept-Encoding"],"identity")
                self.assertIsNotNone(options["auth"])
            source.close()

    def test_range_refusals_and_resource_caps(self):
        for server in [RangeServer(b"123",status=200),RangeServer(b"123",status=302),
                       RangeServer(b"123",etag='W/"weak"'),RangeServer(b"123",truncate=True),
                       RangeServer(b"123",headers={"Content-Range":"bytes 0-2/3"}),
                       RangeServer(b"123",headers={"Content-Encoding":"gzip"}),
                       RangeServer(b"123",headers={"Content-Length":"10000"})]:
            with self.subTest(server=server),patch("requests.Session.get",side_effect=server.get),self.assertRaises(AcquisitionBlocked):
                HTTPRangeSource("https://data.worldpop.org/test.tif",{"data.worldpop.org"})
        for server in [RangeServer(b"12345678",mutate=True),RangeServer(b"12345678")]:
            with patch("requests.Session.get",side_effect=server.get):
                source=HTTPRangeSource("https://data.worldpop.org/test.tif",{"data.worldpop.org"},max_bytes=4,block_size=4)
                with self.assertRaises(AcquisitionBlocked):
                    source.read_at(0,4)
                source.close()
        server=RangeServer(b"12345678",mutate=True)
        with patch("requests.Session.get",side_effect=server.get):
            source=HTTPRangeSource("https://data.worldpop.org/test.tif",{"data.worldpop.org"},block_size=4)
            with self.assertRaisesRegex(AcquisitionBlocked,"changed"):
                source.read_at(0,4)
            source.close()

    def test_reject_credentials_queries_unapproved_hosts_before_network(self):
        with patch("requests.Session.get") as request:
            for url in ["http://data.worldpop.org/test.tif","https://user:secret@data.worldpop.org/test.tif",
                        "https://data.worldpop.org/test.tif?token=secret","https://example.org/test.tif"]:
                with self.assertRaises(AcquisitionBlocked):
                    HTTPRangeSource(url,{"data.worldpop.org"})
            request.assert_not_called()

    def test_inventory_and_checked_in_review_cli_never_fetch(self):
        with patch("requests.Session.get") as request,redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(main([]),0)
            self.assertEqual(json.loads(stdout.getvalue())["mode"],"inventory_only_no_network")
            with tempfile.TemporaryDirectory() as temporary,redirect_stdout(io.StringIO()):
                self.assertEqual(main(["--source","worldpop_2020_ind","--review",
                    str(ROOT/"config/exposure_review_template.json"),"--output",str(Path(temporary)/"none")]),2)
            request.assert_not_called()
