from __future__ import annotations

from typing import List

from ..domain.ports import GitRepository


class InMemoryGitRepository(GitRepository):
    """GitRepository adapter that stores staged files and message in memory."""
    def __init__(self, staged_files: List[str] | None = None, commit_message: str = "") -> None:
        self._staged = staged_files or []
        self._message = commit_message

    def get_staged_files(self) -> List[str]:
        return list(self._staged)

    def get_commit_message(self) -> str:
        return self._message
