"""Validate/process committed real uploads; never modify the raw files or app."""
import argparse
import json
from pathlib import Path
from src.floodcat.patna_processing import prepare, audit_bundle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New directory for compact reproducible outputs")
    parser.add_argument("--tile-rows", type=int, default=2)
    parser.add_argument("--audit-only", action="store_true", help="Audit an existing processed bundle without full remapping")
    args = parser.parse_args()
    if args.audit_only:
        print(json.dumps(audit_bundle(args.output),indent=2))
        return
    report = prepare(args.output, tile_rows=args.tile_rows, progress=lambda x: print(json.dumps(x), flush=True))
    audit_bundle(args.output)
    print(json.dumps({"common_cells": report["common_cells"], "exposure": report["exposure"],
                      "budgets": report["budgets"], "performance": report["performance"]}, indent=2))


if __name__ == "__main__":
    main()
