"""Robust, feature-complete JSON to CSV converter."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any, Union


def flatten_dict(
    d: dict[str, Any],
    parent_key: str = "",
    sep: str = ".",
    flatten_arrays: bool = False,
) -> dict[str, Any]:
    """Recursively flatten a nested dictionary into dot-notation keys."""
    items: list[tuple[str, Any]] = []

    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else str(k)
        if isinstance(v, dict) and v:
            items.extend(flatten_dict(v, new_key, sep=sep, flatten_arrays=flatten_arrays).items())
        elif isinstance(v, list) and flatten_arrays and v:
            for idx, item in enumerate(v):
                array_key = f"{new_key}[{idx}]"
                if isinstance(item, dict):
                    items.extend(flatten_dict(item, array_key, sep=sep, flatten_arrays=flatten_arrays).items())
                else:
                    items.append((array_key, item))
        elif isinstance(v, list):
            # Serialize array as a compact JSON string or join
            items.append((new_key, json.dumps(v, ensure_ascii=False)))
        else:
            items.append((new_key, v))

    return dict(items)


def json_to_csv(
    json_input: Union[str, Path, list[dict[str, Any]], dict[str, Any], io.TextIOBase],
    output_path: Union[str, Path, None] = None,
    delimiter: str = ",",
    flatten: bool = True,
    columns: list[str] | None = None,
    lineterminator: str = "\n",
    null_value: str = "",
) -> str:
    """Convert JSON object, array, or NDJSON into a well-formed RFC 4180 CSV string."""
    data: list[dict[str, Any]]

    # Parse input into a Python list of dicts
    if isinstance(json_input, (list, dict)):
        raw_obj = json_input
    elif isinstance(json_input, Path) or (isinstance(json_input, str) and "\n" not in json_input and Path(json_input).is_file()):
        text = Path(json_input).read_text(encoding="utf-8")
        raw_obj = _parse_json_or_ndjson(text)
    elif isinstance(json_input, io.TextIOBase):
        raw_obj = _parse_json_or_ndjson(json_input.read())
    else:
        raw_obj = _parse_json_or_ndjson(str(json_input))

    if isinstance(raw_obj, dict):
        data = [raw_obj]
    elif isinstance(raw_obj, list):
        data = [item for item in raw_obj if isinstance(item, dict)]
    else:
        data = []

    if not data:
        empty_csv = ""
        if output_path:
            Path(output_path).write_text(empty_csv, encoding="utf-8")
        return empty_csv

    # Flatten nested dictionaries if requested
    processed_records: list[dict[str, Any]] = []
    for item in data:
        processed_records.append(flatten_dict(item) if flatten else item)

    # Determine headers (preserve order of first appearance, take union of all keys)
    if columns is not None:
        headers = columns
    else:
        seen_keys: dict[str, None] = {}
        for rec in processed_records:
            for k in rec.keys():
                seen_keys[k] = None
        headers = list(seen_keys.keys())

    # Write CSV
    output_io = io.StringIO()
    writer = csv.writer(
        output_io,
        delimiter=delimiter,
        lineterminator=lineterminator,
        quoting=csv.QUOTE_MINIMAL,
    )

    # Write Header
    writer.writerow(headers)

    # Write Rows
    for rec in processed_records:
        row: list[Any] = []
        for h in headers:
            val = rec.get(h)
            if val is None:
                row.append(null_value)
            elif isinstance(val, (list, dict)):
                row.append(json.dumps(val, ensure_ascii=False))
            else:
                row.append(str(val))
        writer.writerow(row)

    csv_result = output_io.getvalue()

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(csv_result, encoding="utf-8")

    return csv_result


def _parse_json_or_ndjson(text: str) -> Any:
    """Parse either standard JSON or newline-delimited JSON (NDJSON)."""
    stripped = text.strip()
    if not stripped:
        return []
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        # Try line by line (NDJSON)
        lines = stripped.splitlines()
        records: list[Any] = []
        for line in lines:
            line = line.strip()
            if line:
                records.append(json.loads(line))
        return records
