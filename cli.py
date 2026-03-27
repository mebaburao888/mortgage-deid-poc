"""
T7: Unified CLI for the mortgage de-ID POC.
"""
import argparse
import json
import sys
import os

# Ensure src/ is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def _chroma_paths(args):
    if getattr(args, "test", False):
        return "./data/chroma_test", "mortgage_signals_test"
    return "./data/chroma", "mortgage_signals"


# ── ingest ────────────────────────────────────────────────────────────────────
def cmd_ingest(args):
    from ingest import ingest
    chroma_path, collection_name = _chroma_paths(args)
    manifest = ingest(
        csv_path=args.csv_path,
        collection_name=collection_name,
        chroma_path=chroma_path,
    )
    print(json.dumps(manifest, indent=2))


# ── outcomes ──────────────────────────────────────────────────────────────────
def cmd_outcomes(args):
    from outcomes import bulk_outcomes
    chroma_path, collection_name = _chroma_paths(args)
    summary = bulk_outcomes(
        outcomes_csv=args.outcomes_csv,
        chroma_path=chroma_path,
        collection_name=collection_name,
    )
    print(json.dumps(summary, indent=2))


# ── query ─────────────────────────────────────────────────────────────────────
def cmd_query(args):
    from query import find_similar
    chroma_path, collection_name = _chroma_paths(args)
    results = find_similar(
        text=args.text,
        top_k=args.top_k,
        chroma_path=chroma_path,
        collection_name=collection_name,
    )
    print(f"Top {len(results)} results for: \"{args.text}\"")
    for i, r in enumerate(results, 1):
        meta = r["metadata"]
        gen = meta.get("demographics_generation", "?")
        purpose = meta.get("loan_intent_purpose", "?")
        credit = meta.get("financial_credit_profile", "?")
        outcome = meta.get("outcome", "unknown") or "unknown"
        print(f"  [{i:2d}] dist={r['distance']:.4f}  email={r['email_token'][:8]}..."
              f"  {gen} {purpose} {credit} outcome={outcome}")


# ── score ─────────────────────────────────────────────────────────────────────
def cmd_score(args):
    from deid import deid_csv
    from query import propensity_score
    chroma_path, collection_name = _chroma_paths(args)

    signals = deid_csv(args.csv_path)
    if not signals:
        print("ERROR: no records found in CSV", file=sys.stderr)
        sys.exit(1)
    signal = signals[0]

    result = propensity_score(
        signal,
        chroma_path=chroma_path,
        collection_name=collection_name,
    )
    print(f"Propensity score: {result['score']}/100")
    print(f"  funded_rate:    {result['funded_rate']:.1%}")
    print(f"  neighbor_count: {result['neighbor_count']}")
    print("  Top neighbors:")
    for n in result["top_neighbors"][:5]:
        print(f"    dist={n['distance']:.4f}  outcome={n['outcome']}"
              f"  fico={n['fico_band']}  income={n['income_range']}")


# ── export ────────────────────────────────────────────────────────────────────
def cmd_export(args):
    from export import export_audience
    chroma_path, collection_name = _chroma_paths(args)

    filters = {}
    for f in (args.filter or []):
        if "=" not in f:
            print(f"ERROR: invalid filter format '{f}' (use key=value)", file=sys.stderr)
            sys.exit(1)
        k, v = f.split("=", 1)
        filters[k.strip()] = v.strip()

    path = export_audience(
        query_text=args.query or None,
        filters=filters if filters else None,
        top_k=args.top_k,
        output_path=args.output or None,
        chroma_path=chroma_path,
        collection_name=collection_name,
    )
    print(f"Exported audience -> {path}")


# ── segments ──────────────────────────────────────────────────────────────────
def cmd_segments(args):
    from segments import discover_segments, describe_segment
    chroma_path, collection_name = _chroma_paths(args)

    result = discover_segments(
        n_clusters=args.n,
        chroma_path=chroma_path,
        collection_name=collection_name,
    )
    print(f"Discovered {result['n_clusters']} segments over {result['total_records']} records")
    print()
    for seg in result["segments"]:
        desc = describe_segment(seg["id"])
        print(f"  {desc}")


# ── segment <id> ──────────────────────────────────────────────────────────────
def cmd_segment(args):
    from segments import describe_segment
    desc = describe_segment(args.id)
    print(desc)


# ── status ────────────────────────────────────────────────────────────────────
def cmd_status(args):
    import chromadb
    chroma_path, collection_name = _chroma_paths(args)

    try:
        client = chromadb.PersistentClient(path=chroma_path)
        collection = client.get_collection(name=collection_name)
    except Exception as e:
        print(f"ERROR: could not open collection '{collection_name}' at {chroma_path}: {e}",
              file=sys.stderr)
        sys.exit(1)

    total = collection.count()
    all_docs = collection.get(include=["metadatas"])

    outcome_counts = {}
    tranches = set()
    for meta in all_docs["metadatas"]:
        outcome = meta.get("outcome") or ""
        if outcome:
            outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1
        tranche = meta.get("tranche_id") or ""
        if tranche:
            tranches.add(tranche)

    print(f"Collection:   {collection_name}")
    print(f"Chroma path:  {chroma_path}")
    print(f"Total docs:   {total}  ({total // 2} records x 2 vectors)")
    print()
    print("Outcome breakdown:")
    if outcome_counts:
        for outcome, count in sorted(outcome_counts.items()):
            print(f"  {outcome:<15} {count:>5}  ({count/total*100:.1f}%)")
    else:
        print("  (no outcomes recorded yet)")
    print()
    print("Tranches:")
    if tranches:
        for t in sorted(tranches):
            print(f"  {t}")
    else:
        print("  (none)")


# ── main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Mortgage De-ID POC — unified CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--test", action="store_true", help="Use test Chroma collection")

    sub = parser.add_subparsers(dest="command", required=True)

    # ingest
    p = sub.add_parser("ingest", help="Run full ingest pipeline")
    p.add_argument("csv_path", help="Path to raw leads CSV")

    # outcomes
    p = sub.add_parser("outcomes", help="Bulk load outcomes from CSV")
    p.add_argument("outcomes_csv", help="Path to outcomes CSV")

    # query
    p = sub.add_parser("query", help="Similarity search")
    p.add_argument("text", help="Query text")
    p.add_argument("--top-k", type=int, default=20, dest="top_k")

    # score
    p = sub.add_parser("score", help="Score a single raw lead CSV (1 record)")
    p.add_argument("csv_path", help="Path to raw lead CSV")

    # export
    p = sub.add_parser("export", help="Export audience CSV")
    p.add_argument("--query", default=None, help="Similarity query text")
    p.add_argument("--top-k", type=int, default=200, dest="top_k")
    p.add_argument("--output", default=None, help="Output file path")
    p.add_argument("--filter", action="append", default=[], metavar="KEY=VALUE",
                   help="Metadata filter (repeatable)")

    # segments
    p = sub.add_parser("segments", help="Discover + print all segments")
    p.add_argument("--n", type=int, default=8, help="Number of clusters")

    # segment <id>
    p = sub.add_parser("segment", help="Describe a specific segment")
    p.add_argument("id", type=int, help="Segment ID")

    # status
    sub.add_parser("status", help="Print Chroma collection stats")

    args = parser.parse_args()

    dispatch = {
        "ingest": cmd_ingest,
        "outcomes": cmd_outcomes,
        "query": cmd_query,
        "score": cmd_score,
        "export": cmd_export,
        "segments": cmd_segments,
        "segment": cmd_segment,
        "status": cmd_status,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
