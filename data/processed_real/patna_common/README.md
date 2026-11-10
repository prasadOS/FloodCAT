# Verified common-cell screening bundle

`aligned_common.npz` (323,391 bytes) contains native WRI depth, aligned extensive
population/built-up totals, independent source/available coverage fractions,
completeness/uncertainty masks and known subtotals. Load with NumPy
`allow_pickle=False`; verify its SHA-256 against `validation.json` first.
`audit.json` must say `passed` before using it.

**Domain: 6,113 complete WRI cells in the uploaded export bounding rectangle,
not the Patna district polygon.** This is 55.98% of uploaded WRI cells. At 0 m,
3,101 of the full raster's 5,217 flooded cells are outside this common domain;
those cells have no complete joint exposure total. Do not label common-cell
results as full district/export totals or fill missing exposure with zero.

`validation.json` records full native metadata/WKT, raw hashes, the user-supplied
export recipe, source/retained/clipped known budgets, common-domain strict-threshold
results and measured bounded processing. `audit.json` adds independent threshold
sums, full-domain missing/flooded counts, source hash checks, software versions
and sampled geometric refinement. Timings/timestamps can differ on reproduction.

Attribution and redistribution: WorldPop, University of Southampton, legacy India
2020 population (CC BY 4.0); European Commission JRC, Pesaresi and Politis (2023),
GHS-BUILT-S R2023A, DOI 10.2905/9F06F36F-4B11-47EC-ABB0-4F8B7B1D72EA (reuse with
source acknowledgement); WRI Aqueduct Floods Hazard Maps V2, historical WATCH
T100, via Earth Engine (existing project WRI attribution/terms apply). Exact
product IDs, official catalog evidence and recipe are in the manifests. No GAUL
boundary geometry is redistributed. This compact derived bundle adds no raw
raster copies. Exposure is modeled screening, not observed inundation or damage.

Rebuild to a new directory from the repository root with the optional acquisition
environment: `python -m scripts.validate_patna_uploads --output work/patna-rebuild`.
Audit an existing bundle without full remapping using the same command with
`--audit-only`. The Streamlit app is deliberately unchanged.
