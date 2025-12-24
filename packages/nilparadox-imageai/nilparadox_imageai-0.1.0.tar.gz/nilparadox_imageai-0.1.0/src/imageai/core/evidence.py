from __future__ import annotations
from dataclasses import dataclass
from typing import Set

@dataclass(frozen=True)
class Evidence:
    score: float        # 0..1
    reliability: float  # 0..1
    supports: Set[str]  # hypothesis labels
