"""Tests for CSV to JSON converter."""

import json
from pathlib import Path

from src.csv_to_json import csv_to_json, infer_value


def test_infer_value():
    assert infer_value("123") == 123
    assert infer_value("-45") == -45
    assert infer_value("3.1415") == 3.1415
    assert infer_value("true") is True
    assert infer_value("FALSE") is False
    assert infer_value("null") is None
    assert infer_value("") is None
    assert infer_value("hello world") == "hello world"


def test_basic_csv_to_json():
    csv_data = "name,age,active\nAlice,30,true\nBob,25,false"
    records = csv_to_json(csv_data, infer_types=True)

    assert len(records) == 2
    assert records[0] == {"name": "Alice", "age": 30, "active": True}
    assert records[1] == {"name": "Bob", "age": 25, "active": False}


def test_autodetect_delimiter_and_bom():
    # Semicolon delimited with UTF-8 BOM
    csv_data = "\ufeffid;city;temperature\n1;Lagos;31.5\n2;Abuja;28.0"
    records = csv_to_json(csv_data, infer_types=True)

    assert len(records) == 2
    assert records[0] == {"id": 1, "city": "Lagos", "temperature": 31.5}


def test_nested_keys_and_arrays():
    csv_data = (
        "id,user.name,user.contact.email,tags[0],tags[1]\n"
        "101,Alice,alice@example.com,dev,python\n"
        "102,Bob,bob@example.com,designer,ui"
    )
    records = csv_to_json(csv_data, infer_types=True, nested=True)

    assert len(records) == 2
    assert records[0]["user"]["name"] == "Alice"
    assert records[0]["user"]["contact"]["email"] == "alice@example.com"
    assert records[0]["tags"] == ["dev", "python"]


def test_ndjson_output(tmp_path: Path):
    csv_data = "id,name\n1,Alpha\n2,Beta"
    out_file = tmp_path / "output.jsonl"
    csv_to_json(csv_data, output_path=out_file, ndjson=True)

    lines = out_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0]) == {"id": "1", "name": "Alpha"}
    assert json.loads(lines[1]) == {"id": "2", "name": "Beta"}
