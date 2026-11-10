"""Independent tiny area budgets, with no real exposure datasets."""

import math
import unittest

import numpy as np

from src.floodcat.aggregation import GridSpec, aggregate_extensive
from src.floodcat.exposure import calculate_exposure


def planar(shape, transform):
    # Synthetic equal-area coordinates in metres, not an actual source CRS.
    return GridSpec(shape, transform, crs="fixture equal-area metres", area_model="planar")


class TestAggregation(unittest.TestCase):
    def setUp(self):
        self.source = planar((2, 3), (1, 0, 0, 0, -1, 2))
        self.target = planar((1, 2), (1.5, 0, 0, 0, -2, 2))
        self.people = np.array([[1., 2., 3.], [4., 5., 6.]])

    def test_noninteger_resolution_conserves_people_and_built_surface(self):
        # Left target gets columns 0 + half of 1. Right gets half of 1 + 2.
        for source, expected, total in [
            (self.people, [[8.5, 12.5]], 21),
            ([[10., 40., 90.], [160., 250., 360.]], [[315., 595.]], 910),
        ]:
            with self.subTest(total=total):
                result = aggregate_extensive(source, self.source, self.target)
                np.testing.assert_allclose(result.values, expected, rtol=0, atol=1e-12)
                self.assertAlmostEqual(result.values.sum(), total)
                np.testing.assert_array_equal(result.valid, [[True, True]])
                np.testing.assert_array_equal(result.source_coverage_fraction, [[1, 1]])
                np.testing.assert_array_equal(result.valid_coverage_fraction, [[1, 1]])

    def test_offset_in_both_axes_and_boundary_clipping(self):
        # Target x=[.5,2.5], y=[.5,2.5]. Source row 0 contributes
        # .5*1 + 2 + .5*3 = 4; row 1 contributes .25*4 + .5*5 + .25*6 = 5.
        target = planar((1, 1), (2, 0, .5, 0, -2, 2.5))
        result = aggregate_extensive(self.people, self.source, target)
        self.assertEqual(result.known_values[0, 0], 9)
        self.assertEqual(result.source_coverage_fraction[0, 0], .75)
        self.assertEqual(result.valid_coverage_fraction[0, 0], .75)
        self.assertFalse(result.valid[0, 0])
        self.assertTrue(np.isnan(result.values[0, 0]))

    def test_target_extent_clips_source_without_redistribution(self):
        source = planar((1, 1), (2, 0, 0, 0, -2, 2))
        target = planar((1, 1), (1, 0, .5, 0, -1, 1.5))
        result = aggregate_extensive([[80]], source, target)
        # Target covers a quarter of the 4 m² source cell: 20 retained, 60 outside.
        self.assertEqual(result.values[0, 0], 20)
        self.assertEqual(result.valid_coverage_fraction[0, 0], 1)

    def test_nan_and_masked_sentinel_are_missing_independently(self):
        people = self.people.copy()
        people[0, 1] = np.nan
        pop = aggregate_extensive(people, self.source, self.target)
        built = aggregate_extensive([[10, 20, -9999], [40, 50, 60]],
            self.source, self.target, source_valid=[[True, True, False], [True, True, True]])
        # Missing 1 m² pixel is split into halves across the 3 m² targets.
        np.testing.assert_allclose(pop.known_values, [[7.5, 11.5]])
        np.testing.assert_allclose(pop.valid_coverage_fraction, [[5/6, 5/6]])
        np.testing.assert_array_equal(pop.source_coverage_fraction, [[1, 1]])
        self.assertTrue(np.isnan(pop.values).all())
        np.testing.assert_allclose(built.known_values, [[85, 95]])
        np.testing.assert_allclose(built.valid_coverage_fraction, [[1, 2/3]])
        np.testing.assert_array_equal(built.valid, [[True, False]])
        self.assertEqual(built.values[0, 0], 85)

    def test_all_missing_zero_and_no_overlap_are_distinct(self):
        missing = aggregate_extensive(np.full((2, 3), np.nan), self.source, self.target)
        zeros = aggregate_extensive(np.zeros((2, 3)), self.source, self.target)
        outside = planar((1, 1), (1, 0, 10, 0, -1, 20))
        absent = aggregate_extensive(self.people, self.source, outside)
        for result in (missing, absent):
            self.assertTrue(np.isnan(result.values).all())
            self.assertFalse(result.valid.any())
            self.assertEqual(result.known_values.sum(), 0)
            self.assertEqual(result.valid_coverage_fraction.sum(), 0)
        self.assertEqual(missing.source_coverage_fraction.sum(), 2)
        self.assertEqual(absent.source_coverage_fraction.sum(), 0)
        np.testing.assert_array_equal(zeros.values, [[0, 0]])
        self.assertTrue(zeros.valid.all())

    def test_edge_touch_is_not_overlap(self):
        # Nodata cell touches target at x=1 and must not invalidate it.
        source = planar((1, 2), (1, 0, 0, 0, -1, 1))
        target = planar((1, 1), (1, 0, 0, 0, -1, 1))
        result = aggregate_extensive([[7, np.nan]], source, target)
        self.assertEqual(result.values[0, 0], 7)
        outside = planar((1, 1), (1, 0, 2, 0, -1, 1))
        self.assertEqual(aggregate_extensive([[7, 8]], source, outside)
                         .source_coverage_fraction[0, 0], 0)

    def test_tiny_missing_overlap_does_not_round_to_complete(self):
        source = planar((1, 2), (1, 0, 0, 0, -1, 1))
        target = planar((1, 1), (1, 0, 1e-13, 0, -1, 1))
        result = aggregate_extensive([[5, np.nan]], source, target)
        self.assertGreater(result.valid_coverage_fraction[0, 0], .999999999999)
        self.assertFalse(result.valid[0, 0])
        self.assertTrue(np.isnan(result.values[0, 0]))

    def test_missing_pixels_outside_target_do_not_invalidate_it(self):
        source = planar((1, 2), (1, 0, 0, 0, -1, 1))
        target = planar((1, 1), (.5, 0, .25, 0, -.5, .75))
        result = aggregate_extensive([[8, np.nan]], source, target)
        self.assertEqual(result.values[0, 0], 2)
        self.assertTrue(result.valid[0, 0])

    def test_partial_coverage_includes_known_and_missing_source_areas(self):
        source = planar((1, 2), (1, 0, 0, 0, -1, 1))
        target = planar((1, 1), (4, 0, -1, 0, -1, 1))
        result = aggregate_extensive([[8, np.nan]], source, target)
        # Of 4 m² target area: 1 known, 1 nodata, 2 outside source extent.
        self.assertEqual(result.known_values[0, 0], 8)
        self.assertEqual(result.source_coverage_fraction[0, 0], .5)
        self.assertEqual(result.valid_coverage_fraction[0, 0], .25)
        self.assertTrue(np.isnan(result.values[0, 0]))

    def test_axis_direction_and_identity(self):
        result = aggregate_extensive(self.people, self.source, self.source)
        np.testing.assert_array_equal(result.values, self.people)
        # Reverse source and target axes independently; preserve array indexing.
        for flip_x, flip_y in [(True, False), (False, True), (True, True)]:
            source = planar((2, 3), (-1 if flip_x else 1, 0, 3 if flip_x else 0,
                                      0, 1 if flip_y else -1, 0 if flip_y else 2))
            values = self.people[::(-1 if flip_y else 1), ::(-1 if flip_x else 1)]
            np.testing.assert_allclose(aggregate_extensive(values, source, self.target).values,
                                       [[8.5, 12.5]])
        target = planar((1, 2), (-1.5, 0, 3, 0, 2, 0))
        np.testing.assert_allclose(aggregate_extensive(self.people, self.source, target).values,
                                   [[12.5, 8.5]])

    def test_finer_target_retains_fractional_counts(self):
        source = planar((1, 1), (3, 0, 0, 0, -2, 2))
        target = planar((2, 3), (1, 0, 0, 0, -1, 2))
        result = aggregate_extensive([[1.5]], source, target)
        np.testing.assert_allclose(result.values, np.full((2, 3), .25))
        self.assertEqual(result.values.sum(), 1.5)

    def test_wgs84_area_weighting_against_independent_quadrature(self):
        source = GridSpec((1, 1), (2, 0, 85, 0, -60, 60))
        target = GridSpec((2, 1), (2, 0, 85, 0, -30, 60))
        result = aggregate_extensive([[120]], source, target)
        # Independent midpoint integration of the ellipsoid's differential area.
        # No use of the production antiderivative or WRI area implementation.
        def area_integral(south, north):
            phi = np.deg2rad(south + (np.arange(100000) + .5) * (north-south)/100000)
            f = 1 / 298.257223563
            e2 = f * (2-f)
            return np.mean(np.cos(phi) / (1-e2*np.sin(phi)**2)**2) * math.radians(north-south)
        low, high = area_integral(0, 30), area_integral(30, 60)
        np.testing.assert_allclose(result.values[:, 0], [120*high/(low+high),
                                                       120*low/(low+high)], rtol=1e-11)
        self.assertAlmostEqual(result.values.sum(), 120, places=12)
        self.assertLess(result.values[0, 0], 60)  # Degree-area weighting would give 60.

    def test_native_wri_grid_coarsening_fixture(self):
        step = 1/120
        target = GridSpec((2, 2), (step, 0, 85, 0, -step, 25.85))
        source = GridSpec((6, 6), (step/3, 0, 85, 0, -step/3, 25.85))
        result = aggregate_extensive(np.full((6, 6), 2.5), source, target)
        np.testing.assert_allclose(result.values, np.full((2, 2), 22.5), atol=1e-8, rtol=0)
        self.assertAlmostEqual(result.values.sum(), 90, places=8)
        self.assertTrue(result.valid.all())

    def test_aggregation_handoff_keeps_incomplete_exposure_unknown(self):
        population = aggregate_extensive([[1, np.nan, 3], [4, 5, 6]], self.source, self.target)
        built = aggregate_extensive(self.people*10, self.source, self.target)
        result = calculate_exposure([[1, 2]], [[True, True]], population.values,
            built.values, population_valid=population.valid, built_surface_valid=built.valid)
        self.assertIsNone(result.population.total_exposed)
        self.assertEqual(result.population.available_flooded_cells, 0)
        self.assertEqual(result.built_surface_m2.total_exposed, 210)
        # Partial source subtotals remain accessible at the aggregation stage.
        self.assertEqual(population.known_values.sum(), 19)

    def test_input_validation(self):
        for values in [np.ones(6), np.ones((1, 3)), np.empty((0, 3)),
                       np.ones((2, 3), dtype=bool), np.ones((2, 3), dtype=complex),
                       np.full((2, 3), "2"), np.ma.array(self.people, mask=False)]:
            with self.subTest(values=values), self.assertRaises(ValueError):
                aggregate_extensive(values, self.source, self.target)
        for mask in [np.ones((2, 3)), [[True]], np.ma.array(np.ones((2, 3), dtype=bool))]:
            with self.subTest(mask=mask), self.assertRaises(ValueError):
                aggregate_extensive(self.people, self.source, self.target, source_valid=mask)
        for bad in [-1, np.inf, -np.inf]:
            values = self.people.copy()
            values[0, 0] = bad
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                aggregate_extensive(values, self.source, self.target)
        # Explicit invalidity may carry arbitrary numeric sentinels.
        result = aggregate_extensive([[np.inf, -2, np.nan], [4, 5, 6]], self.source,
                                     self.target, source_valid=[[False]*3, [True]*3])
        np.testing.assert_allclose(result.known_values, [[6.5, 8.5]])

    def test_grid_validation_and_reprojection_rejection(self):
        for shape in [None, (), (0, 2), (1.5, 2), (True, 2), (2, 3, 4)]:
            with self.subTest(shape=shape), self.assertRaises(ValueError):
                aggregate_extensive(self.people, planar(shape, self.source.transform), self.target)
        with self.assertRaises(ValueError):
            aggregate_extensive(self.people, self.source, planar((True, 2), self.target.transform))
        for transform in [(0, 0, 0, 0, -1, 2), (1, .1, 0, 0, -1, 2),
                          (1, 0, 0, .1, -1, 2), (1, 0, 0, 0, 0, 2),
                          (1, 0, np.inf, 0, -1, 2), (1, 0, 0),
                          (1e-20, 0, 1, 0, -1, 2)]:
            with self.subTest(transform=transform), self.assertRaises(ValueError):
                aggregate_extensive(self.people, planar((2, 3), transform), self.target)
        for grid in [None, GridSpec((2, 3), (1, 0, 0, 0, -1, 2), crs=""),
                     GridSpec((2, 3), (1, 0, 0, 0, -1, 2), area_model="planar"),
                     GridSpec((2, 3), (1, 0, 0, 0, -1, 2), crs="EPSG:3857"),
                     GridSpec((2, 3), (1, 0, 179, 0, -1, 2)),
                     GridSpec((2, 3), (1, 0, 0, 0, -1, 91)),
                     GridSpec((2, 3), self.source.transform, crs="other", area_model="planar")]:
            with self.subTest(grid=grid), self.assertRaises(ValueError):
                aggregate_extensive(self.people, grid, self.target)

    def test_overflow_and_large_integer_totals(self):
        target = planar((1, 1), (3, 0, 0, 0, -2, 2))
        integers = np.full((2, 3), np.iinfo(np.int64).max)
        result = aggregate_extensive(integers, self.source, target)
        self.assertEqual(result.values[0, 0], 6*float(np.iinfo(np.int64).max))
        with self.assertRaises(ValueError):
            aggregate_extensive(np.full((2, 3), 1e308), self.source, target)

    def test_inputs_are_unchanged(self):
        mask = np.ones((2, 3), dtype=bool)
        mask[0, 0] = False
        before_values, before_mask = self.people.copy(), mask.copy()
        aggregate_extensive(self.people, self.source, self.target, source_valid=mask)
        np.testing.assert_array_equal(self.people, before_values)
        np.testing.assert_array_equal(mask, before_mask)
