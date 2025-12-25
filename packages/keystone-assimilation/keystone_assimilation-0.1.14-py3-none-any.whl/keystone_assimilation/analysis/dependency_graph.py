"""Dependency graph extraction from import statements."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Dict, Set

SKIP_DIRS = {".venv", "venv", "env", "__pycache__"}


def should_skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def run_dependency_graph(base_dir: Path | str = ".") -> Dict[str, object]:
    root = Path(base_dir)
    imports: Set[str] = set()

    for py in root.rglob("*.py"):
        if should_skip(py):
            continue

        tree = ast.parse(py.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.add(name.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)

    return {
        "imports": sorted(imports),
        "count": len(imports),
    }
