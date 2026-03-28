# The Full Picture: De-ID, Embed, Delete, Intelligence

A framework for mortgage companies to extract audience intelligence from lead data while achieving NIST-compliant de-identification and full data minimization.

---

## Step 1: Raw Data Arrives

A mortgage company gets a tranche of lead data. It looks like this:

```
Name:     Brenda Morgan
SSN:      405-91-9317
DOB:      1955-08-01
Phone:    823-403-3504
Email:    brenda.morgan1@icloud.com
Address:  5410 Sycamore Ave, Portland OR 97201
Employer: Intel
Income:   $91,000
Loan:     $475,900 Purchase, Conventional, Investment PUD
FICO:     769   DTI: 0.46   LTV: 0.64
Channel:  Social / Warm Transfer   Score: 66
Status:   Withdrawn
```

Full of PII. Cannot be stored, shared, or used for marketing as-is.

---

## Step 2: De-Identify

Three operations happen simultaneously, in memory, never written to disk.

**DROP — pure identifiers, zero signal value:**

- Brenda Morgan (name adds nothing to targeting)
- 405-91-9317 (SSN adds nothing to targeting)
- 5410 Sycamore Ave (street number/name adds nothing)
- All GUIDs, loan numbers, agent names

**HASH — identifiers with platform value:**

```
EmailToken  = SHA256("brenda.morgan1@icloud.com" + salt)
           -> "b82cf41d..."   (used for Facebook/Google matching)

PhoneToken  = SHA256("823-403-3504" + salt)
           -> "a3f9e821..."   (used for platform matching)
```

**TRANSFORM — identifiers that carry real signal:**

```
1955-08-01   ->  age_range: "70-74"
                 life_stage: "pre-retirement"
                 generation: "Boomer"

Intel        ->  industry: "Technology"
                 employer_tier: "Fortune500"
                 employment_stability: "high"

97201        ->  zip3: "972"
                 city: Portland
                 state: OR
                 metro: "Portland-Vancouver"
                 urban_class: "Urban"

$91,000      ->  income_range: "75k-100k"
                 income_tier: "middle"

$475,900     ->  loan_amount_bucket: "450k-500k"
```

---

## Step 3: Build the Signal Record

What remains after de-ID is rich, usable, and contains no personal information:

```json
{
  "email_token":   "b82cf41d...",
  "phone_token":   "a3f9e821...",

  "demographics": {
    "age_range":    "70-74",
    "life_stage":   "pre-retirement",
    "generation":   "Boomer",
    "gender":       "Female",
    "marital":      "Married",
    "dependents":   2,
    "military":     false
  },
  "geography": {
    "state":        "OR",
    "city":         "Portland",
    "zip3":         "972",
    "metro":        "Portland-Vancouver",
    "region":       "West",
    "urban_class":  "Urban"
  },
  "financial": {
    "credit_profile":  "Excellent",
    "fico_band":       "760-779",
    "income_range":    "75k-100k",
    "dti_bucket":      "0.40-0.50",
    "ltv_bucket":      "0.60-0.65",
    "bankruptcy":      "None",
    "foreclosure":     "None"
  },
  "employment": {
    "status":       "Employed",
    "tenure_band":  "15+ years",
    "industry":     "Technology",
    "tier":         "Fortune500",
    "stability":    "high"
  },
  "loan_intent": {
    "purpose":       "Purchase",
    "type":          "Conventional",
    "amount_bucket": "450k-500k",
    "property_type": "PUD",
    "occupancy":     "Investment",
    "term":          15
  },
  "lead_behavior": {
    "channel":          "Social",
    "type":             "Warm Transfer",
    "score":            66,
    "journey_stage":    "Application",
    "first_time_buyer": true,
    "quarter":          "Q3"
  },
  "offer": {
    "type":            "HELOC",
    "rate":            8.433,
    "monthly_savings": 433.46,
    "annual_savings":  5201.52
  },
  "outcome":    null,
  "tranche_id": "2026-03-T1"
}
```

---

## Step 4: Generate Two Text Templates

**Profile vector — who is this person:**

> Boomer female, pre-retirement, age 70-74. Portland OR metro, urban West region. Married, 2 dependents, non-military. Fortune500 tech employee, 15+ years tenure, high stability. Excellent credit, FICO 760-779, income $75k-100k. DTI 0.40-0.50, LTV 0.60-0.65. No bankruptcy or foreclosure. Investment property owner.

**Intent vector — what do they want:**

> Purchase loan $450k-500k, conventional 15yr, investment PUD. Social channel warm transfer, score 66, application stage. First-time buyer. Q3. HELOC offer, 8.4% rate, $433/mo savings. Status: Withdrawn.

---

## Step 5: Embed Locally

Both templates run through `nomic-embed-text` on Ollama. No data leaves the machine.

```
Profile text  ->  [0.021, -0.847, 0.334, 0.612 ... x 768 dims]
Intent text   ->  [0.445, 0.112, -0.923, 0.087 ... x 768 dims]
```

---

## Step 5b: Optional — Add Gaussian Noise (Differential Privacy)

After embedding and before storing, small random noise can be added to each vector. This is an optional hardening step for higher-sensitivity deployments.

**How it works:**

```
Clean vector:   [0.021, -0.847, 0.334, 0.612 ...]
                         +
Gaussian noise: [0.002, -0.003,  0.001, 0.004 ...]  (epsilon = 0.01)
                         =
Stored vector:  [0.023, -0.850, 0.335, 0.616 ...]
```

The noise is drawn from a Gaussian distribution with mean 0 and standard deviation epsilon (e). A value of e = 0.01 is imperceptible to similarity search but meaningfully raises the cost of embedding inversion attacks.

**The tradeoff:**

| Noise Level (e) | Similarity Accuracy | Inversion Attack Resistance |
|---|---|---|
| 0 (no noise) | Perfect | Baseline |
| 0.01 (recommended) | Near-perfect | Significantly harder |
| 0.05 | Minor drift | Strong resistance |
| 0.10+ | Noticeable degradation | Very strong resistance |

**When to use it:**

Use Gaussian noise when the de-identified attributes themselves are still commercially sensitive, or when the deployment requires a stronger technical argument under NIST Expert Determination. For most mortgage marketing use cases, e = 0.01 is the right balance. The noise value is recorded in the tranche manifest so it can be accounted for in any future audit.

The epsilon value is logged in the tranche manifest alongside the model version, making the noise level part of the auditable record.

---

## Step 6: Store in Chroma

```
Vector store entry:
  profile_vector:  [0.021, -0.847, ...]
  intent_vector:   [0.445, 0.112, ...]
  metadata:        { all signal fields above }
  tokens:          { email_token, phone_token }
  tranche_id:      "2026-03-T1"
  outcome:         null
```

---

## Step 7: Delete Everything

```
Raw CSV               -> secure wiped
De-ID intermediate    -> never written to disk
Text templates        -> discarded after embedding

Tranche manifest written:
{
  "tranche_id":     "2026-03-T1",
  "record_count":   100,
  "source_hash":    "sha256:abc123...",
  "source_deleted": true,
  "deleted_at":     "2026-03-17T16:17:00Z",
  "model":          "nomic-embed-text",
  "noise_epsilon":  0.01
}
```

**What remains: vectors + metadata + tokens. Zero PII. Anywhere.**

---

## Step 8: Outcomes Flow Back In

```
Day 0:    outcome: null,      stage: "Application"
Day 45:   outcome: "funded",  days_to_close: 45
Month 6:  servicing: "current"
Month 18: new lead -> linked via email_token -> 360 view complete
```

No PII needed. The token is the thread connecting the full lifecycle.

---

## Step 9: Next Tranche Arrives

```
March:   100 vectors   outcomes pending
April:   200 vectors   March outcomes arriving
May:     300 vectors   March fully resolved -> propensity patterns emerge
Q4:    1,200 vectors   -> genuine audience intelligence asset
```

---

## What This Enables

**Lookalike audiences — no data science team required**

Query: "Find 200 profiles nearest to my funded loans"
Chroma returns nearest vectors. Extract email_token + phone_token.
Upload to Facebook Custom Audience. Facebook finds 2M people who look like them.
Cost: one query. Time: minutes.

**Propensity scoring at the door**

New lead arrives. Embed. Find 20 nearest neighbors.
14 of 20 funded historically = lead scores 70/100.
Route to priority queue. No model training. The store IS the model.

**Segment discovery you did not plan for**

Cluster all vectors:

- Segment A: military VA buyers, Pacific Northwest, mid-30s, first-time, 78% funded rate
- Segment B: Boomer cash-out, investment property, excellent credit, high re-engagement at 18 months

Neither was predefined. Both are actionable.

**Re-engagement targeting**

Query: funded 18-24 months ago + investment property + rate above 7% + excellent credit.
Extract tokens. Build suppression list and retargeting campaign.

---

## The Benefits

| Benefit | What It Means |
|---|---|
| Zero PII retained | Nothing to breach. Nothing to audit. Compliance story is clean. |
| Data minimization | Source deleted immediately. Only the intelligence layer persists. |
| NIST defensible | De-id before embed. Expert Determination standard. |
| GLBA compliant | No consumer financial data retained beyond processing window. |
| Proprietary signal | Your data, your model, your audience. No licensing fees. |
| Compounds over time | Each tranche makes the next one smarter. |
| No data science team | The vector store is the model. Query it directly. |
| Platform-ready tokens | EmailToken and PhoneToken work natively with Facebook, Google, LiveRamp. |

---

## The Compliance Story This Tells

"We ingest raw data, apply NIST-compliant de-identification, embed the sanitized signal locally, and immediately destroy all source and intermediate files. The only persistent artifact is a vector store containing no personal information, queryable only for aggregate audience intelligence."

That is a clean story for a compliance team, a regulator, or a client's legal department.

---

## Bottom Line

Most mortgage companies do one of three things with their lead data:

1. **Keep it raw** — compliance liability, breach risk, ongoing regulatory exposure
2. **Delete it** — compliant but zero residual value
3. **Sell it to a data broker** — one-time revenue, lose control permanently

This architecture does something none of those do:

> Extract every usable signal, destroy every identifier, and build a compounding intelligence asset that gets more valuable with every tranche — with zero ongoing PII exposure.

The de-identification cost is the same cost you would pay to store it in SQL. The embedding cost is minimal. What you get back is a proprietary audience intelligence layer that replaces expensive third-party data, enables lookalike modeling without a data science team, and closes the 360 loop from lead to outcome to re-engagement — all without a single name, SSN, or phone number ever persisting anywhere.

| Approach | De-ID? | Compliant? | Data Minimization? |
|---|---|---|---|
| Embed raw, keep source | No | No | No |
| Embed raw, delete source | No | No | Partial |
| De-ID, embed, keep both | Yes | Yes | No |
| **De-ID, embed, delete everything** | **Yes** | **Yes** | **Yes** |
