# M2B-2 GitHub-hosted provider access diagnostic

Workflow: [`.github/workflows/provider-access-check.yml`](../.github/workflows/provider-access-check.yml)
— **FloodCAT provider access check**. It uses `workflow_dispatch` only; commits,
pull requests, merges and schedules do not start it. No GitHub-hosted execution
has completed as part of this PR, so **GitHub-hosted provider access is unverified**.

## What runs

An `ubuntu-latest` GitHub-hosted runner with Python **3.11** executes only the
standard-library diagnostic and its offline tests. No pip/application/scientific
packages or CLIMADA are installed. The application requirements and all existing
acquisition/calculation code remain unchanged.

The six default requests are **HEAD only**:

- WorldPop website, `https://www.worldpop.org/`.
- WorldPop data host, `https://data.worldpop.org/`.
- Official legacy and R2025A Earth Engine catalog pages.
- Official GHSL producer page, `https://ghsl.jrc.ec.europa.eu/ghs_buS2023.php`.
- JRC candidate product directory,
  `https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_BUILT_S_GLOBE_R2023A/`.

A directory/page response is not evidence of an available raster. A HEAD 405 is
recorded without automatically retrying GET. No file URL is guessed or scraped.
The checked-in M2B-1 source-review records remain unverified.

Optional inputs accept an **exact reviewed public native TIFF URL** for each
provider. Only `data.worldpop.org` and `jeodpp.jrc.ec.europa.eu`, respectively,
are allowed. Queries, fragments, user/password URLs, non-HTTPS, other ports/hosts
and archives are rejected before requests. Leave inputs blank until a real URL
has been identified; there is no assumed default population/GHSL filename.

For each supplied raster URL the tool performs one HEAD and one
`GET Range: bytes=0-0`. It reads **one byte only** if status 206, Content-Range
`bytes 0-0/<size greater than 1>`, Content-Length 1 and identity/non-chunked
encoding agree. The byte is discarded. A full-response 200, malformed/encoded
partial response, redirect or denial causes **no body read and no fallback**.
HEAD `Accept-Ranges` is only an advisory header, never proof of actual Range
support. No response bodies, binary samples or raster files enter the artifact.

## Bounds, redirects and credentials

- **5 s socket-operation timeout**, **15 s hard per-request deadline** enforced
  by terminating an isolated subprocess, with no retries.
- A shared worker reader caps consumed HTTP status/headers/body at **16,385
  bytes** across responses, including proxy CONNECT. TLS/request overhead and
  operating-system/socket buffering are not a measured wire-byte budget. An
  oversized response is classified as a response/protocol limit.
- Six default requests; at most **10** with both optional URLs. At most **two
  discarded body bytes** in a complete optional run. The job has a **5 min cap**.
- Redirects are **never followed**, including same-host redirects. Status and
  a location stripped of credentials/query/fragment are recorded. A redirect's
  destination must be reviewed separately before any later run.
- No Earth Engine/provider auth, cookies, `.netrc`, keys, signed URLs, secret
  inputs, alternate proxy or disabled TLS. Normal inherited proxy/CA settings
  are respected. Denials/rate limits are recorded without bypass or retry.
- GitHub's normal checkout/artifact infrastructure is used with `contents: read`,
  no secret references and `persist-credentials: false`. No GitHub token is
  supplied to provider requests. Official actions are pinned to observed v6
  commit SHAs, rather than floating tags.

The diagnostic saves only `report.json` and `report.md`. JSON contains the request
URL/method, UTC, origin HTTP status, separate proxy CONNECT failure status, allowed
response headers, redirect policy/location, byte counters, limits and classified
DNS/TLS/socket/protocol/access failures. Raw exception text, response bodies and
ambient environment/proxy credentials are not saved. Only a short allowlist of
GitHub run/ref/SHA/workflow-ref/runner-context fields is recorded. A terminated
worker reports unknown byte counts rather than inventing zero.

## Manual run through the Actions tab

GitHub's [official workflow_dispatch documentation](https://github.com/github/docs/blob/main/data/reusables/actions/workflow-dispatch.md)
states: **“This trigger only receives events when the workflow file is on the
default branch.”** At the task's confirmed main `5e9687e`, no workflow files
exist. This new file is only in the unmerged feature branch, and this task must
not merge it. That is the precise current GitHub-hosted execution blocker; no
hosted run or provider result is claimed. We did not add an automatic trigger or
modify main to work around the prerequisite.

After the repository owner merges this PR:

1. Open [FloodCAT → Actions](https://github.com/prasadOS/FloodCAT/actions).
2. Choose **FloodCAT provider access check** in the left workflow list.
3. Click **Run workflow**, select **main** (or a reviewed branch after the workflow
   exists on default main), and leave both optional raster URLs blank for an
   initial website/data-host check. If Actions is disabled by repository policy,
   the owner must enable it in **Settings → Actions → General** first.
4. Supply optional TIFF URLs only when their exact public identities are known;
   never paste credential-bearing or signed links. Click **Run workflow**.
5. Wait for completion. Review the job summary and download the
   **provider-access-report** artifact (`report.json`, `report.md`). Retention is
   **14 days**. Save the run URL, commit SHA, execution context and result details
   before treating them as evidence.

There are no automatic runs after merge, and this workflow never commits data,
changes review flags, acquires exposure grids or opens/merges another PR.

## Interpreting a run

A green job means the **diagnostic completed and reported its observations**.
Network denials and HTTP errors are valid diagnostic outcomes; they do not make
all sources accessible. Do not infer source success from job colour alone.

- A successful website/directory HEAD proves only that the endpoint responded
  in that runner at that time. It proves no raster/product availability.
- A redirect records an unvisited destination; an auth/access denial receives
  no authentication attempt. A proxy CONNECT status is not an origin HTTP status.
- `observed_exact_one_byte` is limited evidence that that specific URL served
  the requested byte. It does not validate product identity, full download,
  stable ETag across requests, CRS/WKT, units, mask/zero semantics, licensing or
  usable Patna coverage. M2B-1's acquisition checks still apply.
- Without optional URLs, Range support is explicitly **not tested**. An
  `Accept-Ranges` header alone cannot change that result.
- Local Codex results cannot establish GitHub-hosted connectivity. Inspect the
  actual Actions run and its `RUNNER_ENVIRONMENT=github-hosted`/run/ref/SHA context.
  Scientific raster availability remains `not_established` in this diagnostic.

## Local evidence and limits

Run offline safeguards without installing dependencies:

```sh
python3.11 -m unittest discover -s tests -p test_provider_access.py -v
python3.11 -m scripts.check_provider_access --output work/provider-access
```

The second command makes the six bounded HEAD requests; optional URLs come only
from `WORLDPOP_RASTER_URL` / `GHSL_RASTER_URL`. No provider credentials are read.
The observed local Codex run had **six proxy CONNECT 403 failures**, zero body
bytes read, no origin HTTP status, and both raster Range checks skipped. This is
local policy evidence only, not an Actions-run result. Unit tests exercise exact
and ignored ranges, redirects/auth suppression, response budgets, hard timeouts,
HTTP/proxy parsing/cleanup, redaction and metadata-only reports. Workflow syntax
and trigger/permission structure were also validated locally; see
[TEST_RESULTS.md](TEST_RESULTS.md) for exact commands/results.

Next single task: once this workflow is present on main, manually dispatch it and
review its actual GitHub-hosted artifact. Producer access, native asset identity
and all M2B-1 scientific/data checks remain unverified until separately evidenced.
