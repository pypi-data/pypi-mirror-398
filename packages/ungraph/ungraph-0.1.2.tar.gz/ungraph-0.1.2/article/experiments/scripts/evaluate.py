#!/usr/bin/env python
"""Simple evaluator for inferred facts.

If gold file provided, computes precision/recall/F1 by equality of (subject,predicate,object).
If no gold provided, writes a sampling file for human annotation.
"""
import argparse
import json
from collections import Counter
from pathlib import Path


def load_jsonl(path):
    return [json.loads(l) for l in Path(path).read_text(encoding="utf8").splitlines() if l.strip()]


def compute_prf(pred, gold):
    pred_set = set((p['subject'], p['predicate'], p['object']) for p in pred)
    gold_set = set((g['subject'], g['predicate'], g['object']) for g in gold)
    tp = len(pred_set & gold_set)
    fp = len(pred_set - gold_set)
    fn = len(gold_set - pred_set)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    return {"precision": precision, "recall": recall, "f1": f1, "tp": tp, "fp": fp, "fn": fn}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pred", required=True)
    parser.add_argument("--gold", required=False)
    parser.add_argument("--sample-out", required=False)
    args = parser.parse_args()

    pred = load_jsonl(args.pred)
    if args.gold and Path(args.gold).exists():
        gold = load_jsonl(args.gold)
        metrics = compute_prf(pred, gold)
        print("Metrics:", metrics)
    else:
        # produce sample file for human annotation
        sample = pred[:min(50, len(pred))]
        if args.sample_out:
            Path(args.sample_out).write_text(json.dumps(sample, indent=2, ensure_ascii=False))
            print(f"Written sample for annotation to {args.sample_out}")
        else:
            print("No gold provided. Output sample to annotate via --sample-out <path>")


if __name__ == "__main__":
    main()
