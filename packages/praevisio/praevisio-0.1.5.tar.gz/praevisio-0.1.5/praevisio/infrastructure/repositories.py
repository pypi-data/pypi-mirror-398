from __future__ import annotations

from typing import Dict, Optional

from ..domain.models import Promise
from ..domain.ports import PromiseRepository


class InMemoryPromiseRepository(PromiseRepository):
    """Simple in-memory repository for Promises.

    Suitable for tests and early development. Replace with a persistent
    implementation when needed (e.g., SQLite, Postgres).
    """

    def __init__(self) -> None:
        self._store: Dict[str, Promise] = {}

    def save(self, promise: Promise) -> Promise:
        self._store[promise.id] = promise
        return promise

    def get(self, promise_id: str) -> Optional[Promise]:
        return self._store.get(promise_id)

