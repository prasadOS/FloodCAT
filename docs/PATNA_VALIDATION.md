# M2C-1 real Patna upload validation and common-footprint exposure

Started from remote main `2ee214a`, which added the three source TIFFs after PR #5.
An AGENTS-only update arrived during validation; the feature branch was then
fast-forwarded to `7fe68c8`, with no source-data or application changes.
All three are actual **little-endian BigTIFF GeoTIFFs**, not LFS pointers. Sources
were opened read-only and have not been rewritten, deleted or copied into the
processed bundle. No provider acquisition, authentication or CLIMADA was needed.

## Source identity, units and export provenance

The user supplied the Earth Engine recipe after initial inspection found no
source IDs or unit tags in the TIFFs. Its scientific operations are transcribed
in [scripts/gee/export_patna_native.js](../scripts/gee/export_patna_native.js),
bound to source SHA-256 hashes in
[config/patna_upload_provenance.json](../config/patna_upload_provenance.json).
The map/print-only presentation was omitted. The recipe was not re-run here;
export task IDs and acquisition timestamps were not supplied and remain null.
This is user-attested export provenance, not an independent new Earth Engine query.

- WRI: `WRI/Aqueduct_Flood_Hazard_Maps/V2/inunriver_historical_000000000WATCH_1980_rp00100`,
  `inundation_depth`, metres. Grid alignment and **all 2,030 overlapping pilot
  cells (35×58)** match bit-for-bit; maximum difference **0 m**. The match
  corroborates identity on the overlap, not independent verification of every
  cell outside it. The recipe identifies the full asset.
- WorldPop: legacy `WorldPop/GP/100m/pop`, `country=IND`, `year=2020`, with uniqueness
  and exact `IND_2020` index guards; `population`, estimated **people/cell**,
  not density and not R2025A. Fractional counts are retained.
- GHSL: `JRC/GHSL/P2023A/GHS_BUILT_S/2020`, total `built_surface`, **m²/cell**,
  producer R2023A, not the NRES band. All available native values in this upload
  are integral m² before fractional spatial allocation.

The recipe uses source `projection()` CRS and `crsTransform`, then
`toFloat().unmask(-9999,false)`, with no explicit interpolation or aggregation.
It selects a unique `FAO/GAUL/2025/level2` IND/Bihar/Patna feature but exports
`district.buffer(500).bounds(1)`. **Exports are the buffered bounding rectangle,
not clipped district polygons.** The visualization-only `.clip(district)` does
not affect exported pixels. No district geometry was supplied or reconstructed.

TIFF unit tags are absent; units are established by the exact recipe-selected
bands and the pinned official catalog evidence from M2B-1. WorldPop is CC BY 4.0;
GHSL's catalog permits open/free reuse with source acknowledgement (custom EC
terms, not a fabricated CC BY label); WRI's existing attribution/redistribution
terms apply. The compact derivative includes these attributions and source IDs.
No GAUL geometry or new large native copy is redistributed.

## Actual raster metadata

All are one-band float32, pixel-is-area, scale 1 / offset 0, declared nodata -9999.
Pillow and Rasterio independently read every sample identically, including NaNs.
The complete actual decoded WKT, SHA-256, tags, affine and bounds are in
[validation.json](../data/processed_real/patna_common/validation.json); CRS aliases
below were resolved from these WKT definitions, not assumed from old fixtures.

| Input | Rows×columns | Bytes | CRS | Available pixels | Valid zero | Unavailable |
| --- | --- | ---: | --- | ---: | ---: | --- |
| WRI | 65×168 | 13,086 | EPSG:4326 | 10,920 | 5,703 | None |
| WorldPop | 644×1,672 | 5,758,647 | EPSG:4326 | 961,554 | 0 | 115,214 masked -9999 |
| GHSL | 638×1,532 | 1,741,467 | World Mollweide, resolves ESRI:54009 | 836,265 | 628,967 | 141,151 NaNs |

GHSL's stored nodata mask is **255 everywhere**, despite its NaNs. The pipeline
explicitly defines availability as stored-valid **and finite**. Unmask(-9999)
does not replace NaN samples that are already unmasked. The NaNs are preserved
in raw files and treated as unknown, never zero. The precise upstream cause of
these NaNs is unverified; their locations do not receive exposure totals. This
mismatch is a data-quality caveat, not a reason to invent a zero-valued surface.

Actual affine tuples `(dx,0,left,0,dy,top)`:

- WRI `(0.008333333333333333,0,84.67500000000001,0,-0.008333333333333333,25.741666666666674)`;
  bounds `(84.67500000000001,25.200000000000006,86.07500000000002,25.741666666666674)`.
- WorldPop `(0.0008333333300071276,0,84.68124967549109,0,-0.0008333333299997101,25.737916764723398)`;
  bounds `(84.68124967549109,25.201250100203584,86.074583003263,25.737916764723398)`.
  The measured transform is retained at full precision; no snapping to a nominal
  1/1200° grid or equal physical pixel-area assumption is applied.
- GHSL `(100,0,7955800,0,-100,3141100)`;
  projected bounds `(7955800,3077300,8109000,3141100)` metres. Actual WKT declares
  Mollweide with central meridian 0, false easting/northing 0, WGS84 datum/ellipsoid
  (a=6378137, inverse flattening=298.257223563), metre coordinates.

Available ranges: WRI **0–7.031288146972656 m**; population
**0.5546262264251709–416.09808349609375 people/cell**; built surface
**0–10,000 m²/cell**. No available negative/infinite values were found. WRI has
5,217 positive-depth cells; no missing hazard cells. A sum of depth samples in
inventory metadata is only a numeric fingerprint, not a flood volume metric.

## Conservative processing, coverage and budgets

M2A-2 aggregates population on the actual shared WGS84 grids using ellipsoid
physical-area intersections. The complete population source extent lies within
the larger WRI extent, independently establishing expected **zero clipping**.
The source total and retained subtotal agree exactly at printed float precision;
clipping is not inferred as a residual to make a balance tautologically pass.

M2A-3 remaps GHSL using its actual WKT and physical ellipsoid footprint areas.
A new adapter partitions the target into disjoint row strips, reads two-native-cell
halo windows and reuses the unchanged mapper. Source allocation fractions are
accumulated across strips, including split edge pixels. Weights are never
renormalized. A 60,000-source-cell cap is enforced before mapping; smaller strips
are selected if necessary. The actual maximum was **33,250 cells** per strip,
rather than retaining nearly one million GEOS source polygons at once.

| Known quantity | Source total | Retained inside WRI | Clipped outside WRI | Balance error |
| --- | ---: | ---: | ---: | ---: |
| Population, people | 15,827,395.092694104 | 15,827,395.092694104 | 0 | 0 |
| Built surface, m² | 244,426,882 | 244,425,812.59697458 | 1,069.4030445377978 | 0.000019133091 m² |

Built balance error is **7.83e-14 relative**; acceptance is 1e-10 relative or
1e-6 absolute. These are **known** source totals, excluding masked/NaN source
pixels. They do not establish unknown source values or conservation of an unknown
complete population/built-up total.

Population is complete on **6,113** target cells; built surface on **10,458**.
Their intersection with valid WRI is **6,113 cells**, **4,730.679260 km²**,
**55.979853% of uploaded WRI cells**. No target cell was classified geometrically
uncertain in this run; incomplete/missing cells remain explicit. Aligned arrays
store NaN for incomplete totals and retain separate known partial subtotals.

Known amounts retained outside the common-cell selection are **6,224,662.835504
people** and **89,538,372.099977 m²**. These are not redistributed into selected
cells. The complete common cells contain **9,602,732.257190 people** and
**154,887,440.496997 m²** before a depth threshold. These are not district totals.

## Real exposure on the complete common cells only

The unchanged M2A-1 engine selects valid whole cells with **depth strictly above**
the threshold. Dry zero and equality are excluded. Population/built-up availability
is complete within this explicitly selected common domain.

| Threshold m | Common flooded cells | Common flooded km² | Exposed estimated people | Exposed built surface m² |
| ---: | ---: | ---: | ---: | ---: |
| >0 | 2,116 | 1,637.310066 | 2,840,320.502107 | 32,216,343.944108 |
| >1 | 264 | 204.140478 | 438,591.003790 | 6,166,476.587885 |
| >2 | 183 | 141.504626 | 331,405.762198 | 4,659,542.437945 |
| >5 | 55 | 42.481048 | 145,829.645435 | 2,169,140.957512 |

**Coverage selection is material.** The full upload has 5,217, 1,382, 1,110 and
318 flooded cells at these thresholds. Respectively **3,101, 1,118, 927 and 263**
are excluded from the common domain. Do not label the table as complete exposure
for the upload or district. Missingness and cell selection can bias regional
interpretation. The audit records separate missing-population and missing-built
counts, with their overlap, for every threshold.

## Numerical checks and performance

- WRI's 2,030-cell pilot overlap is exact. Source raw hashes are rechecked after
  processing; all raw files are unchanged. Checksums bind this recipe/evidence
  to these particular uploads.
- Tiny independently hand-calculated fixtures check 36 → 3+7+11+15, a quarter
  clip 80 → 20 retained + 60 clipped, missing/zero distinctions and resource caps.
  Strip results agree with a monolithic map on the small fixture.
- Independent direct threshold sums of the real bundle (without calling the
  exposure engine) reproduce all reported totals. Source/retained/clipped budgets
  and checksum/readback/mask invariants pass.
- The first real-cell audit used an overly tight 0.001 m² / 1e-7 comparison and
  detected a 0.0125 m² change under refinement. Follow-up checks use **10 spatially
  distributed/common-centre cells** at 1 cm, 0.1 mm and 1 µm edge controls. Maximum
  default-to-1µm difference is **0.016615 m²**; maximum 0.1mm-to-1µm change is
  **0.004102 m²**. All pass declared sampled tolerances max(0.1 m², 1 ppm of
  target built surface), with refinement-to-refinement ≤0.01 m². The absolute
  allowance is below the observed native 1 m² value quantization. This is sampled
  convergence, **not a global error bound or independent proof** of PROJ/GEOS.
  M2A-3's independent analytic/quadrature tests remain part of the regression suite.
- Population took **1.065 s**. GHSL's **33 strips** totalled **269.740 s** of
  mapping/apply time (orchestration/GC excluded), maximum **9.433 s** per strip;
  peak whole-process Linux RSS **318,128 KiB / 310.67 MiB**. This is practical for
  this offline tile, not an application-startup operation or global-scale claim.

## Reproducible compact outputs and next step

[The processed directory](../data/processed_real/patna_common/) contains a
**323,391-byte NPZ**, detailed validation/provenance JSON, independent audit JSON
and attribution/readiness notes. It is a compact coarse-grid derivative, not
another raw dataset copy. Total files are under 0.4 MiB. SHA-256 of the NPZ is
`f807ca277167e027435845f00e02b239fb76d18c1020d2df58259e2db8548167`.

Using the existing optional acquisition environment, from repository root:

```sh
python -m scripts.validate_patna_uploads --output work/patna-rebuild
python -m scripts.validate_patna_uploads --output work/patna-rebuild --audit-only
python -m unittest discover -s tests -v
```

Use a new output directory; the command refuses to replace existing evidence.
The second command audits a bundle without repeating full remapping. Scientific
arrays reproduce within the recorded numerical tolerances; timestamps, timings
and byte encodings can vary by tool version. No new packages or hosted runtime
requirements were added. The Streamlit app and WRI calculations are unchanged.

Smallest next integration: add a NumPy-only, checksum-verified bundle loader and
an opt-in REAL common-footprint exposure panel showing **common coverage,
excluded flooded cells, source attribution and domain limits** alongside these
metrics. Keep Synthetic demo/default and the existing WRI pilot view. Do not load
Rasterio/GEOS or run remapping in Streamlit. A district-only dashboard additionally
needs the exact district polygon and another reviewed clipping/domain decision.
The missing export task IDs/acquisition times and upstream NaN cause remain
provenance/data-quality limitations. Exposure is not damage or observed inundation.
