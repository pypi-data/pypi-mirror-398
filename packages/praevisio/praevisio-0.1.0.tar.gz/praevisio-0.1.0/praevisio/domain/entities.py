from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Sequence

from .value_objects import HookType, ExitCode, FilePattern


@dataclass(frozen=True)
class Hook:
    id: str
    name: str
    type: HookType
    command: Sequence[str]
    patterns: Sequence[FilePattern] = field(default_factory=list)
    depends_on: Sequence[str] = field(default_factory=list)
    enabled: bool = True
    file_scoped: bool = True  # whether to filter by matching files


@dataclass(frozen=True)
class HookResult:
    hook_id: str
    skipped: bool
    exit_code: ExitCode
    matched_files: List[str]


@dataclass(frozen=True)
class ValidationRule:
    id: str
    description: str


@dataclass(frozen=True)
class CommitContext:
    staged_files: List[str]
    commit_message: str = ""


@dataclass(frozen=True)
class EvaluationResult:
    credence: float | None
    verdict: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StaticFinding:
    file: str
    line: int | None = None
    code: str = ""


@dataclass(frozen=True)
class StaticAnalysisResult:
    total_llm_calls: int
    violations: int
    coverage: float
    findings: List[StaticFinding] = field(default_factory=list)
    error: str | None = None
