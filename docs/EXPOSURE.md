# Exposure engine and conservative aggregation

`src/floodcat/exposure.py::calculate_exposure` is an independent calculation API.
It is not connected to either dashboard mode. No real exposure data are bundled.

## Input contract

All grids must be nonempty 2D real numeric arrays of exactly the same shape;
validity masks must be boolean arrays of that shape (no broadcasting). Masked
arrays are rejected to avoid silently discarding their masks. `depth_m` contains
metres and `valid_depth` explicitly distinguishes nodata from valid dry zero.
Depth must be finite and nonnegative on valid cells. Invalid hazard cells are
excluded, even if they contain positive depth or large exposure.

`population_count` is people per target cell, not density; fractional estimated
counts are retained. `built_surface_m2` is total GHSL built-up surface in square
metres per target cell, not a fraction, footprint count, or square kilometres.
Both must be nonnegative where declared valid. Zero is available data. NaN is
missing. Optional `population_valid` and `built_surface_valid` masks mark finite
nodata sentinels as unavailable. Unmasked negative values and infinities are
errors anywhere in exposure grids. No missing value is imputed or scaled up.

The caller must verify CRS, affine transform, extent, orientation, pixel support,
units, source vintage, and correct spatial alignment before calling. Equal shapes
do not establish alignment. Source counts and m² must already be conservatively
aggregated to the hazard grid, with documented source/target intersections,
boundary clipping and partial coverage. This engine performs no reprojection,
resampling, area multiplication or subpixel flood allocation. A partially known
aggregate must be marked missing unless completeness has been established;
cell masks cannot describe fractional source coverage. Whole-cell exposure is
selected by the target cell's modeled depth, not observed inundation or damage.

## Outputs and missing data

The finite nonnegative scalar `threshold_m` selects only valid depth strictly
above the threshold. At zero, valid dry cells are excluded. Each result measure
reports `known_exposed` (a subtotal over available flooded cells), and
`total_exposed` (the same value only if all flooded cells have exposure data;
otherwise `None`). Do not label a partial subtotal as the complete total.
Population and built-up masks and totals are independent.

Coverage fields count available and missing exposure cells within valid hazard
and within its flooded subset. Fractions use these respective cell denominators;
they are not area-weighted or fractions of total people/built surface. Unknown
hazard cells are outside both denominators. A zero denominator yields `None`, not
100% coverage. No flooded cells yields a known exposure total of zero, including
when all hazard cells are invalid; consult valid-hazard counts before interpreting
that result as evidence of no hazard. All exposure missing in a nonempty flooded
subset yields subtotal zero, unknown total and zero flooded coverage.

Inputs are not mutated. Sums use float conversion and standard-library `fsum`;
integer wraparound is avoided, but arbitrary precision integer counts are not
promised beyond float64 precision. Nonfinite aggregate sums are rejected.
M2A-1 conservation tests use independently calculated aligned fixtures. M2A-2
adds independent source-to-target overlap fixtures below; neither validates
real-data reprojection.

## M2A-2 conservative aggregation API

`src/floodcat/aggregation.py::aggregate_extensive(source_values, source_grid,
target_grid, source_valid=None)` accepts one extensive measure at a time. Call it
independently for population (people per source cell) and built-up surface (m² per
source cell); each may have a different source grid and mask. Density, built-up
fractions and depth are not valid inputs to this method.

`GridSpec(shape, transform, crs="EPSG:4326", area_model="wgs84")` describes a
pixel-is-area grid. `shape` is `(rows, columns)` and the affine tuple is
`(dx, 0, x_origin, 0, dy, y_origin)`, with origin at the outer pixel corner.
Coordinates locate cell boundaries, not centres. Both axis directions are
supported. Steps may differ between axes and grids, including noninteger
resolution ratios and offset origins. Source and target CRS strings and area
models must match exactly. Equal shapes do not establish alignment.

The default `wgs84` model requires EPSG:4326, longitude in [-180, 180] and
latitude in [-90, 90]. Intersections are rectangles bounded by meridians and
parallels. Areas integrate the WGS84 ellipsoid, including latitude-dependent
pixel areas; degree-area weighting is not used. `planar` requires an explicit
shared projected CRS and caller-verified equal-area coordinates. It uses planar
rectangle areas. Declaring a non-equal-area projection planar does not correct
its distortion. EPSG:4326 cannot be declared planar.

Rotation, shear, longitude wrapping, arbitrary polygon clipping and cross-CRS
reprojection are rejected or outside this API. For cross-CRS grids, use the separate optional M2A-3 method below. Do not
relabel a CRS or apply ordinary interpolation to per-cell totals. The M2A-2 API
continues to reject cross-CRS inputs.
No additional dependencies, real datasets or CLIMADA are used in M2A-2.

### Allocation and conservation

For source cell i and target cell j:

`contribution_ij = source_total_i * area(source_i ∩ target_j) / area(source_i)`

This assumes uniform exposure per unit physical area within each valid source
pixel. It produces fractional counts/m² without rounding and makes no inference
about within-pixel buildings, population locations, flood allocation or damage.
The algorithm builds sparse axis overlaps rather than a dense source-by-target
matrix and uses float64 weights and `math.fsum` for target subtotals. Nonfinite
subtotals are rejected; arbitrary integer precision is not promised.

When the target grid fully covers the source grid, summing `known_values`
preserves all **known** source population or built-up surface to floating-point
precision. When both grids fully cover the same domain and all source pixels are
valid, all `values` are complete and their sum preserves the source total.
With missing source pixels, the unknown source total cannot be claimed conserved.
With incomplete target cells, sum `known_values` only as a labelled known subtotal;
`values` deliberately contains NaN there.

The target extent clips source cells using their actual intersection areas.
Amounts outside it are discarded, never redistributed or scaled up. A target
cell extending beyond the source extent is incomplete. Coverage denominators are
always the entire target cell area. The API does not treat an uncovered edge as
zero, crop that denominator to available data, or extrapolate outside the source.
There is no extra ROI mask: boundary clipping refers to the target extent.

### Outputs, missingness and exposure handoff

- `known_values`: target-shaped known allocated subtotals. Zero is the known
  subtotal when no valid source contributes; consult coverage before interpreting.
- `values`: the same number only when the entire target cell is spatially covered
  by valid source pixels; NaN otherwise.
- `valid`: boolean completeness mask suitable for M2A-1's exposure validity input.
- `source_coverage_fraction`: area covered by source pixels, including nodata,
  divided by whole target cell area.
- `valid_coverage_fraction`: area covered by finite, declared-valid source pixels,
  divided by whole target cell area. This is area coverage, not a fraction of
  people/m², and differs from M2A-1's cell-count coverage.

NaN or an explicit False `source_valid` pixel means missing. Finite nodata
sentinels require that mask; valid zero remains valid. Unmasked negative or
infinite values are rejected everywhere, including outside the target extent.
Masks must be boolean and shape-exact. Masked arrays are rejected. Missing areas
contribute no known amount but invalidate every target cell with positive-area
overlap. Edge touching has zero area. Even tiny missing overlaps invalidate a
total: no rounded coverage threshold promotes it to complete. Grid edges must be
finite and distinct at float64 precision; no automatic alignment snapping is done.
Inputs are not modified. Roundoff in reported fractions is bounded to [0, 1].

Use the complete grids and masks when calling the existing engine:

```python
from src.floodcat.aggregation import GridSpec, aggregate_extensive
from src.floodcat.exposure import calculate_exposure

# Source metadata and arrays must be verified by the caller.
wri_grid = GridSpec(depth_m.shape, wri_transform)
pop = aggregate_extensive(population_count, population_grid, wri_grid,
                          source_valid=population_valid)
built = aggregate_extensive(built_surface_m2, built_grid, wri_grid,
                            source_valid=built_valid)
result = calculate_exposure(depth_m, valid_depth, pop.values, built.values,
                            population_valid=pop.valid,
                            built_surface_valid=built.valid)
```

M2A-1 intentionally excludes incomplete target cells from its known flooded
subtotal. Partial source subtotals remain available in aggregation's
`known_values`; they must not be passed as complete whole-cell exposure. Hazard
validity and flood thresholds do not participate in aggregation.

## M2A-3 conservative cross-CRS remapping

The optional `src/floodcat/remapping.py` API adds `RasterGrid`,
`build_conservative_map` and reusable `ConservativeMap.apply`. It uses PROJ
boundary transformations and GEOS polygon intersections in WGS84 ellipsoidal
equal-area coordinates, with adaptive edge densification. It preserves the
M2A-2 result fields and adds a boundary-accuracy uncertainty mask; incomplete
or uncertain target totals remain NaN. Existing engines and the dashboard do
not import it. Install `requirements-science.txt` only for the scientific pipeline.

See [REMAPPING.md](REMAPPING.md) for the complete API, supported regional domains,
scientific assumptions, independent accuracy evidence, numerical tolerances,
performance and limitations. Native GHSL projected m² are not automatically
physical ellipsoid areas. The World Mollweide fixtures do not verify the exact
WKT or masks of a future acquired GHSL asset. No real exposure rasters were acquired.

## Next single verifiable milestone

Validate exact candidate WorldPop/GHSL source metadata and design a bounded
acquisition/processing plan. Acquisition remains separately authorized work;
no exposure API is connected to the dashboard yet.
