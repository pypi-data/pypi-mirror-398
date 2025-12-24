from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Dict, List

from ..domain.config import Configuration
from ..domain.entities import EvaluationResult
from ..domain.evaluation_config import EvaluationConfig
from ..domain.ports import ConfigLoader, FileSystemService
from .configuration_service import ConfigurationService
from .evaluation_service import EvaluationService


@dataclass(frozen=True)
class GateResult:
    evaluation: EvaluationResult
    report_entry: Dict[str, Any]
    should_fail: bool


class PraevisioEngine:
    """Library-first orchestration facade for evaluation and gates."""

    def __init__(
        self,
        config_loader: ConfigLoader,
        fs: FileSystemService,
        evaluation_service: EvaluationService | None = None,
    ) -> None:
        self._config_loader = config_loader
        self._fs = fs
        self._evaluation_service = evaluation_service or EvaluationService()

    def load_config(self, path: str = ".praevisio.yaml") -> Configuration:
        service = ConfigurationService(self._config_loader, self._fs, config_path=path)
        return service.load()

    def evaluate(self, path: str, evaluation: EvaluationConfig) -> EvaluationResult:
        return self._evaluation_service.evaluate_path(path, config=evaluation)

    def pre_commit_gate(
        self,
        path: str,
        evaluation: EvaluationConfig,
        threshold_override: float | None = None,
    ) -> GateResult:
        effective = self.apply_threshold(evaluation, threshold_override, None)
        result = self.evaluate(path, effective)
        entry = self._build_report_entry(result, effective, severity=effective.severity or "high")
        should_fail = self._should_fail(result, effective, fail_on_violation=True)
        return GateResult(evaluation=result, report_entry=entry, should_fail=should_fail)

    def ci_gate(
        self,
        path: str,
        evaluation: EvaluationConfig,
        severity: str | None = None,
        threshold_override: float | None = None,
        fail_on_violation: bool = False,
    ) -> GateResult:
        effective = self.apply_threshold(evaluation, threshold_override, severity)
        result = self.evaluate(path, effective)
        entry = self._build_report_entry(result, effective, severity=effective.severity or "high")
        should_fail = self._should_fail(result, effective, fail_on_violation=fail_on_violation)
        return GateResult(evaluation=result, report_entry=entry, should_fail=should_fail)

    def apply_threshold(
        self,
        evaluation: EvaluationConfig,
        threshold_override: float | None,
        severity: str | None,
    ) -> EvaluationConfig:
        effective_severity = severity or evaluation.severity
        if threshold_override is not None:
            effective_threshold = threshold_override
        elif effective_severity and effective_severity in evaluation.thresholds:
            effective_threshold = evaluation.thresholds[effective_severity]
        else:
            effective_threshold = evaluation.threshold
        return replace(evaluation, threshold=effective_threshold, severity=effective_severity)

    def _build_report_entry(
        self,
        result: EvaluationResult,
        evaluation: EvaluationConfig,
        severity: str,
    ) -> Dict[str, Any]:
        reasons: List[str] = []
        semgrep_error = result.details.get("semgrep_error")
        if semgrep_error:
            reasons.append(semgrep_error)
        if result.verdict == "n/a":
            reasons.append("not_applicable")

        status = "pass"
        if result.verdict == "error":
            status = "error"
        elif result.verdict == "n/a":
            status = "na"
        elif result.credence is not None and result.credence < evaluation.threshold:
            status = "fail"

        return {
            "id": evaluation.promise_id,
            "credence": result.credence,
            "verdict": result.verdict,
            "threshold": evaluation.threshold,
            "severity": severity,
            "applicable": result.details.get("applicable", True),
            "status": status,
            "reasons": reasons,
            "audit_path": result.details.get("audit_path"),
            "audit_sha256": result.details.get("audit_sha256"),
            "manifest_path": result.details.get("manifest_path"),
            "manifest_sha256": result.details.get("manifest_sha256"),
        }

    def _should_fail(
        self,
        result: EvaluationResult,
        evaluation: EvaluationConfig,
        fail_on_violation: bool,
    ) -> bool:
        if not fail_on_violation:
            return False
        if result.verdict == "error":
            return True
        applicable = result.details.get("applicable", True)
        if not applicable:
            return False
        if result.credence is None:
            return True
        return result.credence < evaluation.threshold
