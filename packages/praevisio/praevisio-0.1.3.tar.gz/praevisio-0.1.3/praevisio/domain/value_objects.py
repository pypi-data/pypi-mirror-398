from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fnmatch import fnmatch


class HookType(str, Enum):
    PRE_COMMIT = "pre-commit"
    COMMIT_MSG = "commit-msg"
    PRE_PUSH = "pre-push"


@dataclass(frozen=True)
class ExitCode:
    code: int = 0

    @property
    def is_success(self) -> bool:
        return self.code == 0


@dataclass(frozen=True)
class FilePattern:
    pattern: str

    def matches(self, filepath: str) -> bool:
        return fnmatch(filepath, self.pattern)

