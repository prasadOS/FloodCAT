"""Hand-calculated fixtures; no real exposure datasets."""
import unittest
import numpy as np
from src.floodcat.exposure import calculate_exposure


class TestExposure(unittest.TestCase):
    def setUp(self):
        self.depth = np.array([[0., 1., 2.], [3., np.nan, -9999.]])
        self.valid = np.array([[True, True, True], [True, False, False]])
        self.people = np.array([[100., 10., 20.], [30., 400., 500.]])
        self.built = np.array([[1000., 100., 200.], [300., 4000., 5000.]])

    def run_engine(self, **kwargs):
        args = dict(depth_m=self.depth, valid_depth=self.valid,
                    population_count=self.people, built_surface_m2=self.built)
        args.update(kwargs)
        return calculate_exposure(**args)

    def test_strict_threshold_dry_and_hazard_nodata(self):
        for threshold, people, built, cells in [(0, 60, 600, 3), (1, 50, 500, 2),
                                                (2, 30, 300, 1), (3, 0, 0, 0)]:
            with self.subTest(threshold=threshold):
                r = self.run_engine(threshold_m=threshold)
                self.assertEqual(r.population.total_exposed, people)
                self.assertEqual(r.built_surface_m2.total_exposed, built)
                self.assertEqual(r.population.flooded_cells, cells)
                self.assertEqual(r.population.valid_hazard_cells, 4)

    def test_positive_depth_outside_hazard_mask_is_excluded(self):
        depth = np.array([[1., 8.]])
        result = calculate_exposure(depth, [[True, False]], [[2., 900.]], [[3., 800.]])
        self.assertEqual(result.population.total_exposed, 2)
        self.assertEqual(result.built_surface_m2.total_exposed, 3)
        self.assertEqual(result.population.available_cells, 1)

    def test_population_mask_and_independent_complete_built_total(self):
        self.people[0, 1] = -9999
        mask = np.array([[True, False, True], [True, True, True]])
        result = self.run_engine(population_valid=mask)
        self.assertIsNone(result.population.total_exposed)
        self.assertEqual(result.population.known_exposed, 50)
        self.assertEqual(result.population.missing_flooded_cells, 1)
        self.assertEqual(result.built_surface_m2.total_exposed, 600)
        self.assertEqual(result.built_surface_m2.coverage_fraction, 1)

    def test_zero_is_available(self):
        r = self.run_engine(population_count=np.zeros((2, 3)), built_surface_m2=np.zeros((2, 3)))
        for m in (r.population, r.built_surface_m2):
            self.assertEqual(m.total_exposed, 0)
            self.assertEqual(m.flooded_coverage_fraction, 1)
            self.assertEqual(m.missing_cells, 0)

    def test_independent_missing_exposure_and_coverage(self):
        self.people[0, 1] = np.nan
        self.built[1, 0] = -9999
        mask = np.array([[True, True, True], [False, True, True]])
        r = self.run_engine(built_surface_valid=mask)
        self.assertEqual(r.population.known_exposed, 50)
        self.assertEqual(r.built_surface_m2.known_exposed, 300)
        for m in (r.population, r.built_surface_m2):
            self.assertIsNone(m.total_exposed)
            self.assertEqual(m.missing_flooded_cells, 1)
            self.assertEqual(m.coverage_fraction, 3 / 4)
            self.assertEqual(m.flooded_coverage_fraction, 2 / 3)

    def test_missing_dry_exposure_does_not_invalidate_flooded_total(self):
        self.people[0, 0] = np.nan
        r = self.run_engine().population
        self.assertEqual(r.total_exposed, 60)
        self.assertEqual(r.missing_cells, 1)
        self.assertEqual(r.missing_flooded_cells, 0)

    def test_all_missing_and_empty_domains(self):
        missing = np.full((2, 3), np.nan)
        r = self.run_engine(population_count=missing).population
        self.assertIsNone(r.total_exposed)
        self.assertEqual(r.known_exposed, 0)
        self.assertEqual(r.flooded_coverage_fraction, 0)
        for kwargs in [dict(threshold_m=9), dict(valid_depth=np.zeros((2, 3), dtype=bool))]:
            r = self.run_engine(population_count=missing, **kwargs).population
            self.assertEqual(r.total_exposed, 0)
            self.assertIsNone(r.flooded_coverage_fraction)
        self.assertIsNone(r.coverage_fraction)

    def test_conservation_and_fractional_counts(self):
        # Independent manual partition: dry 0.5, wet bands 1.25 + 2.5 + 3.75.
        p = np.array([[0.5, 1.25, 2.5], [3.75, 99, 99]])
        low = self.run_engine(population_count=p).population.total_exposed
        high = self.run_engine(population_count=p, threshold_m=1).population.total_exposed
        self.assertEqual(low, 7.5)
        self.assertEqual(high, 6.25)
        self.assertEqual(low - high, 1.25)
        self.assertEqual(low + 0.5, 8)
        self.assertEqual(self.run_engine().built_surface_m2.total_exposed + 1000, 1600)

    def test_shape_and_type_validation(self):
        for name in ['depth_m', 'valid_depth', 'population_count', 'built_surface_m2',
                     'population_valid', 'built_surface_valid']:
            for value in [np.ones((1, 3)), np.ones(6), np.empty((0, 3))]:
                with self.subTest(name=name, shape=value.shape), self.assertRaises(ValueError):
                    self.run_engine(**{name: value})
        for kwargs in [dict(valid_depth=np.ones((2, 3))),
                       dict(population_valid=np.ones((2, 3))),
                       dict(population_count=np.full((2, 3), '2')),
                       dict(built_surface_m2=np.ones((2, 3), dtype=complex)),
                       dict(depth_m=np.ma.array(self.depth, mask=False)),
                       dict(population_count=np.ma.array(self.people, mask=False))]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.run_engine(**kwargs)

    def test_invalid_thresholds_and_values(self):
        for t in [-1, np.nan, np.inf, True, '1', [1], 1j]:
            with self.subTest(threshold=t), self.assertRaises(ValueError):
                self.run_engine(threshold_m=t)
        for name in ['depth_m', 'population_count', 'built_surface_m2']:
            for bad in [-1, np.inf, -np.inf] + ([np.nan] if name == 'depth_m' else []):
                value = np.ones((2, 3))
                value[0, 0] = bad
                with self.subTest(name=name, bad=bad), self.assertRaises(ValueError):
                    self.run_engine(**{name: value})

    def test_overflow_rejected_and_integer_sum_not_wrapped(self):
        values = np.full((2, 3), np.iinfo(np.int64).max, dtype=np.int64)
        self.assertEqual(self.run_engine(population_count=values).population.total_exposed,
                         3 * float(np.iinfo(np.int64).max))
        with self.assertRaises(ValueError):
            self.run_engine(population_count=np.full((2, 3), 1e308))

    def test_inputs_unchanged(self):
        copies = [a.copy() for a in (self.depth, self.valid, self.people, self.built)]
        self.run_engine()
        for before, after in zip(copies, (self.depth, self.valid, self.people, self.built)):
            np.testing.assert_array_equal(before, after)
