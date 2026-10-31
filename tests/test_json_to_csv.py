"""Tests for JSON to CSV converter."""

import csv
import io
from pathlib import Path

from src.json_to_csv import flatten_dict, json_to_csv


def test_flatten_dict():
    nested = {
        "user": {
            "name": "Chidi",
            "address": {
                "city": "Enugu",
                "zip": "400001",
            },
        },
        "role": "admin",
    }
    flattened = flatten_dict(nested)
    assert flattened == {
        "user.name": "Chidi",
        "user.address.city": "Enugu",
        "user.address.zip": "400001",
        "role": "admin",
    }


def test_basic_json_to_csv():
    data = [
        {"name": "Alice", "score": 95},
        {"name": "Bob", "score": 88},
    ]
    csv_str = json_to_csv(data)
    reader = list(csv.reader(io.StringIO(csv_str)))

    assert reader[0] == ["name", "score"]
    assert reader[1] == ["Alice", "95"]
    assert reader[2] == ["Bob", "88"]


def test_missing_keys_sparse_data():
    data = [
        {"id": 1, "name": "First"},
        {"id": 2, "email": "second@example.com"},  # missing name
        {"id": 3, "name": "Third", "email": "third@example.com", "extra": "bonus"},
    ]
    csv_str = json_to_csv(data)
    reader = list(csv.reader(io.StringIO(csv_str)))

    headers = reader[0]
    assert headers == ["id", "name", "email", "extra"]

    # Row 2 (missing name)
    row2 = dict(zip(headers, reader[2]))
    assert row2["id"] == "2"
    assert row2["name"] == ""
    assert row2["email"] == "second@example.com"
    assert row2["extra"] == ""


def test_custom_columns_and_delimiter():
    data = [
        {"a": 1, "b": 2, "c": 3},
        {"a": 4, "b": 5, "c": 6},
    ]
    csv_str = json_to_csv(data, delimiter=";", columns=["c", "a"])
    lines = [line.strip() for line in csv_str.strip().splitlines()]

    assert lines[0] == "c;a"
    assert lines[1] == "3;1"
    assert lines[2] == "6;4"


def test_file_output_roundtrip(tmp_path: Path):
    data = [{"title": "Test, with comma", "count": 42}]
    out_file = tmp_path / "test.csv"
    json_to_csv(data, output_path=out_file)

    content = out_file.read_text(encoding="utf-8")
    assert '"Test, with comma"' in content
