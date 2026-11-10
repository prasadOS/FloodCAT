"""Fail closed on identity inferred only from filenames or geometry."""
import importlib.util
import json
import unittest
from pathlib import Path

AVAILABLE=all(importlib.util.find_spec(n) for n in ('rasterio','shapely','pyproj'))
if AVAILABLE:
    from scripts.validate_multiscenario_inputs import validate, assess_source, same_grid


@unittest.skipUnless(AVAILABLE,'Optional native scientific dependencies required')
class TestMultiscenarioInputs(unittest.TestCase):
    def test_actual_report_is_reproducible_and_source_supported(self):
        expected=json.loads(Path('config/patna_multiscenario_validation.json').read_text())
        actual=validate()
        self.assertEqual(actual,expected)
        self.assertEqual(len(actual['entries']),15)
        self.assertEqual(len(actual['blockers']),0)
        self.assertTrue(actual['ready_for_dashboard'])
        self.assertEqual(actual['candidate_common_cells'],6113)
        self.assertTrue(actual['exposure_reuse_geometry_eligible'])
        self.assertFalse(actual['processing_performed'])
        self.assertEqual(sum(e['source_identity']['verified_against_existing_recipe'] for e in actual['entries']),15)

    def test_renamed_identical_bytes_do_not_prove_new_source(self):
        provenance=json.loads(Path('config/patna_upload_provenance.json').read_text())
        digest=provenance['sources']['hazard']['sha256']
        self.assertTrue(assess_source('FloodCAT_Patna_WRI_Historical_T100.tif',digest,provenance)['verified_against_existing_recipe'])
        for name,h in [('FloodCAT_Patna_WRI_RCP85_2050_T100.tif',digest),('FloodCAT_Patna_WRI_Historical_T100.tif','0'*64)]:
            self.assertFalse(assess_source(name,h,provenance)['verified_against_existing_recipe'])

    def test_same_dimensions_do_not_establish_geometry(self):
        ref={'shape':[2,2],'crs_wkt':'EPSG:4326','transform':[1,0,0,0,-1,2],'bounds':[0,0,2,2]}
        self.assertTrue(same_grid(ref,ref))
        for key,value in [('crs_wkt','EPSG:3857'),('transform',[1,0,.1,0,-1,2]),('bounds',[.1,0,2.1,2])]:
            self.assertFalse(same_grid(ref|{key:value},ref))
