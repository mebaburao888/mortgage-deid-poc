"""
Integration test: generate 10 synthetic records, ingest into Chroma,
verify 20 vectors stored, run a sample similarity query.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))

from generate_csv import generate_csv
from ingest import ingest
from embedder import embed_record

import chromadb


CHROMA_PATH = "./data/chroma_test"
COLLECTION_NAME = "mortgage_signals_test"


def test_ingest():
    # 1. Generate 10 synthetic records to a temp CSV
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
        tmp_path = tmp.name

    try:
        generate_csv(n=10, output_path=tmp_path)
        print(f"Generated 10 records -> {tmp_path}")

        # 2. Ingest
        manifest = ingest(
            csv_path=tmp_path,
            collection_name=COLLECTION_NAME,
            chroma_path=CHROMA_PATH,
        )
        print("\n--- Manifest ---")
        import json
        print(json.dumps(manifest, indent=2))

        # 3. Verify 20 entries (10 records x 2 vectors)
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        collection = client.get_collection(COLLECTION_NAME)
        total = collection.count()
        print(f"\nChroma entry count: {total}")
        assert total == 20, f"Expected 20 entries, got {total}"
        print("PASS: 20 entries verified")

        # 4. Sample similarity query: embed a query string, find top 3 profile entries
        print("\n--- Similarity query: 'Millennial tech worker purchase loan' ---")
        query_signal = {
            "demographics": {
                "generation": "Millennial",
                "life_stage": "early-career",
                "age_range": "30-34",
                "city": "San Francisco",
                "state": "CA",
            },
            "geography": {"zip3": "941", "region": "West", "urban_class": "Urban"},
            "financial": {
                "credit_profile": "Very Good",
                "fico_band": "740-759",
                "income_range": "100k-150k",
                "income_tier": "upper-middle",
                "dti_bucket": "0.30-0.35",
                "ltv_bucket": "0.80-0.85",
            },
            "employment": {
                "status": "Employed",
                "tenure_band": "3-7yr",
                "industry": "Technology",
                "tier": "Fortune500",
                "stability": "high",
            },
            "loan_intent": {
                "purpose": "Purchase",
                "type": "Conventional",
                "amount_bucket": "400k-450k",
                "property_type": "SFR",
                "occupancy": "Primary",
                "term": 30,
            },
            "lead_behavior": {
                "channel": "Search",
                "type": "Internet Lead",
                "score": 75,
                "journey_stage": "Consideration",
                "first_time_buyer": True,
                "quarter": "Q1",
            },
            "offer": {"type": "Purchase", "rate": 6.875, "monthly_savings": 250.0, "annual_savings": 3000.0},
            "outcome": None,
            "tranche_id": "query",
        }

        embedded_query = embed_record(query_signal)
        results = collection.query(
            query_embeddings=[embedded_query["profile_vector"]],
            n_results=3,
            where={"type": "profile"},
        )

        print("Top 3 profile matches:")
        for i, (doc_id, meta, dist) in enumerate(zip(
            results["ids"][0],
            results["metadatas"][0],
            results["distances"][0],
        )):
            print(f"  [{i+1}] id={doc_id}  distance={dist:.4f}")
            print(f"       text={meta.get('text', '')[:100]}")

    finally:
        os.unlink(tmp_path)


if __name__ == "__main__":
    test_ingest()
