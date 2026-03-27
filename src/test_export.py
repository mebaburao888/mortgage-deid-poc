"""
T5 test: Audience export via query and via filter.
"""
import csv
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))

import chromadb
from generate_csv import generate_csv
from ingest import ingest
from outcomes import record_outcome
from export import export_audience

CHROMA_PATH = "./data/chroma_test"
COLLECTION_NAME = "mortgage_signals_test"


def test_export():
    # Populate test collection
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
        tmp_path = tmp.name
    try:
        generate_csv(n=10, output_path=tmp_path)
        ingest(csv_path=tmp_path, collection_name=COLLECTION_NAME, chroma_path=CHROMA_PATH)
    finally:
        os.unlink(tmp_path)

    # Mark a few records as funded
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_collection(COLLECTION_NAME)
    sample = collection.get(limit=4, include=["metadatas"])
    for meta in sample["metadatas"]:
        record_outcome(
            email_token=meta["email_token"],
            outcome="funded",
            chroma_path=CHROMA_PATH,
            collection_name=COLLECTION_NAME,
        )

    # --- Export 1: query-based ---
    print("=== export_audience via query: 'funded loans Millennial tech worker' ===")
    path1 = export_audience(
        query_text="funded loans Millennial tech worker",
        top_k=10,
        chroma_path=CHROMA_PATH,
        collection_name=COLLECTION_NAME,
    )
    print(f"  Output: {path1}")
    with open(path1, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    print(f"  Total rows: {len(rows)}")
    print("  First 3 rows:")
    for r in rows[:3]:
        print(f"    email={r['email_token'][:8]}...  phone={r['phone_token'][:8]}...")

    # --- Export 2: filter-based ---
    print("\n=== export_audience via filter: outcome=funded ===")
    path2 = export_audience(
        filters={"outcome": "funded"},
        chroma_path=CHROMA_PATH,
        collection_name=COLLECTION_NAME,
    )
    print(f"  Output: {path2}")
    with open(path2, newline="", encoding="utf-8") as fh:
        rows2 = list(csv.DictReader(fh))
    print(f"  Total rows: {len(rows2)}")
    print("  First 3 rows:")
    for r in rows2[:3]:
        print(f"    email={r['email_token'][:8]}...  phone={r['phone_token'][:8]}...")

    assert os.path.exists(path1), "query export file not created"
    assert os.path.exists(path2), "filter export file not created"
    print("\nPASS: both export files created successfully")


if __name__ == "__main__":
    test_export()
