"""
T6: Segment discovery — KMeans clustering over Chroma profile vectors.
"""
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone

import chromadb
import numpy as np
from sklearn.cluster import KMeans

sys.path.insert(0, os.path.dirname(__file__))

# Metadata fields to use for top_features analysis
FEATURE_FIELDS = {
    "generation": "demographics_generation",
    "credit_profile": "financial_credit_profile",
    "income_range": "financial_income_range",
    "loan_intent_purpose": "loan_intent_purpose",
    "geography_metro": "geography_region",
    "employment_industry": "employment_industry",
}


def _top_value(values: list) -> str:
    if not values:
        return ""
    return Counter(v for v in values if v).most_common(1)[0][0]


def discover_segments(
    n_clusters: int = 8,
    vector_type: str = "profile",
    chroma_path: str = "./data/chroma",
    collection_name: str = "mortgage_signals",
    output_path: str = "./data/segments.json",
) -> dict:
    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_collection(name=collection_name)

    results = collection.get(
        where={"type": vector_type},
        include=["metadatas", "embeddings"],
    )

    if not results["ids"]:
        raise ValueError("No vectors found for clustering")

    embeddings = np.array(results["embeddings"], dtype=np.float32)
    metadatas = results["metadatas"]
    ids = results["ids"]
    n_samples = len(ids)

    # Clamp n_clusters to available samples
    k = min(n_clusters, n_samples)

    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans.fit(embeddings)
    labels = kmeans.labels_

    segments = []
    for cluster_id in range(k):
        mask = [i for i, lbl in enumerate(labels) if lbl == cluster_id]
        cluster_metas = [metadatas[i] for i in mask]
        cluster_ids = [ids[i] for i in mask]

        # Funded rate (outcome may be "" for unset)
        funded = sum(1 for m in cluster_metas if m.get("outcome") == "funded")
        funded_rate = funded / len(cluster_metas) if cluster_metas else 0.0

        # Top features
        top_features = {}
        for label, field in FEATURE_FIELDS.items():
            values = [m.get(field, "") for m in cluster_metas]
            top_features[label] = _top_value(values)

        # Auto label
        gen = top_features.get("generation", "")
        region = top_features.get("geography_metro", "")
        purpose = top_features.get("loan_intent_purpose", "")
        credit = top_features.get("credit_profile", "")
        label_parts = [p for p in [gen, region, purpose, credit] if p]
        label = " ".join(label_parts) if label_parts else f"Segment {cluster_id}"

        segments.append({
            "id": cluster_id,
            "label": label,
            "size": len(cluster_ids),
            "funded_rate": round(funded_rate, 4),
            "top_features": top_features,
            "record_ids": cluster_ids,
        })

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_clusters": k,
        "total_records": n_samples,
        "segments": segments,
    }

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(output, fh, indent=2)

    return output


def describe_segment(segment_id: int, segments_path: str = "./data/segments.json") -> str:
    with open(segments_path, encoding="utf-8") as fh:
        data = json.load(fh)

    seg = next((s for s in data["segments"] if s["id"] == segment_id), None)
    if seg is None:
        raise ValueError(f"Segment {segment_id} not found")

    tf = seg["top_features"]
    parts = [f"Segment {seg['id']}: {seg['size']} records. {seg['label']}."]

    details = []
    if tf.get("generation"):
        details.append(tf["generation"])
    if tf.get("geography_metro"):
        details.append(f"{tf['geography_metro']} region")
    if tf.get("employment_industry"):
        details.append(f"{tf['employment_industry']} workers")
    if tf.get("credit_profile"):
        details.append(f"{tf['credit_profile']} credit")
    if tf.get("income_range"):
        details.append(f"{tf['income_range']} income")
    if tf.get("loan_intent_purpose"):
        details.append(f"{tf['loan_intent_purpose']} loans")

    if details:
        parts.append(", ".join(details) + ".")

    parts.append(f"{seg['funded_rate']*100:.1f}% funded rate.")
    return " ".join(parts)
