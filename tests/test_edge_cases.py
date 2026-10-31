"""Comprehensive edge-case and stress tests for CSV <-> JSON converters."""

import subprocess
import sys
from pathlib import Path

from src.csv_to_json import csv_to_json, infer_value
from src.json_to_csv import json_to_csv


def test_special_string_preservation():
    # Zip codes with leading zeroes must not be truncated to numbers
    assert infer_value("01234") == "01234"
    assert infer_value("007") == "007"
    assert infer_value("0") == 0
    assert infer_value("0.75") == 0.75

    # International phone numbers with + must not lose the plus
    assert infer_value("+2348012345678") == "+2348012345678"
    assert infer_value("+14155552671") == "+14155552671"


def test_csv_embedded_commas_and_newlines(tmp_path: Path):
    csv_text = (
        'name,bio,score\n'
        '"Lovelace, Ada","Pioneer of computing.\nSecond line of bio.",99\n'
        '"Turing, Alan","Father of modern CS.",100\n'
    )
    records = csv_to_json(csv_text, infer_types=True)

    assert len(records) == 2
    assert records[0]["name"] == "Lovelace, Ada"
    assert "Second line of bio." in records[0]["bio"]
    assert records[0]["score"] == 99
    assert records[1]["name"] == "Turing, Alan"


def test_roundtrip_fidelity(tmp_path: Path):
    original_data = [
        {"user.name": "Amaka", "user.age": 28, "status": "active"},
        {"user.name": "Tunde", "user.age": 34, "status": "inactive"},
    ]

    # JSON -> CSV
    csv_str = json_to_csv(original_data, flatten=False)

    # CSV -> JSON
    reconstructed = csv_to_json(csv_str, infer_types=True)

    assert len(reconstructed) == 2
    assert reconstructed[0]["user.name"] == "Amaka"
    assert reconstructed[0]["user.age"] == 28
    assert reconstructed[1]["user.name"] == "Tunde"
    assert reconstructed[1]["user.age"] == 34


def test_cli_subprocess(tmp_path: Path):
    project_root = Path(__file__).resolve().parent.parent
    sample_csv = tmp_path / "sample.csv"
    output_json = tmp_path / "output.json"
    recreated_csv = tmp_path / "recreated.csv"

    sample_csv.write_text("item,qty,price\nApple,10,1.50\nOrange,5,2.00\n", encoding="utf-8")

    # Run csv2json CLI
    res1 = subprocess.run(
        [sys.executable, "-m", "src.cli", "csv2json", str(sample_csv), "-o", str(output_json), "--infer-types"],
        cwd=str(project_root),
        capture_output=True,
        text=True,
    )
    assert res1.returncode == 0
    assert output_json.exists()

    # Run json2csv CLI
    res2 = subprocess.run(
        [sys.executable, "-m", "src.cli", "json2csv", str(output_json), "-o", str(recreated_csv)],
        cwd=str(project_root),
        capture_output=True,
        text=True,
    )
    assert res2.returncode == 0
    assert recreated_csv.exists()
    assert "Apple,10,1.5" in recreated_csv.read_text(encoding="utf-8")
