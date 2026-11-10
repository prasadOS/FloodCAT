"""Bounded anonymous diagnostics, not raster acquisition or product validation.

Python 3.11 standard library only. Each request runs in a killable subprocess.
No bodies are saved: HEAD reads zero body bytes; an optional exact raster probe
reads one byte only after validating a 206 response. Redirects are never followed.
"""

import argparse
from datetime import datetime, timezone
import http.client
import json
import os
from pathlib import Path
import re
import socket
import ssl
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

SOCKET_TIMEOUT_SECONDS = 5
REQUEST_DEADLINE_SECONDS = 15
RESPONSE_BYTE_LIMIT = 16*1024+1  # Status, headers and optional body; excludes TLS overhead.
DEFAULT_PROBES = {
    "worldpop_website": "https://www.worldpop.org/",
    "worldpop_data_host": "https://data.worldpop.org/",
    "worldpop_legacy_catalog": "https://developers.google.com/earth-engine/datasets/catalog/WorldPop_GP_100m_pop",
    "worldpop_r2025a_catalog": "https://developers.google.com/earth-engine/datasets/catalog/WorldPop_GP_100m_R2025A_v1_pop",
    "ghsl_website": "https://ghsl.jrc.ec.europa.eu/ghs_buS2023.php",
    "ghsl_data_directory": "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_BUILT_S_GLOBE_R2023A/",
}
RASTER_HOSTS = {"worldpop": "data.worldpop.org", "ghsl": "jeodpp.jrc.ec.europa.eu"}


class ResponseLimitError(Exception):
    pass


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, new_url):
        return None


class _LimitedReader:
    """Limit HTTP status/header/body reads across all responses in one worker."""
    def __init__(self, stream, budget):
        self.stream, self.budget = stream, budget

    def _read(self, method, size=-1):
        remaining = RESPONSE_BYTE_LIMIT-self.budget[0]
        if remaining <= 0:
            raise ResponseLimitError("HTTP response byte limit reached")
        size = remaining if size < 0 else min(size, remaining)
        data = getattr(self.stream, method)(size)
        self.budget[0] += len(data)
        return data

    def read(self, size=-1):
        return self._read("read", size)

    def readline(self, size=-1):
        return self._read("readline", size)

    def close(self):
        self.stream.close()

    def flush(self):
        self.stream.flush()

    @property
    def closed(self):
        return self.stream.closed


def raster_url(provider, url):
    parts = urlsplit(url)
    if (len(url) > 2048 or any(ord(c) < 33 or ord(c) == 127 for c in url) or
            parts.scheme != "https" or parts.hostname != RASTER_HOSTS[provider] or
            parts.username or parts.password or parts.query or parts.fragment or
            parts.port not in (None, 443) or not parts.path.lower().endswith((".tif", ".tiff"))):
        raise ValueError("Optional raster URL must be a public HTTPS TIFF on its exact provider host, without credentials/query/fragment")
    return url


def probe_plan(worldpop_url="", ghsl_url=""):
    probes = [{"id": name, "url": url, "method": "HEAD", "kind": "website_or_directory"}
              for name, url in DEFAULT_PROBES.items()]
    skipped = []
    for provider, url in (("worldpop", worldpop_url), ("ghsl", ghsl_url)):
        if not url:
            skipped.append({"provider": provider, "range_support": "not_tested",
                            "reason": "No exact reviewed native raster URL supplied; no filename guessed"})
            continue
        url = raster_url(provider, url)
        for method in ("HEAD", "GET"):
            probes.append({"id": f"{provider}_raster_{method.lower()}", "url": url,
                           "method": method, "kind": "exact_raster", "provider": provider})
    return probes, skipped


def _validate_probe(probe):
    if probe.get("id") in DEFAULT_PROBES:
        if probe != {"id": probe["id"], "url": DEFAULT_PROBES[probe["id"]],
                     "method": "HEAD", "kind": "website_or_directory"}:
            raise ValueError("Invalid fixed endpoint request")
    else:
        provider = probe.get("provider")
        method = probe.get("method")
        if provider not in RASTER_HOSTS or method not in ("HEAD", "GET") or probe.get("kind") != "exact_raster":
            raise ValueError("Invalid raster probe")
        if probe.get("id") != f"{provider}_raster_{method.lower()}":
            raise ValueError("Invalid raster probe identifier")
        raster_url(provider, probe["url"])


def _location(value):
    # Never persist redirect credentials, query strings or fragments.
    try:
        parts = urlsplit(value)
    except ValueError:
        return {"invalid_location": True}
    host = parts.hostname or ""
    return {"url_without_query_or_credentials": urlunsplit((parts.scheme, host, parts.path, "", ""))[:2048],
            "query_or_credentials_redacted": bool(parts.query or parts.fragment or parts.username or parts.password)}


def perform_probe(probe):
    _validate_probe(probe)
    started = time.monotonic()
    budget = [0]
    original = http.client.HTTPConnection.response_class

    class LimitedResponse(original):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fp = _LimitedReader(self.fp, budget)

    # Isolated worker process only: include proxy CONNECT responses in the limit.
    http.client.HTTPConnection.response_class = LimitedResponse
    result = {**probe, "checked_utc": datetime.now(timezone.utc).isoformat(), "http_status": None,
              "redirect_policy": "never_follow", "body_bytes_read": 0, "range_support": "not_tested"}
    headers = {"User-Agent": "FloodCAT-M2B-2-access-check", "Accept-Encoding": "identity"}
    if probe["method"] == "GET":
        headers["Range"] = "bytes=0-0"
    request = Request(probe["url"], headers=headers, method=probe["method"])
    try:
        opener = build_opener(_NoRedirect())  # Default TLS/proxy trust; no auth/cookie handlers or .netrc.
        try:
            response = opener.open(request, timeout=SOCKET_TIMEOUT_SECONDS)
        except HTTPError as error:
            response = error  # Record HTTP errors without reading their bodies.
        with response:
            status = response.code
            result["http_status"] = status
            result["headers"] = {key: response.headers[key][:512] for key in
                                  ("Content-Type", "Content-Length", "Accept-Ranges", "Content-Range", "ETag")
                                  if key in response.headers}
            if response.headers.get("Location"):
                result["redirect_location"] = _location(response.headers["Location"])
            if 300 <= status < 400:
                result["outcome"] = "redirect_not_followed"
            elif status in (401, 403, 407):
                result["outcome"] = "http_access_denied_no_authentication_attempted"
            elif status == 429:
                result["outcome"] = "rate_limited_no_retry"
            else:
                result["outcome"] = "http_response_observed"
            if probe["method"] == "GET":
                match = re.fullmatch(r"bytes 0-0/(\d+)", response.headers.get("Content-Range", ""))
                exact = (status == 206 and match and int(match[1]) > 1 and
                         response.headers.get("Content-Length") == "1" and
                         response.headers.get("Content-Encoding", "identity").lower() == "identity" and
                         not response.headers.get("Transfer-Encoding"))
                if exact:
                    data = response.read(1)
                    result["body_bytes_read"] = len(data)  # Byte discarded, never saved.
                    result["range_support"] = "observed_exact_one_byte" if len(data) == 1 else "truncated"
                else:
                    result["range_support"] = "not_observed_exact_one_byte_no_body_read"
            # HEAD Accept-Ranges is advisory only; no inference of actual support.
    except (URLError, OSError, http.client.HTTPException, ResponseLimitError) as error:
        reason = error.reason if isinstance(error, URLError) else error
        result["error_type"] = type(reason).__name__
        if isinstance(reason, (socket.timeout, TimeoutError)):
            result["outcome"] = "socket_timeout"
        elif isinstance(reason, socket.gaierror):
            result["outcome"] = "dns_failure"
        elif isinstance(reason, ssl.SSLError):
            result["outcome"] = "tls_failure"
        elif isinstance(reason, (ResponseLimitError, http.client.HTTPException)):
            result["outcome"] = "response_or_protocol_limit"
        elif re.search(r"Tunnel connection failed: (\d{3})", str(reason)):
            result["outcome"] = "proxy_connect_failure"
            result["proxy_connect_status"] = int(re.search(r"Tunnel connection failed: (\d{3})", str(reason))[1])
        else:
            result["outcome"] = "network_failure"
    finally:
        http.client.HTTPConnection.response_class = original
    result["response_bytes_consumed"] = budget[0]
    result["elapsed_seconds"] = round(time.monotonic()-started, 3)
    return result


def run_probe(probe):
    _validate_probe(probe)
    try:
        completed = subprocess.run([sys.executable, "-m", "scripts.check_provider_access", "--worker"],
                                   input=json.dumps(probe), text=True, capture_output=True,
                                   timeout=REQUEST_DEADLINE_SECONDS, check=False)
    except subprocess.TimeoutExpired:
        return {**probe, "http_status": None, "outcome": "hard_deadline_worker_terminated",
                "redirect_policy": "never_follow", "range_support": "not_tested",
                "body_bytes_read": None, "response_bytes_consumed": None}
    if completed.returncode != 0:
        # No raw stderr: it can contain ambient proxy or credential information.
        return {**probe, "http_status": None, "outcome": "worker_failure",
                "worker_exit_code": completed.returncode, "redirect_policy": "never_follow",
                "range_support": "not_tested", "body_bytes_read": None}
    try:
        return json.loads(completed.stdout)
    except ValueError:
        return {**probe, "http_status": None, "outcome": "invalid_worker_report",
                "redirect_policy": "never_follow", "range_support": "not_tested", "body_bytes_read": None}


def write_report(directory, results, skipped):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    context = {key: os.environ.get(key) for key in ("GITHUB_ACTIONS", "GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT",
               "GITHUB_SHA", "GITHUB_REF", "GITHUB_WORKFLOW_REF", "RUNNER_ENVIRONMENT", "RUNNER_OS")}
    report = {"schema_version": 1, "created_utc": datetime.now(timezone.utc).isoformat(),
              "execution_context": context, "python": sys.version.split()[0],
              "limits": {"socket_timeout_seconds": SOCKET_TIMEOUT_SECONDS,
                         "request_hard_deadline_seconds": REQUEST_DEADLINE_SECONDS,
                         "response_byte_limit_per_worker": RESPONSE_BYTE_LIMIT,
                         "maximum_body_bytes_per_range_probe": 1, "maximum_requests": 10,
                         "redirects": "never", "retries": 0},
              "results": results, "skipped_range_checks": skipped,
              "raster_availability_and_scientific_validity": "not_established"}
    (directory/"report.json").write_text(json.dumps(report, indent=2)+"\n")
    lines = ["# FloodCAT provider access diagnostic", "",
             "Diagnostic completion does not establish raster availability, license, masks or usable coverage.", "",
             "| Endpoint | Method | Origin HTTP | Proxy CONNECT | Outcome | Range | Body bytes |",
             "| --- | --- | --- | --- | --- | --- | --- |"]
    for r in results:
        lines.append(f"| {r['id']} | {r['method']} | {r.get('http_status')} | "
                     f"{r.get('proxy_connect_status', '-')} | {r['outcome']} | "
                     f"{r['range_support']} | {r.get('body_bytes_read')} |")
    for r in skipped:
        lines.append(f"\n{r['provider']}: Range not tested — no reviewed exact raster URL supplied.")
    lines += ["", "Review report.json for redirect locations, response headers, blockers and execution context.",
              "No response bodies or raster files are saved."]
    (directory/"report.md").write_text("\n".join(lines)+"\n")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("work/provider-access"))
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.worker:
        print(json.dumps(perform_probe(json.load(sys.stdin))))
        return 0
    try:
        probes, skipped = probe_plan(os.environ.get("WORLDPOP_RASTER_URL", ""), os.environ.get("GHSL_RASTER_URL", ""))
    except ValueError:
        parser.error("Invalid optional provider URL; no request sent (credentials/query/fragment and non-provider hosts are forbidden)")
    write_report(args.output, [run_probe(probe) for probe in probes], skipped)
    print(f"Diagnostic report written to {args.output}; raster availability remains unverified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
