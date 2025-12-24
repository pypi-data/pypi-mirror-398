from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Promise:
    """A verifiable compliance promise."""

    id: str
    statement: str
    version: str = "0.1.0"
    domain: str = ""
    critical: bool = True
    credence_threshold: float = 0.95
