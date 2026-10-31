"""High-performance, robust CSV to JSON converter."""

from __future__ import annotations

import csv
import io
import json
import re
from pathlib import Path
from typing import Any, Union


def infer_value(value: str) -> Any:
    """Infer Python primitive types from string representations safely."""
    trimmed = value.strip()
    if trimmed == "":
        return None

    # Booleans
    lower = trimmed.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    if lower in ("null", "none", "nil"):
        return None

    # Preserve phone numbers and country code strings (+123456789)
    if trimmed.startswith("+"):
        return value

    # Preserve strings with leading zeros (e.g., zip codes '01234', IDs '007')
    # but allow single '0' or standard decimals like '0.5'
    if len(trimmed) > 1 and trimmed.startswith("0") and not trimmed.startswith("0."):
        return value
    if len(trimmed) > 2 and trimmed.startswith("-0") and not trimmed.startswith("-0."):
        return value

    # Integers
    if re.fullmatch(r"-?\d+", trimmed):
        try:
            return int(trimmed)
        except ValueError:
            pass

    # Floats
    if re.fullmatch(r"-?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?", trimmed):
        try:
            return float(trimmed)
        except ValueError:
            pass

    # Fallback to string (preserve original whitespace if needed, or stripped)
    return value


def set_nested_field(target: dict[str, Any], key_path: str, value: Any) -> None:
    """Set a nested value in a dict supporting dot notation (a.b.c) and array notation (tags[0])."""
    # Tokenize path: "user.emails[0].address" -> ["user", "emails", 0, "address"]
    tokens: list[Union[str, int]] = []
    parts = key_path.split(".")
    
    for part in parts:
        # Check for array indices like tags[0] or items[1][2]
        matches = list(re.finditer(r"([^\[\]]+)|(?:\[(\d+)\])", part))
        for match in matches:
            prop, idx = match.groups()
            if prop is not None:
                tokens.append(prop)
            elif idx is not None:
                tokens.append(int(idx))

    if not tokens:
        return

    curr: Any = target
    for i, token in enumerate(tokens[:-1]):
        next_token = tokens[i + 1]
        
        if isinstance(token, str):
            if isinstance(next_token, int):
                # Next is an index, ensure list
                if token not in curr or not isinstance(curr[token], list):
                    curr[token] = []
                curr = curr[token]
            else:
                # Next is a string prop, ensure dict
                if token not in curr or not isinstance(curr[token], dict):
                    curr[token] = {}
                curr = curr[token]
        elif isinstance(token, int):
            # Current token is a list index
            while len(curr) <= token:
                curr.append({} if isinstance(next_token, str) else [])
            curr = curr[token]

    last_token = tokens[-1]
    if isinstance(last_token, str):
        curr[last_token] = value
    elif isinstance(last_token, int):
        while len(curr) <= last_token:
            curr.append(None)
        curr[last_token] = value


def detect_delimiter(sample_text: str, default: str = ",") -> str:
    """Automatically detect delimiter from CSV sample text."""
    try:
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(sample_text[:4096], delimiters=",\t;|")
        return dialect.delimiter
    except Exception:
        # Fallback heuristic
        first_line = sample_text.splitlines()[0] if sample_text else ""
        counts = {d: first_line.count(d) for d in [",", "\t", ";", "|"]}
        best = max(counts, key=counts.get)  # type: ignore[arg-type]
        return best if counts[best] > 0 else default


def csv_to_json(
    csv_input: Union[str, Path, io.TextIOBase],
    output_path: Union[str, Path, None] = None,
    delimiter: str | None = None,
    infer_types: bool = False,
    nested: bool = False,
    ndjson: bool = False,
    indent: int | None = 2,
    encoding: str = "utf-8-sig",
) -> Union[list[dict[str, Any]], str]:
    """Convert CSV data into JSON or NDJSON structure."""
    text_content: str

    if isinstance(csv_input, Path) or (isinstance(csv_input, str) and "\n" not in csv_input and Path(csv_input).is_file()):
        path = Path(csv_input)
        text_content = path.read_text(encoding=encoding)
    elif isinstance(csv_input, io.TextIOBase):
        text_content = csv_input.read()
    else:
        text_content = str(csv_input)

    if not text_content.strip():
        result_empty: list[dict[str, Any]] = []
        if output_path:
            Path(output_path).write_text("[]" if not ndjson else "", encoding="utf-8")
        return result_empty

    if delimiter is None:
        delimiter = detect_delimiter(text_content)

    reader = csv.reader(io.StringIO(text_content), delimiter=delimiter)
    try:
        headers = next(reader)
    except StopIteration:
        return []

    # Strip BOM or whitespace from header names
    clean_headers = [h.strip().lstrip("\ufeff") for h in headers]

    records: list[dict[str, Any]] = []

    for row in reader:
        # Skip completely empty trailing lines
        if not row or (len(row) == 1 and row[0].strip() == ""):
            continue

        record: dict[str, Any] = {}
        for idx, header in enumerate(clean_headers):
            raw_val = row[idx] if idx < len(row) else ""
            val = infer_value(raw_val) if infer_types else raw_val

            if nested and ("." in header or "[" in header):
                set_nested_field(record, header, val)
            else:
                record[header] = val

        records.append(record)

    # Output formatting
    if ndjson:
        formatted_str = "\n".join(json.dumps(r, ensure_ascii=False) for r in records)
    else:
        formatted_str = json.dumps(records, indent=indent, ensure_ascii=False)

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(formatted_str, encoding="utf-8")

    return records if output_path is None else formatted_str
