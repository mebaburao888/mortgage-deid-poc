# T3–T7: Mortgage De-ID POC — Remaining Build

Project: C:\Users\mebab\.openclaw\workspace\projects\mortgage-deid-poc

## Context

T1 (de-id pipeline) and T2 (embed + Chroma store) are complete.
- `src/deid.py` — deid_csv(csv_path) -> List[dict] signal records
- `src/embedder.py` — embed_record(signal) -> {profile_vector, intent_vector, profile_text, intent_text}
- `src/ingest.py` — ingest(csv_path) -> manifest dict, stores 2 vectors per record in Chroma
- Chroma collection: "mortgage_signals" at ./data/chroma
- Each Chroma doc has metadata with all flattened signal fields + type="profile" or "intent"
- email_token and phone_token are the linkage keys (SHA256 of PII + salt)

## T3: Outcome Feedback

### src/outcomes.py
Function: record_outcome(email_token: str, outcome: str, metadata: dict = None, chroma_path: str = "./data/chroma", collection_name: str = "mortgage_signals") -> dict

- outcome values: "funded", "denied", "withdrawn", "in-progress"
- Find all Chroma docs matching email_token in metadata (query where metadata filter email_token == value)
- Update their metadata: outcome=outcome, outcome_recorded_at=ISO timestamp
- If metadata dict provided, merge it in (e.g. days_to_close, servicing_status)
- Return: {updated: int, email_token: email_token[:8]+"...", outcome: outcome}

Function: bulk_outcomes(outcomes_csv: str, chroma_path: str = "./data/chroma") -> dict
- CSV columns: email_token, outcome, days_to_close (optional), servicing_status (optional)
- Calls record_outcome for each row
- Returns summary: {total, updated, errors}

### src/test_outcomes.py
- Load test Chroma collection (chroma_test)
- Get a known email_token from the collection
- Call record_outcome with outcome="funded", days_to_close=42
- Verify the metadata was updated in Chroma
- Print before/after

## T4: Query Engine

### src/query.py
Function: find_similar(text: str, top_k: int = 20, vector_type: str = "profile", chroma_path: str = "./data/chroma", collection_name: str = "mortgage_signals", filters: dict = None) -> List[dict]
- Embed the query text via Ollama nomic-embed-text (same as embedder.py)
- Query Chroma for top_k nearest vectors of the specified type (metadata filter: type=vector_type)
- If filters provided, add as Chroma where clause (e.g. {"outcome": "funded"})
- Return list of: {id, distance, email_token, phone_token, metadata}

Function: propensity_score(signal: dict, chroma_path: str = "./data/chroma", collection_name: str = "mortgage_signals", top_k: int = 20) -> dict
- Take a new (just de-identified) signal record
- Embed it (call embed_record from embedder.py)
- Find top_k nearest profile vectors
- Calculate: funded_rate = count(outcome=="funded") / top_k
- Return: {score: int (0-100), funded_rate: float, neighbor_count: top_k, top_neighbors: list of {distance, outcome, fico_band, income_range}}

Function: reengagement_query(filters: dict, chroma_path: str = "./data/chroma", collection_name: str = "mortgage_signals") -> List[dict]
- filters: e.g. {"outcome": "funded", "financial_fico_band": "760-779", "loan_intent_purpose": "Purchase"}
- Query Chroma with metadata where clause
- Return matching records with email_token + phone_token + metadata

### src/test_query.py
- Test find_similar("Millennial tech worker purchase loan", top_k=5)
- Test propensity_score with a synthetic signal record
- Test reengagement_query with a filter
- Print all results clearly

## T5: Audience Export

### src/export.py
Function: export_audience(query_text: str = None, filters: dict = None, top_k: int = 200, output_path: str = None, chroma_path: str = "./data/chroma", collection_name: str = "mortgage_signals") -> str
- If query_text: run find_similar to get top_k results
- If filters only: run reengagement_query
- Extract email_token and phone_token from results
- Write CSV: columns = email_token, phone_token (Facebook/Google Custom Audience format)
- output_path defaults to ./data/exports/audience_{timestamp}.csv
- Create exports dir if needed
- Return output_path

Function: export_segment(segment_id: int, output_path: str = None, chroma_path: str = "./data/chroma", collection_name: str = "mortgage_signals") -> str
- Load segments from ./data/segments.json (built by T6)
- Get all email/phone tokens for a segment
- Write CSV same format
- Return output_path

### src/test_export.py
- Export audience via query: "funded loans Millennial tech worker"
- Export audience via filter: {"outcome": "funded"}
- Print file paths and first 3 rows of each

## T6: Segment Discovery

### src/segments.py
Function: discover_segments(n_clusters: int = 8, vector_type: str = "profile", chroma_path: str = "./data/chroma", collection_name: str = "mortgage_signals", output_path: str = "./data/segments.json") -> dict

- Load all vectors of type=vector_type from Chroma
- Run KMeans clustering (sklearn) with n_clusters
- For each cluster, compute:
  - size: record count
  - funded_rate: % with outcome=="funded"
  - top_features: most common values for key metadata fields (generation, credit_profile, income_range, loan_intent_purpose, geography_metro, employment_industry)
  - label: auto-generated string like "Boomer Portland Purchase Excellent" from top features
  - centroid: mean vector
- Save segments to output_path as JSON:
  {
    "generated_at": ISO timestamp,
    "n_clusters": n_clusters,
    "total_records": int,
    "segments": [
      {
        "id": 0,
        "label": "...",
        "size": int,
        "funded_rate": float,
        "top_features": {...},
        "record_ids": [chroma doc ids]
      }
    ]
  }
- Return the segments dict

Function: describe_segment(segment_id: int, segments_path: str = "./data/segments.json") -> str
- Return a human-readable paragraph describing the segment
- e.g. "Segment 3: 47 records. Boomer females, pre-retirement, Portland OR metro. Fortune500 tech workers, excellent credit (FICO 760-779), $75k-100k income. Primarily Purchase loans $450k-500k. 68% funded rate."

### src/test_segments.py
- Run discover_segments(n_clusters=4) on test chroma (chroma_test)
- Print each segment label + size + funded_rate
- Print describe_segment for segment 0

## T7: CLI

### cli.py (in project root)
Unified CLI using argparse or click. Commands:

```
python cli.py ingest <csv_path>              # Run full ingest pipeline
python cli.py outcomes <outcomes_csv>         # Bulk load outcomes
python cli.py query "<text>" [--top-k 20]    # Similarity search
python cli.py score <csv_path>               # Score a single raw lead CSV (1 record)
python cli.py export --query "<text>" --top-k 200 --output <path>
python cli.py export --filter outcome=funded --filter fico_band=760-779
python cli.py segments [--n 8]              # Discover + print all segments
python cli.py segment <id>                  # Describe a specific segment
python cli.py status                        # Print Chroma collection stats (total records, outcome breakdown, tranche list)
```

- Use argparse
- Each command prints clean output to stdout
- Errors go to stderr with clear messages
- All Chroma paths use defaults (./data/chroma, ./data/chroma_test if --test flag)

## requirements.txt additions needed
- scikit-learn (for KMeans in T6)
- click (optional, argparse is fine too)

Add to existing requirements.txt (don't replace it, check what's there first).

## Final step
When ALL tasks (T3–T7) are completely finished and tested:
- Run: python cli.py status (from the project dir) and capture output
- Run: python src/test_outcomes.py
- Run: python src/test_query.py
- Run: python src/test_segments.py
- Commit all new files: git add -A && git commit -m "feat: T3-T7 complete - outcomes, query, export, segments, CLI"
- Then run: openclaw system event --text "Done: mortgage-deid T3-T7 complete - outcomes loop, query engine, audience export, segment discovery, CLI all built and tested" --mode now
