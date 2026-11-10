"""Optional, regional cross-CRS conservative remapping. See docs/REMAPPING.md.

Import this module only in the scientific pipeline (requirements-science.txt).
No projection formulas, raster interpolation, or cell-centre allocation are used.
"""

from dataclasses import dataclass, field
import math

import numpy as np
from pyproj import CRS, Transformer
from pyproj.exceptions import ProjError
from shapely import Polygon, STRtree, union_all

from .aggregation import AggregationResult, _finite_sum
from .exposure import _grid

AREA_CRS = "EPSG:6933"  # WGS84 ellipsoidal cylindrical equal area, in metres.
WORLD_MOLLWEIDE = "ESRI:54009"  # Explicit fixture CRS; verify real GHSL WKT separately.
WGS84 = CRS.from_epsg(4326)


@dataclass(frozen=True)
class RasterGrid:
    """Pixel-is-area affine grid; native coordinates, always x/y axis order.

    Transform is (a, b, c, d, e, f): x=a*column+b*row+c,
    y=d*column+e*row+f at outer corners. Invertible rotations are supported.
    CRS must be WGS84 geographic or projected from WGS84, without datum shifts.
    """

    shape: tuple[int, int]
    transform: tuple[float, float, float, float, float, float]
    crs: str


@dataclass(frozen=True)
class RemapResult(AggregationResult):
    """M2A-2 result fields plus an explicit boundary-accuracy uncertainty mask."""

    geometry_uncertain: np.ndarray


@dataclass(frozen=True)
class ConservativeMap:
    """Reusable sparse physical-area intersections, independent of values/masks.

    All indices use C-order flattening. Areas are WGS84 ellipsoid m², not
    necessarily native projected areas (notably spherical World Mollweide).
    Arrays are read-only; build once and apply independently to each measure.
    """

    source_shape: tuple[int, int]
    target_shape: tuple[int, int]
    source_indices: np.ndarray
    target_indices: np.ndarray
    intersection_area_m2: np.ndarray
    source_area_m2: np.ndarray
    target_area_m2: np.ndarray
    source_allocated_fraction: np.ndarray
    source_coverage_fraction: np.ndarray
    edge_tolerance_m: float
    max_segment_m: float
    boundary_margin_m: float
    footprint_vertices: int
    _source_polygons: tuple = field(repr=False)
    _target_polygons: tuple = field(repr=False)
    _complete: np.ndarray = field(repr=False)

    def apply(self, source_values, *, source_valid=None):
        """Apply area fractions without renormalization, filling or rounding.

        Missing and unrepresented source areas are distinct from valid zeros.
        Incomplete/uncertain totals are NaN; known_values retains partial sums.
        """
        values = _grid(source_values, "source_values")
        if values.shape != self.source_shape:
            raise ValueError("source_values shape must match source grid")
        mask = (np.ones(values.shape, dtype=bool) if source_valid is None else
                _grid(source_valid, "source_valid", values.shape, boolean=True))
        if np.any(mask & (np.isinf(values) | (values < 0))):
            raise ValueError("Unmasked source values must be nonnegative or NaN")
        available = (mask & np.isfinite(values)).ravel()
        flat = values.ravel()
        known = np.zeros(math.prod(self.target_shape))
        coverage = np.zeros_like(known)
        missing = np.zeros_like(known, dtype=bool)
        offsets = np.searchsorted(self.target_indices, np.arange(len(known) + 1))
        for j in range(len(known)):
            sl = slice(offsets[j], offsets[j + 1])
            indices, areas = self.source_indices[sl], self.intersection_area_m2[sl]
            good = available[indices]
            missing[j] = bool(np.any(~good))
            known[j] = _finite_sum(float(flat[i]) * (area / self.source_area_m2[i])
                                   for i, area in zip(indices[good], areas[good]))
            coverage[j] = _finite_sum(float(a / self.target_area_m2[j]) for a in areas[good])
        uncertain = np.zeros_like(missing)
        # Buffer only for classification, never for allocation or coverage areas.
        # No rounded coverage fraction can promote a missing total to complete.
        if self.boundary_margin_m:
            missing_polygons = [p for p, good in zip(self._source_polygons, available) if not good]
            missing_domain = union_all(missing_polygons) if missing_polygons else None
            domain = union_all(self._source_polygons)
            for j, polygon in enumerate(self._target_polygons):
                uncertain[j] = (domain.covers(polygon) and not self._complete[j])
                if missing_domain is not None and not missing[j]:
                    uncertain[j] |= missing_domain.intersects(polygon.buffer(self.boundary_margin_m))
        complete = self._complete & ~missing & ~uncertain
        shape = self.target_shape
        return RemapResult(np.where(complete, known, np.nan).reshape(shape), known.reshape(shape),
                           complete.reshape(shape), self.source_coverage_fraction.reshape(shape).copy(),
                           np.minimum(coverage, self.source_coverage_fraction).reshape(shape),
                           uncertain.reshape(shape))


def _grid_definition(grid):
    if not isinstance(grid, RasterGrid):
        raise ValueError("Expected a RasterGrid (not M2A-2 GridSpec)")
    shape = np.asarray(grid.shape)
    if (np.ma.isMaskedArray(grid.shape) or shape.shape != (2,) or shape.dtype.kind not in "iu" or
            np.any(shape <= 0) or any(isinstance(n, (bool, np.bool_)) for n in grid.shape)):
        raise ValueError("Grid shape must contain two positive integers")
    t = np.asarray(grid.transform)
    if (np.ma.isMaskedArray(grid.transform) or t.shape != (6,) or t.dtype.kind not in "iuf" or
            not np.isfinite(t).all()):
        raise ValueError("Transform must contain six finite real numbers")
    a, b, _, d, e, _ = t.astype(float)
    determinant = a*e - b*d
    if not math.isfinite(determinant) or determinant == 0:
        raise ValueError("Grid transform must be invertible")
    try:
        crs = CRS.from_user_input(grid.crs)
    except (ProjError, TypeError) as error:
        raise ValueError("Invalid CRS") from error
    if (not (crs.is_projected or crs.is_geographic) or len(crs.axis_info) != 2 or
            not crs.geodetic_crs.equals(WGS84, ignore_axis_order=True)):
        raise ValueError("Only two-dimensional WGS84 CRSs without datum shifts are supported")
    return tuple(map(int, shape)), t.astype(float), crs


def _positive(value, name):
    array = np.asarray(value)
    if (np.ma.isMaskedArray(value) or array.ndim != 0 or array.dtype.kind not in "iuf" or
            not 0 < float(array) < math.inf):
        raise ValueError(f"{name} must be a finite positive real scalar")
    return float(array)


class _Footprints:
    """Shared edge cache ensures adjacent source cells have identical boundaries."""

    def __init__(self, grid, tolerance, segment, max_depth):
        self.shape, self.transform, self.crs = _grid_definition(grid)
        self.to_lonlat = Transformer.from_crs(self.crs, WGS84, always_xy=True,
                                              allow_ballpark=False, only_best=True)
        self.to_area = Transformer.from_crs(WGS84, AREA_CRS, always_xy=True,
                                           allow_ballpark=False, only_best=True)
        self.back = Transformer.from_crs(WGS84, self.crs, always_xy=True,
                                        allow_ballpark=False, only_best=True)
        self.tolerance, self.segment, self.max_depth = tolerance, segment, max_depth
        self.points, self.edges, self.lonlat = {}, {}, []
        self.area_direct = self.crs.equals(CRS(AREA_CRS), ignore_axis_order=True)
        # These cases have exactly straight mapped edges; no curvature margin.
        a, b, c, d, e, f = self.transform
        self.curved = not (self.area_direct or
                          (self.crs.equals(WGS84, ignore_axis_order=True) and b == d == 0))

    def point(self, native):
        if native not in self.points:
            try:
                if self.crs.is_geographic and (abs(native[0]) > 180 or abs(native[1]) > 85):
                    raise ValueError("Geographic grid crosses supported longitude/latitude bounds")
                lon, lat = self.to_lonlat.transform(*native, errcheck=True)
                if not (math.isfinite(lon) and math.isfinite(lat) and -180 < lon < 180 and abs(lat) < 85):
                    raise ValueError("Footprints must remain away from antimeridian and |latitude| >= 85")
                roundtrip = self.back.transform(lon, lat, errcheck=True)
                # PROJ's ellipsoidal CEA inverse uses a latitude series with
                # millimetre-scale round-trip residuals. This is a domain guard,
                # not the geometric accuracy estimator. Preserve native 6933
                # coordinates directly for area rather than round-tripping them.
                limit = .01 if self.crs.is_projected else math.radians(1e-9)
                if any(abs(p-q)*axis.unit_conversion_factor > limit
                       for p, q, axis in zip(native, roundtrip, self.crs.axis_info)):
                    raise ValueError("Projection round trip failed; input may lie outside its valid domain")
                xy = native if self.area_direct else self.to_area.transform(lon, lat, errcheck=True)
                if not all(math.isfinite(v) for v in xy):
                    raise ValueError("Nonfinite equal-area coordinate")
            except ProjError as error:
                raise ValueError("Projection failed for a cell boundary") from error
            self.points[native] = xy
            self.lonlat.append((lon, lat))
        return self.points[native]

    def edge(self, start, end):
        reverse = start > end
        key = (end, start) if reverse else (start, end)
        if key not in self.edges:
            def refine(p, q, depth):
                u, v = np.asarray(self.point(p)), np.asarray(self.point(q))
                chord = v-u
                length = float(np.linalg.norm(chord))
                deviations = []
                for fraction in (.25, .5, .75):
                    native = tuple(x + fraction*(y-x) for x, y in zip(p, q))
                    point = np.asarray(self.point(native))
                    location = np.clip(np.dot(point-u, chord) / (length*length), 0, 1) if length else 0
                    deviations.append(float(np.linalg.norm(point - (u + location*chord))))
                if length <= self.segment and max(deviations) <= self.tolerance:
                    return [tuple(u), tuple(v)]
                if depth >= self.max_depth:
                    raise ValueError("Edge densification did not converge; refine settings/domain")
                midpoint = tuple((x+y)/2 for x, y in zip(p, q))
                if midpoint in (p, q):
                    raise ValueError("Edge refinement exhausted coordinate precision")
                return refine(p, midpoint, depth+1)[:-1] + refine(midpoint, q, depth+1)
            self.edges[key] = refine(*key, 0)
        points = self.edges[key]
        return points[::-1] if reverse else points

    def build(self):
        a, b, c, d, e, f = self.transform
        def corner(row, col):
            return (float(a*col+b*row+c), float(d*col+e*row+f))
        polygons = []
        for row in range(self.shape[0]):
            for col in range(self.shape[1]):
                corners = [corner(row, col), corner(row, col+1),
                           corner(row+1, col+1), corner(row+1, col)]
                ring = []
                for start, end in zip(corners, corners[1:] + corners[:1]):
                    ring.extend(self.edge(start, end)[:-1])
                polygon = Polygon(ring)
                if not polygon.is_valid or not 0 < polygon.area < math.inf:
                    raise ValueError("Invalid transformed footprint; no automatic geometry repair")
                polygons.append(polygon)
        positions = np.asarray(self.lonlat)
        if np.ptp(positions[:, 0]) > 60 or np.ptp(positions[:, 1]) > 60:
            raise ValueError("Only regional grids spanning at most 60 degrees on each axis are supported")
        return tuple(polygons)


def build_conservative_map(source_grid, target_grid, *, edge_tolerance_m=0.01,
                           max_segment_m=10000., max_depth=20):
    """Intersect adaptively transformed footprints in ellipsoidal EPSG:6933.

    Quarter/mid/three-quarter chord deviations and maximum chord length control
    refinement. This is an empirically validated accuracy approach, not a formal
    error bound for arbitrary projections. Failure to refine raises ValueError.
    Curved boundary completeness uses a 2*tolerance margin per curved grid;
    allocations always use unbuffered intersections without renormalization.
    See docs/REMAPPING.md for supported domains, accuracy evidence and limitations.
    """
    tolerance = _positive(edge_tolerance_m, "edge_tolerance_m")
    segment = _positive(max_segment_m, "max_segment_m")
    if isinstance(max_depth, bool) or not isinstance(max_depth, int) or not 0 <= max_depth <= 30:
        raise ValueError("max_depth must be an integer between 0 and 30")
    source = _Footprints(source_grid, tolerance, segment, max_depth)
    target = _Footprints(target_grid, tolerance, segment, max_depth)
    sp, tp = source.build(), target.build()
    # Reject seam-crossing combinations as well as individual seam-crossing grids.
    positions = np.asarray(source.lonlat + target.lonlat)
    if np.ptp(positions[:, 0]) > 60 or np.ptp(positions[:, 1]) > 60:
        raise ValueError("Combined grids exceed the supported regional domain")
    source_area = np.array([p.area for p in sp])
    target_area = np.array([p.area for p in tp])
    tree = STRtree(sp)
    si, ti, area = [], [], []
    for j, polygon in enumerate(tp):
        for i in sorted(tree.query(polygon)):
            intersection = polygon.intersection(sp[i]).area
            if intersection > 0:
                si.append(i)
                ti.append(j)
                area.append(intersection)
    si, ti, area = np.array(si, dtype=int), np.array(ti, dtype=int), np.array(area, dtype=float)
    source_coverage = np.bincount(ti, weights=area, minlength=len(tp)) / target_area
    source_allocated = np.bincount(si, weights=area, minlength=len(sp)) / source_area
    if np.any(source_coverage > 1+1e-10) or np.any(source_allocated > 1+1e-10):
        raise ValueError("Overlapping footprints or unstable intersection areas")
    domain = union_all(sp)
    margin = 2*tolerance*(int(source.curved)+int(target.curved))
    complete = np.array([domain.covers(p.buffer(margin) if margin else p) for p in tp])
    arrays = [si, ti, area, source_area, target_area, source_allocated,
              np.minimum(source_coverage, 1), complete]
    for array in arrays:
        array.setflags(write=False)
    return ConservativeMap(source.shape, target.shape, *arrays[:7], tolerance, segment, margin,
                           sum(len(p.exterior.coords) for p in sp+tp), sp, tp, complete)
