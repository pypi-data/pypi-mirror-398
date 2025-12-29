"""Re-upload Opik backup payloads (manual retry)

Usage:
    python reupload_opik_backup.py --backup results/opik_experiment_backup_batch_1.jsonl

Behavior:
- Loads JSONL backup payload
- Attempts up to 3 uploads with exponential backoff
- On success: prints confirmation and returns
- On repeated failure: writes failed payload to `results/failed_reuploads/` with timestamp
"""
import argparse
import json
import logging
import time
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

import os
try:
    from opik import Opik
except Exception as e:
    Opik = None

# If OPIK_API_KEY is not in environment, try to load from repo .env files
if 'OPIK_API_KEY' not in os.environ:
    for env_path in [Path('src/.env'), Path('.env')]:
        if env_path.exists():
            for ln in env_path.read_text().splitlines():
                if ln.strip().startswith('OPIK_API_KEY='):
                    os.environ['OPIK_API_KEY'] = ln.split('=', 1)[1].strip()
                    logger.info(f"Loaded OPIK_API_KEY from {env_path}")
                    break
    if 'OPIK_API_KEY' not in os.environ:
        logger.warning('OPIK_API_KEY not found in environment or .env files; upload will likely fail if key is required')


def load_jsonl(path: Path):
    items = []
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            items.append(json.loads(line))
    return items


def save_jsonl(items, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + '\n')


def reupload(backup_path: Path, dataset_name: str, experiment_name: str, max_attempts: int = 3) -> bool:
    if Opik is None:
        raise RuntimeError('Opik SDK not installed in the environment.')

    client = Opik()
    payload = load_jsonl(backup_path)
    logger.info(f'Loaded {len(payload)} items from backup {backup_path}')

    backoff = 1.0
    for attempt in range(1, max_attempts + 1):
        try:
            logger.info(f'Attempt {attempt} to upload to Opik (experiment: {experiment_name})')
            client.rest_client.experiments.experiment_items_bulk(
                experiment_name=experiment_name,
                dataset_name=dataset_name,
                items=payload
            )
            logger.info('Upload successful')
            return True
        except Exception as e:
            logger.exception(f'Upload attempt {attempt} failed')
            if attempt < max_attempts:
                logger.info(f'Waiting {backoff:.1f}s before retrying')
                time.sleep(backoff)
                backoff *= 2
                continue
            else:
                # Save failed payload
                failed_dir = backup_path.parent / 'failed_reuploads'
                failed_dir.mkdir(parents=True, exist_ok=True)
                ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
                failed_path = failed_dir / f'failed_reupload_{ts}.jsonl'
                save_jsonl(payload, failed_path)
                logger.error(f'All attempts failed. Saved failed payload to {failed_path}')
                return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--backup', type=str, default='results/opik_experiment_backup_batch_1.jsonl')
    parser.add_argument('--dataset-name', type=str, default='E1_chunking_finance')
    parser.add_argument('--experiment-name', type=str, default=f'E1-chunking-smoke-retry-{datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")}')
    parser.add_argument('--max-attempts', type=int, default=3)
    args = parser.parse_args()

    try:
        ok = reupload(Path(args.backup), args.dataset_name, args.experiment_name, args.max_attempts)
        if ok:
            print('Re-upload completed successfully')
        else:
            print('Re-upload failed; backup saved under results/failed_reuploads')
    except Exception as e:
        logger.exception('Reupload script failed to run')
        raise
