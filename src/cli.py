"""CLI Interface for OpenTask CSV ↔ JSON Converters."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.csv_to_json import csv_to_json
from src.json_to_csv import json_to_csv


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="opentask-converter",
        description="High-performance, bidirectional CSV and JSON conversion utility.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: csv2json
    csv_parser = subparsers.add_parser("csv2json", help="Convert CSV file to JSON or NDJSON")
    csv_parser.add_argument("input", type=Path, help="Path to input CSV file")
    csv_parser.add_argument("-o", "--output", type=Path, default=None, help="Output JSON file path")
    csv_parser.add_argument("-d", "--delimiter", type=str, default=None, help="CSV delimiter (default: auto-detect)")
    csv_parser.add_argument("--infer-types", action="store_true", help="Automatically infer int, float, bool, null")
    csv_parser.add_argument("--nested", action="store_true", help="Reconstruct nested JSON from dot-notation headers")
    csv_parser.add_argument("--ndjson", action="store_true", help="Export as Newline-Delimited JSON (NDJSON)")
    csv_parser.add_argument("--minified", action="store_true", help="Produce compact JSON without extra whitespace")

    # Subcommand: json2csv
    json_parser = subparsers.add_parser("json2csv", help="Convert JSON or NDJSON file to CSV")
    json_parser.add_argument("input", type=Path, help="Path to input JSON file")
    json_parser.add_argument("-o", "--output", type=Path, default=None, help="Output CSV file path")
    json_parser.add_argument("-d", "--delimiter", type=str, default=",", help="CSV delimiter (default: ,)")
    json_parser.add_argument("--no-flatten", dest="flatten", action="store_false", help="Do not flatten nested dictionaries")
    json_parser.add_argument("--columns", nargs="+", default=None, help="Explicit columns and ordering to export")

    args = parser.parse_args()

    if args.command == "csv2json":
        if not args.input.exists():
            sys.stderr.write(f"Error: Input file '{args.input}' not found.\n")
            sys.exit(1)

        indent = None if args.minified else 2
        result = csv_to_json(
            csv_input=args.input,
            output_path=args.output,
            delimiter=args.delimiter,
            infer_types=args.infer_types,
            nested=args.nested,
            ndjson=args.ndjson,
            indent=indent,
        )
        if args.output is None:
            print(result)

    elif args.command == "json2csv":
        if not args.input.exists():
            sys.stderr.write(f"Error: Input file '{args.input}' not found.\n")
            sys.exit(1)

        result_csv = json_to_csv(
            json_input=args.input,
            output_path=args.output,
            delimiter=args.delimiter,
            flatten=args.flatten,
            columns=args.columns,
        )
        if args.output is None:
            print(result_csv, end="")


if __name__ == "__main__":
    main()
