"""Dashboard artifacts, independent arithmetic and fail-closed app behavior."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from src.floodcat import patna


class TestPatnaDashboard(unittest.TestCase):
    def test_verified_bundle_and_real_thresholds(self):
        bundle = patna.load_bundle()
        for t, count, excluded, people in [(0,2116,3101,2840320.5021073623),
                (1,264,1118,438591.0037895779), (2,183,927,331405.76219787373),
                (5,55,263,145829.6454354833), (8,0,0,0)]:
            row = patna.summarize(bundle,t)
            self.assertEqual(row['Common flooded cells'],count)
            self.assertEqual(row['Excluded flooded cells (incomplete joint coverage)'],excluded)
            self.assertAlmostEqual(row['Estimated exposed population (people)'],people)
            self.assertIn('NOT all of Patna district',row['Analysis domain'])
        self.assertFalse(bundle[0]['depth_m'].flags.writeable)
        self.assertAlmostEqual(row['Joint coverage (% of valid hazard cells)'],6113/10920*100)

    def test_independent_tiny_strict_threshold_missing_and_zero(self):
        # Only first two cells jointly covered. At 1 m equality is excluded;
        # valid zero exposure remains available; missing flooded cell excluded.
        a={'depth_m':np.array([[1.,2.,3.,0.]]), 'valid_depth':np.ones((1,4),bool),
           'common_valid':np.array([[True,True,False,True]]),
           'population_count':np.array([[10.,0.,np.nan,50.]]),
           'built_surface_m2':np.array([[4.,8.,np.nan,6.]]),
           'population_valid':np.array([[True,True,False,True]]),
           'built_valid':np.array([[True,True,False,True]])}
        row=patna.summarize((a,{}, {},np.array([[2.,3.,4.,5.]])),1)
        self.assertEqual(row['Estimated exposed population (people)'],0)
        self.assertEqual(row['Exposed built-up surface (m²)'],8)
        self.assertEqual(row['Common flooded area (km²)'],3)
        self.assertEqual(row['Common flooded cells'],1)
        self.assertEqual(row['Excluded flooded cells (incomplete joint coverage)'],1)
        for t in (-1,np.nan,np.inf,'1'):
            with self.assertRaises(ValueError): patna.summarize((a,{}, {},np.ones((1,4))),t)

    def test_each_checksum_and_missing_artifact_rejected(self):
        for name in ('aligned_common.npz','validation.json','audit.json'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp)/'bundle';shutil.copytree(patna.DIRECTORY,p)
                (p/name).write_bytes((p/name).read_bytes()+b' ')
                with self.assertRaisesRegex(patna.BundleError,'Checksum'):patna.load_bundle(p)
                (p/name).unlink()
                with self.assertRaises(patna.BundleError):patna.load_bundle(p)

    def test_rejected_audit_malformed_json_arrays_and_common_mask(self):
        for kind in ('audit','json','object','mask','shape','negative'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp)/'bundle';shutil.copytree(patna.DIRECTORY,p)
                if kind=='audit':
                    (p/'audit.json').write_text('{"status":"failed"}')
                elif kind=='json':
                    (p/'validation.json').write_text('not json')
                else:
                    with np.load(p/'aligned_common.npz',allow_pickle=False) as z:
                        a={k:z[k] for k in z.files}
                    if kind=='object':a['depth_m']=a['depth_m'].astype(object)
                    if kind=='mask':a['common_valid']=~a['common_valid']
                    if kind=='shape':a['depth_m']=a['depth_m'][:1]
                    if kind=='negative':a['depth_m'][0,0]=-1
                    np.savez_compressed(p/'aligned_common.npz',**a)
                    v=json.loads((p/'validation.json').read_text())
                    v['processed_artifact'].update(sha256=hashlib.sha256((p/'aligned_common.npz').read_bytes()).hexdigest(),bytes=(p/'aligned_common.npz').stat().st_size)
                    (p/'validation.json').write_text(json.dumps(v))
                manifest=Path(tmp)/'pins.json'
                manifest.write_text(json.dumps({n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in ('aligned_common.npz','validation.json','audit.json')}))
                with self.assertRaises(patna.BundleError):patna.load_bundle(p,manifest)

    def test_streamlit_real_view_and_invalid_bundle(self):
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(str(patna.ROOT/'app.py'),default_timeout=30).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.sidebar.radio[0].value,'Synthetic demo')
        app.sidebar.radio[0].set_value(patna.MODE).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[0].value,'2,840,321')
        self.assertEqual(len(app.sidebar.slider),1)
        self.assertEqual(len(app.sidebar.radio),1)
        self.assertEqual(len(app.get('download_button')),2)
        self.assertTrue(any('3,101' in w.value and 'Excluded flooded cells' in w.value for w in app.warning))
        self.assertTrue(any('55.98%' in m.value for m in app.markdown))
        app.sidebar.slider[0].set_value(1.).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[0].value,'438,591')
        with patch.object(patna,'load_bundle',side_effect=patna.BundleError('checksum fixture')):
            app.run()
            self.assertFalse(app.exception)
            self.assertFalse(app.metric)
            self.assertTrue(any('checksum fixture' in w.value for w in app.warning))
        app.sidebar.radio[0].set_value('REAL — WRI').run()
        self.assertFalse(app.exception)
        app.sidebar.radio[0].set_value('Synthetic demo').run()
        self.assertFalse(app.exception)
