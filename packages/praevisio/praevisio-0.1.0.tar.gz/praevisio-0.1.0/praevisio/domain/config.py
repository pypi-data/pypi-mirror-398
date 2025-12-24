from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .entities import Hook
from .evaluation_config import EvaluationConfig


@dataclass(frozen=True)
class Configuration:
    hooks: List[Hook] = field(default_factory=list)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)
