"""
Embed de-identified signal records using Ollama nomic-embed-text.
Adds differential privacy noise to each vector.
"""
import os
import requests
import numpy as np

OLLAMA_URL = "http://localhost:11434/api/embeddings"
OLLAMA_MODEL = "nomic-embed-text"
NOISE_EPSILON = float(os.environ.get("NOISE_EPSILON", "0.01"))


def _ollama_embed(text: str) -> list:
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": text},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["embedding"]
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            f"Cannot connect to Ollama at {OLLAMA_URL}. "
            "Make sure Ollama is running: ollama serve"
        )
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"Ollama HTTP error: {e}. Is nomic-embed-text pulled?")


def _add_noise(vector: list, epsilon: float) -> list:
    arr = np.array(vector, dtype=np.float32)
    arr += np.random.normal(0, epsilon, len(arr))
    return arr.tolist()


def embed_record(signal: dict, noise_epsilon: float = NOISE_EPSILON) -> dict:
    d = signal["demographics"]
    g = signal["geography"]
    f = signal["financial"]
    e = signal["employment"]
    li = signal["loan_intent"]
    lb = signal["lead_behavior"]
    o = signal["offer"]

    profile_text = (
        f"{d['generation']} person, {d['life_stage']}, age {d['age_range']}. "
        f"{d['city']} {d['state']}, {g['region']} region. "
        f"{e['industry']} worker, {e['tenure_band']} tenure, {e['tier']}. "
        f"{f['credit_profile']} credit, FICO {f['fico_band']}, income {f['income_range']}."
    )

    outcome_str = signal.get("outcome") or "Pending"
    intent_text = (
        f"{li['purpose']} loan {li['amount_bucket']}, {li['type']} {li['term']}yr, {li['occupancy']}. "
        f"{lb['channel']} channel, score {lb['score']}, {lb['journey_stage']} stage. "
        f"{o['type']} offer {o['rate']}%. Status: {outcome_str}."
    )

    profile_vec = _add_noise(_ollama_embed(profile_text), noise_epsilon)
    intent_vec = _add_noise(_ollama_embed(intent_text), noise_epsilon)

    return {
        "profile_vector": profile_vec,
        "intent_vector": intent_vec,
        "profile_text": profile_text,
        "intent_text": intent_text,
    }
