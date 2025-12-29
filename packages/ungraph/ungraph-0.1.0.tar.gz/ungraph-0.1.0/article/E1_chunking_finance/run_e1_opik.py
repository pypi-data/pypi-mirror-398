"""Run E1 with Opik: dataset upload, quick evaluation (smoke test) and bulk upload of results

Usage:
    python run_e1_opik.py --config opik_config.yaml --nb-samples 10

Behavior:
- Loads Opik config and dataset (jsonl)
- Inserts a small sample (nb_samples) into Opik dataset
- For each item: runs ChunkingMaster to select strategy and get chunks
- Creates a simple "prediction" (first chunk truncated) and logs experiment items to Opik via bulk endpoint
- Saves local copy of results

Notes:
- Requires `opik` package installed and `OPIK_API_KEY` set in env or .env
- Designed for smoke tests; does not make LLM calls by default (keeps costs low). Can be extended to call LLMs.
"""
import argparse
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import uuid

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

try:
    import opik
    from opik import Opik
except Exception as e:
    opik = None

try:
    import yaml
except Exception:
    yaml = None

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


def run_smoke(config_path: Path, nb_samples: int = 10) -> Dict:
    if yaml is None:
        raise RuntimeError("PyYAML is required. Install with `pip install pyyaml`.")
    if opik is None:
        raise RuntimeError("Opik SDK not available. Install with `pip install opik`.")

    cfg = yaml.safe_load(open(config_path, 'r', encoding='utf-8'))
    dataset_path = Path(cfg['dataset']['path'])
    results_dir = Path(cfg['reproducibility']['experiments_dir'])
    results_dir.mkdir(parents=True, exist_ok=True)

    items = load_jsonl(dataset_path)
    sample = items[:nb_samples]
    logger.info(f"Loaded dataset with {len(items)} items; using {len(sample)} samples for smoke test")

    # Create Opik client
    client = Opik()

    dataset_name = cfg.get('experiment', {}).get('id', 'e1-edgar')
    dataset = client.get_or_create_dataset(dataset_name)

    # Prepare items with deterministic local_id so we can match after insert
    to_insert = []
    for doc in sample:
        local_id = str(uuid.uuid4())
        to_insert.append({
            'local_id': local_id,
            'input': doc.get('text', '')[:10000],
            'metadata': { 'filename': doc.get('filename'), 'original_id': doc.get('id') }
        })

    logger.info(f'Inserting {len(to_insert)} items into Opik dataset "{dataset_name}"')
    dataset.insert(to_insert)

    # Map inserted items to dataset ids
    all_items = dataset.get_items()
    id_map = { it['local_id']: it['id'] for it in all_items if 'local_id' in it }

    master = ChunkingMaster(model_max_tokens=cfg.get('chunking', {}).get('model_max_tokens'))

    experiment_name = f"E1-chunking-smoke-{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}"

    # Build experiment items for bulk upload
    experiment_items = []
    local_results = []

    for original, ins in zip(sample, to_insert):
        local_id = ins['local_id']
        dataset_item_id = id_map.get(local_id, None)
        doc_id = ins['metadata'].get('original_id') or local_id

        document = Document(page_content=ins['input'], metadata={'id': doc_id, 'filename': ins['metadata'].get('filename')})
        result = master.find_best_chunking_strategy(documents=[document], file_path=None, evaluate_all=True)

        # Simple prediction for smoke: take first chunk (truncated)
        prediction = (result.chunks[0].page_content[:512]) if result.chunks else ""

        # Compute a simple chunk_quality_score (placeholder: sentence completeness avg)
        chunk_quality = getattr(result.metrics, 'avg_sentence_completeness', None) or 0.0

        trace = {
            'name': 'e1_chunking_smoke',
            'input': {'text': ins['input'][:1000]},
            'output': {'prediction': prediction},
            'metadata': {
                'strategy': result.strategy.value if result.strategy else None,
                'num_chunks': result.metrics.num_chunks,
                'avg_chunk_size': result.metrics.avg_chunk_size
            },
            'start_time': datetime.utcnow().isoformat() + 'Z',
            'end_time': datetime.utcnow().isoformat() + 'Z'
        }

        experiment_items.append({
            'dataset_item_id': dataset_item_id,
            'trace': trace,
            'evaluate_task_result': { 'prediction': prediction },
            'feedback_scores': [
                {'name': 'chunk_quality_score', 'value': float(chunk_quality), 'source': 'sdk'}
            ]
        })

        local_results.append({
            'local_id': local_id,
            'dataset_item_id': dataset_item_id,
            'prediction': prediction,
            'strategy': result.strategy.value if result.strategy else None,
            'num_chunks': result.metrics.num_chunks,
            'avg_chunk_size': result.metrics.avg_chunk_size
        })

    # Bulk upload in size-aware batches (API limit ~4MB); use simple half-split if >200
    batch_size = 100
    opik_upload_success = True
    for i in range(0, len(experiment_items), batch_size):
        batch = experiment_items[i:i+batch_size]
        logger.info(f"Uploading batch {i//batch_size + 1} with {len(batch)} items to Opik experiment '{experiment_name}'")
        payload = [{
                'dataset_item_id': it['dataset_item_id'],
                'trace': it['trace'],
                'feedback_scores': it['feedback_scores']
            } for it in batch]
        try:
            client.rest_client.experiments.experiment_items_bulk(
                experiment_name=experiment_name,
                dataset_name=dataset_name,
                items=payload
            )
        except Exception as e:
            opik_upload_success = False
            logger.exception('Opik upload failed for batch; writing local backup of payload')
            # Save backup
            backup_path = results_dir / f'opik_experiment_backup_batch_{i//batch_size + 1}.jsonl'
            save_jsonl(payload, backup_path)
            logger.info(f'Wrote backup payload to {backup_path}')
            # Continue to next batch (do not raise)
            continue

    if not opik_upload_success:
        logger.warning('One or more batches failed to upload to Opik; check backup files in results dir')

    # Save local copy
    save_jsonl(local_results, results_dir / 'opik_smoke_results.jsonl')
    logger.info(f"Saved local results to {results_dir / 'opik_smoke_results.jsonl'}")

    return {
        'experiment_name': experiment_name,
        'num_items': len(experiment_items),
        'results_file': str(results_dir / 'opik_smoke_results.jsonl')
    }


def main():
    parser = argparse.ArgumentParser(description='Run E1 Opik smoke test')
    parser.add_argument('--config', type=str, default='opik_config.yaml')
    parser.add_argument('--nb-samples', type=int, default=10)
    args = parser.parse_args()

    try:
        res = run_smoke(Path(args.config), args.nb_samples)
        print(f"SMOKE TEST FINISHED: {res}")
    except Exception as e:
        logger.exception("Smoke test failed")
        raise


if __name__ == '__main__':
    main()
