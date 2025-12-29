"""Run script for E1 - Chunking strategies evaluation (Finance)

Usage:
    python run_e1_chunking.py --config opik_config.yaml

What it does (template):
- Loads config
- Loads dataset (jsonl)
- For each document, runs ChunkingMaster.find_best_chunking_strategy (evaluate_all=True)
- Saves chunks per strategy and metrics to results dir
- Produces a summary metrics CSV for later analysis

Notes:
- This script assumes the package has `src.utils.chunking_master.ChunkingMaster` available
- For Opik integration, wrap calls to this script in Opik experiment runner or CI
"""
import argparse
import json
import os
from pathlib import Path
from typing import List, Dict

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from src.utils.chunking_master import ChunkingMaster
from langchain_core.documents import Document


def load_jsonl(path: Path) -> List[Dict]:
    items = []
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            items.append(json.loads(line))
    return items


def save_jsonl(items: List[Dict], path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + '\n')


def main(config_path: Path):
    config = json.loads(os.popen(f"python -c 'import yaml,sys;print(yaml.safe_load(open(\"{config_path}\")) )'").read())
    # Minimal parsing for this template
    dataset_path = Path(config['dataset']['path'])
    results_dir = Path(config['reproducibility']['experiments_dir'])
    strategies = config['chunking']['strategies']

    docs = load_jsonl(dataset_path)
    logger.info(f"Loaded {len(docs)} documents from dataset")

    master = ChunkingMaster(model_max_tokens=config.get('chunking', {}).get('model_max_tokens'))

    all_metrics = []
    for doc in docs:
        doc_id = doc.get('id') or doc.get('filename')
        document = Document(page_content=doc['text'], metadata={'id': doc_id, 'filename': doc.get('filename')})

        # Evaluate strategies (evaluate_all=True will try candidates) - returns best currently
        result = master.find_best_chunking_strategy(
            documents=[document],
            file_path=None,
            evaluate_all=True
        )

        # Save per-strategy chunks and metrics
        strategy = result.strategy.value
        chunks = [{'id': f"{doc_id}-{i}", 'strategy': strategy, 'content': c.page_content} for i, c in enumerate(result.chunks, start=1)]
        save_jsonl(chunks, results_dir / 'chunks' / f"{doc_id}__{strategy}.jsonl")

        metrics = {
            'id': doc_id,
            'strategy': strategy,
            'num_chunks': result.metrics.num_chunks,
            'avg_chunk_size': result.metrics.avg_chunk_size,
            'min_chunk_size': result.metrics.min_chunk_size,
            'max_chunk_size': result.metrics.max_chunk_size,
            'sentence_completeness': result.metrics.avg_sentence_completeness,
            'paragraph_preservation': result.metrics.avg_paragraph_preservation,
        }
        all_metrics.append(metrics)

    # Save aggregated metrics
    save_jsonl(all_metrics, results_dir / 'metrics' / 'chunking_metrics.jsonl')
    logger.info(f"Saved metrics for {len(all_metrics)} documents to {results_dir / 'metrics'}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run E1 chunking experiment')
    parser.add_argument('--config', type=str, default='opik_config.yaml')
    args = parser.parse_args()

    main(Path(args.config))
