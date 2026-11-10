# FloodCAT data sources

Current M2C-1 inputs include three user-uploaded native Earth Engine exports and
an audited common-cell derivative; see [exact metadata/provenance](PATNA_VALIDATION.md).
Earlier not-acquired statements below are historical milestone records.

## Synthetic demonstration inputs

**Generated synthetic grids** (`src/floodcat/demo.py`): stylized river corridor, five fictive scenario depth surfaces, hypothetical population counts and built-up surface. Longitude 85.00–85.48 °E, latitude 25.45–25.85 °N, 42×48 analytical grid. No authentic flood, exposure or built-up observations.

These grids have no external license requirements beyond this source's code rights; they are not public provider datasets. No Earth Engine tokens or datasets are distributed.

## Additional external data — NOT DOWNLOADED

- Additional WRI Aqueduct Flood Hazard Maps V2 scenarios beyond the bundled historical WATCH T100 tile below. Confirm source IDs, licensing, comparability and units before use.
- WorldPop population (source vintage and counting units to be verified).
- GHSL built-up surface (epoch and per-pixel units to be verified).
- Optional genuine CMIP6/SSP future depth only after access and semantics are verified.

Maintain source manifests, SHA-256, scenario/year/return period, CRS, license URL, download date, dataset identifier and transformation steps for real inputs.

## M1A live Earth Engine catalog inspection (2026-11-10)

Catalog-inspected only. No raster downloaded. All three source footprints contain the provisional WGS84 Patna box (85.00–85.48° E, 25.45–25.85° N). Valid-pixel coverage and nodata semantics remain open.

WRI collection `WRI/Aqueduct_Flood_Hazard_Maps/V2`. All five exact riverine filters returned one image by scenario, year, return period and model. All five have `inundation_depth` in metres. Live system indexes:

- `inunriver_historical_000000000WATCH_1980_rp00025`
- `inunriver_historical_000000000WATCH_1980_rp00100`
- `inunriver_historical_000000000WATCH_1980_rp00500`
- `inunriver_rcp4p5_0000HadGEM2-ES_2050_rp00100`
- `inunriver_rcp8p5_0000HadGEM2-ES_2050_rp00100`

Each future query returned five models before model filtering: `00000NorESM1-M`, `0000GFDL-ESM2M`, `0000HadGEM2-ES`, `00IPSL-CM5A-LR`, `MIROC-ESM-CHEM`. Historical T100 uses EPSG:4326 and affine transform `[1/120, 0, -180, 0, -1/120, 90]`. WRI requests attribution. [Earth Engine catalog](https://developers.google.com/earth-engine/datasets/catalog/WRI_Aqueduct_Flood_Hazard_Maps_V2)

WorldPop `WorldPop/GP/100m/pop` returned one image for `country=IND`, `year=2020`, with index `IND_2020` and band `population` (estimated people per cell). EPSG:4326, nominal 92.77 m. CC BY 4.0. The live probe flagged this legacy collection as deprecated and named R2025A as its successor. [Earth Engine catalog](https://developers.google.com/earth-engine/datasets/catalog/WorldPop_GP_100m_pop)

GHSL `JRC/GHSL/P2023A/GHS_BUILT_S/2020` returned `built_surface` and `built_surface_nres` in m² per cell. The inspected total built-up band uses a 100 m World Mollweide grid reported as WKT, with affine transform `[100, 0, -18041000, 0, -100, 9000000]`. Attribute European Commission JRC. [Earth Engine catalog](https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_BUILT_S)

## M1B acquired tile (2026-11-10)

`data/demo_real/patna_wri_watch_t100.tif` is the 3,801-byte Earth Engine GeoTIFF for `WRI/Aqueduct_Flood_Hazard_Maps/V2/inunriver_historical_000000000WATCH_1980_rp00100`. The accompanying JSON manifest records attribution, acquisition UTC, ROI, source checks, output grid and SHA-256.

The tile covers 48 rows by 58 columns on the native EPSG:4326 grid, with affine transform `[1/120, 0, 85, 0, -1/120, 25.85]`. Whole native cells extend the eastern bound to 85.4833333333° E. Depth is float32 in metres. The source mask and downloaded depths agree on 1,222 valid dry zeros, 1,562 positive cells, and zero masked cells. Valid coverage is 100% of the snapped tile. The TIFF has no nodata tag. Maximum valid depth is 5.577278 m.

At thresholds of 0, 1, and 2 m, area is respectively 1,206.56, 430.13, and 335.93 km². These sums use whole-cell areas on the WGS84 ellipsoid and strict depth thresholds. Attribution and limitations apply to modeled regional screening. [WRI data and methodology](https://www.wri.org/data/aqueduct-floods-hazard-maps)

## M2A-1 calculation-only extension

No WorldPop or GHSL pixels have been acquired or integrated. The new engine is tested only on hand-calculated fixtures. Its input units, alignment, aggregation, coverage and edge assumptions are specified in [EXPOSURE.md](EXPOSURE.md). Existing catalog inspection is not evidence of usable exposure coverage.

## M2A-2 calculation-only aggregation

No additional datasets were downloaded. Fabricated population and built-up totals
exercise area-overlap aggregation, including a fine grid over the native WRI
transform. This is not evidence of real WorldPop/GHSL coverage. The M2A-2 method accepts
shared-CRS grids only. M2A-3 adds a separate cross-CRS calculation API below;
real GHSL-to-WRI integration remains unverified. See [coverage, geometry and conservation assumptions](EXPOSURE.md).

## M2A-3 calculation-only cross-CRS remapping

No additional data were acquired. Synthetic extensive totals exercise a known
World Mollweide fixture CRS (`ESRI:54009`) against WRI-style EPSG:4326 grids.
Exact real GHSL WKT, pixel support, masks, epoch and redistribution terms still
require source verification; this milestone does not establish real coverage.
Physical ellipsoid areas are computed after footprint transformation, rather
than equating native Mollweide projected m² with WGS84 area. See
[remapping accuracy and limits](REMAPPING.md).

## M2B-1 source verification and blocked acquisition

No WorldPop/GHSL rasters or derived exposure products acquired. The original WRI
48×58 tile and checksum were reverified; use its snapped east bound
85.48333333333333°E, not only the original ROI ending at 85.48°E.

The official `google/earthengine-catalog` source at
[`e69b2b9006b4313120b32d8a68b051732a88fbec`](https://github.com/google/earthengine-catalog/tree/e69b2b9006b4313120b32d8a68b051732a88fbec)
confirms these catalog facts:

| Product | Verified catalog semantics | Remaining file-level gaps |
| --- | --- | --- |
| Legacy `WorldPop/GP/100m/pop`, verification target `IND_2020` | Deprecated catalog version 0.1; estimated residential people/cell; nominal 92.77 m; CC BY 4.0 | Public India 2020 file/model/adjustment mapping, current native WKT/shape, masks/nodata, valid zero and usable coverage |
| Successor `WorldPop/GP/100m/R2025A/v1/pop` | 2015–2030 annual epochs including 2020; constrained to settlements and adjusted to national estimates; CC BY 4.0; DOI 10.5258/SOTON/WP00839 | Actual India 2020 image/file, mask and comparability; not silently substituted for the legacy candidate |
| `JRC/GHSL/P2023A/GHS_BUILT_S/2020`, `built_surface` | Producer R2023A; total built-up m² per 100 m cell; source acknowledgement/reuse terms; DOI 10.2905/9F06F36F-4B11-47EC-ABB0-4F8B7B1D72EA | Exact public native file, WKT, dtype, nodata/mask/zero semantics and coverage; exact asset/EC legal notices |

WorldPop catalog licensing is explicit CC BY 4.0. GHSL's catalog uses a generic
non-standard-license category, defined as covering both open and closed licenses,
while its human terms say open/free reuse with acknowledgement; do not mislabel
it CC BY or infer closed data. Exact artifact redistribution/size review is still
pending because no artifact was obtained. Do not confuse catalog minimum/visual
zero with verified valid-zero pixels, or the M2A-3 Mollweide fixture with actual
GHSL WKT.

All direct producer/storage/catalog website probes were denied by the configured
cloud proxy with CONNECT 403; no personal Earth Engine credentials are configured.
Official catalog source was read through permitted GitHub access. See
[ACQUISITION.md](ACQUISITION.md) for precise evidence, licensing distinctions,
blocked metadata, the tested native-window route and phase-3 criteria, and
[the machine-readable access record](../config/exposure_access_status.json).

## M2C-1 uploaded real sources

`data/demo_real/FloodCAT_Patna_{WRI_Historical_T100,WorldPop_2020,GHSL_BuiltSurface_2020}.tif`
are committed BigTIFFs from main `2ee214a`. The user-supplied native-grid recipe
selects historical WATCH T100, legacy WorldPop `IND_2020` and GHSL R2023A total
`built_surface`; toFloat/unmask(-9999) preserves zeros and no explicit resampling
is requested. Exact hashes and source IDs are in `config/patna_upload_provenance.json`.
Actual decoded WKT/grids/masks are recorded in the processed validation manifest.
WRI overlap with the old pilot is exact over 2,030 cells. NaN GHSL samples are
missing despite all-valid stored masks. The footprint is a buffered GAUL bounding
rectangle; district geometry is not bundled. Common-cell exposure only, licensing,
known-source budgets, exclusions and remaining provenance limits are documented
in [PATNA_VALIDATION.md](PATNA_VALIDATION.md). No raw sources were modified or copied.
