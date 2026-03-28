# UI Task: Mortgage De-ID POC — Web Interface

Project: C:\Users\mebab\.openclaw\workspace\projects\mortgage-deid-poc

## What exists already
- `src/query.py` — find_similar(text, top_k, vector_type, chroma_path, collection_name, filters), propensity_score(signal), reengagement_query(filters)
- `src/export.py` — export_audience(query_text, filters, top_k, output_path, chroma_path, collection_name)
- `src/segments.py` — discover_segments(n_clusters, ...), describe_segment(segment_id)
- `src/ingest.py` — ingest(csv_path, collection_name, chroma_path)
- `cli.py` — status command prints collection stats
- Chroma DB at ./data/chroma with collection "mortgage_signals"

## What to build

### 1. FastAPI Backend — `api.py` (project root)

Install: `pip install fastapi uvicorn python-multipart` (add to requirements.txt)

#### Routes

**GET /api/status**
Returns collection stats. Call cli.py's logic directly:
- Use chromadb.PersistentClient to get collection
- Return: { total_docs, record_count (total_docs/2), tranches: [], outcome_breakdown: {funded: n, ...} }

**POST /api/query**
Body: { "text": "...", "top_k": 10 }
Calls find_similar(text, top_k=top_k, chroma_path="./data/chroma")
Returns: { results: [ { rank, distance, email_token, outcome, generation, credit_profile, loan_purpose } ] }
Extract fields from metadata for display.

**POST /api/score**
Body: a raw lead dict (same shape as generate_csv output — name, ssn, dob, phone, email, address, employer, income, loan_amount, loan_purpose, loan_type, occupancy, property_type, fico, dti, ltv, channel, lead_type, lead_score, status)
OR accept a simpler form: { fico, income, loan_purpose, loan_type, generation, credit_profile, channel }
Run deid on it (import deid_record from src/deid.py, or use deid_csv on a temp file), then call propensity_score(signal)
Returns: { score: 72, funded_rate: 0.72, neighbor_count: 20, top_neighbors: [...] }

**POST /api/export**
Body: { "query_text": "...", "top_k": 200 } OR { "filters": {"outcome": "funded"} }
Calls export_audience(...)
Returns: { file_url: "/api/download/<filename>", count: n, path: "..." }

**GET /api/download/{filename}**
Serves files from ./data/exports/ as CSV download.

**GET /api/segments**
Body/Query: ?n=4 (default 4)
Calls discover_segments(n_clusters=n)
Returns: { segments: [ { id, label, size, funded_rate, top_features } ] }

**GET /api/segment/{id}**
Calls describe_segment(id)
Returns: { id, description: "..." }

**POST /api/ingest**
Accepts multipart file upload (CSV)
Saves to ./data/raw/upload_{timestamp}.csv
Calls ingest(csv_path)
Returns manifest dict

#### CORS
Add CORS middleware: allow origins ["http://localhost:5173", "http://localhost:3000"]

#### Run command
`uvicorn api:app --reload --port 8000`

---

### 2. React Frontend — `ui/` directory

Init with Vite: `npm create vite@latest ui -- --template react` then `cd ui && npm install`
Also install: `npm install axios`

#### Pages / Tabs (single page app, tab navigation)

**Tab 1: Status**
- On load, fetch GET /api/status
- Show: Total Records, Total Vectors, Tranche list, Outcome breakdown as simple bar chart (CSS only, no charting lib)
- Auto-refresh every 30s

**Tab 2: Query**
- Text input: "Search profiles..."
- Slider or number input: Top K (default 10, max 50)
- Submit button
- Results table: Rank | Distance | Generation | Credit | Loan Purpose | Outcome | Email Token (truncated 8 chars)
- Color code outcome: funded=green, rejected=red, ghost=gray, unknown=gray

**Tab 3: Score a Lead**
Simple form with these fields:
- FICO score (number, 300-850)
- Annual Income ($)
- Loan Purpose (dropdown: Purchase / Refinance / Cash-Out / HELOC)
- Loan Type (dropdown: Conventional / FHA / VA / Jumbo)
- Generation (dropdown: GenZ / Millennial / GenX / Boomer / Silent)
- Credit Profile (dropdown: Exceptional / Excellent / Very Good / Good / Fair / Poor)
- Channel (dropdown: Social / Direct / Referral / Broker / Online)
Submit → show score prominently (big number 0-100), funded rate, and a brief interpretation
(e.g. score >= 70 = "High propensity", 40-70 = "Medium", < 40 = "Low")

**Tab 4: Segments**
- Number input: clusters (default 4)
- Discover button → GET /api/segments?n=4
- Show segment cards: label, size, funded rate (color: >50% green, 20-50% yellow, <20% red)
- Click a segment card → show full description paragraph

**Tab 5: Export Audience**
Two modes (radio toggle):
- Mode A: Similarity Query — text input + top_k slider → export_audience by query
- Mode B: Filter — key=value pairs (add row button) → export_audience by filter
Submit → show download link + count of records exported

**Tab 6: Ingest**
- File upload input (CSV only)
- Upload button
- Show progress / result: tranche_id, record_count, timestamp

#### Styling
- Clean, minimal dark theme (dark gray background, white text, orange/amber accent — match the brand)
- No external CSS frameworks — plain CSS modules or a single CSS file
- Mobile-friendly enough to not look broken on a phone

---

### 3. Start Script — `start.ps1` (project root)

```powershell
# Start the mortgage de-ID POC web interface
Write-Host "Starting API server..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot'; uvicorn api:app --reload --port 8000"

Start-Sleep -Seconds 2

Write-Host "Starting UI dev server..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot\ui'; npm run dev"

Start-Sleep -Seconds 3
Write-Host "Opening browser..."
Start-Process "http://localhost:5173"
```

---

## Implementation Notes
- All Python imports use `sys.path.insert(0, '.')` at the top of api.py so `from src.X import Y` works
- Chroma path in api.py defaults to `./data/chroma` (relative to project root)
- Run api.py from the project root
- The score endpoint can accept a simplified form — no need for real PII. Build a synthetic signal record from the form fields, fill in sensible defaults for missing fields (e.g. state="CA", zip3="900", metro="Los Angeles", employment_status="Employed")
- For deid in score endpoint, just build the signal dict directly — no need to run full deid pipeline on fake data

## When done
1. Run: `pip install fastapi uvicorn python-multipart`
2. Run: `cd ui && npm install`
3. Start both servers and verify all 6 tabs load and work
4. Commit: `git add -A && git commit -m "feat: web UI - FastAPI backend + React frontend"`
5. Run: `openclaw system event --text "Done: mortgage-deid web UI built - FastAPI backend + React frontend, 6 tabs: status/query/score/segments/export/ingest" --mode now`
