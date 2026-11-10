# M2C-3 interface and maps

Exactly two modes: **Synthetic Demo** (default) and **REAL — Patna**. Both have
Overview, Hazard, Exposure, Depth severity, Compare, Data & methods. Synthetic
values/scenarios remain hypothetical. The separate REAL — WRI selector is removed;
its verified small pilot remains inside REAL Hazard/Data & methods with hazard
summaries at the selected threshold, attribution, GeoTIFF, manifest and CSV.

Real pages show four dynamically calculated KPIs, compact joint coverage and
excluded flooded-cell counts. The domain is **complete common WRI cells inside
the uploaded buffered bounding rectangle, not all of Patna district**. Details
move to Data & methods and expanders; coverage limitations remain visible on every
results module. Missing/incomplete cells never become zero. Invalid bundle hashes,
audit or array schema disable exposure results, retaining a warning/pilot reference.

## Geographic display

`geographic_map.py` embeds locally vendored Leaflet 1.9.4 (BSD-2-Clause), its CSS,
and a small canvas layer. Upstream JS/CSS match Leaflet's SHA-256 SRI pins; exact
source URLs and license are in `src/floodcat/static/leaflet/`. No Python package,
CDN call, API key or spatial-processing dependency is added. Hosted requirements
are unchanged. The only external map requests are normal current-viewport OSM
tiles, with attribution and no prefetch/bulk caching. Review the
[OSM usage policy](https://operations.osmfoundation.org/policies/tiles/) before
increasing traffic. Tile requests are made by the viewer browser, not the server.

The scientific overlay uses the actual 65×168 arrays and affine transform:

```
[0.008333333333333333, 0, 84.67500000000001,
 0, -0.008333333333333333, 25.741666666666674]
Bounds: west 84.675, south 25.2, east 86.075, north 25.741666666666674
```

Leaflet projects each geographic cell's edges to Web Mercator for display.
Rectilinear longitude/latitude cell boundaries stay straight under that display
projection; no midpoint allocation, raster resampling, smoothing or invented
subcell detail occurs. Each cell has one flat color; `imageSmoothingEnabled=false`.
At fit zoom several subpixel boundaries may be limited by screen resolution;
zoom in to see native boundaries. Cell outlines are drawn when wide enough.
Hover/click inverts the native affine to read the original cell, never a screen
interpolation. Display colors are binned, while native depth values remain intact.
The map does not calculate any scientific area; numerical area still uses the
unchanged WGS84 ellipsoid helper.

Depth colors distinguish valid dry zero, positive depth bands and missing hazard.
Diagonals mark incomplete joint exposure, including in depth view. The separate
coverage layer shows complete common cells versus incomplete/excluded cells.
Depth view includes valid hazard beyond the exposure domain. Layer selection
never changes the numerical mask. The displayed rectangle is not a district
boundary. Controls support wheel zoom, drag pan, +/−, fit and native-cell popup.
On mobile, click popups replace the hover panel to avoid obstructing the map.

## Numerical behavior

M2C-1/M2C-2 artifacts, checksums, raw sources and allocation/exposure engines are
unchanged. Runtime thresholds use strict **depth > threshold**. Bands are
(0,1], (1,2], (2,5], (5,∞), intersected with the selected strict threshold and
common-valid mask; four band sums reconcile to the current KPI totals. Compare
uses only available historical T100 thresholds. Future genuine return-period or
RCP layers require new separately verified inputs; none are fabricated.

At >0 m, the band counts are 1,852 + 81 + 128 + 55 = **2,116**. Their population
sums reconcile to **2,840,320.5021073623**, built surface to
**32,216,343.94410771 m²**, area to **1,637.3100663957925 km²**. Source missingness,
within-source uniformity, whole-target-cell hazard assumptions, sampled geometric
accuracy and common-cell selection bias remain as documented in
[PATNA_VALIDATION.md](PATNA_VALIDATION.md). Source task IDs/times, upstream GHSL
NaN cause and district-only metrics remain unavailable. No damage/loss inference.

## Browser evidence and performance

[Desktop screenshot](images/m2c-3/desktop.png) ·
[Mobile map screenshot](images/m2c-3/mobile.png)

Screenshots show the actual scientific grid with the tile-failure fallback;
**successful OSM basemap loading is not claimed**. In the managed cloud,
normal tile requests failed with `ERR_TUNNEL_CONNECTION_FAILED` under the enforced
network policy. No bypass was attempted. Subsequent deterministic browser tests
abort tiles deliberately, verify the failure notice and confirm nonempty canvas
pixels and working controls. Local Leaflet needs no external network.

`tests/browser/patna_map.cjs` tests fixed geographic bounds and first/last cell
lookup, +/−, wheel zoom, drag pan, reset/fit, layer switching, popup values,
blocked-tile fallback, CSV controls and desktop/mobile sizes. It requires a
separate development Playwright/Chromium environment, not hosted dependencies:

```sh
python -m streamlit run app.py --server.headless true --server.port 8501
FLOODCAT_URL=http://localhost:8501 node tests/browser/patna_map.cjs
```

The final measured run: initial page→real-map readiness **2,542 ms** (warm local
server; not a cold deployment benchmark); native layer draw **8.6 ms** initially,
**6.2 ms** after interaction; mobile **2.9 ms**. Desktop viewport 1440×1100,
canvas 980 px; mobile viewport 390×844, canvas 358 px, no map horizontal overflow.
These are small-grid, single-machine observations, not scalability guarantees.
Canvas work scales with the native grid; large new rasters require a separate
performance review. [Exact regression evidence](TEST_RESULTS.md).

The read-only cloud home prevented Streamlit from writing its telemetry UUID.
Final live smoke used a scratch-only launcher stubbing that UUID getter and
turning statistics off. No application/package was patched for this adaptation.
Hosted deployment and ordinary browser OSM success still require verification.
