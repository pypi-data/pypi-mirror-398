"""Collector to pull assimilation artifacts from external repositories."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable, Optional, Tuple

import requests

GITHUB_API = "https://api.github.com"
TOKEN = os.environ.get("GITHUB_TOKEN")

# This list is intentionally explicit and curated via governance.
ASSIMILATED_REPOS = [
    "djh00t/kcmt",
]

HEADERS = {"Accept": "application/vnd.github+json"}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"

BASE_DIR = Path("assimilation")


def fetch_latest_artifact(repo: str) -> Optional[Tuple[str, int, str]]:
    runs_url = f"{GITHUB_API}/repos/{repo}/actions/runs"
    runs = requests.get(runs_url, headers=HEADERS).json().get("workflow_runs", [])

    for run in runs:
        if (
            run.get("name") == "Keystone Assimilation Watcher"
            and run.get("conclusion") == "success"
        ):
            artifacts_url = run.get("artifacts_url")
            artifacts = requests.get(artifacts_url, headers=HEADERS).json().get("artifacts", [])
            for artifact in artifacts:
                if artifact.get("name") == "keystone-assimilation-report":
                    return repo, run["id"], artifact["archive_download_url"]
    return None


def collect_once(repos: Iterable[str]) -> None:
    BASE_DIR.mkdir(exist_ok=True)

    for repo in repos:
        result = fetch_latest_artifact(repo)
        if not result:
            continue

        repo_name, run_id, url = result
        ts = datetime.now(UTC).strftime("%Y-%m-%d")

        target = BASE_DIR / repo_name.replace("/", "_") / ts
        target.mkdir(parents=True, exist_ok=True)

        resp = requests.get(url, headers=HEADERS)
        zip_path = target / "artifacts.zip"
        zip_path.write_bytes(resp.content)

        with open(target / "source.json", "w") as f:
            json.dump(
                {
                    "repo": repo_name,
                    "workflow_run_id": run_id,
                    "collected_at": ts,
                },
                f,
                indent=2,
            )

        print(f"Collected assimilation data for {repo_name}")


def collect_main() -> None:
    if not TOKEN:
        raise RuntimeError("GITHUB_TOKEN is required to collect artifacts")

    collect_once(ASSIMILATED_REPOS)


if __name__ == "__main__":
    collect_main()
