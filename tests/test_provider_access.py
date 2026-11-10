"""Standard-library-only offline tests for the manually dispatched diagnostic."""

import http.client
import io
import json
import os
from pathlib import Path
import socket
import ssl
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError
from urllib.request import HTTPBasicAuthHandler, HTTPCookieProcessor

from scripts import check_provider_access as probe


class Response:
    def __init__(self, status=200, headers=None, body=b"", allow_read=False):
        self.code, self.headers, self.body = status, headers or {}, body
        self.allow_read, self.reads = allow_read, []
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        self.closed = True

    def read(self, count=-1):
        if not self.allow_read:
            raise AssertionError("No body may be read for this response")
        self.reads.append(count)
        return self.body[:count]


class TestProviderAccess(unittest.TestCase):
    def setUp(self):
        self.head = probe.probe_plan()[0][0]
        self.range = probe.probe_plan("https://data.worldpop.org/TEST.tif")[0][-1]

    def perform(self, request, response):
        opener = Mock()
        opener.open.return_value = response
        with patch.object(probe, "build_opener", return_value=opener):
            result = probe.perform_probe(request)
        return result, opener.open.call_args

    def test_default_heads_optional_ranges_and_no_guessed_files(self):
        plan, skipped = probe.probe_plan()
        self.assertEqual(len(plan), 6)
        self.assertTrue(all(p["method"] == "HEAD" for p in plan))
        self.assertEqual(len(skipped), 2)
        plan, skipped = probe.probe_plan("https://data.worldpop.org/a.tif",
                                         "https://jeodpp.jrc.ec.europa.eu/b.tiff")
        self.assertEqual(len(plan), 10)
        self.assertEqual(sum(p["method"] == "GET" for p in plan), 2)
        self.assertEqual(skipped, [])

    def test_optional_urls_reject_auth_queries_wrong_hosts_and_archives(self):
        for url in ["http://data.worldpop.org/a.tif", "https://user:password@data.worldpop.org/a.tif",
                    "https://data.worldpop.org/a.tif?token=secret", "https://data.worldpop.org/a.tif#fragment",
                    "https://data.worldpop.org.evil.invalid/a.tif", "https://example.org/a.tif",
                    "https://data.worldpop.org:8443/a.tif", "https://data.worldpop.org/a.zip",
                    "https://data.worldpop.org/a\r\n.tif"]:
            with self.subTest(url=url), self.assertRaises(ValueError):
                probe.probe_plan(url)
        with patch.object(probe, "build_opener") as opener, self.assertRaises(ValueError):
            probe.perform_probe({**self.head, "method": "GET"})
        opener.assert_not_called()

    def test_head_records_status_advisory_range_and_reads_no_body(self):
        result, call = self.perform(self.head, Response(headers={"Accept-Ranges": "bytes", "Content-Length": "999999999"}))
        self.assertEqual(result["http_status"], 200)
        self.assertEqual(result["body_bytes_read"], 0)
        self.assertEqual(result["range_support"], "not_tested")
        request = call.args[0]
        self.assertEqual(request.get_method(), "HEAD")
        self.assertNotIn("Authorization", dict(request.header_items()))
        self.assertNotIn("Cookie", dict(request.header_items()))
        self.assertEqual(call.kwargs["timeout"], 5)

    def test_exact_partial_response_reads_one_byte_and_discards_content(self):
        response = Response(206, {"Content-Range": "bytes 0-0/50000000", "Content-Length": "1"},
                            body=b"X_EXTRA_DATA_MUST_NOT_BE_READ", allow_read=True)
        result, call = self.perform(self.range, response)
        self.assertEqual(response.reads, [1])
        self.assertEqual(result["body_bytes_read"], 1)
        self.assertEqual(result["range_support"], "observed_exact_one_byte")
        self.assertNotIn("EXTRA_DATA", json.dumps(result))
        self.assertEqual(call.args[0].get_header("Range"), "bytes=0-0")

    def test_ignored_invalid_encoded_or_full_object_range_reads_nothing(self):
        for status, headers in [(200, {"Content-Length": "999999999"}),
                                (206, {"Content-Range": "bytes 0-0/1", "Content-Length": "1"}),
                                (206, {"Content-Range": "bytes 0-1/999", "Content-Length": "2"}),
                                (206, {"Content-Range": "bytes 0-0/999", "Content-Length": "1", "Content-Encoding": "gzip"}),
                                (206, {"Content-Range": "bytes 0-0/999", "Content-Length": "1", "Transfer-Encoding": "chunked"}),
                                (403, {})]:
            with self.subTest(status=status, headers=headers):
                result, _ = self.perform(self.range, Response(status, headers))
                self.assertEqual(result["body_bytes_read"], 0)
                self.assertEqual(result["range_support"], "not_observed_exact_one_byte_no_body_read")

    def test_truncated_exact_range_remains_inconclusive(self):
        result, _ = self.perform(self.range, Response(206, {"Content-Range": "bytes 0-0/999", "Content-Length": "1"},
                                                     allow_read=True))
        self.assertEqual(result["range_support"], "truncated")

    def test_redirects_are_not_followed_and_locations_are_redacted(self):
        location = "https://user:password@example.org/path?token=secret#fragment"
        result, _ = self.perform(self.head, Response(302, {"Location": location}))
        self.assertEqual(result["outcome"], "redirect_not_followed")
        self.assertEqual(result["redirect_location"]["url_without_query_or_credentials"], "https://example.org/path")
        self.assertNotIn("password", json.dumps(result))
        self.assertNotIn("secret", json.dumps(result))
        handler = probe._NoRedirect()
        self.assertIsNone(handler.redirect_request(None, None, 302, "", {}, location))
        opener = probe.build_opener(handler)
        self.assertFalse(any(isinstance(h, (HTTPBasicAuthHandler, HTTPCookieProcessor)) for h in opener.handlers))

    def test_http_errors_are_recorded_without_body_or_auth(self):
        for status, outcome in [(403, "http_access_denied_no_authentication_attempted"), (429, "rate_limited_no_retry")]:
            opener = Mock()
            opener.open.side_effect = HTTPError(self.head["url"], status, "fixture", {}, Response(status))
            with patch.object(probe, "build_opener", return_value=opener):
                result = probe.perform_probe(self.head)
            self.assertEqual(result["http_status"], status)
            self.assertEqual(result["outcome"], outcome)
            self.assertEqual(opener.open.call_count, 1)

    def test_network_errors_are_classified_without_raw_environment_details(self):
        for error, outcome in [(socket.timeout(), "socket_timeout"),
                               (socket.gaierror(-2, "private fixture"), "dns_failure"),
                               (ssl.SSLError("private fixture"), "tls_failure"),
                               (OSError("Tunnel connection failed: 403 Forbidden"), "proxy_connect_failure")]:
            opener = Mock()
            opener.open.side_effect = URLError(error)
            with patch.object(probe, "build_opener", return_value=opener):
                result = probe.perform_probe(self.head)
            self.assertEqual(result["outcome"], outcome)
            self.assertNotIn("private fixture", json.dumps(result))

    def test_cumulative_response_budget_includes_status_and_headers(self):
        budget = [0]
        one = probe._LimitedReader(io.BytesIO(b"a"*100), budget)
        self.assertEqual(len(one.read(100)), 100)
        two = probe._LimitedReader(io.BytesIO(b"b"*(probe.RESPONSE_BYTE_LIMIT+10)), budget)
        self.assertEqual(len(two.readline()), probe.RESPONSE_BYTE_LIMIT-100)
        with self.assertRaises(probe.ResponseLimitError):
            two.read(1)
        self.assertEqual(budget[0], probe.RESPONSE_BYTE_LIMIT)

    def test_http_parser_uses_response_budget_and_restores_global_class(self):
        original = http.client.HTTPConnection.response_class

        class Socket:
            def makefile(self, *args):
                return io.BytesIO(b"HTTP/1.1 200 OK\r\nX-Large: "+b"a"*20000+b"\r\n\r\n")

        class Opener:
            def open(self, *args, **kwargs):
                response = http.client.HTTPConnection.response_class(Socket(), method="HEAD")
                response.begin()
                return response

        with patch.object(probe, "build_opener", return_value=Opener()):
            result = probe.perform_probe(self.head)
        self.assertEqual(result["outcome"], "response_or_protocol_limit")
        self.assertEqual(result["response_bytes_consumed"], probe.RESPONSE_BYTE_LIMIT)
        self.assertIs(http.client.HTTPConnection.response_class, original)

    def test_real_http_parser_handles_head_range_and_proxy_cleanup(self):
        for request, payload, expected_body in [
            (self.head, b"HTTP/1.1 200 OK\r\nContent-Length: 999999\r\n\r\n", 0),
            (self.range, b"HTTP/1.1 206 Partial Content\r\nContent-Range: bytes 0-0/999\r\nContent-Length: 1\r\n\r\nX", 1),
        ]:
            class Socket:
                def makefile(self, *args):
                    return io.BytesIO(payload)

            class Opener:
                def open(self, *args, **kwargs):
                    response = http.client.HTTPConnection.response_class(Socket(), method=request["method"])
                    response.begin()
                    return response

            with patch.object(probe, "build_opener", return_value=Opener()):
                result = probe.perform_probe(request)
            self.assertEqual(result["body_bytes_read"], expected_body)
            self.assertLessEqual(result["response_bytes_consumed"], probe.RESPONSE_BYTE_LIMIT)

        class DenyingSocket:
            def makefile(self, *args):
                return io.BytesIO(b"HTTP/1.1 403 Forbidden\r\n\r\n")

            def sendall(self, *args):
                pass

            def close(self):
                pass

        class ProxyOpener:
            def open(self, *args, **kwargs):
                connection = http.client.HTTPConnection("fixture")
                connection.set_tunnel("www.worldpop.org", 443)
                connection.sock = DenyingSocket()
                connection._tunnel()

        with patch.object(probe, "build_opener", return_value=ProxyOpener()):
            result = probe.perform_probe(self.head)
        self.assertEqual(result["outcome"], "proxy_connect_failure")
        self.assertEqual(result["proxy_connect_status"], 403)

    def test_hard_deadline_terminates_worker_and_reports_unknown_bytes(self):
        with patch.object(probe.subprocess, "run", side_effect=subprocess.TimeoutExpired("fixture", 15)) as run:
            result = probe.run_probe(self.head)
        self.assertEqual(run.call_args.kwargs["timeout"], 15)
        self.assertEqual(result["outcome"], "hard_deadline_worker_terminated")
        self.assertIsNone(result["body_bytes_read"])

    def test_report_contains_only_metadata_and_whitelisted_execution_context(self):
        result, _ = self.perform(self.head, Response())
        with tempfile.TemporaryDirectory() as temporary, patch.dict(os.environ, {"SECRET_FIXTURE": "do_not_persist"}):
            report = probe.write_report(temporary, [result], probe.probe_plan()[1])
            payload = (Path(temporary)/"report.json").read_text()
            self.assertNotIn("do_not_persist", payload)
            self.assertEqual(report["raster_availability_and_scientific_validity"], "not_established")
            self.assertEqual(sorted(p.name for p in Path(temporary).iterdir()), ["report.json", "report.md"])


if __name__ == "__main__":
    unittest.main()
