"""Cross-CRS numerical evidence, with independent analytic/area budgets.

Install requirements-science.txt to run these tests; the lightweight app does not
import the optional pipeline. Quadrature shares PROJ coordinate transforms, but
does not use polygon intersections or the production equal-area area calculation.
Projection controls are checked separately using exact Mollweide identities.
"""

import math
import unittest
import importlib.util

import numpy as np

SCIENCE_AVAILABLE = all(importlib.util.find_spec(n) for n in ("pyproj", "shapely"))
if SCIENCE_AVAILABLE:
    from pyproj import Geod, Transformer
    from src.floodcat.remapping import (RasterGrid, build_conservative_map,
                                        WORLD_MOLLWEIDE, AREA_CRS)
    from src.floodcat.exposure import calculate_exposure


def moll_grid(shape=(1, 1), step=100000., lon=85., lat=25.7):
    x, y = Transformer.from_crs(4326, WORLD_MOLLWEIDE, always_xy=True).transform(lon, lat)
    return RasterGrid(shape, (step, 0, x-step*shape[1]/2, 0, -step, y+step*shape[0]/2),
                      WORLD_MOLLWEIDE)


def moll_quadrature(grid, bounds=None, panels=512):
    """Integrate physical ellipsoid area in native Mollweide x/y coordinates.

    Mollweide is equal-area on the sphere of radius a, not on the ellipsoid.
    dA_ellipsoid/dA_sphere=(1-e²)/(1-e² sin²(phi))². Integrate this Jacobian
    directly over source x/y support, optionally clipped by a lon/lat rectangle.
    Composite Gauss-Legendre integration avoids any transformed polygon area.
    """
    dx, _, left, _, dy, top = grid.transform
    right, bottom = left+dx*grid.shape[1], top+dy*grid.shape[0]
    forward = Transformer.from_crs(4326, WORLD_MOLLWEIDE, always_xy=True)
    inverse = Transformer.from_crs(WORLD_MOLLWEIDE, 4326, always_xy=True)
    low, high = bottom, top
    if bounds:
        west, south, east, north = bounds
        low = max(low, forward.transform(0, south)[1])
        high = min(high, forward.transform(0, north)[1])
    if low >= high:
        return 0.
    nodes, weights = np.polynomial.legendre.leggauss(16)
    edges = np.linspace(low, high, panels+1)
    midpoints, halves = (edges[1:]+edges[:-1])/2, np.diff(edges)/2
    y = (midpoints[:, None]+halves[:, None]*nodes).ravel()
    _, lat = inverse.transform(np.zeros_like(y), y)
    f = 1/298.257223563
    e2 = f*(2-f)
    jacobian = (1-e2)/(1-e2*np.sin(np.deg2rad(lat))**2)**2
    width = np.full_like(y, right-left)
    if bounds:
        x_west, _ = forward.transform(np.full_like(lat, west), lat)
        x_east, _ = forward.transform(np.full_like(lat, east), lat)
        width = np.maximum(0, np.minimum(right, x_east)-np.maximum(left, x_west))
    return float(np.sum((width*jacobian).reshape(-1, 16)*weights*halves[:, None]))


@unittest.skipUnless(SCIENCE_AVAILABLE, "Optional science dependencies not installed")
class TestRemapping(unittest.TestCase):
    def test_mollweide_exact_projection_controls_and_roundtrip(self):
        forward = Transformer.from_crs(4326, WORLD_MOLLWEIDE, always_xy=True)
        inverse = Transformer.from_crs(WORLD_MOLLWEIDE, 4326, always_xy=True)
        # Snyder Mollweide identities: 2theta+sin(2theta)=pi*sin(phi),
        # x=2sqrt(2)*a*lambda*cos(theta)/pi, y=sqrt(2)*a*sin(theta).
        # Pick theta=pi/6 so no numerical inverse projection is used by the oracle.
        theta = math.pi/6
        latitude = math.degrees(math.asin((math.pi/3+math.sqrt(3)/2)/math.pi))
        for longitude, lat, expected_x, expected_y in [
            (0, 0, 0, 0),
            (90, 0, math.sqrt(2)*6378137, 0),
            (30, latitude, math.sqrt(6)*6378137/6, 6378137/math.sqrt(2)),
        ]:
            actual = forward.transform(longitude, lat)
            np.testing.assert_allclose(actual, [expected_x, expected_y], rtol=0, atol=2e-8)
            np.testing.assert_allclose(inverse.transform(*actual), [longitude, lat], atol=1e-11, rtol=0)
        lon, lat = np.meshgrid([84.8, 85.2, 85.6], [25.4, 25.7, 26.])
        np.testing.assert_allclose(inverse.transform(*forward.transform(lon, lat)), [lon, lat],
                                   rtol=0, atol=2e-11)

    def test_mollweide_physical_area_against_jacobian_quadrature(self):
        for lat, step in [(-30, 300000.), (0, 300000.), (25.7, 100.),
                          (25.7, 300000.), (65, 300000.)]:
            with self.subTest(lat=lat, step=step):
                source = moll_grid(step=step, lat=lat)
                target = RasterGrid((1, 1), (20, 0, 75, 0, -10, lat+5), "EPSG:4326")
                mapping = build_conservative_map(source, target)
                expected = moll_quadrature(source)
                self.assertLess(abs(mapping.source_area_m2[0]/expected-1), 2e-8)
                # Spherical projected m² differ materially from ellipsoid m².
                self.assertGreater(abs(expected/step**2-1), .003)

    def test_dense_geodesic_area_crosscheck(self):
        source = moll_grid(step=300000.)
        target = RasterGrid((1, 1), (4, 0, 83, 0, -4, 27.7), "EPSG:4326")
        mapping = build_conservative_map(source, target)
        dx, _, x, _, dy, y = source.transform
        corners = [(x, y), (x+dx, y), (x+dx, y+dy), (x, y+dy), (x, y)]
        xx, yy = [], []
        for start, end in zip(corners[:-1], corners[1:]):
            fraction = np.linspace(0, 1, 4096, endpoint=False)
            xx.extend(start[0] + (end[0]-start[0])*fraction)
            yy.extend(start[1] + (end[1]-start[1])*fraction)
        lon, lat = Transformer.from_crs(WORLD_MOLLWEIDE, 4326, always_xy=True).transform(xx, yy)
        expected = abs(Geod(ellps="WGS84").polygon_area_perimeter(lon, lat)[0])
        # Supplementary cross-check: shares PROJ transforms and ellipsoid, so
        # this alone would not independently validate the projection or model.
        self.assertLess(abs(mapping.source_area_m2[0]/expected-1), 2e-8)

    def test_geographic_rectangle_area_against_independent_surface_integral(self):
        source = moll_grid(step=500000.)
        target = RasterGrid((1, 1), (.4, 0, 84.8, 0, -.3, 25.85), "EPSG:4326")
        mapping = build_conservative_map(source, target)
        nodes, weights = np.polynomial.legendre.leggauss(64)
        south, north = math.radians(25.55), math.radians(25.85)
        phi = (south+north)/2 + (north-south)*nodes/2
        f = 1/298.257223563
        e2 = f*(2-f)
        integral = np.sum(weights*6378137**2*(1-e2)*np.cos(phi)/(1-e2*np.sin(phi)**2)**2)
        expected = integral*(north-south)/2*math.radians(.4)
        self.assertAlmostEqual(mapping.target_area_m2[0]/expected, 1, places=10)
        result = mapping.apply([[1000.]])
        self.assertTrue(result.valid[0, 0])
        self.assertAlmostEqual(result.values[0, 0], 1000*expected/moll_quadrature(source), places=5)

    def test_independent_clipped_budget_and_curvature_refinement(self):
        source = moll_grid(step=300000.)
        # Cut through a curved source edge; retain only the actual intersection.
        bounds = (85., 24., 88., 28.)
        target = RasterGrid((1, 1), (3, 0, 85, 0, -4, 28), "EPSG:4326")
        expected = 120*moll_quadrature(source, bounds)/moll_quadrature(source)
        refined_reference = (120*moll_quadrature(source, bounds, panels=1024) /
                             moll_quadrature(source, panels=1024))
        self.assertLess(abs(expected-refined_reference), 2e-8)
        default = build_conservative_map(source, target)
        tight = build_conservative_map(source, target, edge_tolerance_m=.0001, max_segment_m=1000)
        amount = default.apply([[120.]]).known_values[0, 0]
        tighter = tight.apply([[120.]]).known_values[0, 0]
        self.assertLess(abs(amount-expected), 5e-6)
        self.assertLess(abs(tighter-expected), 5e-6)
        self.assertLess(abs(amount-tighter), 2e-6)
        self.assertGreater(tight.footprint_vertices, default.footprint_vertices)
        self.assertLess(amount, 120)
        self.assertTrue(np.isnan(default.apply([[120.]]).values[0, 0]))

    def test_complete_domain_conserves_population_and_built_surface(self):
        source = moll_grid((4, 5), step=100)
        target = RasterGrid((4, 4), (.01, 0, 84.98, 0, -.01, 25.72), "EPSG:4326")
        mapping = build_conservative_map(source, target)
        people = np.arange(1, 21).reshape(4, 5)/4
        built = np.arange(1, 21).reshape(4, 5)*100.
        for values, total in [(people, 52.5), (built, 21000.)]:
            result = mapping.apply(values)
            self.assertLess(abs(math.fsum(result.known_values.ravel())-total), total*1e-10)
        np.testing.assert_allclose(mapping.source_allocated_fraction, 1, rtol=0, atol=1e-10)
        self.assertFalse(mapping.source_indices.flags.writeable)

    def test_hand_budget_cross_crs_split_and_clipping(self):
        # In EPSG:6933 at the equator these cells are exact physical-area boxes.
        forward = Transformer.from_crs(4326, AREA_CRS, always_xy=True)
        width = forward.transform(2, 0)[0]
        height = forward.transform(0, 2)[1]
        source = RasterGrid((1, 1), (width, 0, 0, 0, -height, height), AREA_CRS)
        target = RasterGrid((1, 2), (1, 0, 0, 0, -2, 2), "EPSG:4326")
        mapping = build_conservative_map(source, target)
        np.testing.assert_allclose(mapping.apply([[80.]]).known_values, [[40., 40.]], atol=1e-8)
        clipped = RasterGrid((1, 1), (.5, 0, .5, 0, -2, 2), "EPSG:4326")
        result = build_conservative_map(source, clipped).apply([[80.]])
        self.assertAlmostEqual(result.known_values[0, 0], 20, places=8)
        self.assertTrue(result.valid[0, 0])

    def test_missing_zeros_partial_and_absent_coverage(self):
        source = RasterGrid((1, 2), (1000, 0, 0, 0, -1000, 1000), AREA_CRS)
        target = RasterGrid((1, 1), (4000, 0, -1000, 0, -1000, 1000), AREA_CRS)
        mapping = build_conservative_map(source, target)
        result = mapping.apply([[8, np.nan]])
        self.assertAlmostEqual(result.source_coverage_fraction[0, 0], .5, places=10)
        self.assertAlmostEqual(result.valid_coverage_fraction[0, 0], .25, places=10)
        self.assertAlmostEqual(result.known_values[0, 0], 8, places=9)
        self.assertTrue(np.isnan(result.values[0, 0]))
        identity = build_conservative_map(source, source)
        zero = identity.apply([[0, 0]])
        np.testing.assert_array_equal(zero.values, [[0, 0]])
        sentinel = identity.apply([[0, -9999]], source_valid=[[True, False]])
        self.assertEqual(sentinel.values[0, 0], 0)
        self.assertTrue(np.isnan(sentinel.values[0, 1]))
        missing = identity.apply([[np.nan, np.nan]])
        self.assertEqual(missing.known_values.sum(), 0)
        self.assertFalse(missing.valid.any())
        absent_target = RasterGrid((1, 1), (1000, 0, 5000, 0, -1000, 1000), AREA_CRS)
        absent = build_conservative_map(source, absent_target).apply([[1, 2]])
        self.assertEqual(absent.source_coverage_fraction[0, 0], 0)
        self.assertTrue(np.isnan(absent.values[0, 0]))

    def test_nodata_handoff_and_inputs_unchanged(self):
        source = moll_grid((3, 3), step=1000)
        target = RasterGrid((1, 1), (.001, 0, 84.9995, 0, -.001, 25.7005), "EPSG:4326")
        mapping = build_conservative_map(source, target)
        values = np.ones((3, 3))
        mask = np.ones((3, 3), dtype=bool)
        mask[1, 1] = False
        before = values.copy(), mask.copy()
        pop, built = mapping.apply(values, source_valid=mask), mapping.apply(values*10)
        result = calculate_exposure([[1]], [[True]], pop.values, built.values,
                                    population_valid=pop.valid, built_surface_valid=built.valid)
        self.assertIsNone(result.population.total_exposed)
        self.assertIsNotNone(result.built_surface_m2.total_exposed)
        np.testing.assert_array_equal(values, before[0])
        np.testing.assert_array_equal(mask, before[1])

    def test_rotations_axis_reversal_and_edge_touch(self):
        source = RasterGrid((2, 2), (100, 25, 0, 10, -100, 1000), AREA_CRS)
        result = build_conservative_map(source, source).apply([[1, 2], [3, 4]])
        np.testing.assert_allclose(result.values, [[1, 2], [3, 4]], atol=1e-8)
        reverse = RasterGrid((1, 2), (-100, 0, 200, 0, 100, 0), AREA_CRS)
        target = RasterGrid((1, 2), (100, 0, 0, 0, -100, 100), AREA_CRS)
        np.testing.assert_allclose(build_conservative_map(reverse, target).apply([[2, 1]]).values,
                                   [[1, 2]], atol=1e-8)
        single = RasterGrid((1, 1), (100, 0, 0, 0, -100, 100), AREA_CRS)
        result = build_conservative_map(target, single).apply([[5, np.nan]])
        self.assertEqual(result.values[0, 0], 5)

    def test_boundary_uncertainty_is_not_promoted_to_complete(self):
        # Web Mercator is supported as coordinate geometry, never as area.
        # A target only ~1 mm inside its source boundary is closer than the
        # conservative 2 cm classification margin, despite nominal full overlap.
        transform = Transformer.from_crs(4326, 3857, always_xy=True)
        left, bottom = transform.transform(85, 25)
        right, top = transform.transform(86, 26)
        source = RasterGrid((1, 1), (right-left, 0, left, 0, bottom-top, top), "EPSG:3857")
        inset = 1e-8
        target = RasterGrid((1, 1), (1-2*inset, 0, 85+inset, 0, -(1-2*inset), 26-inset),
                            "EPSG:4326")
        mapping = build_conservative_map(source, target)
        result = mapping.apply([[12.]])
        self.assertTrue(result.geometry_uncertain[0, 0])
        self.assertFalse(result.valid[0, 0])
        self.assertTrue(np.isnan(result.values[0, 0]))
        self.assertGreater(result.known_values[0, 0], 11.999)
        self.assertGreater(result.source_coverage_fraction[0, 0], .99999999)
        # Missing source just outside a nominal target can lie within the same
        # uncertainty margin; it must not be silently treated as known coverage.
        split = RasterGrid((1, 2), ((right-left)/2, 0, left, 0, bottom-top, top), "EPSG:3857")
        for inset, expected_valid in [(1e-8, False), (1e-4, True)]:
            near = RasterGrid((1, 1), (.01-inset, 0, 85.49, 0, -.2, 25.6), "EPSG:4326")
            result = build_conservative_map(split, near).apply([[4, np.nan]])
            self.assertEqual(bool(result.valid[0, 0]), expected_valid)
            self.assertEqual(bool(result.geometry_uncertain[0, 0]), not expected_valid)

    def test_tiny_nodata_overlap_and_sum_overflow(self):
        source = RasterGrid((1, 2), (100, 0, 0, 0, -100, 100), AREA_CRS)
        target = RasterGrid((1, 1), (100, 0, 1e-6, 0, -100, 100), AREA_CRS)
        result = build_conservative_map(source, target).apply([[4, np.nan]])
        self.assertGreater(result.valid_coverage_fraction[0, 0], .9999999)
        self.assertTrue(np.isnan(result.values[0, 0]))
        coarse = RasterGrid((1, 1), (200, 0, 0, 0, -100, 100), AREA_CRS)
        mapping = build_conservative_map(source, coarse)
        with self.assertRaises(ValueError):
            mapping.apply([[1e308, 1e308]])
        integers = np.full((1, 2), np.iinfo(np.int64).max)
        self.assertEqual(mapping.apply(integers).values[0, 0], 2*float(integers[0, 0]))

    def test_failure_limits_and_input_validation(self):
        source = moll_grid()
        target = RasterGrid((1, 1), (1, 0, 85, 0, -1, 26), "EPSG:4326")
        with self.assertRaisesRegex(ValueError, "did not converge"):
            build_conservative_map(source, target, edge_tolerance_m=1e-9, max_depth=0)
        for options in [dict(edge_tolerance_m=0), dict(edge_tolerance_m=True),
                        dict(max_segment_m=np.inf), dict(max_depth=-1), dict(max_depth=True)]:
            with self.subTest(options=options), self.assertRaises(ValueError):
                build_conservative_map(source, target, **options)
        for grid in [RasterGrid((1, 1), (1, 0, 0, 0, 0, 0), AREA_CRS),
                     RasterGrid((1, 1), (1, 0, 0, 0, -1, 1), "EPSG:4269"),
                     RasterGrid((1, 1), (1, 0, 179.5, 0, -1, 1), "EPSG:4326"),
                     RasterGrid((1, 1), (1, 0, 0, 0, -1, 86), "EPSG:4326"),
                     RasterGrid((True, 1), source.transform, WORLD_MOLLWEIDE),
                     RasterGrid((1, 1), source.transform, "not a CRS")]:
            with self.subTest(grid=grid), self.assertRaises(ValueError):
                build_conservative_map(grid, target)
        mapping = build_conservative_map(source, target)
        for values in [[[np.inf]], [[-1]], [[True]], [[1j]], [["2"]], [1],
                       np.ma.array([[1]], mask=False), [[1, 2]]]:
            with self.subTest(values=values), self.assertRaises(ValueError):
                mapping.apply(values)
        with self.assertRaises(ValueError):
            mapping.apply([[1]], source_valid=[[1]])


if __name__ == "__main__":
    unittest.main()
