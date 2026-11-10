"""Actual uploaded metadata plus independent tiny strip/conservation fixtures."""
import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest

import numpy as np

AVAILABLE = all(importlib.util.find_spec(n) for n in ("rasterio", "pyproj", "shapely"))
if AVAILABLE:
    import rasterio
    from rasterio.transform import from_origin
    from src.floodcat.patna_processing import (ROOT, FILENAMES, inventory, pilot_overlap,
                                              remap_strips, budget, sha256)
    from src.floodcat.remapping import RasterGrid, build_conservative_map


@unittest.skipUnless(AVAILABLE, "Optional native-raster scientific environment required")
class TestPatnaProcessing(unittest.TestCase):
    def test_actual_upload_shapes_values_and_availability(self):
        expected = {"hazard": ((65,168),10920,5703,0,0),
                    "population": ((644,1672),961554,0,115214,0),
                    "built_surface": ((638,1532),836265,628967,0,141151)}
        provenance = json.loads((ROOT/"config/patna_upload_provenance.json").read_text())
        for key, (shape, known, zeros, masked, nan) in expected.items():
            with self.subTest(key=key):
                info, values, valid = inventory(ROOT/"data/demo_real"/FILENAMES[key])
                self.assertEqual(tuple(info["shape"]),shape)
                self.assertEqual(info["available_pixels"],known)
                self.assertEqual(info["valid_zero"],zeros)
                self.assertEqual(info["declared_mask_invalid"],masked)
                self.assertEqual(info["nan_pixels"],nan)
                self.assertEqual(info["sha256"],provenance["sources"][key]["sha256"])
                self.assertEqual(info["format"],"BigTIFF")
                self.assertFalse(valid[np.isnan(values)].any())

    def test_lfs_pointer_rejected_without_raster_open(self):
        with tempfile.TemporaryDirectory() as temporary:
            p=Path(temporary)/"pointer.tif"
            p.write_text("version https://git-lfs.github.com/spec/v1\noid sha256:fixture\nsize 123\n")
            with self.assertRaisesRegex(ValueError,"LFS pointer"):
                inventory(p)

    def test_nan_and_sentinel_missing_are_distinct_from_valid_zero(self):
        with tempfile.TemporaryDirectory() as temporary:
            p=Path(temporary)/"fixture.tif"
            with rasterio.open(p,"w",driver="GTiff",height=2,width=2,count=1,dtype="float32",
                               crs="EPSG:4326",transform=from_origin(85,26,.01,.01),nodata=-9999) as ds:
                ds.write(np.array([[0,np.nan],[-9999,2]],dtype="float32"),1)
            info,values,valid=inventory(p)
            np.testing.assert_array_equal(valid,[[True,False],[False,True]])
            self.assertEqual(info["valid_zero"],1)
            self.assertEqual(info["declared_mask_invalid"],1)
            self.assertEqual(info["nan_pixels"],1)
            self.assertEqual(info["known_numeric_sum"],2)
            self.assertTrue(np.isnan(values[0,1]))
            self.assertEqual(values[1,0],-9999)

    def test_actual_pilot_overlap_exact_and_wrong_grid_rejected(self):
        info,depth,_=inventory(ROOT/"data/demo_real"/FILENAMES["hazard"])
        grid=RasterGrid(depth.shape,tuple(info["transform"]),info["crs_wkt"])
        overlap=pilot_overlap(depth,grid)
        self.assertEqual(overlap["cells"],2030)
        self.assertEqual(overlap["equal_cells"],2030)
        self.assertEqual(overlap["max_absolute_difference_m"],0)
        shifted=list(grid.transform);shifted[2]+=.001
        with self.assertRaises(ValueError):
            pilot_overlap(depth,RasterGrid(depth.shape,tuple(shifted),grid.crs))

    def test_strip_adapter_hand_budget_and_monolithic_agreement(self):
        source=RasterGrid((2,4),(100,0,0,0,-100,200),"EPSG:6933")
        target=RasterGrid((2,2),(200,0,0,0,-100,200),"EPSG:6933")
        values=np.arange(1,9,dtype=float).reshape(2,4)
        mask=np.ones(values.shape,dtype=bool)
        result,allocated,timing=remap_strips(values,mask,source,target,tile_rows=1)
        np.testing.assert_allclose(result.values,[[3,7],[11,15]],atol=1e-9)
        np.testing.assert_allclose(allocated,1,atol=1e-10)
        full=build_conservative_map(source,target).apply(values)
        np.testing.assert_allclose(result.values,full.values,atol=1e-9)
        totals=budget(values,mask,result.known_values,allocated)
        self.assertAlmostEqual(totals["known_source_total"],36)
        self.assertLess(abs(totals["balance_error"]),1e-8)
        self.assertEqual(timing["strips"],2)

    def test_strip_missing_clipping_and_resource_cap(self):
        source=RasterGrid((1,1),(200,0,0,0,-200,200),"EPSG:6933")
        target=RasterGrid((1,1),(100,0,50,0,-100,150),"EPSG:6933")
        values=np.array([[80.]])
        result,allocated,_=remap_strips(values,np.array([[True]]),source,target)
        self.assertAlmostEqual(result.values[0,0],20)
        totals=budget(values,np.array([[True]]),result.known_values,allocated)
        self.assertAlmostEqual(totals["known_clipped_outside_wri_extent"],60)
        missing,_,_=remap_strips(np.array([[np.nan]]),np.array([[False]]),source,target)
        self.assertFalse(missing.valid[0,0])
        self.assertEqual(missing.known_values[0,0],0)
        self.assertTrue(np.isnan(missing.values[0,0]))
        with self.assertRaisesRegex(ValueError,"conservation"):
            budget(values,np.array([[True]]),np.array([[79.]]))
        with self.assertRaises(ValueError):
            remap_strips(values,np.array([[1.]]),source,target)
        wide=RasterGrid((1,2),(100,0,0,0,-100,100),"EPSG:6933")
        with self.assertRaisesRegex(ValueError,"source-cell cap"):
            remap_strips(np.array([[1.,2.]]),np.array([[True,True]]),wide,target,max_source_cells=1)

    def test_committed_bundle_matches_independent_threshold_sums(self):
        directory=ROOT/"data/processed_real/patna_common"
        if not (directory/"validation.json").is_file():
            self.skipTest("Processed real bundle has not been generated yet")
        report=json.loads((directory/"validation.json").read_text())
        audit=json.loads((directory/"audit.json").read_text())
        self.assertEqual(audit["status"],"passed")
        self.assertEqual(sha256(directory/"aligned_common.npz"),report["processed_artifact"]["sha256"])
        with np.load(directory/"aligned_common.npz",allow_pickle=False) as arrays:
            common=arrays["common_valid"]
            self.assertEqual(int(common.sum()),report["common_cells"])
            self.assertFalse((common & ~arrays["population_valid"]).any())
            self.assertFalse((common & ~arrays["built_valid"]).any())
            self.assertTrue(np.isfinite(arrays["population_count"][common]).all())
            self.assertTrue(np.isfinite(arrays["built_surface_m2"][common]).all())
            for row in report["exposure"]:
                flooded=common & (arrays["depth_m"]>row["threshold_m"])
                pop=math.fsum(float(x) for x in arrays["population_count"][flooded])
                built=math.fsum(float(x) for x in arrays["built_surface_m2"][flooded])
                self.assertAlmostEqual(pop,row["population"]["total_exposed"],places=7)
                self.assertAlmostEqual(built,row["built_surface_m2"]["total_exposed"],places=6)
                self.assertEqual(int(flooded.sum()),row["population"]["flooded_cells"])
