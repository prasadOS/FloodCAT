# M2C-4 · depth-weighted exposure screening

The REAL navigation item **Vulnerability** prominently states:

> Depth-weighted exposure screening — not a validated vulnerability model.

UNDRR vulnerability means susceptibility to harm, arising from physical, social,
economic and environmental conditions. FloodCAT has modeled flood depths,
estimated population and built-up surface, not validated susceptibility/fragility
inputs. No vulnerability coefficient, depth-damage ratio, mortality, displacement,
monetary loss or comprehensive probabilistic risk is estimated. T100 is a return-
period hazard scenario, not annualized expected impacts. The screening products
below are linear exposure weightings, without calibrated impact meaning.

## Domain, definitions and units

Let C be the unchanged complete common WRI cells in the uploaded buffered
bounding rectangle. This is **not all of Patna district**. At present |C| = 6,113
out of 10,920 valid uploaded hazard cells (55.98% by count). No district polygon
is bundled. Let dᵢ be modeled native WRI depth (m), Pᵢ estimated population
(people/cell) and Bᵢ aligned built-up surface (m²/cell). For selected threshold t,
S(t) = {i ∈ C : dᵢ > t}; equality is excluded.

- Fixed deeper-water exposure: P(1), P(2), P(5), where P(t) = Σᵢ∈S(t) Pᵢ.
  Units people; these three fixed thresholds are independent of the sidebar t.
- Depth-weighted population: Wp(t) = Σᵢ∈S(t) Pᵢ dᵢ, **person-metres**.
- Depth-weighted built surface: Wb(t) = Σᵢ∈S(t) Bᵢ dᵢ, **m²·m**, dimensionally m³.
  This is **not flood volume or physical building damage**. Built-up surface does
  not describe ponded water, building heights, occupancy or fragility.

Wp is not an affected-population count; multiplying people by metres changes the
unit. Neither product is a vulnerability index, casualty prediction, expected
loss or flood risk. No new source-total conservation claim is made for these
scenario-specific target-cell products. The original population/built-surface
allocation budgets remain applicable and unchanged.

The verified checksum loader still gates all results. Unknown/incomplete common
coverage is excluded, never imputed. Weighted arrays retain NaN outside common
cells, serialized as null in the map. Common cells at/below the selected threshold
have a defined zero indicator; valid zero population/built-up remains valid, also
when flooded. This does not replace source missingness with zero.

## Map and priorities

Overview/Hazard start on **Flood Depth (m)** with a selectable **Depth-weighted
population exposure** layer. Vulnerability starts on the latter. The scenario
subtitle retains **WRI Aqueduct V2 — WATCH T100**. All three map layers share the
unchanged 65×168 grid, true EPSG:4326 cell edges and Leaflet display projection.
No interpolation, high-resolution hotspots or administrative boundaries are
invented. Sequential orange/red legend classes (person-metres) are presentation
bins, not harm thresholds: >0–1,000, >1,000–5,000, >5,000–10,000,
>10,000–20,000, >20,000. They stay fixed across threshold selections.

Hover/click shows native row/column, coordinates, modeled depth, common status,
estimated population and the selected-threshold product where available.
Incomplete cells remain gray/diagonal and unavailable; below-threshold common
cells have zero product by definition. Tile failures do not hide scientific
layers. Mobile uses click popups in place of a persistent hover panel.

Top 10 priorities are complete flooded native cells sorted by descending Wpᵢ,
with stable row then column tie-breaks. Coordinates are native cell centres.
Valid zero products can appear if a selected cell has zero population. There is
no ranking of incomplete or non-selected cells. Empty selections have no rows.
These approximately kilometre-scale cells are **not neighborhood risk estimates
or administrative/community rankings**. CSVs retain full precision; screening
and priority exports include domain, threshold and non-vulnerability context.

At t=0: Wp = **2,923,557.7298654984 person-metres** and
Wb = **35,969,112.45142127 m²·m**. Fixed population sums above 1 / 2 / 5 m are
**438,591.0037895779 / 331,405.76219787373 / 145,829.6454354833 people**.
The top cell is row 12, column 88 (zero-based), centre **85.4125°E, 25.6375°N**:
modeled depth 5.435956001281738 m × estimated population 5,126.351453354646 =
**27,866.62094754255 person-metres**. These are recalculated from arrays, not
hardcoded application outputs. Existing >0 m exposure remains 2,840,320.5021073623
estimated people, 32,216,343.94410771 m² built-up, 1,637.3100663957925 km² and
2,116 flooded common cells, excluding 3,101 flooded cells with incomplete coverage.

## Presentation and evidence

Exposure consolidates the non-overlapping depth bands (0,1], (1,2], (2,5], (5,∞),
clipped to depth > t. Three charts show population, built-up km² and flooded km²;
detailed numerical values are optional and the depth-band CSV remains available.
Compare remains a historical T100 threshold comparison. Synthetic retains all
six hypothetical modules, including its Depth severity page.

[Desktop screening/map screenshot](images/m2c-4/screening-map.png) ·
[Mobile screening/map screenshot](images/m2c-4/screening-mobile.png)

Screenshots show tile-failure fallback, not successful OSM access. Deterministic
browser checks abort tiles, test the actual canvas, layer/popup values, controls,
mobile layout, screening/priorities CSV contents and empty selections. The local
server uses the documented scratch telemetry adaptation for the read-only cloud
home, without product/package changes. Live Community Cloud deployment has not
been verified. See [exact tests and commands](TEST_RESULTS.md).

## Remaining limitations and a genuine impact model

All [M2C-1 provenance/coverage limitations](PATNA_VALIDATION.md) remain: selection
bias from incomplete coverage, missing export task metadata, unknown upstream GHSL
NaN cause, uniform source-pixel exposure allocation, whole-target-cell hazard and
sampled geometric accuracy. Depth alone omits flow velocity, duration, warning,
flood defenses and other determinants of harm. Population is an estimated spatial
distribution, not time-specific presence. Built-up m² is not building count or
asset value. Coarse grid aggregation can hide within-cell differences.

A genuine impact model would need outcome-specific, locally validated social
vulnerability/capacity, building types and fragility, floor elevations, occupancy,
warning/evacuation information and depth/other-hazard impact functions, with
calibration, independent validation and uncertainty analysis. No function from
the references below is adopted here.

## References

- [UNDRR: vulnerability](https://www.undrr.org/terminology/vulnerability),
  [exposure](https://www.undrr.org/terminology/exposure),
  [disaster risk](https://www.undrr.org/terminology/disaster-risk).
- Huizinga, J., de Moel, H. & Szewczyk, W. (2017), *Global flood depth-damage
  functions: Methodology and the database with guidelines*, JRC, EUR 28552 EN,
  [doi:10.2760/16510](https://doi.org/10.2760/16510).
- Merz, B., Kreibich, H., Schwarze, R. & Thieken, A. (2010), *Assessment of economic
  flood damage*, Natural Hazards and Earth System Sciences 10, 1697–1724,
  [doi:10.5194/nhess-10-1697-2010](https://doi.org/10.5194/nhess-10-1697-2010).

References establish terminology and additional impact-method requirements;
they do not validate these exposure products as vulnerability or damage models.
