"""Independent depth-band accounting, native-map alignment and two-mode navigation."""
import json
import math
from unittest.mock import patch
import unittest
import numpy as np
from src.floodcat import patna
from src.floodcat.geographic_map import map_payload, map_html
from src.floodcat.patna_analysis import MODULES, depth_bands


class TestPatnaRedesign(unittest.TestCase):
    def test_hand_calculated_bands_boundaries_and_threshold_clipping(self):
        # Exact 0,1,2,5 belong to dry/preceding band; NaN missing excluded.
        a={'depth_m':np.array([[0.,1.,2.,5.,6.,np.nan,7.]]),
           'common_valid':np.array([[True,True,True,True,True,False,False]]),
           'valid_depth':np.array([[True,True,True,True,True,False,True]]),
           'population_valid':np.array([[True,True,True,True,True,False,False]]),
           'built_valid':np.array([[True,True,True,True,True,False,False]]),
           'population_count':np.array([[100.,10.,20.,30.,40.,np.nan,np.nan]]),
           'built_surface_m2':np.array([[1.,0.,2.,3.,4.,np.nan,np.nan]])}
        bundle=(a,{}, {},np.array([[1.,2.,3.,4.,5.,6.,7.]]))
        bands=depth_bands(bundle)
        self.assertEqual([b['Estimated people'] for b in bands],[10,20,30,40])
        self.assertEqual([b['Area (km²)'] for b in bands],[2,3,4,5])
        self.assertEqual([b['Built-up surface (m²)'] for b in bands],[0,2,3,4])
        self.assertEqual([b['Flooded cells'] for b in bands],[1,1,1,1])
        clipped=depth_bands(bundle,2)
        self.assertEqual([b['Estimated people'] for b in clipped],[0,0,30,40])
        self.assertEqual(sum(b['Flooded cells'] for b in clipped),2)
        self.assertTrue(all(b['Estimated people']==0 for b in depth_bands(bundle,8)))
        with self.assertRaises(ValueError):depth_bands(bundle,-1)

    def test_real_bands_reconcile_all_quantities(self):
        bundle=patna.load_bundle()
        for threshold in (0.,.25,1.,1.5,2.,4.75,5.,8.):
            row=patna.summarize(bundle,threshold);bands=depth_bands(bundle,threshold)
            for key,total in [('Estimated people','Estimated exposed population (people)'),
                              ('Built-up surface (m²)','Exposed built-up surface (m²)'),
                              ('Area (km²)','Common flooded area (km²)'),('Flooded cells','Common flooded cells')]:
                self.assertTrue(math.isclose(math.fsum(b[key] for b in bands),row[total],rel_tol=1e-12,abs_tol=1e-8))

    def test_native_geographic_edges_and_values_not_interpolated(self):
        a,report,_,_=patna.load_bundle()
        p=map_payload(a['depth_m'],a['valid_depth'],a['common_valid'],report['target_grid']['transform'])
        np.testing.assert_allclose(p['bounds'],[[25.2,84.675],[25.74166666666667,86.075]],rtol=0,atol=1e-12)
        self.assertEqual((p['rows'],p['cols']),(65,168))
        np.testing.assert_array_equal(np.array(p['depth']).reshape(65,168),a['depth_m'])
        self.assertEqual(sum(p['common']),6113)
        html=map_html(a['depth_m'],a['valid_depth'],a['common_valid'],report['target_grid']['transform'])
        self.assertNotIn('/* GRID_DATA */',html)
        self.assertIn('imageSmoothingEnabled=false',html)
        self.assertIn('tile.openstreetmap.org',html)
        self.assertIn('OpenStreetMap contributors',html)
        self.assertIn('Fit study area',html)
        self.assertLess(len(html.encode()),500_000)

    def test_map_missing_zero_and_invalid_affine(self):
        p=map_payload(np.array([[0.,np.nan]]),np.array([[True,False]]),np.array([[True,False]]),(1,0,85,0,-1,26))
        self.assertEqual(p['depth'],[0,None])
        self.assertEqual(p['common'],[1,0])
        with self.assertRaises(ValueError):map_payload(np.ones((1,1)),np.ones((1,1),bool),np.ones((1,1),bool),(1,.1,85,0,-1,26))

    def test_exact_modes_modules_and_pilot_downloads(self):
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(str(patna.ROOT/'app.py'),default_timeout=30).run()
        self.assertEqual(app.sidebar.radio[0].options,['Synthetic Demo','REAL — Patna'])
        for mode in app.sidebar.radio[0].options:
            app.sidebar.radio[0].set_value(mode).run()
            self.assertEqual(tuple(app.sidebar.radio[1].options),MODULES)
            for module in MODULES:
                app.sidebar.radio[1].set_value(module).run()
                self.assertFalse(app.exception,(mode,module))
                if mode=='REAL — Patna':
                    self.assertEqual(app.metric[0].value,'2,840,321')
                    self.assertTrue(any('Not all of Patna district' in c.value for c in app.caption))
                    self.assertTrue(any('3,101' in m.value and 'excluded flooded cells' in m.value for m in app.markdown))
                    self.assertTrue(any(b.label=='Download current exposure CSV' for b in app.get('download_button')))
                    if module in ('Hazard','Data & methods'):
                        self.assertTrue(any(b.label=='Download pilot GeoTIFF' for b in app.get('download_button')))
        with patch('src.floodcat.wri.load_pilot',side_effect=FileNotFoundError('pilot fixture')):
            app.sidebar.radio[1].set_value('Hazard').run()
            self.assertFalse(app.exception)
            self.assertTrue(any('pilot fixture' in w.value for w in app.warning))
