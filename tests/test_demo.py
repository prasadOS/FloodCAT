import unittest
import numpy as np
from src.floodcat.demo import make_demo_data, SCENARIO_NAMES, summarize, severity, ROWS, COLS
from src.floodcat.exports import metadata_json, table_csv

class TestDemo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=make_demo_data()

    def test_shapes_and_positive_area(self):
        d=self.data
        self.assertEqual(d.area_km2.shape,(ROWS,COLS))
        self.assertEqual(d.people.shape,(ROWS,COLS))
        self.assertTrue(np.all(d.area_km2>0))
        self.assertTrue(np.all(d.builtup_km2<=d.area_km2))

    def test_all_scenarios_are_nonnegative(self):
        self.assertEqual(len(SCENARIO_NAMES),5)
        for a in self.data.depths.values():
            self.assertEqual(a.shape,(ROWS,COLS))
            self.assertTrue(np.isfinite(a).all())
            self.assertTrue((a>=0).all())

    def test_return_period_depth_order(self):
        a=self.data.depths
        self.assertTrue(np.all(a[SCENARIO_NAMES[0]]<=a[SCENARIO_NAMES[1]]))
        self.assertTrue(np.all(a[SCENARIO_NAMES[1]]<=a[SCENARIO_NAMES[2]]))

    def test_high_threshold_reduces_exposure(self):
        low=summarize(self.data,SCENARIO_NAMES[1],0)
        high=summarize(self.data,SCENARIO_NAMES[1],2)
        self.assertGreater(low['Inundated area (km²)'], high['Inundated area (km²)'])
        self.assertGreaterEqual(low['Exposed people (synthetic)'],high['Exposed people (synthetic)'])

    def test_outside_max_depth_is_empty(self):
        r=summarize(self.data,SCENARIO_NAMES[0],99)
        self.assertEqual(r['Flooded cells'],0)
        self.assertEqual(r['Exposed people (synthetic)'],0)

    def test_severity_sums_to_summary(self):
        name=SCENARIO_NAMES[1]
        bands=severity(self.data,name,0)
        total=summarize(self.data,name,0)
        self.assertAlmostEqual(sum(r['Area (km²)'] for r in bands),total['Inundated area (km²)'],places=8)
        self.assertEqual(sum(r['People (synthetic)'] for r in bands),total['Exposed people (synthetic)'])

    def test_export_metadata_is_honest(self):
        self.assertIn(b'SYNTHETIC',metadata_json(SCENARIO_NAMES[1],1))
        self.assertIn(b'Scenario',table_csv([summarize(self.data,SCENARIO_NAMES[1],0)]))

if __name__=='__main__':
    unittest.main()
