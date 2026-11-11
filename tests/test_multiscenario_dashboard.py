"""Independent real-array budgets, all selectors and corruption rejection."""
import json
import math
from pathlib import Path
import shutil
import tempfile
import unittest
import numpy as np
from src.floodcat import patna, scenarios
from src.floodcat.patna_analysis import depth_bands, screening_summary, POP_WEIGHT_LABEL, BUILT_WEIGHT_LABEL


class TestScenarioDashboard(unittest.TestCase):
    def test_all_fifteen_independent_sums_and_reuse(self):
        catalog,report=scenarios.load_scenarios();base=patna.load_bundle()
        self.assertEqual(len(catalog),15)
        self.assertEqual(report['common_cells'],6113)
        for key,bundle in catalog.items():
            a=bundle[0]
            np.testing.assert_array_equal(a['common_valid'],base[0]['common_valid'])
            np.testing.assert_array_equal(a['population_count'],base[0]['population_count'])
            np.testing.assert_array_equal(a['built_surface_m2'],base[0]['built_surface_m2'])
            for t in (0.,1.,2.,5.,15.):
                row=scenarios.comparison_row(bundle,t)
                cells=[(r,c) for r in range(65) for c in range(168) if a['common_valid'][r,c] and float(a['depth_m'][r,c])>t]
                pop=math.fsum(float(a['population_count'][r,c]) for r,c in cells)
                built=math.fsum(float(a['built_surface_m2'][r,c]) for r,c in cells)
                weighted=math.fsum(float(a['population_count'][r,c])*float(a['depth_m'][r,c]) for r,c in cells)
                self.assertEqual(row['Estimated exposed population (people)'],pop)
                self.assertEqual(row['Exposed built-up surface (m²)'],built)
                self.assertEqual(row[POP_WEIGHT_LABEL],weighted)
                self.assertEqual(row['Common flooded cells'],len(cells))
                bands=depth_bands(bundle,t)
                self.assertAlmostEqual(sum(x['Estimated people'] for x in bands),pop,places=7)
                self.assertEqual(sum(x['Flooded cells'] for x in bands),len(cells))
                self.assertEqual(row['Scenario ID'],key)
                self.assertEqual(row['Exposure year'],2020)
        hist=scenarios.comparison_row(catalog['Historical_T100'],0)
        self.assertEqual(hist['Common flooded cells'],2116)
        self.assertAlmostEqual(hist[POP_WEIGHT_LABEL],2923557.7298654984)
        self.assertAlmostEqual(hist[BUILT_WEIGHT_LABEL],35969112.45142127)

    def test_independent_source_decoder_and_historical_masks(self):
        from PIL import Image
        catalog,report=scenarios.load_scenarios()
        for record in report['scenarios']:
            with Image.open(patna.ROOT/'data/demo_real'/('FloodCAT_Patna_WRI_'+record['id']+'.tif')) as image:
                source=np.array(image)
            bundle=catalog[record['id']]
            np.testing.assert_array_equal(source,bundle[0]['depth_m'])
            np.testing.assert_array_equal(np.isfinite(source)&(source!=-9999),bundle[0]['valid_depth'])

    def test_corruption_or_missing_rejected(self):
        for name in ('hazards.npz','validation.json'):
            with tempfile.TemporaryDirectory() as d:
                p=Path(d)/'bundle';shutil.copytree(scenarios.DIRECTORY,p)
                (p/name).write_bytes((p/name).read_bytes()+b'changed')
                with self.assertRaises(patna.BundleError):scenarios.load_scenarios(p)
                (p/name).unlink()
                with self.assertRaises(patna.BundleError):scenarios.load_scenarios(p)

    def test_safe_percentages_hand_fixture(self):
        rows=scenarios.differences({'a':0,'b':4},{'a':3,'b':2},['a','b'])
        self.assertIsNone(rows[0]['Percentage difference'])
        self.assertEqual(rows[0]['Absolute difference'],3)
        self.assertEqual(rows[1]['Percentage difference'],-50)

    def test_selectors_all_modules_and_comparison(self):
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(str(patna.ROOT/'app.py'),default_timeout=30).run()
        app.sidebar.radio[0].set_value('REAL — Patna').run()
        self.assertEqual(app.sidebar.selectbox[0].value,'Historical WATCH')
        self.assertEqual(app.sidebar.selectbox[1].value,100)
        catalog,_=scenarios.load_scenarios()
        for climate,token in scenarios.CLIMATES.items():
            app.sidebar.selectbox[0].set_value(climate).run()
            for period in scenarios.PERIODS:
                app.sidebar.selectbox[1].set_value(period).run()
                expected=patna.summarize(catalog[f'{token}_T{period}'],0)
                self.assertFalse(app.exception)
                self.assertEqual(app.metric[0].value,f"{expected['Estimated exposed population (people)']:,.0f}")
                for module in ('Exposure','Vulnerability'):
                    app.sidebar.radio[1].set_value(module).run()
                    self.assertFalse(app.exception)
                    self.assertEqual(app.metric[0].value,f"{expected['Estimated exposed population (people)']:,.0f}")
        app.sidebar.radio[1].set_value('Compare').run()
        for choice in ('Return periods','T100 climates','Two scenarios','Threshold sensitivity'):
            next(r for r in app.radio if r.label=='Comparison').set_value(choice).run()
            self.assertFalse(app.exception)
            self.assertTrue(any(x.label=='Download scenario comparison CSV' for x in app.get('download_button')))
        app.sidebar.radio[0].set_value('Synthetic Demo').run()
        self.assertFalse(app.exception)
