"""Ingest assimilation artifacts into a local evidence tree."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def ingest(repo: str, run_id: str, base_dir: Path = Path("assimilation")) -> Path:
    base = base_dir / repo / run_id
    base.mkdir(parents=True, exist_ok=True)

    payload = {
        "repo": repo,
        "workflow_run_id": run_id,
    }

    with open(base / "source.json", "w") as f:
        json.dump(payload, f, indent=2)

    return base


def ingest_main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()

    base = ingest(args.repo, args.run_id)
    print(f"Ingested assimilation data for {args.repo} at {base}")


if __name__ == "__main__":
    ingest_main()
