# FloodCAT decisions

- D01: Recover a cloud-deployable minimal Streamlit demo before installing optional complex GIS/CLIMADA packages.
- D02: Preserve scientific truth: all displayed values in this ZIP are synthetic and cannot be interpreted as real Patna flood risk.
- D03: Use GitHub + Streamlit Community Cloud for portability after user approval and safety checks.
- D04: Keep original FloodCAT objective: real raster hazard, scenario comparison, WorldPop/GHSL physical exposure; no financial loss modelling.
- D05: Do not present the earlier `E:\Citi` Codex/Claude outputs as recovered data.
- D06: Keep the pilot on its native WRI grid, using whole cells that cover the requested box and WGS84 ellipsoid cell areas. Report the snapped bounds explicitly.
- D07: Keep Earth Engine in the local acquisition script. The real Streamlit view validates a local TIFF and manifest before showing metrics.

- D08 (M2A-1): Keep the aligned-grid exposure engine separate from the dashboard. Report independent population/built-up coverage and known subtotals; incomplete flooded exposure has no complete total. Require conservative upstream aggregation and explicit missing-data handling. See [exposure assumptions](EXPOSURE.md).

- D09 (M2A-2): Allocate extensive cell totals by physical intersection/source area, assuming uniform density within each source pixel. Preserve known subtotals, distinguish source-footprint and valid-source area coverage, and mark incomplete target totals missing. Clip at target boundaries without renormalizing. Use shared-CRS rectilinear WGS84 ellipsoid or caller-verified equal-area geometry; reject cross-CRS inputs until conservative reprojection is separately validated. Keep aggregation independent of the dashboard and hazard calculations. See [exposure assumptions](EXPOSURE.md).

- D10 (M2A-3): Keep pyproj/PROJ and Shapely/GEOS in an optional scientific pipeline. Transform adaptively densified native cell footprints to WGS84 ellipsoidal equal-area coordinates, intersect them, and reuse sparse physical-area weights without renormalization. Report boundary uncertainty as unknown exposure. Native spherical World Mollweide m² are not ellipsoidal physical areas. Validate with analytic projection controls, independent area/quadrature budgets and convergence evidence; preserve all existing runtime engines. See [cross-CRS remapping](REMAPPING.md).

- D11 (M2B-1): Keep catalog verification distinct from native pixel/mask verification. Pin the official Google catalog evidence, make legacy WorldPop versus R2025A and GHSL total versus NRES selections explicit, and stop real acquisition when provider access or source semantics remain unverified. Use anonymous bounded native GeoTIFF ranges, a two-cell halo, actual WKT/masks and per-window provenance; preserve raw masked values and keep source windows separate from derived grids. Dataset commits require per-artifact redistribution/size checks. No network/authentication bypass, fabricated exposure or dashboard change. See [acquisition status and route](ACQUISITION.md).

- D12 (M2B-2): Test GitHub-hosted connectivity only with an explicitly dispatched, time/byte-bounded metadata diagnostic. HEAD responses and advisory Range headers do not establish raster availability; optional exact-source Range checks read/discard at most one byte. Never follow redirects, retry denials, add provider credentials or alter acquisition review gates. Preserve execution context and keep local proxy evidence distinct from completed Actions-run evidence. See [manual Actions diagnostic](ACTIONS_ACCESS_CHECK.md).

- D13 (M2C-1): Bind user-supplied native export operations and exact asset/unit selections to raw hashes; corroborate WRI on pilot overlap. Treat stored-valid NaNs as unavailable. Reuse existing conservative engines through bounded target strips and publish only complete common-cell exposure, with known clipping budgets and excluded flooded-cell counts. The exported region is a buffered bounding rectangle, not the district polygon. Ship a small audited derivative and leave dashboard integration separate. See [real validation](PATNA_VALIDATION.md).
