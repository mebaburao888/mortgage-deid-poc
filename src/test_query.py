"""
T4 test: similarity search, propensity scoring, reengagement query.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))

import chromadb
from generate_csv import generate_csv
from ingest import ingest
from outcomes import record_outcome
from query import find_similar, propensity_score, reengagement_query

CHROMA_PATH = "./data/chroma_test"
COLLECTION_NAME = "mortgage_signals_test"


def test_query():
    # Populate test collection with 10 records
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
        tmp_path = tmp.name
    try:
        generate_csv(n=10, output_path=tmp_path)
        ingest(csv_path=tmp_path, collection_name=COLLECTION_NAME, chroma_path=CHROMA_PATH)
    finally:
        os.unlink(tmp_path)

    # Mark first 3 records as funded for propensity/reengagement testing
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_collection(COLLECTION_NAME)
    sample = collection.get(limit=3, include=["metadatas"])
    for meta in sample["metadatas"]:
        record_outcome(
            email_token=meta["email_token"],
            outcome="funded",
            chroma_path=CHROMA_PATH,
            collection_name=COLLECTION_NAME,
        )

    # --- Test 1: find_similar ---
    print("=== find_similar: 'Millennial tech worker purchase loan' ===")
    results = find_similar(
        "Millennial tech worker purchase loan",
        top_k=5,
        chroma_path=CHROMA_PATH,
        collection_name=COLLECTION_NAME,
    )
    for r in results:
        print(f"  id={r['id']}  dist={r['distance']:.4f}  email={r['email_token'][:8]}...")
    print(f"  -> {len(results)} results returned")

    # --- Test 2: propensity_score ---
    print("\n=== propensity_score (synthetic Millennial tech signal) ===")
    synthetic_signal = {
        "demographics": {
            "generation": "Millennial", "life_stage": "early-career",
            "age_range": "30-34", "city": "San Francisco", "state": "CA",
        },
        "geography": {"zip3": "941", "region": "West", "urban_class": "Urban"},
        "financial": {
            "credit_profile": "Very Good", "fico_band": "740-759",
            "income_range": "100k-150k", "income_tier": "upper-middle",
            "dti_bucket": "0.30-0.35", "ltv_bucket": "0.80-0.85",
        },
        "employment": {
            "status": "Employed", "tenure_band": "3-7yr",
            "industry": "Technology", "tier": "Fortune500", "stability": "high",
        },
        "loan_intent": {
            "purpose": "Purchase", "type": "Conventional",
            "amount_bucket": "400k-450k", "property_type": "SFR",
            "occupancy": "Primary", "term": 30,
        },
        "lead_behavior": {
            "channel": "Search", "type": "Internet Lead", "score": 75,
            "journey_stage": "Consideration", "first_time_buyer": True, "quarter": "Q1",
        },
        "offer": {
            "type": "Purchase", "rate": 6.875,
            "monthly_savings": 250.0, "annual_savings": 3000.0,
        },
        "outcome": None,
        "tranche_id": "test_query",
    }
    score = propensity_score(
        synthetic_signal,
        chroma_path=CHROMA_PATH,
        collection_name=COLLECTION_NAME,
    )
    print(f"  score={score['score']}  funded_rate={score['funded_rate']:.2f}"
          f"  neighbors={score['neighbor_count']}")
    print("  top 3 neighbors:")
    for n in score["top_neighbors"][:3]:
        print(f"    dist={n['distance']:.4f}  outcome={n['outcome']}"
              f"  fico={n['fico_band']}  income={n['income_range']}")

    # --- Test 3: reengagement_query ---
    print("\n=== reengagement_query: outcome=funded ===")
    reeng = reengagement_query(
        {"outcome": "funded"},
        chroma_path=CHROMA_PATH,
        collection_name=COLLECTION_NAME,
    )
    print(f"  Found {len(reeng)} funded records")
    for r in reeng[:3]:
        print(f"    email={r['email_token'][:8]}...  phone={r['phone_token'][:8]}...")

    assert len(results) > 0, "find_similar returned no results"
    assert score["neighbor_count"] > 0, "propensity_score returned no neighbors"
    print("\nPASS: all query tests complete")


if __name__ == "__main__":
    test_query()
