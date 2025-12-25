"""CLI entrypoint for assimilation analysis runs."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable, Dict

import yaml

from .analysis import run_ast_analysis, run_coverage_map, run_dependency_graph
from .config import get_report_dir, load_config
from .states import AssimilationState

Runner = Callable[[str], int]


def build_report(cfg: Dict[str, Any], report_dir: Path, runner: Runner = os.system) -> Path:
    state = AssimilationState(cfg["state"])

    report_dir.mkdir(parents=True, exist_ok=True)

    report: Dict[str, Any] = {
        "project_id": cfg["project_id"],
        "state": state.value,
        "signals": {},
        "enforcement": {},
    }

    if cfg.get("analysis", {}).get("enabled", False):
        report["signals"]["ast"] = run_ast_analysis()
        report["signals"]["dependencies"] = run_dependency_graph()
        report["signals"]["coverage"] = run_coverage_map()

    if state in {
        AssimilationState.GOVERNED,
        AssimilationState.CANONICAL,
        AssimilationState.IPBANKED,
    }:
        if cfg.get("enforcement", {}).get("require_make_check"):
            rc = runner("make check")
            if rc != 0:
                raise RuntimeError("make check failed")

    report_path = report_dir / "assimilation_report.yaml"
    with report_path.open("w") as handle:
        yaml.safe_dump(report, handle)

    return report_path


def run_main(config_path: str | None = None, report_dir: str | None = None) -> Path:
    cfg = load_config(config_path)
    output_dir = get_report_dir(report_dir)
    return build_report(cfg, output_dir)


if __name__ == "__main__":
    run_main()
