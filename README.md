# Mortgage De-ID POC

NIST-compliant de-identification pipeline for mortgage lead data.

## Setup

```bash
pip install -r requirements.txt
```

Set the HMAC salt (never use the default in production):

```bash
export DEID_SALT="your-secret-salt-here"
```

## Usage

### Generate synthetic leads

```bash
python src/generate_csv.py
```

Writes 100 synthetic records to `data/raw/leads-2026-03-T1.csv`.

### De-identify a CSV

```python
from src.deid import deid_csv

signal_records = deid_csv('data/raw/leads-2026-03-T1.csv')
```

Returns a list of signal record dicts. No PII is written to disk.

### Run tests

```bash
python src/test_deid.py
```

Generates 5 test records, runs them through the de-identification engine,
prints a side-by-side before/after view, and verifies no PII keys appear
in the output signal records.
