"""
T6 test: Segment discovery on test Chroma collection.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))

from generate_csv import generate_csv
from ingest import ingest
from segments import discover_segments, describe_segment

CHROMA_PATH = "./data/chroma_test"
COLLECTION_NAME = "mortgage_signals_test"
SEGMENTS_PATH = "./data/segments_test.json"


def test_segments():
    # Populate test collection with 20 records for meaningful clustering
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
        tmp_path = tmp.name
    try:
        generate_csv(n=20, output_path=tmp_path)
        ingest(csv_path=tmp_path, collection_name=COLLECTION_NAME, chroma_path=CHROMA_PATH)
    finally:
        os.unlink(tmp_path)

    print("=== discover_segments(n_clusters=4) ===")
    result = discover_segments(
        n_clusters=4,
        chroma_path=CHROMA_PATH,
        collection_name=COLLECTION_NAME,
        output_path=SEGMENTS_PATH,
    )

    print(f"  Total records: {result['total_records']}")
    print(f"  Clusters: {result['n_clusters']}")
    print(f"  Saved to: {SEGMENTS_PATH}")
    print()

    for seg in result["segments"]:
        print(f"  Segment {seg['id']}: label='{seg['label']}'  "
              f"size={seg['size']}  funded_rate={seg['funded_rate']:.2%}")

    print("\n=== describe_segment(0) ===")
    desc = describe_segment(0, segments_path=SEGMENTS_PATH)
    print(f"  {desc}")

    assert os.path.exists(SEGMENTS_PATH), "segments.json not created"
    assert len(result["segments"]) == 4, f"expected 4 segments, got {len(result['segments'])}"
    print("\nPASS: segment discovery complete")


if __name__ == "__main__":
    test_segments()
