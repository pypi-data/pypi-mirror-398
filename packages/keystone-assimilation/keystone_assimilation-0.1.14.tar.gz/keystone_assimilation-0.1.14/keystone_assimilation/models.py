from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class AssimilationReport:
    project_id: str
    state: str
    signals: Dict[str, Any] = field(default_factory=dict)
    enforcement: Dict[str, Any] = field(default_factory=dict)
