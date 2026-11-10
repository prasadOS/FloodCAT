import io
import math
import unittest

import numpy as np
from PIL import Image, TiffImagePlugin

from src.floodcat import wri


def synthetic_tile(west=85, epsg=4326, shape=wri.SHAPE):
    depth = np.zeros(shape, dtype=np.float32)
    depth[0, :3] = [-9999, 0.5, 2]
    tags = TiffImagePlugin.ImageFileDirectory_v2()
    tags[34735] = (1, 1, 0, 2, 1025, 0, 1, 1, 2048, 0, 1, epsg)
    tags[33550] = (wri.STEP, wri.STEP, 0.)
    tags[33922] = (0., 0., 0., float(west), 25.85, 0.)
    tags[42113] = "-9999"
    output = io.BytesIO()
    Image.fromarray(depth).save(output, format="TIFF", tiffinfo=tags)
    return output.getvalue()


class TestWri(unittest.TestCase):
    def test_nodata_dry_zero_and_strict_threshold(self):
        depth = np.array([[9999., 0., 1., 2., np.nan]])
        zero = wri.summarize(depth, 9999, 0)
        self.assertEqual(zero["Nodata cells"], 2)
        self.assertEqual(zero["Valid dry cells"], 1)
        self.assertEqual(zero["Flooded cells"], 2)
        one = wri.summarize(depth, 9999, 1)
        self.assertEqual(one["Flooded cells"], 1)
        self.assertEqual(one["Maximum valid depth (m)"], 2)
        self.assertAlmostEqual(one["Flooded area (km²)"], zero["Flooded area (km²)"] / 2)
        self.assertEqual(wri.summarize(depth, 9999, 2)["Flooded area (km²)"], 0)

    def test_area_against_numerical_ellipsoid_integration(self):
        dx, _, _, _, dy, north = wri.TRANSFORM
        a, f = 6378137.0, 1 / 298.257223563
        e2 = f * (2 - f)
        lat = np.deg2rad(north + dy * (np.arange(128) + 0.5) / 128)
        integrand = a**2 * (1 - e2) * np.cos(lat) / (1 - e2 * np.sin(lat)**2)**2
        expected = integrand.mean() * math.radians(dx) * abs(math.radians(dy)) / 1e6
        areas = wri.pixel_areas_km2(wri.TRANSFORM, 48)
        self.assertAlmostEqual(areas[0], expected, places=9)
        self.assertGreater(areas[-1], areas[0])

    def test_geotiff_decodes_valid_zero_and_nodata(self):
        depth, nodata = wri.decode_tile(synthetic_tile())
        self.assertEqual(depth.dtype, np.float32)
        self.assertEqual(nodata, -9999)
        np.testing.assert_array_equal(depth[0, :4], [-9999, 0.5, 2, 0])

    def test_geotiff_rejects_bad_crs_shape_and_alignment(self):
        for settings in ({"west": 85 + wri.STEP / 2}, {"epsg": 4269}, {"shape": (47, 58)}):
            with self.subTest(settings=settings), self.assertRaises(ValueError):
                wri.decode_tile(synthetic_tile(**settings))

    @unittest.skipUnless((wri.ASSETS / wri.TIFF).is_file(), "Pilot GeoTIFF is absent")
    def test_acquired_tile_matches_source(self):
        depth, nodata, manifest, _, _ = wri.load_pilot()
        result = wri.summarize(depth, nodata, 0)
        self.assertEqual(result["Flooded cells"], 1562)
        self.assertEqual(result["Valid dry cells"], 1222)
        self.assertEqual(result["Nodata cells"], 0)
        self.assertAlmostEqual(result["Flooded area (km²)"], 1206.561619, places=5)
        self.assertEqual(manifest["valid_pixel_fraction"], 1)
