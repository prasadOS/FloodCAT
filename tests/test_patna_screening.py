"""Independent screening products, missingness, ranking and UI semantics."""
import math
import unittest
import numpy as np
from src.floodcat import patna
from src.floodcat.patna_analysis import (MODULES, weighted_cells, screening_summary, priority_cells,
                                        SCREENING_LABEL, POP_WEIGHT_LABEL, BUILT_WEIGHT_LABEL)
from src.floodcat.geographic_map import map_payload, map_html


def fixture():
    a={'depth_m':np.array([[0.,1.,2.],[5.,6.,3.]]),
       'valid_depth':np.ones((2,3),bool), 'common_valid':np.array([[True,True,True],[True,False,True]]),
       'population_valid':np.array([[True,True,True],[True,False,True]]),
       'built_valid':np.array([[True,True,True],[True,False,True]]),
       'population_count':np.array([[100.,10.,20.],[0.,np.nan,20.]]),
       'built_surface_m2':np.array([[10.,4.,0.],[8.,np.nan,2.]])}
    return a, {'target_grid':{'transform':(1.,0.,84.,0.,-1.,26.)}}, {}, np.ones((2,3))


class TestPatnaScreening(unittest.TestCase):
    def test_hand_products_thresholds_and_zero(self):
        b=fixture();a=b[0]
        # Common products at >0: people 10*1+20*2+0*5+20*3=110;
        # built 4*1+0*2+8*5+2*3=50. Missing 6 m cell excluded.
        for threshold, people, built in ((0,110,50),(1,100,46),(2,60,46),(3,0,40),(5,0,0),(8,0,0)):
            s=screening_summary(b,threshold)
            self.assertEqual(s[POP_WEIGHT_LABEL],people)
            self.assertEqual(s[BUILT_WEIGHT_LABEL],built)
            self.assertEqual(s['Population at depth >1 m (people)'],40)
            self.assertEqual(s['Population at depth >2 m (people)'],20)
            self.assertEqual(s['Population at depth >5 m (people)'],0)
        selected,pop,built=weighted_cells(b,1)
        np.testing.assert_array_equal(selected,[[False,False,True],[True,False,True]])
        self.assertTrue(np.isnan(pop[1,1]));self.assertTrue(np.isnan(built[1,1]))
        self.assertEqual(pop[1,0],0)  # valid zero people in selected flooded cell
        self.assertEqual(built[0,2],0)  # valid zero built surface
        self.assertEqual(pop[0,1],0)  # below threshold: defined zero indicator
        self.assertFalse(pop.flags.writeable)
        self.assertTrue(np.isnan(a['population_count'][1,1]))
        for threshold in (-1,np.nan,np.inf,'1',True):
            with self.assertRaises(ValueError): screening_summary(b,threshold)

    def test_nan_depth_missing_cell_and_overflow(self):
        b=fixture();a=b[0]
        a['depth_m'][1,1]=np.nan;a['valid_depth'][1,1]=False
        self.assertEqual(screening_summary(b)[POP_WEIGHT_LABEL],110)
        a['population_count'][0,2]=1e308
        with self.assertRaisesRegex(ValueError,'finite float'):screening_summary(b)

    def test_rank_coordinates_ties_and_no_incomplete_ranking(self):
        b=fixture();rows=priority_cells(b)
        self.assertEqual([(r['WRI row (0-based)'],r['WRI column (0-based)']) for r in rows],[(1,2),(0,2),(0,1),(1,0)])
        self.assertEqual([r[POP_WEIGHT_LABEL] for r in rows],[60,40,10,0])
        self.assertEqual(rows[0]['Longitude (°E)'],86.5)
        self.assertEqual(rows[0]['Latitude (°N)'],24.5)
        self.assertEqual(rows[0]['Modeled flood depth (m)'],3)
        self.assertEqual(rows[0]['Estimated population (people/cell)'],20)
        self.assertEqual(priority_cells(b,5),[])
        b[0]['population_count'][0,2]=30 # tie at 60: row-major order
        rows=priority_cells(b,limit=2)
        self.assertEqual([(r['WRI row (0-based)'],r['WRI column (0-based)']) for r in rows],[(0,2),(1,2)])
        for limit in (0,-1,True,1.5):
            with self.assertRaises(ValueError):priority_cells(b,limit=limit)

    def test_weighted_native_payload_units_and_missing_not_zero(self):
        b=fixture();a=b[0];_,pop,_=weighted_cells(b,1)
        kwargs=dict(population=a['population_count'],weighted_population=pop,threshold_m=1,initial_layer='weighted')
        p=map_payload(a['depth_m'],a['valid_depth'],a['common_valid'],b[1]['target_grid']['transform'],**kwargs)
        self.assertEqual(p['weightedPopulation'],[0,0,40,0,None,60])
        self.assertEqual(p['population'],[100,10,20,0,None,20])
        self.assertEqual(p['bounds'],[[24.,84.],[26.,87.]])
        self.assertEqual(p['initialLayer'],'weighted')
        html=map_html(a['depth_m'],a['valid_depth'],a['common_valid'],b[1]['target_grid']['transform'],**kwargs)
        for text in ('Depth-weighted population exposure','person-metres','Incomplete / excluded','Flood Depth (m)','imageSmoothingEnabled=false'):
            self.assertIn(text,html)
        bad=pop.copy();bad[0,2]=41
        with self.assertRaisesRegex(ValueError,'product'):
            map_payload(a['depth_m'],a['valid_depth'],a['common_valid'],b[1]['target_grid']['transform'],**(kwargs|{'weighted_population':bad}))
        self.assertIn('m²·m',BUILT_WEIGHT_LABEL)
        self.assertIn('not flood volume',screening_summary(b)['Built-up indicator interpretation'])
        self.assertIn('not a validated vulnerability model',SCREENING_LABEL)

    def test_real_independent_sums_and_priorities(self):
        b=patna.load_bundle();a=b[0]
        for t in (0,1,2,5,8):
            # Independent Python iteration over native samples, not weighted_cells.
            expected_pop=[];expected_built=[]
            for r in range(65):
                for c in range(168):
                    if a['common_valid'][r,c] and a['depth_m'][r,c]>t:
                        expected_pop.append(float(a['population_count'][r,c])*float(a['depth_m'][r,c]))
                        expected_built.append(float(a['built_surface_m2'][r,c])*float(a['depth_m'][r,c]))
            s=screening_summary(b,t)
            self.assertAlmostEqual(s[POP_WEIGHT_LABEL],math.fsum(expected_pop),places=8)
            self.assertAlmostEqual(s[BUILT_WEIGHT_LABEL],math.fsum(expected_built),places=7)
            rows=priority_cells(b,t)
            self.assertLessEqual(len(rows),10)
            self.assertEqual([r[POP_WEIGHT_LABEL] for r in rows],sorted([r[POP_WEIGHT_LABEL] for r in rows],reverse=True))
            for row in rows:
                r,c=row['WRI row (0-based)'],row['WRI column (0-based)']
                self.assertTrue(a['common_valid'][r,c]);self.assertGreater(a['depth_m'][r,c],t)
        top=priority_cells(b)[0]
        self.assertEqual((top['WRI row (0-based)'],top['WRI column (0-based)']),(12,88))
        self.assertAlmostEqual(top['Longitude (°E)'],85.4125)
        self.assertAlmostEqual(top['Latitude (°N)'],25.6375)

    def test_streamlit_screening_and_consolidated_exposure(self):
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(str(patna.ROOT/'app.py'),default_timeout=30).run()
        app.sidebar.radio[0].set_value('REAL — Patna').run()
        self.assertEqual(tuple(app.sidebar.radio[1].options),('Overview','Hazard','Exposure','Vulnerability','Compare','Data & methods'))
        self.assertNotIn('Depth severity',app.sidebar.radio[1].options)
        app.sidebar.radio[1].set_value('Vulnerability').run()
        self.assertFalse(app.exception)
        self.assertTrue(any(SCREENING_LABEL==s.value for s in app.subheader))
        self.assertTrue(any(m.label==POP_WEIGHT_LABEL and m.value=='2,923,558' for m in app.metric))
        self.assertTrue(any('not flood volume' in c.value for c in app.caption))
        self.assertTrue(any(b.label=='Download raster-cell priorities CSV' for b in app.get('download_button')))
        app.sidebar.slider[0].set_value(8.).run()
        self.assertFalse(app.exception)
        self.assertFalse(any(b.label=='Download raster-cell priorities CSV' for b in app.get('download_button')))
        self.assertTrue(any(m.label==POP_WEIGHT_LABEL and m.value=='0' for m in app.metric))
        app.sidebar.radio[1].set_value('Exposure').run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.get('plotly_chart')),3)
        self.assertTrue(any(e.label=='Detailed depth-band values' for e in app.expander))
        self.assertTrue(any(b.label=='Download depth-band CSV' for b in app.get('download_button')))

        app.sidebar.radio[1].set_value('Data & methods').run()
        self.assertFalse(app.exception)
        self.assertTrue(any('Σᵢ∈S populationᵢ × depthᵢ' in m.value and 'UNDRR' in m.value for m in app.markdown))
