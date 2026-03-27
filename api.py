"""
FastAPI backend for Mortgage De-ID POC web interface.
Run from project root: uvicorn api:app --reload --port 8000
"""
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, ".")

import chromadb
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.export import export_audience
from src.query import find_similar, propensity_score
from src.segments import describe_segment, discover_segments
from src.ingest import ingest
from src.deid import (
    _credit_profile,
    _fico_band,
    _income_range,
    _income_tier,
)

app = FastAPI(title="Mortgage De-ID POC API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CHROMA_PATH = "./data/chroma"
COLLECTION_NAME = "mortgage_signals"
EXPORTS_DIR = "./data/exports"
UPLOADS_DIR = "./data/raw"


# ── /api/status ────────────────────────────────────────────────────────────────

@app.get("/api/status")
def get_status():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    try:
        collection = client.get_collection(name=COLLECTION_NAME)
    except Exception:
        return {"total_docs": 0, "record_count": 0, "tranches": [], "outcome_breakdown": {}}

    total_docs = collection.count()
    record_count = total_docs // 2

    # Get all profile metadata for outcome breakdown
    results = collection.get(where={"type": "profile"}, include=["metadatas"])
    outcomes = {}
    tranches = set()
    for meta in results["metadatas"]:
        outcome = meta.get("outcome") or "unknown"
        outcomes[outcome] = outcomes.get(outcome, 0) + 1
        t = meta.get("tranche_id", "")
        if t:
            tranches.add(t)

    return {
        "total_docs": total_docs,
        "record_count": record_count,
        "tranches": sorted(tranches),
        "outcome_breakdown": outcomes,
    }


# ── /api/query ─────────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    text: str
    top_k: int = 10


@app.post("/api/query")
def query_profiles(req: QueryRequest):
    results = find_similar(
        req.text,
        top_k=req.top_k,
        chroma_path=CHROMA_PATH,
        collection_name=COLLECTION_NAME,
    )
    out = []
    for rank, r in enumerate(results, 1):
        meta = r.get("metadata", {})
        out.append({
            "rank": rank,
            "distance": round(r["distance"], 4),
            "email_token": (r.get("email_token") or "")[:8],
            "outcome": meta.get("outcome") or "unknown",
            "generation": meta.get("demographics_generation", ""),
            "credit_profile": meta.get("financial_credit_profile", ""),
            "loan_purpose": meta.get("loan_intent_purpose", ""),
        })
    return {"results": out}


# ── /api/score ─────────────────────────────────────────────────────────────────

class ScoreRequest(BaseModel):
    fico: int = 700
    income: float = 80000
    loan_purpose: str = "Purchase"
    loan_type: str = "Conventional"
    generation: str = "Millennial"
    credit_profile: str = "Good"
    channel: str = "Online"


@app.post("/api/score")
def score_lead(req: ScoreRequest):
    # Build synthetic signal dict directly — no PII involved
    fico = max(300, min(850, req.fico))
    signal = {
        "email_token": "synthetic00",
        "phone_token": "synthetic00",
        "demographics": {
            "age_range": "30-34",
            "life_stage": "early-career",
            "generation": req.generation,
            "city": "Los Angeles",
            "state": "CA",
        },
        "geography": {
            "zip3": "900",
            "region": "West",
            "urban_class": "Urban",
        },
        "financial": {
            "credit_profile": _credit_profile(fico),
            "fico_band": _fico_band(fico),
            "income_range": _income_range(req.income),
            "income_tier": _income_tier(req.income),
            "dti_bucket": "0.30-0.35",
            "ltv_bucket": "0.75-0.80",
        },
        "employment": {
            "status": "Employed",
            "tenure_band": "3-7yr",
            "industry": "Technology",
            "tier": "SMB",
            "stability": "medium",
        },
        "loan_intent": {
            "purpose": req.loan_purpose,
            "type": req.loan_type,
            "amount_bucket": "300k-350k",
            "property_type": "Single Family",
            "occupancy": "Primary",
            "term": 30,
        },
        "lead_behavior": {
            "channel": req.channel,
            "type": "organic",
            "score": 60,
            "journey_stage": "consideration",
            "first_time_buyer": False,
            "quarter": "Q1",
        },
        "offer": {
            "type": "Standard",
            "rate": 6.75,
            "monthly_savings": 0.0,
            "annual_savings": 0.0,
        },
        "outcome": None,
        "tranche_id": "synthetic",
    }

    result = propensity_score(signal, chroma_path=CHROMA_PATH, collection_name=COLLECTION_NAME)
    return result


# ── /api/export ────────────────────────────────────────────────────────────────

class ExportRequest(BaseModel):
    query_text: str = None
    top_k: int = 200
    filters: dict = None


@app.post("/api/export")
def export(req: ExportRequest):
    if not req.query_text and not req.filters:
        raise HTTPException(status_code=400, detail="Provide query_text or filters")

    os.makedirs(EXPORTS_DIR, exist_ok=True)
    path = export_audience(
        query_text=req.query_text,
        filters=req.filters,
        top_k=req.top_k,
        chroma_path=CHROMA_PATH,
        collection_name=COLLECTION_NAME,
    )

    filename = Path(path).name
    # Count rows
    count = 0
    try:
        with open(path, encoding="utf-8") as fh:
            count = sum(1 for _ in fh) - 1  # subtract header
    except Exception:
        pass

    return {"file_url": f"/api/download/{filename}", "count": max(count, 0), "path": path}


# ── /api/download/{filename} ───────────────────────────────────────────────────

@app.get("/api/download/{filename}")
def download(filename: str):
    # Sanitize: no path traversal
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    path = os.path.join(EXPORTS_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, media_type="text/csv", filename=filename)


# ── /api/segments ──────────────────────────────────────────────────────────────

@app.get("/api/segments")
def get_segments(n: int = 4):
    data = discover_segments(
        n_clusters=n,
        chroma_path=CHROMA_PATH,
        collection_name=COLLECTION_NAME,
    )
    segments = []
    for seg in data["segments"]:
        segments.append({
            "id": seg["id"],
            "label": seg["label"],
            "size": seg["size"],
            "funded_rate": seg["funded_rate"],
            "top_features": seg["top_features"],
        })
    return {"segments": segments}


# ── /api/segment/{id} ──────────────────────────────────────────────────────────

@app.get("/api/segment/{segment_id}")
def get_segment(segment_id: int):
    try:
        description = describe_segment(segment_id)
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"id": segment_id, "description": description}


# ── /api/ingest ────────────────────────────────────────────────────────────────

@app.post("/api/ingest")
async def ingest_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files accepted")

    os.makedirs(UPLOADS_DIR, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = os.path.join(UPLOADS_DIR, f"upload_{ts}.csv")

    content = await file.read()
    with open(dest, "wb") as fh:
        fh.write(content)

    try:
        manifest = ingest(dest, collection_name=COLLECTION_NAME, chroma_path=CHROMA_PATH)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return manifest
