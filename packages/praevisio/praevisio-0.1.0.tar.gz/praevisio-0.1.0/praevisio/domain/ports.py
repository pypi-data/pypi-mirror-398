from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Iterable, List

from .models import Promise
from .value_objects import HookType
from .config import Configuration
from .entities import CommitContext, StaticAnalysisResult


class PromiseRepository(ABC):
    """Abstract repository for promises (domain port)."""

    @abstractmethod
    def save(self, promise: Promise) -> Promise:  # pragma: no cover - interface
        raise NotImplementedError

    @abstractmethod
    def get(self, promise_id: str) -> Optional[Promise]:  # pragma: no cover - interface
        raise NotImplementedError


class GitRepository(ABC):
    """Port for interacting with Git repositories."""

    @abstractmethod
    def get_staged_files(self) -> List[str]:  # pragma: no cover - interface
        raise NotImplementedError

    @abstractmethod
    def get_commit_message(self) -> str:  # pragma: no cover - interface
        raise NotImplementedError


class ProcessExecutor(ABC):
    """Port for executing external processes/commands."""

    @abstractmethod
    def run(self, command: Iterable[str]) -> int:  # pragma: no cover - interface
        raise NotImplementedError


class FileSystemService(ABC):
    """Port for reading/writing files."""

    @abstractmethod
    def read_text(self, path: str) -> str:  # pragma: no cover - interface
        raise NotImplementedError

    @abstractmethod
    def write_text(self, path: str, content: str) -> None:  # pragma: no cover - interface
        raise NotImplementedError


class ConfigLoader(ABC):
    """Port for loading configuration into domain objects."""

    @abstractmethod
    def load(self, path: str) -> Configuration:  # pragma: no cover - interface
        raise NotImplementedError


class StaticAnalyzer(ABC):
    """Port for running static analysis over a commit / code tree."""

    @abstractmethod
    def analyze(self, path: str) -> StaticAnalysisResult:  # pragma: no cover - interface
        """Analyze code under `path` and return a structured result."""
        raise NotImplementedError


class TestRunner(ABC):
    """Port for running tests in a target repository."""

    @abstractmethod
    def run(self, path: str, args: Iterable[str]) -> int:  # pragma: no cover - interface
        raise NotImplementedError
