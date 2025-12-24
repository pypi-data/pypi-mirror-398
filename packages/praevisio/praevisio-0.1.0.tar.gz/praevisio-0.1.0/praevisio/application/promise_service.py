from __future__ import annotations

from ..domain.models import Promise
from ..domain.ports import PromiseRepository


class PromiseService:
    """Application service for managing promises.

    Returns domain objects, keeping this layer decoupled from presentation.
    """

    def __init__(self, repository: PromiseRepository) -> None:
        self._repo = repository

    def register_promise(self, promise_id: str, statement: str) -> Promise:
        """Create and persist a new Promise.

        Parameters
        - promise_id: unique identifier for the promise
        - statement: the promise statement

        Returns
        - Promise (domain object)
        """
        promise = Promise(id=promise_id, statement=statement)
        return self._repo.save(promise)
