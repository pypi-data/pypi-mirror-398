"""Wrapper to run the finance demo experiment using the central runner (committed in experiments/)."""
import argparse
import sys
from pathlib import Path

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="experiments/finance_demo/opik_config.yaml")
    parser.add_argument("--nb-samples", default=10, type=int)
    parser.add_argument("--seed", default=None)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    cfg = args.config
    cmd = [sys.executable, "scripts/run_experiment.py", "--config", cfg, "--nb-samples", str(args.nb_samples)]
    if args.seed:
        cmd += ["--seed", str(args.seed)]
    if args.out:
        cmd += ["--out", args.out]

    import subprocess
    subprocess.check_call(cmd)
