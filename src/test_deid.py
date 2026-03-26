"""
Test script: generates 5 synthetic records, runs them through deid_csv(),
prints side-by-side before/after, and verifies no PII keys leak through.
"""
import csv
import json
import os
import sys
import tempfile

# Allow running from repo root or src/
sys.path.insert(0, os.path.dirname(__file__))

from generate_csv import generate_csv, FIELDNAMES
from deid import deid_csv

PII_KEYS = {'first_name', 'last_name', 'ssn', 'street_address', 'email', 'phone'}


def find_pii_keys(obj, path='') -> list:
    """Recursively walk a dict/list and return any paths containing PII key names."""
    violations = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            current = f'{path}.{k}' if path else k
            if k in PII_KEYS:
                violations.append(current)
            violations.extend(find_pii_keys(v, current))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            violations.extend(find_pii_keys(item, f'{path}[{i}]'))
    return violations


def main():
    # Write 5 records to a temp file
    tmp_path = tempfile.mktemp(suffix='.csv')
    try:
        generate_csv(n=5, output_path=tmp_path)

        # Read raw records for display
        with open(tmp_path, 'r', encoding='utf-8') as f:
            raw_records = list(csv.DictReader(f))

        signal_records = deid_csv(tmp_path)

        all_violations = []

        for i, (raw, signal) in enumerate(zip(raw_records, signal_records)):
            print(f'\n{"="*70}')
            print(f'RECORD {i+1}')
            print(f'{"-"*70}')
            print('BEFORE (raw):')
            for k, v in raw.items():
                print(f'  {k}: {v}')
            print('\nAFTER (signal):')
            print(json.dumps(signal, indent=2, default=str))

            violations = find_pii_keys(signal)
            if violations:
                all_violations.extend([f'Record {i+1}: {v}' for v in violations])

        print(f'\n{"="*70}')
        if all_violations:
            print('PII VIOLATION DETECTED:')
            for v in all_violations:
                print(f'  !! {v}')
            sys.exit(1)
        else:
            print('ALL CLEAR: No PII detected in signal records')

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
            print(f'Cleaned up temp file: {tmp_path}')


if __name__ == '__main__':
    main()
