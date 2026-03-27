"""
T5: Audience export — write email/phone token CSVs for ad platform upload.
"""
import csv
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
from query import find_similar, reengagement_query


def export_audience(
    query_text: str = None,
    filters: dict = None,
    top_k: int = 200,
    output_path: str = None,
    chroma_path: str = "./data/chroma",
    collection_name: str = "mortgage_signals",
) -> str:
    if query_text:
        records = find_similar(
            query_text,
            top_k=top_k,
            chroma_path=chroma_path,
            collection_name=collection_name,
            filters=filters,
        )
    elif filters:
        records = reengagement_query(
            filters,
            chroma_path=chroma_path,
            collection_name=collection_name,
        )
    else:
        raise ValueError("Provide query_text or filters (or both)")

    if output_path is None:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        exports_dir = "./data/exports"
        os.makedirs(exports_dir, exist_ok=True)
        output_path = os.path.join(exports_dir, f"audience_{ts}.csv")
    else:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["email_token", "phone_token"])
        writer.writeheader()
        for r in records:
            writer.writerow({
                "email_token": r.get("email_token", ""),
                "phone_token": r.get("phone_token", ""),
            })

    return output_path


def export_segment(
    segment_id: int,
    output_path: str = None,
    chroma_path: str = "./data/chroma",
    collection_name: str = "mortgage_signals",
) -> str:
    segments_path = "./data/segments.json"
    with open(segments_path, encoding="utf-8") as fh:
        data = json.load(fh)

    segment = next(
        (s for s in data["segments"] if s["id"] == segment_id), None
    )
    if segment is None:
        raise ValueError(f"Segment {segment_id} not found in {segments_path}")

    import chromadb
    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_collection(name=collection_name)

    results = collection.get(
        ids=segment["record_ids"],
        include=["metadatas"],
    )

    if output_path is None:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        exports_dir = "./data/exports"
        os.makedirs(exports_dir, exist_ok=True)
        output_path = os.path.join(exports_dir, f"segment_{segment_id}_{ts}.csv")
    else:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["email_token", "phone_token"])
        writer.writeheader()
        for meta in results["metadatas"]:
            writer.writerow({
                "email_token": meta.get("email_token", ""),
                "phone_token": meta.get("phone_token", ""),
            })

    return output_path
