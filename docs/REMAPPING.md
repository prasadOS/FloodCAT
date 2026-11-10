# M2A-3 conservative cross-CRS remapping

This optional scientific pipeline transforms **cell footprints**, intersects them
by physical area and remaps extensive people/cell or built-up m²/cell. It does not
resample hazard, allocate cell centres, interpolate values, infer missing pixels or
connect exposure to the dashboard. The M2A-1 and M2A-2 APIs remain unchanged.

## Environment and dependencies

The hosted `requirements.txt` is unchanged. Install `requirements-science.txt`
only in a scientific environment: NumPy 2.4.6 (already used by the app), pyproj
3.7.2 and Shapely 2.1.2. The tested wheels contain PROJ 9.5.1 and GEOS 3.13.1.
The scientific module is not imported by the application or existing engines.
A minimal science environment needs just this file; the full regression suite
also needs the original application requirements:

```sh
python3.11 -m venv .venv-science
.venv-science/bin/python -m pip install -r requirements.txt -r requirements-science.txt
.venv-science/bin/python -m unittest discover -s tests -v
.venv-science/bin/python -m scripts.benchmark_remapping
```

Without optional packages, the 13 cross-CRS tests explicitly skip and the original
42 tests still run. A science validation run must have **no skips**. No CLIMADA,
GIS command-line tools, external transformation grids or real datasets are needed.
No network access occurs during remapping; the supported CRSs share WGS84 and
require no datum-shift resources.

## Method and physical area

`src/floodcat/remapping.py` uses pyproj/PROJ for CRS interpretation and all
coordinate transformations, with `always_xy=True`, `allow_ballpark=False` and
`only_best=True`. Shapely/GEOS handles footprint validity, polygon intersections,
union and the STRtree spatial index. No projection formulas are implemented in
the mapping method.

1. Construct each pixel-is-area boundary in its **native** grid coordinates.
2. Transform and adaptively subdivide every edge into **EPSG:6933**, WGS84
   ellipsoidal cylindrical equal-area coordinates in metres. Adjacent cells share
   a canonical edge cache, so their approximations have identical shared borders.
3. Intersect unbuffered source and target polygons. For source i and target j:
   `contribution_ij = source_total_i * intersection_area_ij / source_area_i`.
4. Retain this sparse geometry independently of exposure values. Apply it to
   population and built-up surface separately with their own validity masks.

These are physical areas on the WGS84 ellipsoid. World Mollweide (the fixture
`ESRI:54009`) preserves area on a sphere of radius 6,378,137 m, so its native
projected m² must **not** be substituted for ellipsoid areas. Near the Patna
fixture, a 100×100 projected-metre cell has about 9,958.1 physical ellipsoid m².
Counts/m² per source cell remain extensive totals; only their allocation fractions
change. Assume uniform exposure per unit physical area **within each source
pixel**, without assuming where individual people or buildings lie.

EPSG:6933 coordinates are used directly when already native, avoiding an
unnecessary inverse/forward projection. A geographic EPSG:4326 cell bounded by
meridians and parallels becomes an exact rectangle in this area CRS. An arbitrary
projected cell usually has curved boundaries there; four corners alone are
insufficient. GEOS areas apply to approximating polygons, not exact curved edges.

## Accuracy controls and conservative completeness

Defaults are `edge_tolerance_m=0.01`, `max_segment_m=10000` and `max_depth=20`.
For each candidate edge segment, transform the endpoints and samples at 1/4,
1/2 and 3/4. Recursively bisect until **both** the maximum sample-to-chord distance
is at most 1 cm in EPSG:6933 and chord length is at most 10 km. Distances are in
the area projection, not geodesic ground distances. Reaching the depth/coordinate
precision limit raises an error. Invalid footprints are rejected without repair.

This is an **empirical accuracy control**, not a formal upper bound between all
sample locations or for every possible projection. The maximum chord length and
quarter-point probes reduce missed curvature; independent area integrals and a
100-fold tighter refinement validate the tested cases. New projections, latitudes,
cell sizes or materially smaller desired errors require further validation.
Neither source-total conservation nor agreement after refinement alone proves
correct geography: shared approximate polygons can conserve an incorrect shape.

Classification uses a safety margin of `2 * edge_tolerance_m` per grid whose
edges can be curved in the area CRS (2 cm for Mollweide → unrotated WGS84; 4 cm
if both grids can curve). Exactly straight EPSG:6933 edges and unrotated WGS84
meridian/parallel edges need no margin. Other projected grids use the margin even
when particular edges happen to be straight. This is a conservative heuristic,
not a certified error bound. It may classify a genuinely complete edge cell as
uncertain.

A target is complete only if its footprint plus that margin is covered by the
source footprint union, no positive-area nodata intersection exists, and no
missing source footprint lies within the margin. Buffers are used **only for
classification**, never intersection areas or allocation weights. Tiny missing
intersections still invalidate totals; there is no coverage-percentage threshold,
snapping, filling or rescaling that makes them complete.

The projection round-trip check is a domain guard: 1 cm residual allowed in
projected physical units, 1e-9 degrees in geographic coordinates. PROJ's CEA
inverse latitude series has millimetre-scale residuals; this guard is not an
independent projection accuracy proof. Native EPSG:6933 area calculations avoid
that inverse/forward residual entirely.

## API and missingness

```python
from src.floodcat.remapping import RasterGrid, build_conservative_map
from src.floodcat.exposure import calculate_exposure

# Read/verify native CRS WKT, corner transform and mask from each actual source.
source = RasterGrid(population_count.shape, source_transform, source_crs_wkt)
target = RasterGrid(depth_m.shape, wri_transform, "EPSG:4326")
weights = build_conservative_map(source, target)
population = weights.apply(population_count, source_valid=population_valid)
# Reuse weights for another measure only when its source grid is identical.
built = weights.apply(built_surface_m2, source_valid=built_valid)
exposure = calculate_exposure(depth_m, valid_depth, population.values, built.values,
                             population_valid=population.valid,
                             built_surface_valid=built.valid)
```

`RasterGrid(shape, transform, crs)` has `(rows, columns)`, a pyproj-readable CRS
string/WKT, and the corner affine tuple `(a, b, c, d, e, f)`:
`x = a*column + b*row + c`, `y = d*column + e*row + f`. Axis reversals, rotation
and shear are supported if the transform is invertible. This is a separate grid
type from M2A-2's `GridSpec`; there is no misleading planar-area declaration for a
spherical Mollweide CRS. Equal shapes alone never establish shared source grids.

`ConservativeMap` stores read-only C-order source/target indices, intersection
areas, source/target physical cell areas, source allocation fractions and source
coverage. Retain caller grid/CRS metadata with the map for provenance; it is an
in-memory object, not a serialized acquisition manifest. Do not edit weights.
If measures have different source grids, build a separate map for each.

`apply` returns the existing aggregation result fields plus uncertainty:

| Field | Interpretation |
| --- | --- |
| `known_values` | Sum of known allocated contributions, including partial cells. Zero when nothing known contributes; never infer complete zero from this field alone. |
| `values` | Known sum only for complete target cells; NaN for partial, nodata or geometrically uncertain cells. |
| `valid` | Complete target exposure mask, safe for M2A-1. |
| `source_coverage_fraction` | Source footprint area, including nodata, divided by whole target area. |
| `valid_coverage_fraction` | Known source area divided by whole target area. |
| `geometry_uncertain` | Nominal coverage too near a curved domain boundary, or possibly missing source within the accuracy margin. Consult alongside coverage and validity. |

NaN or explicit False validity is missing. Zero remains valid. Finite sentinels
require a boolean, shape-exact mask. Unmasked negative values/infinities are
rejected even outside the target domain. Masked arrays are rejected; inputs are
not mutated. Float64 weights and `math.fsum` avoid integer wraparound and reject
nonfinite known subtotals; arbitrary integer precision is not promised.

Target boundaries clip contributions without redistribution. For full target
coverage of the source, summing `known_values` conserves the **known** source
total to numerical precision. With missing source values the unknown total cannot
be claimed conserved. Target cells beyond the source edge remain incomplete;
`values` need not sum to the source total even when the known subtotals conserve.
M2A-1 intentionally omits partial target subtotals; retain `known_values` separately
if reporting them, clearly labelled as partial. Do not use `nansum(values)` as a
complete exposed total.

Fractions reported for coverage are capped at 1 only for roundoff. Weights are
never renormalized. Coverage/allocation exceeding 1 by more than 1e-10 raises an
error; that check detects unstable intersections or overlapping footprints and
is **not** a completeness threshold.

## Numerical evidence

The deterministic suite checks the following independent references:

- Exact Mollweide identities at the equator and at a special auxiliary angle
  theta=pi/6, from Snyder's Mollweide equations (also documented by
  [PROJ](https://proj.org/en/stable/operations/projections/moll.html)). These
  analytic test-only controls check coordinates within 2e-8 m and inverse
  longitude/latitude within 1e-11 degrees. Production calls PROJ exclusively.
- Direct quadrature of WGS84 differential surface area for a lon/lat rectangle,
  without EPSG:6933 or GEOS area, agrees within 1e-10 relative.
- Native Mollweide x/y integration of
  `dA_ellipsoid/dA_sphere = (1-e²)/(1-e² sin²(latitude))²`, including clipped
  longitude/latitude support, independently checks the physical intersection
  budgets. Composite 16-point Gauss-Legendre integration over 512 y intervals
  does not construct polygons or call GEOS. It shares PROJ coordinates, so the
  separate analytic projection controls matter. Tests cover -30°, 0°, 25.7° and
  65° latitude, 100 m and 300 km cells; physical source areas agree within 2e-8
  relative. This tolerance is evidence for these fixtures, not a global guarantee.
- A dense geodesic polygon-area calculation (4,096 native samples per edge,
  pyproj.Geod) supplements the area checks. It shares PROJ transforms and WGS84,
  so it is explicitly **not** independent validation of those ingredients.
- Hand budgets split 80 people into 40 + 40 across different CRSs and retain
  exactly 20 for a quarter-domain clip, within 1e-8 people. Full source coverage
  conserves 52.5 people and 21,000 built-up m² within 1e-10 relative.

For the curved 300 km Patna fixture, independent source area is
89,623,161,267.10747 m²; default polygon area differs by 6.19e-10 relative.
The clipped contribution from 120 source units is independently
60.19218571628636. Default mapping gives 60.192187692795606; 0.1 mm/1 km
refinement gives 60.19218572400746. Both pass the 5e-6 unit budget tolerance
(4.17e-8 of the original 120), and differ by less than 2e-6 units.
Doubling the reference quadrature to 1,024 y intervals leaves this clipped
budget unchanged at the printed precision. Refinement is a convergence check,
distinct from the quadrature reference.

Other fixtures check masks, all missing, valid zero, absent/partial coverage,
tiny nodata overlap, boundary uncertainty (including nearby missing source),
edge touching, axis reversals, rotated grids, overflow, unchanged inputs,
exposure handoff, invalid CRS/domain and failed refinement.

## Performance and remaining limits

`python -m scripts.benchmark_remapping` uses fabricated 100 m counts/m² near
Patna on a 32×32 Mollweide grid snapped to a 100 m lattice, mapped to a 6×6 grid
at native WRI resolution. One measured build took **0.261345 s**, followed by
**0.037985 s** for two map applications. There were 1,307 nonzero intersection
pairs and 5,300 polygon vertices. Known totals were 1,280 people and 256,000 m²,
with 1.33e-15 relative aggregate error; maximum per-source allocation residual
was 3.42e-12. Five targets were complete; others were partial or outside. This is
a small single-machine measurement, not a large-raster throughput guarantee.

All footprints and sparse intersections are retained in memory. Edge caches,
STRtree construction, unions and GEOS operations have nontrivial memory/CPU cost;
`apply` also unions missing footprints and checks uncertainty. There is no tiling,
parallel execution, disk-backed weights or billion-pixel scalability claim.
Tighter tolerances and very curved/coarse cells increase vertex counts sharply:
the refinement fixture grows from 1,282 to 19,458 total vertices.

Supported inputs are **regional**, two-dimensional WGS84 geographic/projected
CRSs with no datum shifts. Footprints must stay strictly between -180° and 180°,
strictly within ±85° latitude, and the combined sampled domain must span at most
60° longitude and latitude. Antimeridian wrapping, polar caps, global grids,
other datums, vertical/compound CRSs, custom ROI polygons, source point samples
and malformed/folded footprints are not supported. The adaptive method is
validated most directly for World Mollweide → WGS84; accepting another WGS84
projection does not establish its accuracy at all locations.

`ESRI:54009` is a known World Mollweide **fixture definition**, not proof of the
exact CRS of any future GHSL asset. Verify its actual WKT, affine support, epoch,
band units, mask semantics and license before real use. No WorldPop/GHSL pixels
were acquired. No within-pixel settlement pattern, location accuracy, raster mask
truth or exposure uncertainty has been validated. Exposure is not damage or
observed inundation. Next single task: validate the exact candidate source
metadata and design a bounded acquisition/processing plan, without acquisition
until separately authorized.
