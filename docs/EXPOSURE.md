# M2A-1 exposure engine assumptions

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
Conservation tests use independently calculated aligned fixtures; they do not
validate future real-data reprojection or aggregation.

## Next single verifiable milestone

M2A-2: implement and independently test conservative source-to-target exposure
aggregation with small in-memory grids, including partial overlaps, masked source
cells, edges and count/m² conservation. No real acquisition is required. Real
WorldPop/GHSL source selection, licensing, mask verification and acquisition
remain separate approval-dependent work.
