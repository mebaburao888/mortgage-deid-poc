"""
T3 test: Record an outcome on a known email_token and verify metadata update.
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))

import chromadb
from generate_csv import generate_csv
from ingest import ingest
from outcomes import record_outcome

CHROMA_PATH = "./data/chroma_test"
COLLECTION_NAME = "mortgage_signals_test"


def test_outcomes():
    # Populate test collection
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
        tmp_path = tmp.name
    try:
        generate_csv(n=5, output_path=tmp_path)
        ingest(csv_path=tmp_path, collection_name=COLLECTION_NAME, chroma_path=CHROMA_PATH)
    finally:
        os.unlink(tmp_path)

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_collection(COLLECTION_NAME)

    # Pick a known email_token
    sample = collection.get(limit=1, include=["metadatas"])
    email_token = sample["metadatas"][0]["email_token"]
    print(f"Testing with email_token: {email_token[:8]}...")

    # Before
    before = collection.get(where={"email_token": email_token}, include=["metadatas"])
    print(f"\nBEFORE outcome: {before['metadatas'][0].get('outcome', '<not set>')}")

    # Record outcome
    result = record_outcome(
        email_token=email_token,
        outcome="funded",
        metadata={"days_to_close": 42},
        chroma_path=CHROMA_PATH,
        collection_name=COLLECTION_NAME,
    )
    print(f"\nrecord_outcome result: {json.dumps(result, indent=2)}")

    # After
    after = collection.get(where={"email_token": email_token}, include=["metadatas"])
    print(f"\nAFTER outcome:            {after['metadatas'][0].get('outcome')}")
    print(f"AFTER days_to_close:      {after['metadatas'][0].get('days_to_close')}")
    print(f"AFTER outcome_recorded_at:{after['metadatas'][0].get('outcome_recorded_at')}")

    assert after["metadatas"][0]["outcome"] == "funded", "outcome not updated"
    assert after["metadatas"][0]["days_to_close"] == 42, "days_to_close not updated"
    assert after["metadatas"][0].get("outcome_recorded_at"), "outcome_recorded_at missing"
    print("\nPASS: outcome metadata updated correctly")


if __name__ == "__main__":
    test_outcomes()
