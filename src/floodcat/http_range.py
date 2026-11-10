"""Anonymous, bounded HTTP Range reads; never fall back to whole-file downloads."""

import io
import re
from urllib.parse import urlsplit

import requests


class AcquisitionBlocked(ValueError):
    """Access, verification or resource bounds prevent a defensible acquisition."""


class _Anonymous(requests.auth.AuthBase):
    def __call__(self, request):
        # Suppress implicit .netrc authentication while retaining proxy/CA trust.
        return request


def public_url(url, allowed_hosts):
    if not isinstance(url, str):
        raise AcquisitionBlocked("A verified public HTTPS source URL is required")
    parts = urlsplit(url)
    if (parts.scheme != "https" or parts.hostname not in allowed_hosts or
            parts.username or parts.password or parts.query or parts.fragment or
            parts.port not in (None, 443)):
        raise AcquisitionBlocked("Use an approved public HTTPS URL without credentials, query or fragment")
    return url


class HTTPRangeSource:
    """Shared fixed-size block cache and transfer budget for a public GeoTIFF.

    A strong ETag and exact byte-range responses are mandatory. Request budgets
    include repeated payload bytes, but not HTTP headers. No redirects, auth,
    alternate hosts, decompression or full-file fallback are allowed.
    """

    def __init__(self, url, allowed_hosts, *, max_bytes=32*1024**2, block_size=65536):
        self.url = public_url(url, allowed_hosts)
        if (isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes < 1 or
                isinstance(block_size, bool) or not isinstance(block_size, int) or block_size < 1):
            raise AcquisitionBlocked("Range byte budgets must be positive integers")
        self.max_bytes, self.block_size = max_bytes, block_size
        self.transferred_bytes, self.cache = 0, {}
        self.size, self.etag, self.last_modified = None, None, None
        self.session = requests.Session()
        try:
            self._fetch(0, 0)
        except BaseException:
            self.session.close()
            raise

    def _fetch(self, first, last):
        count = last-first+1
        if count > self.max_bytes-self.transferred_bytes:
            raise AcquisitionBlocked("HTTP payload byte budget exceeded; acquisition stopped")
        headers = {"Range": f"bytes={first}-{last}", "Accept-Encoding": "identity"}
        if self.etag is not None:
            headers["If-Match"] = self.etag
        try:
            with self.session.get(self.url, headers=headers, stream=True, timeout=(10, 30),
                                  allow_redirects=False, auth=_Anonymous()) as response:
                if response.status_code != 206:
                    raise AcquisitionBlocked(f"HTTP {response.status_code}: exact public Range access required")
                if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                    raise AcquisitionBlocked("Encoded HTTP ranges are unsupported")
                match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", response.headers.get("Content-Range", ""))
                if not match or tuple(map(int, match.groups()[:2])) != (first, last):
                    raise AcquisitionBlocked("Incorrect Content-Range")
                if response.headers.get("Content-Length") != str(count):
                    raise AcquisitionBlocked("Exact Content-Length is required for a bounded range response")
                total = int(match[3])
                etag = response.headers.get("ETag", "")
                if not etag.startswith('"') or not etag.endswith('"') or total <= last:
                    raise AcquisitionBlocked("A strong ETag and valid total size are required")
                if self.size is not None and (total != self.size or etag != self.etag):
                    raise AcquisitionBlocked("Source version changed during acquisition")
                chunks, received = [], 0
                for chunk in response.iter_content(chunk_size=min(65536, count+1)):
                    self.transferred_bytes += len(chunk)
                    received += len(chunk)
                    if received > count or self.transferred_bytes > self.max_bytes:
                        raise AcquisitionBlocked("Range response exceeded the requested byte bound")
                    chunks.append(chunk)
                if received != count:
                    raise AcquisitionBlocked("Truncated range response")
                self.size, self.etag = total, etag
                self.last_modified = response.headers.get("Last-Modified")
                return b"".join(chunks)
        except requests.RequestException as error:
            raise AcquisitionBlocked(f"Public HTTPS unavailable ({type(error).__name__}); no fallback attempted") from error

    def read_at(self, position, count):
        if position >= self.size or count == 0:
            return b""
        count = min(count, self.size-position)
        if count < 0:
            raise AcquisitionBlocked("Negative range length")
        # Reject unbounded/full reads before requesting data, not after downloading.
        if count > self.max_bytes:
            raise AcquisitionBlocked("Read exceeds the acquisition byte budget")
        result = []
        while count:
            block, offset = divmod(position, self.block_size)
            if block not in self.cache:
                first = block*self.block_size
                self.cache[block] = self._fetch(first, min(first+self.block_size-1, self.size-1))
            part = self.cache[block][offset:offset+count]
            result.append(part)
            position += len(part)
            count -= len(part)
        return b"".join(result)

    def opener(self, path, mode="rb"):
        if path != self.url or mode not in ("r", "rb"):
            # No implicit external .msk, .aux.xml, directory or sibling requests.
            raise FileNotFoundError("Only the verified GeoTIFF itself may be opened")
        source = self

        class Reader(io.RawIOBase):
            def __init__(self):
                super().__init__()
                self.position = 0

            def readable(self):
                return True

            def seekable(self):
                return True

            def tell(self):
                return self.position

            def seek(self, offset, whence=0):
                position = offset + (0 if whence == 0 else self.position if whence == 1 else source.size)
                if whence not in (0, 1, 2) or position < 0:
                    raise ValueError("Invalid seek")
                self.position = position
                return position

            def read(self, size=-1):
                if self.closed:
                    raise ValueError("Read from closed source")
                if size < 0:
                    size = max(0, source.size-self.position)
                data = source.read_at(self.position, size)
                self.position += len(data)
                return data

        return Reader()

    def close(self):
        self.session.close()
