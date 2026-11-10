"""Physical exposure on already aligned grids; see docs/EXPOSURE.md."""

from dataclasses import dataclass
import math

import numpy as np


@dataclass(frozen=True)
class ExposureMeasure:
    """Coverage is cell-count based, not area- or exposure-weighted."""

    known_exposed: float
    total_exposed: float | None
    valid_hazard_cells: int
    available_cells: int
    flooded_cells: int
    available_flooded_cells: int

    @property
    def missing_cells(self):
        return self.valid_hazard_cells - self.available_cells

    @property
    def missing_flooded_cells(self):
        return self.flooded_cells - self.available_flooded_cells

    @property
    def coverage_fraction(self):
        return self.available_cells / self.valid_hazard_cells if self.valid_hazard_cells else None

    @property
    def flooded_coverage_fraction(self):
        return self.available_flooded_cells / self.flooded_cells if self.flooded_cells else None


@dataclass(frozen=True)
class ExposureResult:
    threshold_m: float
    population: ExposureMeasure
    built_surface_m2: ExposureMeasure


def _grid(value, name, shape=None, boolean=False):
    # Do not discard a numpy.ma mask during conversion.
    if np.ma.isMaskedArray(value):
        raise ValueError(f"{name}: use an explicit validity mask, not a masked array")
    array = np.asarray(value)
    kinds = "b" if boolean else "iuf"
    if array.dtype.kind not in kinds or array.ndim != 2 or not array.size:
        raise ValueError(f"{name}: expected a nonempty 2D {'boolean' if boolean else 'real numeric'} grid")
    if shape is not None and array.shape != shape:
        raise ValueError(f"{name}: shape must match depth exactly")
    return array


def calculate_exposure(depth_m, valid_depth, population_count, built_surface_m2,
                       threshold_m=0.0, *, population_valid=None, built_surface_valid=None):
    """Sum whole-cell exposure where valid depth is strictly above threshold.

    Depth must be finite and nonnegative wherever valid_depth is True.
    Exposure is nonnegative people/cell or m²/cell. NaN means missing; optional
    boolean exposure masks additionally mark finite nodata sentinels invalid.
    Explicitly invalid cells may contain arbitrary numeric sentinels. Unmasked
    infinity or negative exposure is rejected, including outside valid hazard.
    Zero is valid. No inputs are modified, resampled, rounded or imputed.
    """
    depth = _grid(depth_m, "depth_m")
    valid = _grid(valid_depth, "valid_depth", depth.shape, boolean=True)
    threshold = np.asarray(threshold_m)
    if threshold.ndim != 0 or threshold.dtype.kind not in "iuf":
        raise ValueError("threshold_m must be a finite nonnegative real scalar")
    threshold = float(threshold)
    if not math.isfinite(threshold) or threshold < 0:
        raise ValueError("threshold_m must be a finite nonnegative real scalar")
    if np.any(valid & (~np.isfinite(depth) | (depth < 0))):
        raise ValueError("Valid depth must be finite and nonnegative")
    flooded = valid & (depth > threshold)

    def measure(values, mask, name):
        values = _grid(values, name, depth.shape)
        declared = (np.ones(depth.shape, dtype=bool) if mask is None else
                    _grid(mask, name + '_valid', depth.shape, boolean=True))
        if np.any(declared & (np.isinf(values) | (values < 0))):
            raise ValueError(f"{name}: unmasked values must be nonnegative or NaN")
        available = declared & np.isfinite(values)
        # fsum avoids integer overflow and reduces cancellation/roundoff in sums.
        try:
            known = math.fsum(float(v) for v in values[flooded & available])
        except OverflowError as error:
            raise ValueError(f"{name}: exposed sum exceeds finite float range") from error
        if not math.isfinite(known):
            raise ValueError(f"{name}: exposed sum exceeds finite float range")
        wet_count = int(np.count_nonzero(flooded))
        wet_available = int(np.count_nonzero(flooded & available))
        return ExposureMeasure(known, known if wet_available == wet_count else None,
                               int(np.count_nonzero(valid)),
                               int(np.count_nonzero(valid & available)),
                               wet_count, wet_available)

    return ExposureResult(threshold,
                          measure(population_count, population_valid, "population_count"),
                          measure(built_surface_m2, built_surface_valid, "built_surface_m2"))
