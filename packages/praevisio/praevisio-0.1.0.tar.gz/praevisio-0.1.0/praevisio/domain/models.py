from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Promise:
    """A verifiable compliance promise.

    Part of the domain layer. This object contains only domain data and
    is free of presentation or infrastructure concerns.
    """

    id: str
    statement: str

