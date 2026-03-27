"""
T4: Query engine — similarity search, propensity scoring, reengagement queries.
"""
import os
import sys

import chromadb

sys.path.insert(0, os.path.dirname(__file__))
from embedder import embed_record, _ollama_embed, _add_noise, NOISE_EPSILON


def find_similar(
    text: str,
    top_k: int = 20,
    vector_type: str = "profile",
    chroma_path: str = "./data/chroma",
    collection_name: str = "mortgage_signals",
    filters: dict = None,
) -> list:
    vec = _add_noise(_ollama_embed(text), NOISE_EPSILON)

    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_collection(name=collection_name)

    if filters:
        where = {"$and": [{"type": vector_type}] + [{k: v} for k, v in filters.items()]}
    else:
        where = {"type": vector_type}

    results = collection.query(
        query_embeddings=[vec],
        n_results=min(top_k, collection.count()),
        where=where,
        include=["metadatas", "distances"],
    )

    out = []
    for doc_id, meta, dist in zip(
        results["ids"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        out.append({
            "id": doc_id,
            "distance": dist,
            "email_token": meta.get("email_token"),
            "phone_token": meta.get("phone_token"),
            "metadata": meta,
        })
    return out


def propensity_score(
    signal: dict,
    chroma_path: str = "./data/chroma",
    collection_name: str = "mortgage_signals",
    top_k: int = 20,
) -> dict:
    embedded = embed_record(signal)

    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_collection(name=collection_name)

    n = min(top_k, collection.count())
    results = collection.query(
        query_embeddings=[embedded["profile_vector"]],
        n_results=n,
        where={"type": "profile"},
        include=["metadatas", "distances"],
    )

    neighbors = []
    funded_count = 0
    for meta, dist in zip(results["metadatas"][0], results["distances"][0]):
        outcome = meta.get("outcome", "")
        if outcome == "funded":
            funded_count += 1
        neighbors.append({
            "distance": dist,
            "outcome": outcome or "unknown",
            "fico_band": meta.get("financial_fico_band", ""),
            "income_range": meta.get("financial_income_range", ""),
        })

    actual_k = len(neighbors)
    funded_rate = funded_count / actual_k if actual_k > 0 else 0.0

    return {
        "score": int(funded_rate * 100),
        "funded_rate": funded_rate,
        "neighbor_count": actual_k,
        "top_neighbors": neighbors,
    }


def reengagement_query(
    filters: dict,
    chroma_path: str = "./data/chroma",
    collection_name: str = "mortgage_signals",
) -> list:
    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_collection(name=collection_name)

    # Always filter to profile type for one result per person
    if filters:
        where = {"$and": [{"type": "profile"}] + [{k: v} for k, v in filters.items()]}
    else:
        where = {"type": "profile"}

    results = collection.get(where=where, include=["metadatas"])

    out = []
    for doc_id, meta in zip(results["ids"], results["metadatas"]):
        out.append({
            "id": doc_id,
            "email_token": meta.get("email_token"),
            "phone_token": meta.get("phone_token"),
            "metadata": meta,
        })
    return out
