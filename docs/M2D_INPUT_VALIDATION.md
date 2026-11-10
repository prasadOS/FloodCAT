# M2D input validation — blocked before dashboard activation

All 15 uploaded files are readable native GeoTIFFs, not LFS pointers. Every grid matches the existing 65×168 EPSG:4326 reference exactly (affine, WKT, bounds). Candidate fixed exposure footprint remains 6,113 cells. The audited WorldPop/GHSL aligned arrays can geometrically be reused; no remapping or scenario exposure is performed or published at this stage.

**Blocker:** the committed export recipe identifies only Historical T100. The other 14 TIFFs contain no asset/GCM/scenario/epoch/unit metadata; names are not independent source evidence. The requested HadGEM2-ES selection cannot be established. Missing task IDs alone would be a disclosed limitation, but missing source-selection evidence is a material source-identity ambiguity. AGENTS.md requires stopping here. A new export recipe or source/task metadata bound to these file hashes is needed. No credentials or re-download is requested.

Full metadata, SHA-256, bands, dtype, nodata/masks/NaNs/zeros, bounds/WKT and ordering diagnostics are in `config/patna_multiscenario_validation.json`. Filename claims are explicitly unverified and asset IDs remain null rather than guessed. Historical T100 retains the prior user-attested recipe/pilot evidence, not a claim of independent GEE task verification.

| File scenario label (unverified except T100) | Valid zero cells | Positive cells | Maximum numeric depth |
|---|---:|---:|---:|
| Historical_T25 | 6228 | 4692 | 5.689462661743164 |
| Historical_T50 | 5948 | 4972 | 6.405810356140137 |
| Historical_T100 | 5703 | 5217 | 7.031288146972656 |
| Historical_T250 | 5409 | 5511 | 7.730871200561523 |
| Historical_T500 | 5195 | 5725 | 8.182788848876953 |
| RCP45_2050_T25 | 5564 | 5356 | 7.628022193908691 |
| RCP45_2050_T50 | 5353 | 5567 | 8.042304992675781 |
| RCP45_2050_T100 | 5152 | 5768 | 8.410629272460938 |
| RCP45_2050_T250 | 4921 | 5999 | 8.84787368774414 |
| RCP45_2050_T500 | 4750 | 6170 | 9.153129577636719 |
| RCP85_2050_T25 | 4469 | 6451 | 11.686285018920898 |
| RCP85_2050_T50 | 4132 | 6788 | 12.38322639465332 |
| RCP85_2050_T100 | 3851 | 7069 | 13.009347915649414 |
| RCP85_2050_T250 | 3493 | 7427 | 13.767717361450195 |
| RCP85_2050_T500 | 3258 | 7662 | 14.294441223144531 |

Every raster has nodata -9999, no masked or NaN samples and finite nonnegative values. All 12 adjacent return-period pair diagnostics have 0 cells with higher-return-period depth below lower-return-period depth. This is a diagnostic, not proof of identity or an imposed monotonicity assumption.

Validation command (optional acquisition/science environment):

```sh
python -m scripts.validate_multiscenario_inputs --output config/patna_multiscenario_validation.json
```

Expected exit **2**, status `blocked`, 15 inputs and 14 source blockers. Missing/unreadable rasters or corrupt audited artifacts raise an error instead of authorizing results. No hosted dependencies, app controls, raw files, processed bundles or prior audit records change. Existing T100 values remain available unchanged.

Three focused tests pass; full suite 111 passed with no skips. Browser multi-scenario acceptance is not run because no unverified scenario is activated. The feature is incomplete and the PR must not merge until source identity is evidenced, remaining M2D phases implemented, and all numerical/browser acceptance checks pass. No deployment verified.
