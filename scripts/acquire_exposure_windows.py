"""Inventory by default; explicit reviewed source + output required to acquire.

Run from repository root: python -m scripts.acquire_exposure_windows --help
Uses only anonymous, bounded provider GeoTIFF range requests; no Earth Engine.
"""

import argparse
import json
from pathlib import Path

from rasterio.errors import RasterioError

from src.floodcat.acquisition import SOURCES, acquire_window, inspect_source, wri_reference
from src.floodcat.http_range import AcquisitionBlocked


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=sorted(SOURCES))
    parser.add_argument("--review", type=Path, help="Reviewed source records, keyed by source name")
    parser.add_argument("--output", type=Path, help="New local directory, preferably data/exposure_local/<source>")
    parser.add_argument("--inspect", action="store_true", help="Read metadata only after product/license review; no output dataset")
    parser.add_argument("--max-transfer-mib", type=int, default=32)
    parser.add_argument("--max-pixels", type=int, default=1_000_000)
    args = parser.parse_args(argv)
    if args.source is None and args.review is None and args.output is None and not args.inspect:
        print(json.dumps({"mode": "inventory_only_no_network", "wri": wri_reference(),
                          "candidates": SOURCES,
                          "status": "blocked_pending_provider_access_and_source_review"}, indent=2))
        return 0
    if args.source is None or args.review is None or (not args.inspect and args.output is None):
        parser.error("Acquisition requires --source, --review and --output together")
    if args.inspect and args.output is not None:
        parser.error("Metadata inspection prints JSON and does not create an output dataset")
    if not 1 <= args.max_transfer_mib <= 128 or not 1 <= args.max_pixels <= 1_000_000:
        parser.error("Transfer budget must be 1–128 MiB and pixel budget 1–1,000,000")
    try:
        review = json.loads(args.review.read_text())[args.source]
        if args.inspect:
            metadata = inspect_source(args.source, review, max_bytes=min(args.max_transfer_mib, 2)*1024**2)
            print(json.dumps(metadata, indent=2, allow_nan=False))
            return 0
        manifest = acquire_window(args.source, review, args.output,
                                  max_bytes=args.max_transfer_mib*1024**2, max_pixels=args.max_pixels)
    except (AcquisitionBlocked, RasterioError, OSError, ValueError, KeyError) as error:
        print(json.dumps({"status": "blocked", "reason": str(error), "acquisition_published": False}))
        return 2
    print(json.dumps({"status": "native_window_acquired", "output": str(args.output),
                      "sha256": manifest["window_file"]["sha256"],
                      "integration_status": "not_run", "redistribution_review_still_required": True}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
