# M2D — multi-scenario verification and interpretation

Source selection is **user-attested, hash-bound and official-catalog-schema compatible**. It is not independent authentication of completed GEE tasks. The supplied identifiers resolve the previous missing-recipe blocker; task IDs, timestamps, account-side logs and live per-asset GEE property queries remain unavailable. No credentials or network bypass was used. The reproducible prospective GEE script checks floodtype/climate/model/year/returnperiod before creating tasks; it was not executed here and skips re-export of Historical T100.

## Source/catalog evidence

Exact 15 asset IDs/band/units and raw SHA-256 values are in `config/patna_multiscenario_provenance.json`. All use `inundation_depth`, metres, riverine `inunriver`; historical WATCH 1980 or HadGEM2-ES 2050 under RCP4.5/RCP8.5 (CMIP5-era, not CMIP6/SSP). The official Google Earth Engine catalog snapshot from commit e69b2b9006b4313120b32d8a68b051732a88fbec is retained with Apache-2.0 license and hash. Its schema independently corroborates the climate/model/flood-type tokens, band units, years supported and return periods. It does not authenticate individual exports. Source metadata and valid-zero/mask statistics are in `config/patna_multiscenario_validation.json`.

## Geometry and processing

All 15 GeoTIFFs are actual BigTIFFs, not LFS pointers: 65×168, Float32, EPSG:4326, affine [1/120,0,84.67500000000001,0,-1/120,25.741666666666674], bounds [84.675,25.2,86.075,25.741666666666674]. Each declares nodata -9999; every sample is finite, unmasked and nonnegative, including valid dry zero. Stored metadata does not name assets or unit tags. Every native array was also decoded independently with Pillow and compared exactly with the processed array. All 12 adjacent return-period ordering diagnostics show zero reversals; monotonicity was checked, not imposed or used as proof of identity.

Exact WKT/affine/shape/bounds equality permits direct reuse of the unchanged M2C-1 aligned extensive population and built-up surface. No new resampling, projection or remapping occurs. Fixed comparison mask is original complete exposure coverage intersected with every scenario hazard mask: **6,113 cells / 4,730.679260130684 km²**, unchanged from historical T100, 55.98% of 10,920 hazard cells. The buffered export rectangle is not a district polygon. Scenario full-hazard masks and incomplete joint coverage remain distinct. Original population/built-up conservation budgets remain unchanged; there is no new claim of conservation for depth-weighted products.

`hazards.npz` (~170 KiB) and `validation.json` (~53 KiB) hold all native depths/masks and offline per-scenario records; SHA-256 pins gate runtime loading, alongside the original three-artifact audited bundle. No raw raster is changed or copied. WRI permits distribution with attribution; retain WRI attribution/catalog terms from DEPLOYMENT.md. WorldPop and GHSL arrays remain in the existing redistributable audited bundle; no additional native datasets are acquired. Runtime uses NumPy with allow_pickle=False and fail-closed limits/schema/checksum checks; optional Rasterio stays offline. No Python dependency changed.

Reproduce into a NEW directory (the original T100 bundle is never overwritten):

```sh
python -m scripts.validate_multiscenario_inputs --output config/patna_multiscenario_validation.json
python -m scripts.prepare_multiscenario --output work/patna-scenarios-rebuild
```

The preparer writes new checksum pins for its chosen output; review and package that output with the pins before deployment. Both source identities and exact geometry must pass before output is created. Any grid mismatch is rejected; no row/column fallback.

## Per-scenario findings at strict depth >0 m

| Scenario | Max depth m | Dry zeros | Common wet cells | Estimated people | Built km² | Person-metres |
|---|---:|---:|---:|---:|---:|---:|
| Historical_T25 | 5.689463 | 6228 | 1869 | 2520125.330 | 27.550154 | 1966772.714 |
| Historical_T50 | 6.405810 | 5948 | 2000 | 2674730.506 | 29.956046 | 2444463.162 |
| Historical_T100 | 7.031288 | 5703 | 2116 | 2840320.502 | 32.216344 | 2923557.730 |
| Historical_T250 | 7.730871 | 5409 | 2253 | 3028208.781 | 34.802167 | 3560769.054 |
| Historical_T500 | 8.182789 | 5195 | 2358 | 3196879.953 | 37.180472 | 4047916.531 |
| RCP45_2050_T25 | 7.628022 | 5564 | 2251 | 2976482.423 | 34.117578 | 3511130.333 |
| RCP45_2050_T50 | 8.042305 | 5353 | 2371 | 3143950.772 | 36.398015 | 4061859.223 |
| RCP45_2050_T100 | 8.410629 | 5152 | 2469 | 3272081.395 | 38.074783 | 4608517.425 |
| RCP45_2050_T250 | 8.847874 | 4921 | 2597 | 3455069.399 | 41.199849 | 5333328.252 |
| RCP45_2050_T500 | 9.153130 | 4750 | 2696 | 3608051.194 | 43.263131 | 5886687.359 |
| RCP85_2050_T25 | 11.686285 | 4469 | 2810 | 3870128.977 | 47.998548 | 6298880.947 |
| RCP85_2050_T50 | 12.383226 | 4132 | 3015 | 4238060.258 | 55.046047 | 7555662.408 |
| RCP85_2050_T100 | 13.009348 | 3851 | 3200 | 4559002.986 | 62.077133 | 8861302.921 |
| RCP85_2050_T250 | 13.767717 | 3493 | 3429 | 5081431.302 | 72.298742 | 10687591.378 |
| RCP85_2050_T500 | 14.294441 | 3258 | 3592 | 5450417.903 | 79.320915 | 12134802.457 |

Full precision area, built-up m², all depth bands, weighted built-up m²·m, coverage/exclusions, source IDs and hashes are in the machine-readable validation records. Historical T100 reproduces 2,116 cells, 2,840,320.5021073623 people, 32,216,343.94410771 m², 1,637.3100663957925 km², 2,923,557.7298654984 person-metres and 35,969,112.45142127 m²·m. The original benchmark remains separately recorded and its source/audit files are unchanged.

## Dashboard and comparison

Both REAL selectors precede Module, default Historical WATCH/T100 and persist across REAL modules. Threshold range is 0–15 m, strict >. Every page/map/chart/export reflects the selected source. All six REAL modules and Synthetic remain. Exposure bands reconcile; vulnerability remains explicitly depth-weighted exposure, not a susceptibility/damage model. Priority rows and CSVs carry scenario context. Compare supports all return periods in one climate, three T100 climates, two selected combinations with optional paired maps, and threshold sensitivity. Percentage differences are unavailable for zero reference values. All comparisons use the same fixed mask and show each scenario’s exclusions; no probability weighting or AAL/PML is performed.

WorldPop and GHSL stay fixed at **2020**, including future hazard scenarios. Differences are not solely attributable to climate change: WATCH versus HadGEM2-ES, baseline/reference assumptions and fixed exposure must be considered. No neighborhood-scale inference, damage, monetary losses, casualties or validated vulnerability is implied. Existing GHSL NaN cause, source uniformity, incomplete coverage/selection bias and empirical geometric-accuracy limitations remain.

[Future screening screenshot](images/m2d/future-screening.png) · [Two-scenario comparison screenshot](images/m2d/compare.png). OSM tiles were deliberately blocked in deterministic browser checks; scientific layers remain usable. No successful OSM access or live Community Cloud deployment is claimed.

## Delivery status

Feature implementation and local tests are reviewable in PR #8. Do not merge automatically: independent per-asset property/task verification remains unavailable, and hosted/browser-provider access is unverified. Source-selection attestation is documented without presenting it as independent task proof. See TEST_RESULTS.md for exact commands and test outcomes.
