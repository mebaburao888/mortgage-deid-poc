"""
Ingest de-identified mortgage leads into ChromaDB.
Stores two vectors per record: profile and intent.
"""
import json
import os
import sys
from datetime import datetime

import chromadb

# Allow running from any working directory
sys.path.insert(0, os.path.dirname(__file__))
from deid import deid_csv
from embedder import embed_record, NOISE_EPSILON, OLLAMA_MODEL


def _flatten(d: dict, prefix: str = "") -> dict:
    """Recursively flatten nested dict, joining keys with '_'."""
    out = {}
    for k, v in d.items():
        key = f"{prefix}_{k}" if prefix else k
        if isinstance(v, dict):
            out.update(_flatten(v, key))
        else:
            # Chroma metadata only supports str/int/float/bool
            if v is None:
                v = ""
            out[key] = v
    return out


def ingest(
    csv_path: str,
    collection_name: str = "mortgage_signals",
    chroma_path: str = "./data/chroma",
) -> dict:
    signals = deid_csv(csv_path)
    if not signals:
        raise ValueError(f"No records found in {csv_path}")

    tranche_id = signals[0]["tranche_id"]

    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_or_create_collection(name=collection_name)

    profile_ids, profile_vecs, profile_metas = [], [], []
    intent_ids, intent_vecs, intent_metas = [], [], []

    for signal in signals:
        embedded = embed_record(signal)
        token_prefix = signal["email_token"][:8]
        base_id = f"{signal['tranche_id']}_{token_prefix}"

        flat_meta = _flatten({
            k: v for k, v in signal.items()
            if k not in ("email_token", "phone_token")
        })
        # Add tokens separately (already hashed, safe to store)
        flat_meta["email_token"] = signal["email_token"]
        flat_meta["phone_token"] = signal["phone_token"]

        profile_ids.append(f"{base_id}_profile")
        profile_vecs.append(embedded["profile_vector"])
        profile_metas.append({**flat_meta, "type": "profile", "text": embedded["profile_text"]})

        intent_ids.append(f"{base_id}_intent")
        intent_vecs.append(embedded["intent_vector"])
        intent_metas.append({**flat_meta, "type": "intent", "text": embedded["intent_text"]})

    collection.upsert(ids=profile_ids, embeddings=profile_vecs, metadatas=profile_metas)
    collection.upsert(ids=intent_ids, embeddings=intent_vecs, metadatas=intent_metas)

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    manifest = {
        "tranche_id": tranche_id,
        "count": len(signals),
        "timestamp": timestamp,
        "model": OLLAMA_MODEL,
        "noise_epsilon": NOISE_EPSILON,
        "chroma_collection": collection_name,
        "chroma_path": chroma_path,
    }

    manifest_dir = "./data"
    os.makedirs(manifest_dir, exist_ok=True)
    manifest_path = os.path.join(manifest_dir, f"manifest_{tranche_id}_{timestamp}.json")
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    print(f"Manifest saved -> {manifest_path}")

    return manifest
