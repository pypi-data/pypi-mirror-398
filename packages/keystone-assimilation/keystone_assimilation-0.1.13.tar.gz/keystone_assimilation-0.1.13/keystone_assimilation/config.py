"""Configuration helpers for assimilation runs."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

DEFAULT_CONFIG_PATH = ".keystone/assimilation.yaml"
DEFAULT_REPORT_DIR = "keystone-assimilation-report"


def get_config_path(config_path: str | None = None) -> Path:
    """Resolve the config path, defaulting to the working directory .keystone file."""
    path = config_path or os.environ.get("KEYSTONE_ASSIMILATION_CONFIG", DEFAULT_CONFIG_PATH)
    return Path(path)


def get_report_dir(report_dir: str | None = None) -> Path:
    """Resolve the report directory path."""
    path = report_dir or os.environ.get("KEYSTONE_ASSIMILATION_REPORT_DIR", DEFAULT_REPORT_DIR)
    return Path(path)


def load_config(config_path: str | None = None) -> Dict[str, Any]:
    """Load the assimilation config file as a dict."""
    path = get_config_path(config_path)
    if not path.exists():
        raise RuntimeError(f"Missing assimilation config at {path}")

    cfg = path.read_text()
    return yaml_safe_load(cfg)["keystone"]


def yaml_safe_load(content: str) -> Dict[str, Any]:
    """Wrapper to isolate yaml import for easier testing/mocking."""
    import yaml

    return yaml.safe_load(content)
