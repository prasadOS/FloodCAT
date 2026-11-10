"""Conservative remapping of extensive cell totals; see docs/EXPOSURE.md."""

from dataclasses import dataclass
import math

import numpy as np

from .exposure import _grid


@dataclass(frozen=True)
class GridSpec:
    """Pixel-is-area affine grid: (dx, 0, x_origin, 0, dy, y_origin).

    Either axis may run in either direction. Both grids must share a CRS and
    area model. ``planar`` requires caller-verified equal-area coordinates;
    ``wgs84`` integrates ellipsoid area in EPSG:4326 longitude/latitude.
    Rotation, shear, reprojection and longitude wrapping are unsupported.
    """

    shape: tuple[int, int]
    transform: tuple[float, float, float, float, float, float]
    crs: str = "EPSG:4326"
    area_model: str = "wgs84"


@dataclass(frozen=True)
class AggregationResult:
    """Known subtotals and area coverage, independent of hazard validity.

    ``values`` is NaN unless the entire target cell has known source data.
    ``known_values`` retains partial subtotals, including an explicitly known
    subtotal of zero when no valid source overlaps. Never use it as a complete
    exposure grid. Pass ``values`` and ``valid`` to calculate_exposure instead.
    """

    values: np.ndarray
    known_values: np.ndarray
    valid: np.ndarray
    source_coverage_fraction: np.ndarray
    valid_coverage_fraction: np.ndarray


def _axes(grid):
    if not isinstance(grid, GridSpec):
        raise ValueError("Expected a GridSpec")
    shape = np.asarray(grid.shape)
    if (np.ma.isMaskedArray(grid.shape) or shape.shape != (2,) or
            shape.dtype.kind not in "iu" or np.any(shape <= 0) or
            any(isinstance(n, (bool, np.bool_)) for n in grid.shape)):
        raise ValueError("Grid shape must contain two positive integers")
    if np.ma.isMaskedArray(grid.transform):
        raise ValueError("Grid transform must not be a masked array")
    transform = np.asarray(grid.transform)
    if (transform.shape != (6,) or transform.dtype.kind not in "iuf" or
            not np.all(np.isfinite(transform))):
        raise ValueError("Grid transform must contain six finite real numbers")
    dx, shear_x, left, shear_y, dy, top = map(float, transform)
    if shear_x != 0 or shear_y != 0 or dx == 0 or dy == 0:
        raise ValueError("Only unrotated, unsheared grids with nonzero steps are supported")
    if not isinstance(grid.crs, str) or not grid.crs.strip():
        raise ValueError("An explicit CRS is required")
    if grid.area_model not in ("wgs84", "planar"):
        raise ValueError("Area model must be wgs84 or planar")
    x = left + dx * np.arange(grid.shape[1] + 1, dtype=float)
    y = top + dy * np.arange(grid.shape[0] + 1, dtype=float)
    if grid.area_model == "wgs84":
        if grid.crs != "EPSG:4326":
            raise ValueError("wgs84 area requires EPSG:4326")
        if np.any(np.abs(x) > 180) or np.any(np.abs(y) > 90):
            raise ValueError("Longitude/latitude bounds must not wrap or cross a pole")
        x = np.deg2rad(x)
        # Area between meridians and parallels on WGS84. A separable area
        # coordinate makes rectangle intersections exact in this area model.
        sin_lat = np.sin(np.deg2rad(y))
        flattening = 1 / 298.257223563
        e2 = flattening * (2 - flattening)
        e = math.sqrt(e2)
        y = (6378137.0**2 * (1 - e2) / 2 *
             (sin_lat / (1 - e2 * sin_lat**2) + np.arctanh(e * sin_lat) / e))
    elif grid.crs == "EPSG:4326":
        raise ValueError("Longitude/latitude degrees cannot use planar area")
    for axis in (x, y):
        if (not np.all(np.isfinite(axis)) or
                not (np.all(np.diff(axis) > 0) or np.all(np.diff(axis) < 0))):
            raise ValueError("Grid edges must be finite and distinct at float64 precision")
    return x, y


def _overlaps(source, target):
    """Sparse axis overlaps in original array order; no dense grid-pair matrix."""
    source_order = np.arange(len(source) - 1)
    if source[0] > source[-1]:
        source = source[::-1]
        source_order = source_order[::-1]
    result = []
    for start, end in zip(target[:-1], target[1:]):
        low, high = min(start, end), max(start, end)
        first = max(0, int(np.searchsorted(source, low, side="right")) - 1)
        stop = min(len(source) - 1, int(np.searchsorted(source, high, side="left")))
        parts = []
        for i in range(first, stop):
            length = min(high, source[i + 1]) - max(low, source[i])
            if length > 0:
                parts.append((source_order[i], length, length / (source[i + 1] - source[i])))
        result.append((parts, low >= source[0] and high <= source[-1]))
    return result


def _finite_sum(values):
    try:
        total = math.fsum(values)
    except OverflowError as error:
        raise ValueError("Aggregate exceeds finite float range") from error
    if not math.isfinite(total):
        raise ValueError("Aggregate exceeds finite float range")
    return total


def aggregate_extensive(source_values, source_grid, target_grid, *, source_valid=None):
    """Allocate people/cell or built-up m²/cell by source/target area overlap.

    Within each valid source pixel, exposure is assumed uniformly distributed
    over physical area. Contributions are source_total * overlap/source_area.
    Fractions outside the target extent are clipped, never redistributed.
    Missing pixels (NaN or explicit False mask) contribute no known amount and
    invalidate every target cell they overlap. Partial spatial coverage likewise
    gives NaN in ``values``; coverage denominators are whole target cell areas.
    Zero is valid. Negative/infinite unmasked values and masked arrays are errors.
    No inputs are mutated. Different CRSs must not be relabelled to bypass checks.
    """
    sx, sy = _axes(source_grid)
    tx, ty = _axes(target_grid)
    if source_grid.crs != target_grid.crs or source_grid.area_model != target_grid.area_model:
        raise ValueError("Source and target must share a CRS and area model; no reprojection")
    values = _grid(source_values, "source_values")
    if values.shape != tuple(source_grid.shape):
        raise ValueError("source_values shape must match source_grid")
    declared = (np.ones(values.shape, dtype=bool) if source_valid is None else
                _grid(source_valid, "source_valid", values.shape, boolean=True))
    if np.any(declared & (np.isinf(values) | (values < 0))):
        raise ValueError("Unmasked source values must be nonnegative or NaN")
    available = declared & np.isfinite(values)
    known = np.zeros(target_grid.shape)
    complete = np.zeros(target_grid.shape, dtype=bool)
    spatial_coverage = np.zeros(target_grid.shape)
    valid_coverage = np.zeros(target_grid.shape)
    x_parts, y_parts = _overlaps(sx, tx), _overlaps(sy, ty)
    for row, (ys, y_full) in enumerate(y_parts):
        for col, (xs, x_full) in enumerate(x_parts):
            target_area = abs(tx[col + 1] - tx[col]) * abs(ty[row + 1] - ty[row])
            if not math.isfinite(target_area) or target_area <= 0:
                raise ValueError("Target cell area must be positive and finite")
            contributions, valid_areas = [], []
            all_available = bool(xs and ys)
            for sr, height, y_fraction in ys:
                for sc, width, x_fraction in xs:
                    if available[sr, sc]:
                        contributions.append(float(values[sr, sc]) * x_fraction * y_fraction)
                        # Divide each axis before multiplying to avoid area overflow.
                        valid_areas.append((width / abs(tx[col + 1] - tx[col])) *
                                           (height / abs(ty[row + 1] - ty[row])))
                    else:
                        all_available = False
            known[row, col] = _finite_sum(contributions)
            spatial_coverage[row, col] = min(1.,
                _finite_sum(w / abs(tx[col + 1] - tx[col]) for _, w, _ in xs) *
                _finite_sum(h / abs(ty[row + 1] - ty[row]) for _, h, _ in ys))
            valid_coverage[row, col] = min(spatial_coverage[row, col], _finite_sum(valid_areas))
            # Completeness is geometric and logical, not a rounded coverage test:
            # even a tiny missing overlap must keep the target total unknown.
            complete[row, col] = x_full and y_full and all_available
    totals = np.where(complete, known, np.nan)
    return AggregationResult(totals, known, complete, spatial_coverage, valid_coverage)
