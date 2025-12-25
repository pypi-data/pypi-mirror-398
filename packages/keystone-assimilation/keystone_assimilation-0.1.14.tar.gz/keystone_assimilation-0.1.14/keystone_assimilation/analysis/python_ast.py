"""Lightweight AST analysis to enumerate public API symbols."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Dict, List

SKIP_DIRS = {".venv", "venv", "env", "__pycache__"}


def should_skip(path: Path) -> bool:
    """Return True if the path should be skipped for analysis."""
    return any(part in SKIP_DIRS for part in path.parts)


def run_ast_analysis(base_dir: Path | str = ".") -> Dict[str, object]:
    """Enumerate public classes/functions across Python files."""
    root = Path(base_dir)
    public_api: List[str] = []

    for py in root.rglob("*.py"):
        if should_skip(py):
            continue

        tree = ast.parse(py.read_text())
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and not node.name.startswith("_"):
                public_api.append(f"{py}:{node.name}")

    return {
        "public_api": public_api,
        "count": len(public_api),
    }
