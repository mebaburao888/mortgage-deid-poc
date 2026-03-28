# T2: Embed + Chroma Store

Project: C:\Users\mebab\.openclaw\workspace\projects\mortgage-deid-poc

T1 is done: src/generate_csv.py, src/deid.py, src/test_deid.py all work.

deid.py exports: deid_csv(csv_path: str) -> List[dict]
Each signal record has: email_token, phone_token, demographics, geography, financial, employment, loan_intent, lead_behavior, offer, outcome, tranche_id

## What to build

### 1. src/embedder.py
Function: embed_record(signal: dict, noise_epsilon: float = 0.01) -> dict

Build two text templates per record:
- Profile text: "{generation} person, {life_stage}, age {age_range}. {city} {state}, {region} region. {industry} worker, {tenure_band} tenure, {tier}. {credit_profile} credit, FICO {fico_band}, income {income_range}."
- Intent text: "{purpose} loan {amount_bucket}, {loan_type} {term}yr, {occupancy}. {channel} channel, score {lead_score}, {journey_stage} stage. {offer_type} offer {rate}%. Status: {outcome}."

Use nested field access (demographics.generation, demographics.life_stage, etc.)

Embed via Ollama nomic-embed-text:
  POST http://localhost:11434/api/embeddings
  Body: {"model": "nomic-embed-text", "prompt": text}
  Response: {"embedding": [floats]}

Add Gaussian noise: numpy.random.normal(0, noise_epsilon, len(vector)) added to vector
Noise epsilon settable via NOISE_EPSILON env var (default 0.01)

Return: {"profile_vector": [...], "intent_vector": [...], "profile_text": "...", "intent_text": "..."}

Handle Ollama connection errors with a clear message.

### 2. src/ingest.py
Function: ingest(csv_path: str, collection_name: str = "mortgage_signals", chroma_path: str = "./data/chroma") -> dict

- Call deid_csv(csv_path) to get signal records
- For each record, call embed_record(signal)
- Store BOTH vectors in Chroma:
  - id: "{tranche_id}_{email_token[:8]}_profile" with profile_vector, metadata has all flattened signal fields + type="profile"
  - id: "{tranche_id}_{email_token[:8]}_intent" with intent_vector, metadata has all flattened signal fields + type="intent"
- Flatten nested dicts for Chroma metadata: demographics.age_range -> demographics_age_range, etc.
- Use chromadb.PersistentClient(path=chroma_path)
- Save manifest to ./data/manifest_{tranche_id}_{timestamp}.json
- Return manifest: {tranche_id, count, timestamp, model: "nomic-embed-text", noise_epsilon, chroma_collection, chroma_path}

### 3. src/test_ingest.py
- Generate 10 synthetic records (call generate_csv.py's generate function or run as subprocess to a temp file)
- Run ingest() on them
- Verify Chroma has 20 entries (10 records x 2 vectors each)
- Print manifest
- Do a sample similarity query: embed "Millennial tech worker purchase loan" and find top 3 profile entries
- Print query results

## Notes
- requirements.txt already has: faker, chromadb, numpy, requests
- Use chromadb.PersistentClient for persistence
- Flatten metadata dicts before storing in Chroma
- Import generate_csv from src (check how generate_csv.py exposes its function)

When completely finished, run: openclaw system event --text "Done: T2 mortgage-deid embed+chroma built" --mode now
