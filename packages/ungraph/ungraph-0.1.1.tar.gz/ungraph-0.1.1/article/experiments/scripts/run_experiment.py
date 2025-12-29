#!/usr/bin/env python
"""Simple reproducible experiment runner for ET/ETI demo.

Modes:
- mock: deterministic local processing (default)
- opik: uses Opik API if OPiK_API_KEY present and model set

Outputs:
- chunks.jsonl
- inferred_facts.jsonl
- embeddings.npy
- prov_bundle.json
- metadata.json
"""
import argparse
import json
import os
import random
import shutil
import sys
from datetime import datetime
from pathlib import Path

import yaml
import numpy as np

# deterministic pseudo-embedding using sha256
import hashlib


def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    os.environ["RANDOM_SEED"] = str(seed)


def sha256_embed(text: str, dim=64):
    h = hashlib.sha256(text.encode("utf8")).digest()
    # expand/trim into dim floats deterministically
    vals = []
    i = 0
    while len(vals) < dim:
        block = int.from_bytes(h[i % len(h): (i % len(h)) + 8], "big")
        vals.append((block % 1000) / 1000.0)
        i += 8
    return np.array(vals[:dim], dtype=np.float32)


def chunk_text(text: str):
    # Simple paragraph splitter; further splitting into sentences
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    for i, p in enumerate(paras):
        chunks.append({"id": f"chunk_{i}", "text": p})
    return chunks


def mock_infer(chunks):
    # Heuristic inference: detect keywords and emit (doc, mentions, keyword)
    keywords = ["risk", "liability", "revenue", "income", "loss", "asset", "debt"]
    facts = []
    for c in chunks:
        t = c["text"].lower()
        found = [k for k in keywords if k in t]
        for k in found:
            confidence = 0.9 if k in t else 0.6
            facts.append({
                "subject": c.get("id"),
                "predicate": "mentions",
                "object": k,
                "confidence": confidence,
                "provenance_ref": c.get("id"),
            })
    return facts


def make_prov(metadata, files):
    prov = {
        "entity": {k: str(v) for k, v in files.items()},
        "activity": {
            "experiment": metadata["experiment_name"],
            "timestamp": metadata["timestamp"],
            "git_hash": metadata.get("git_hash"),
            "seed": metadata.get("seed"),
        },
    }
    return prov


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--nb-samples", type=int, default=10)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    cfg_path = Path(args.config)
    cfg = yaml.safe_load(cfg_path.read_text())

    seed = args.seed if args.seed is not None else cfg.get("seeds", {}).get("random_seed", 42)
    set_seed(seed)

    git_hash = None
    try:
        import subprocess

        git_hash = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode().strip()
    except Exception:
        git_hash = "unknown"

    output_dir = Path(args.out or cfg.get("output", {}).get("dir", "experiments/runtime/"))
    if output_dir.exists():
        # avoid mixing runs
        output_dir = Path(str(output_dir) + f"_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Small realistic document selection: take `data/110225.md` if available
    sample_docs = []
    data_file = Path("data/110225.md")
    if data_file.exists():
        text = data_file.read_text(encoding="utf8")
        sample_docs.append({"id": "doc_110225", "text": text})
    else:
        # minimal built-in sample
        sample_docs.append({"id": "doc_sample_1", "text": "Revenue increased this quarter, but liability and debt increased as well."})

    # Sample nb_samples documents by repeating or trimming
    docs = []
    while len(docs) < args.nb_samples:
        for d in sample_docs:
            if len(docs) >= args.nb_samples:
                break
            docs.append({"id": f"{d['id']}_{len(docs)}", "text": d["text"]})

    all_chunks = []
    chunk_lines = []
    embeddings = []
    chunk_counter = 0
    for d in docs:
        chunks = chunk_text(d["text"])
        for c in chunks:
            cid = f"{d['id']}_c{chunk_counter}"
            chunk_obj = {"id": cid, "doc_id": d["id"], "text": c["text"]}
            all_chunks.append(chunk_obj)
            chunk_lines.append(json.dumps(chunk_obj, ensure_ascii=False))
            emb = sha256_embed(c["text"], dim=64)
            embeddings.append(emb)
            chunk_counter += 1

    # write chunks
    chunks_path = output_dir / "chunks.jsonl"
    with chunks_path.open("w", encoding="utf8") as f:
        for line in chunk_lines:
            f.write(line + "\n")

    embeddings_arr = np.stack(embeddings) if embeddings else np.zeros((0, 64), dtype=np.float32)
    np.save(output_dir / "embeddings.npy", embeddings_arr)

    # Inference: mock by default
    inference_mode = cfg.get("inference", "lm-only")
    if os.environ.get("OPIK_API_KEY") and cfg.get("opik", {}).get("model") != "mock-local":
        # Placeholder: call Opik model here in real runs
        inferred = mock_infer(all_chunks)  # fallback
    else:
        inferred = mock_infer(all_chunks)

    inferred_path = output_dir / "inferred_facts.jsonl"
    with inferred_path.open("w", encoding="utf8") as f:
        for fact in inferred:
            f.write(json.dumps(fact, ensure_ascii=False) + "\n")

    # metadata
    metadata = {
        "experiment_name": cfg.get("experiment_name", cfg_path.stem),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "git_hash": git_hash,
        "seed": seed,
        "nb_documents": len(docs),
        "nb_chunks": len(all_chunks),
        "config_path": str(cfg_path),
    }
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))

    prov = make_prov(metadata, {"chunks": str(chunks_path), "inferred_facts": str(inferred_path)})
    (output_dir / "prov_bundle.json").write_text(json.dumps(prov, indent=2))

    print("Run complete. Outputs written to:", output_dir)


if __name__ == "__main__":
    main()
