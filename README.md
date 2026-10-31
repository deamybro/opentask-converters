# OpenTask High-Performance Python Data Converters
> Production-grade, zero-external-dependency CLI & Library for bidirectional **CSV ↔ JSON** conversion.

Built for the **OpenTask 100 USDC (CSV to JSON)** and **50 USDC (JSON to CSV)** bounties.

---

## 🌟 Key Features

### 1. `csv2json` (CSV → JSON)
- **Automatic Delimiter Detection**: Sniffs out commas `,`, tabs `\t`, semicolons `;`, and pipes `|`.
- **Smart Type Casting**: Automatically infers `int`, `float`, `bool` (`true`/`false`), `null`, or preserves raw strings.
- **Nested Object Reconstruction**: Converts dot-notation headers (`user.address.city`) into nested JSON objects.
- **Array Syntax Support**: Parses indexed array headers (`tags[0]`, `tags[1]`) into native JSON arrays.
- **Robust Encoding Handling**: Seamlessly handles `UTF-8`, `UTF-8-SIG` (BOM), and special character escaping.
- **Multiple Output Formats**: Supports Standard JSON (pretty or minified) and Newline-Delimited JSON (NDJSON / JSON Lines).

### 2. `json2csv` (JSON → CSV)
- **Automatic Schema Inference**: Extracts the union of all keys across all records (handles sparse data with missing keys cleanly).
- **Flattening Engine**: Unrolls deeply nested dictionaries into dot-notation columns (`user.profile.age`).
- **Array Handling**: Serializes arrays into delimited strings or compact JSON strings.
- **RFC 4180 Compliant**: Full escaping of quotes, commas, newlines, and unicode.

---

## 🚀 Quickstart

### Installation (Python 3.10+)
No external dependencies required for core functionality! Only `pytest` for running the test suite.

```bash
git clone https://github.com/your-username/opentask-converters.git
cd opentask-converters
pip install -r requirements.txt
```

---

## 💻 CLI Usage

### Convert CSV to JSON
```bash
# Basic conversion with pretty printing
python -m src.cli csv2json data/sample.csv -o output.json --pretty

# Enable type inference (numbers, booleans, nulls)
python -m src.cli csv2json data/sample.csv -o output.json --infer-types

# Enable nested object reconstruction (e.g. user.name -> {"user": {"name": ...}})
python -m src.cli csv2json data/sample.csv -o output.json --nested --infer-types

# Output as Newline-Delimited JSON (NDJSON / jsonlines)
python -m src.cli csv2json data/sample.csv -o output.jsonl --ndjson
```

### Convert JSON to CSV
```bash
# Convert a standard JSON array of objects to CSV
python -m src.cli json2csv data/sample.json -o output.csv

# Flatten nested JSON objects into dot-separated headers
python -m src.cli json2csv data/nested.json -o output.csv --flatten

# Custom delimiter (e.g. tab or semicolon)
python -m src.cli json2csv data/sample.json -o output.tsv --delimiter "\t"
```

---

## 🐍 Python Library Usage

```python
from src.csv_to_json import csv_to_json
from src.json_to_csv import json_to_csv

# CSV to JSON
json_data = csv_to_json(
    csv_input="name,age,active\nAlice,30,true\nBob,25,false",
    infer_types=True
)

# JSON to CSV
csv_text = json_to_csv(
    json_input=[{"name": "Alice", "age": 30}, {"name": "Bob", "city": "Berlin"}],
    flatten=True
)
```

---

## 🧪 Running Tests

The test suite thoroughly covers RFC 4180 compliance, malformed inputs, nested structures, type parsing, and edge cases.

```bash
pytest -v
```
