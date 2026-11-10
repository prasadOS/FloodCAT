# M2B-1 real exposure acquisition: verified catalog, blocked raster access

Historical acquisition record. **M2C-1 now validates user-uploaded native rasters**
and prepares a real common-cell bundle; see [PATNA_VALIDATION.md](PATNA_VALIDATION.md).
This does not establish a successful provider download from the cloud.

**No WorldPop/GHSL exposure rasters or derived exposure products were acquired.**
The cloud's enforced HTTP policy denied direct official documentation/data hosts
with proxy CONNECT `403 Forbidden`. No personal Earth Engine credentials or
outbound Earth Engine identity are configured. No Earth Engine/producer authentication, alternate
proxy, network-policy bypass, guessed data mirror or full-country download was
attempted. This task authorizes bounded acquisition when checks pass; the current
blockers are access and source verification, not an additional approval request.

The official **Google Earth Engine Public Data Catalog source** is independently
published at `google/earthengine-catalog` and accessible through the permitted
GitHub connection. It supplied useful current documentation, without fetching
blocked websites indirectly. This is official data-host documentation; direct
WorldPop/JRC producer pages and native raster headers remain inaccessible.

The native-window code is tested offline. It is **not evidence that the selected
providers offer compatible public GeoTIFF Range endpoints**. No exact native
file URL is populated in the checked-in review template.

## Verified WRI target

`wri_reference()` first calls the existing checksum/depth validator, then checks
manifest CRS, shape, affine transform and snapped bounds against decoded pixels.
The bundled WRI depth calculations are unchanged.

| Property | Current evidence |
| --- | --- |
| Asset | `WRI/Aqueduct_Flood_Hazard_Maps/V2/inunriver_historical_000000000WATCH_1980_rp00100` |
| Shape / band / units | 48 rows × 58 columns; `inundation_depth`, float32 metres |
| CRS / pixel support | EPSG:4326, pixel-is-area |
| Affine `(a,b,c,d,e,f)` | `(1/120, 0, 85, 0, -1/120, 25.85)` |
| Exact grid bounds | West 85; south 25.450000000000003; east 85.48333333333333; north 25.85 |
| Mask | No nodata tag; 1,222 valid dry zeros, 1,562 positive cells, no missing cells |
| TIFF bytes | 3,801 |
| SHA-256 | `9d5c2747166f7cdecb84a7067575b311a4d4552cc2cd5ee482b924159bd91ebc` |

Acquire coverage for the **snapped raster footprint**, not merely the original
85.00–85.48°E requested box. The extra eastern native-cell strip matters.

## Exact products and source evidence

Documentation is pinned to official catalog commit
[`e69b2b9006b4313120b32d8a68b051732a88fbec`](https://github.com/google/earthengine-catalog/tree/e69b2b9006b4313120b32d8a68b051732a88fbec).
[config/exposure_access_status.json](../config/exposure_access_status.json) records
source-file URLs, SHA-256 hashes of the catalog documents, claims, probe timestamps
and unresolved facts. Catalog document checksums are **not raster checksums**.

### WorldPop 2020 India

The explicit **verification target** is the previously catalog-inspected legacy
`WorldPop/GP/100m/pop`, with `country=IND`, `year=2020`, image index `IND_2020`,
band `population` (combined candidate ID `WorldPop/GP/100m/pop/IND_2020`). M1A
previously queried that exact image; it has not been live-queried again here.
This maintains the prior source selection while making its deprecated status
explicit. **No underlying public download file has yet been conclusively selected.**

The [legacy official catalog entry](https://github.com/google/earthengine-catalog/blob/e69b2b9006b4313120b32d8a68b051732a88fbec/catalog/WorldPop/WorldPop_GP_100m_pop.jsonnet)
and version table verify:

- Deprecated collection, catalog version label `0.1`, temporal extent 2000–2020.
- Estimated residential people **per cell**, not density; fractional estimates
  must be retained. Random Forest dasymetric redistribution of census-based
  counts uses geospatial covariates. Nominal catalog GSD is 92.77 m, not proof
  of a constant physical pixel area or exact affine transform.
- CC BY 4.0; the catalog explicitly permits copying, distribution and adaptation
  with clear attribution. Cite WorldPop and the exact selected product/release.
- The entry does **not** resolve the underlying India 2020 public filename,
  constrained/unconstrained or UN-adjustment variant, native nodata/mask storage,
  valid-zero semantics, full raster dimensions, or actual usable Patna pixels.
  Prior M1A reported EPSG:4326; the current native TIFF WKT is still unavailable.

The [successor official entry](https://github.com/google/earthengine-catalog/blob/e69b2b9006b4313120b32d8a68b051732a88fbec/catalog/WorldPop/WorldPop_GP_100m_R2025A_v1_pop.jsonnet)
identifies **`WorldPop/GP/100m/R2025A/v1/pop`**, R2025A v1, annual 2015–2030 epochs
(including 2020), `population`, nominal 100 m / citation resolution 3 arcseconds,
DOI `10.5258/SOTON/WP00839`, also CC BY 4.0. Its country rasters are explicitly
**constrained to settlement areas and adjusted to national population estimates**.
This is a model/release distinction, not a harmless renamed collection. The
catalog wording alone does not identify which national estimate series was used.
No actual India 2020 successor image, mask or native download was queried.

R2025A is documented as a comparison candidate, **not silently substituted** for
legacy `IND_2020`. Adopting it requires an explicit source selection with exact
image/file identity and a documented comparability decision; the current
acquisition registry intentionally rejects a release/ID mismatch. Do not guess
`ind_ppp_2020.tif` versus an `_UNadj` or constrained filename.

### GHSL 2020 total built-up surface

The verification target is **`JRC/GHSL/P2023A/GHS_BUILT_S/2020`**, band
**`built_surface`**, producer dataset **GHS-BUILT-S R2023A**, DOI
`10.2905/9F06F36F-4B11-47EC-ABB0-4F8B7B1D72EA`. Earth Engine uses `P2023A` in the
asset path while the producer citation calls the dataset `R2023A`.

The [official catalog source](https://github.com/google/earthengine-catalog/blob/e69b2b9006b4313120b32d8a68b051732a88fbec/catalog/JRC/JRC_GHSL_P2023A_GHS_BUILT_S.jsonnet)
confirms square metres of **total built-up surface per 100 m cell**, separate from
`built_surface_nres`. Do not use the non-residential band as total built-up or
interpret m² as a fraction, building count, floor area, vulnerability or damage.
The release describes spatial/temporal interpolation or extrapolation across
1975–2030 at five-year intervals; epoch 2020 is not a claim of exact observed
building footprints in a historical WRI event.

The catalog says: “open and free data. Reuse is authorised, provided the source
is acknowledged,” linking the EC Reuse and Copyright Notice. Attribute European
Commission JRC and the Pesaresi/Politis (2023) dataset citation. Its machine-readable
license label `proprietary` is a **non-standard-license category**, explicitly
covering both open and closed licenses in the catalog's `spdx.libsonnet`; it must
not be mistaken for a closed-data finding or relabelled CC BY. The full EC legal
notice and exact downloadable-file notices have not been retrieved here.

Prior M1A reported 100 m World Mollweide with global affine
`[100,0,-18041000,0,-100,9000000]`. The public catalog Jsonnet does **not** contain
the exact raster WKT, dtype, nodata sentinel or mask flags. They remain unverified
until actual native metadata is accessible. Do not copy `ESRI:54009` from the
M2A-3 fixtures into a purported real-source manifest. Read and compare the actual
WKT. Native Mollweide projected m² are also not automatically WGS84 ellipsoid
areas; allocation must use the existing physical-area remapping method.

### Zeros, nodata and coverage

Neither catalog visualisation minima nor catalog footprints establish valid-zero
or valid-pixel coverage. Zero **may be real data**; masked zero is missing. A
nodata value of zero, water/country masks or settlement constraints need explicit
provider interpretation. Do not coerce these to known zero or assume complete
India/Patna coverage. Nodata sentinels, external/internal masks, NaN and source
extent boundaries are independently relevant. This milestone has no actual
WorldPop/GHSL mask counts or coverage percentages to report.

## Access findings and remaining blocker

At 2026-11-10 07:51:08 UTC the inherited proxy denied CONNECT for:

- Both official Earth Engine catalog web-page URLs at `developers.google.com`.
- `www.worldpop.org` and `data.worldpop.org`.
- `human-settlement.emergency.copernicus.eu` and JRC storage
  `jeodpp.jrc.ec.europa.eu`.

These are **cloud policy denials**, not evidence that providers refuse anonymous
access or that a guessed path exists. The Google catalog source later identified
the producer GHSL page as `https://ghsl.jrc.ec.europa.eu/ghs_buS2023.php`; that
page and the EC legal-notice host were not retrieved. Current observed outbound
rules cover package-manager/GitHub hosts, not these producer/storage hosts.
GitHub catalog access does not make native pixels available.

If the environment is later configured for provider access, preserve existing
allowlist entries and add the exact producer, catalog, legal and download hosts
actually needed. Validate access normally with the inherited proxy and CA. Do not
use a relay, disable TLS, change proxies or authenticate to Earth Engine merely
to avoid the block. No dataset compatibility, anonymous Range support or ETag
availability has yet been established. Earth Engine catalogs being public does
not make Earth Engine raster API calls anonymous.

## Tested acquisition/validation route

The pipeline is optional. Hosted `requirements.txt`, Streamlit controls, existing
WRI/exposure/aggregation/remapping sources and assets are unchanged. Install the
acquisition extension in an isolated Python 3.11 environment:

```sh
python3.11 -m venv work/venv-acquisition
work/venv-acquisition/bin/python -m pip install -r requirements.txt -r requirements-acquisition.txt
work/venv-acquisition/bin/python -m scripts.acquire_exposure_windows
```

The default command verifies WRI and prints an **inventory only**, making no
network calls. `requirements-acquisition.txt` extends the scientific requirements
with Rasterio 1.4.4 (tested GDAL 3.10.3), Requests 2.34.2 and Pillow 13.0.0; Requests
and Pillow were already present in the application environment. No CLIMADA or
Earth Engine API was added. Tests cover the actual WRI metadata and **clearly
labelled, temporary synthetic TIFF fixtures only**, never substitute exposure data.

1. Copy `config/exposure_review_template.json` outside committed configuration
   and resolve the exact product/file, release, model/adjustment variant, provider
   evidence, attribution and access terms. All checked-in access/review flags are
   false, URLs and actual native metadata are unset. Catalog terms are recorded
   as evidence, not falsely treated as completed pixel-mask verification.
2. Once source selection and legal public access are established, set
   `metadata_access_verified=true`, with dated evidence and `acquisition_permitted`.
   Inspect the actual native header without reading exposure/mask arrays:

   ```sh
   python -m scripts.acquire_exposure_windows --source worldpop_2020_ind \
     --review work/source_reviews.json --inspect
   ```

   This reports WKT, shape, affine, stored units, nodata, mask flags and scaling.
   It still labels mask semantics/coverage unverified. Reads use a 2 MiB metadata
   payload cap; header blocks can contain adjacent payload bytes, but no pixel
   values, masks or coverage counts are decoded in this mode.
3. Establish mask and valid-zero semantics from producer documentation and native
   metadata. Record exact decoded WKT, pixel resolution, dtype, nodata (`null`,
   finite number or `"NaN"`), mask flags and evidence. Declare pixel-is-area and
   internal/nodata masks; external sidecar masks are unsupported by this route.
   Document a separate explicit redistribution decision. Only then set
   `verified=true`. The validator checks product/band/release/units as well as
   actual raster metadata, so an R2025A/non-residential/packed-scale substitution
   does not proceed silently. Review flags assert documented human verification;
   the software cannot prove that assertions are true.
4. Acquire the small native window into the ignored local source directory:

   ```sh
   python -m scripts.acquire_exposure_windows --source worldpop_2020_ind \
     --review work/source_reviews.json --output data/exposure_local/worldpop_2020_ind
   python -m scripts.acquire_exposure_windows --source ghsl_2020_built_surface \
     --review work/source_reviews.json --output data/exposure_local/ghsl_2020_built_surface
   ```

   The checked-in template is deliberately rejected with exit 2 **before network
   or output datasets**, including in metadata mode. No live acquisition command
   has been run with an asserted successful review.

The reader uses public HTTPS on the exact approved producer hosts, no URL secrets,
no `.netrc` credentials, no redirects and no whole-file fallback. Every response
must be 206 with exact Content-Range/Length, identity encoding and a stable strong
ETag; subsequent requests use If-Match. A 64 KiB block cache shares a default
**32 MiB payload request budget** (CLI maximum 128 MiB). Failed/changed/truncated
responses stop. This bounds requested data bytes, not headers/TLS overhead or
server behaviour. Cache/index metadata and GDAL memory add overhead. A native
window is limited to **1,000,000 pixels**. If TIFF layout, ZIP packaging, sidecar
masks, missing validators or provider service behaviour do not fit this route,
stop; no archive/full-country download or interpolation fallback is provided.

Native selection uses the exact WRI bounds, 128 densification samples per edge,
outward floor/ceil and a **two-native-cell halo**. Source-extent clipping is
recorded separately; no uncovered pixels are invented or boundless-filled.
A dense 4,097-sample-per-edge Mollweide fixture independently checks inclusion
of the actual WRI boundary with the halo. This is a tested regional envelope
selection approach, not an arbitrary global reprojection guarantee. Extent
containment is **not usable-pixel coverage**.

Native base-resolution samples are read without `out_shape`, reprojection,
interpolation or scale conversion. Values/dtype/nodata/georeferencing and binary
mask are retained in `source_window.tif`; the mask is re-encoded internally in
RFC15 form. Raw masked values are not replaced with zero or another sentinel.
Declared-valid negative/infinite exposure and fractional masks fail; declared-valid
NaN remains explicitly missing in summary counts without altering the raw file.
Packed/scaled or point-sampled data require separate reviewed support.

`manifest.json` records source IDs/URL/version, ETag/size, acquisition UTC, review
and attribution/terms, actual native WKT/affine/dtype/nodata, mask storage, native
window/halo/clipping, source-window known totals, exact WRI target checksum, HTTP
budget and the cropped TIFF's SHA-256/size. Native-window known fractions are
pixel-count summaries, not WRI coverage or physical-area fractions. GDAL may normalize the WKT representation;
the reviewed producer WKT is retained separately. The complete remote object is
not downloaded or hashed: its full-object SHA-256 is explicitly null. This is a
re-encoded **native source window**, not a byte-identical provider original and
not a WRI-aligned product. No aligned products share its directory.

Outputs are staged and published as a directory only after success, and existing
output directories are not replaced. `data/exposure_local/` is ignored by Git.
No source/derived dataset may be added until the exact artifact's redistribution
terms and size have been checked; current work commits **code and metadata only**.
Do not store credentials in reviews or manifests. There is no authentication code.

## Phase 3: not run, and criteria for continuing

No real source totals, retained/clipped totals, conservation errors, target
coverage or flood-exposure values exist for this milestone. The 71 passing tests
include the preserved calculation tests plus acquisition fixtures; they are not
real-exposure validation. Hand-calculated native fixtures retain 1,843 known
population-like units and 1,110 built-up-like m², with valid zeros and independent
masked cells while preserving their raw values;
these do not establish real population or built-up coverage.

After genuine windows pass source validation, use M2A-2 on verified shared
EPSG:4326 grids and M2A-3 on actual GHSL WKT. Do not relabel CRS to make a fixture
match. Balance known source-window totals against retained contributions inside
the WRI footprint and clipped contributions outside it, including the halo.
Missing source remains unknown; total conservation only applies to the known
measure/domain. Check complete/partial/uncertain target cells independently for
population and built-up surface, then hand complete grids/masks to M2A-1 at
strict depth thresholds. No ordinary bilinear resampling of extensive totals.

M2A-3's full in-memory remapping has not been validated on hundreds of thousands
of real source cells; acquisition budgets do not establish remapping scalability.
Profile, validate numerical convergence/budgets and address memory limits before
production use. Pairing 2020 exposure with modeled historical WATCH hazard is
screening, not reconstruction of a coeval historical disaster or observed damage.
No financial loss, vulnerability or production REAL exposure dashboard is added.

Next single task: enable permitted producer access, resolve exact file/variant
identity and inspect/review native WKT and masks, then run bounded acquisition
within the existing authorization. Do not claim this milestone acquired data.

## M2B-2 GitHub-hosted access diagnostic

A separate [manual Actions workflow](ACTIONS_ACCESS_CHECK.md) can check official
endpoint connectivity and optional one-byte TIFF Range support from a GitHub-hosted
runner. It does not acquire rasters, establish mask/coverage semantics or change
these review gates. No hosted run has completed in this task: the new
`workflow_dispatch` file must first exist on default main, and the PR is left
unmerged. The local Codex proxy result cannot be used as GitHub-hosted evidence.
