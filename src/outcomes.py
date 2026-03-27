"""
T3: Outcome feedback — record and bulk-load loan outcomes into ChromaDB.
"""
import csv
import os
import sys
from datetime import datetime, timezone

import chromadb

sys.path.insert(0, os.path.dirname(__file__))


def record_outcome(
    email_token: str,
    outcome: str,
    metadata: dict = None,
    chroma_path: str = "./data/chroma",
    collection_name: str = "mortgage_signals",
) -> dict:
    valid = {"funded", "denied", "withdrawn", "in-progress"}
    if outcome not in valid:
        raise ValueError(f"outcome must be one of {valid}, got {outcome!r}")

    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_collection(name=collection_name)

    results = collection.get(
        where={"email_token": email_token},
        include=["metadatas", "embeddings"],
    )

    if not results["ids"]:
        return {"updated": 0, "email_token": email_token[:8] + "...", "outcome": outcome}

    timestamp = datetime.now(timezone.utc).isoformat()
    updated_metas = []
    for meta in results["metadatas"]:
        new_meta = {**meta, "outcome": outcome, "outcome_recorded_at": timestamp}
        if metadata:
            for k, v in metadata.items():
                new_meta[k] = v if v is not None else ""
        updated_metas.append(new_meta)

    collection.update(ids=results["ids"], metadatas=updated_metas)

    return {
        "updated": len(results["ids"]),
        "email_token": email_token[:8] + "...",
        "outcome": outcome,
    }


def bulk_outcomes(
    outcomes_csv: str,
    chroma_path: str = "./data/chroma",
    collection_name: str = "mortgage_signals",
) -> dict:
    total = 0
    updated = 0
    errors = 0

    with open(outcomes_csv, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            total += 1
            email_token = row.get("email_token", "").strip()
            outcome = row.get("outcome", "").strip()
            if not email_token or not outcome:
                errors += 1
                continue

            extra = {}
            if row.get("days_to_close"):
                try:
                    extra["days_to_close"] = int(row["days_to_close"])
                except (ValueError, TypeError):
                    pass
            if row.get("servicing_status"):
                extra["servicing_status"] = row["servicing_status"].strip()

            try:
                result = record_outcome(
                    email_token=email_token,
                    outcome=outcome,
                    metadata=extra if extra else None,
                    chroma_path=chroma_path,
                    collection_name=collection_name,
                )
                updated += result["updated"]
            except Exception as e:
                print(f"Error on row {total}: {e}", file=sys.stderr)
                errors += 1

    return {"total": total, "updated": updated, "errors": errors}
