from __future__ import annotations

from dataclasses import replace

from ..domain.evaluation_config import EvaluationConfig
from ..domain.entities import EvaluationResult
from ..domain.ports import StaticAnalyzer, TestRunner
from .evaluation_service import EvaluationService


def evaluate_commit(
    path: str,
    analyzer: StaticAnalyzer | None = None,
    test_runner: TestRunner | None = None,
    threshold: float | None = None,
    config: EvaluationConfig | None = None,
) -> EvaluationResult:
    """Backwards-compatible wrapper over EvaluationService."""
    service = EvaluationService(analyzer=analyzer, test_runner=test_runner)
    if config is None:
        config = EvaluationConfig()
    if threshold is not None:
        config = replace(config, threshold=threshold)
    return service.evaluate_path(path, config=config)
