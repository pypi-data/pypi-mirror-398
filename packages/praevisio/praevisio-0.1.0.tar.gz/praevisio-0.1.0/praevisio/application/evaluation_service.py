from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from abductio_core.application.dto import RootSpec, SessionConfig, SessionRequest
from abductio_core.application.ports import RunSessionDeps
from abductio_core.application.use_cases.run_session import run_session
import abductio_core

from ..domain.entities import EvaluationResult, StaticAnalysisResult
from ..domain.evaluation_config import EvaluationConfig
from ..domain.ports import StaticAnalyzer, TestRunner
from ..infrastructure.abductio_ports import DeterministicDecomposer, DeterministicEvaluator, ListAuditSink
from ..infrastructure.evidence_store import EvidenceStore
from ..infrastructure.static_analysis_semgrep import SemgrepStaticAnalyzer
from ..infrastructure.test_runner_subprocess import SubprocessPytestRunner


class EvaluationService:
    """Evaluate a commit using abductio-core for credence + audit."""

    def __init__(
        self,
        analyzer: StaticAnalyzer | None = None,
        test_runner: TestRunner | None = None,
    ) -> None:
        self._analyzer = analyzer
        self._test_runner = test_runner or SubprocessPytestRunner()

    def evaluate_path(self, path: str, config: EvaluationConfig | None = None) -> EvaluationResult:
        evaluation = config or EvaluationConfig()
        repo_root = Path(path)
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

        run_root = repo_root / evaluation.run_dir / run_id
        run_root.mkdir(parents=True, exist_ok=True)
        evidence_store = EvidenceStore(run_root)

        analyzer, semgrep_rules_path = self._build_analyzer(evaluation, self._analyzer)

        test_passes, tests_skipped, test_exit_code, test_error = self._run_tests(path, evaluation)
        pytest_ref = evidence_store.write_json(
            "evidence/pytest.json",
            {
                "targets": list(evaluation.pytest_targets),
                "args": list(evaluation.pytest_args),
                "exit_code": test_exit_code,
                "skipped": tests_skipped,
                "error": test_error,
            },
            kind="pytest",
        )

        static_skipped = False
        if analyzer is None:
            if not semgrep_rules_path:
                static_skipped = True
                sa_result = StaticAnalysisResult(
                    total_llm_calls=0, violations=0, coverage=0.0, findings=[]
                )
            else:
                sa_result = StaticAnalysisResult(
                    total_llm_calls=0,
                    violations=0,
                    coverage=0.0,
                    findings=[],
                    error="semgrep rule ids not configured",
                )
        else:
            sa_result = analyzer.analyze(path)

        semgrep_payload = {
            "rules_path": semgrep_rules_path,
            "callsite_rule_id": evaluation.semgrep_callsite_rule_id,
            "violation_rule_id": evaluation.semgrep_violation_rule_id,
            "coverage": sa_result.coverage,
            "total_calls": sa_result.total_llm_calls,
            "violations": sa_result.violations,
            "error": sa_result.error,
            "skipped": static_skipped,
            "findings": [f.__dict__ for f in sa_result.findings],
        }
        semgrep_ref = evidence_store.write_json("evidence/semgrep.json", semgrep_payload, kind="semgrep")

        evidence = {
            "test_passes": test_passes,
            "tests_skipped": tests_skipped,
            "tests_configured": bool(evaluation.pytest_targets),
            "test_error": test_error,
            "semgrep_coverage": sa_result.coverage,
            "violations_found": sa_result.violations,
            "total_llm_calls": sa_result.total_llm_calls,
            "semgrep_error": sa_result.error,
            "semgrep_rules_configured": bool(semgrep_rules_path),
            "no_call_sites": sa_result.total_llm_calls == 0 and sa_result.error is None,
        }
        evidence_refs = {"pytest": [pytest_ref], "semgrep": [semgrep_ref]}

        manifest_path = None
        manifest_sha = None
        audit_path = None
        audit_sha = None
        manifest_metadata = {
            "run_id": run_id,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "praevisio_version": self._praevisio_version(),
            "abductio_core_version": getattr(abductio_core, "__version__", "unknown"),
            "session_config": {
                "credits": evaluation.abductio_credits,
                "tau": evaluation.abductio_tau,
                "epsilon": evaluation.abductio_epsilon,
                "gamma": evaluation.abductio_gamma,
                "alpha": evaluation.abductio_alpha,
                "required_slots": list(evaluation.abductio_required_slots),
            },
        }

        if sa_result.error or test_error:
            manifest_path, manifest_sha = evidence_store.write_manifest(metadata=manifest_metadata)
            return EvaluationResult(
                credence=0.0,
                verdict="error",
                details=self._details(
                    evaluation=evaluation,
                    evidence=evidence,
                    evidence_refs=evidence_refs,
                    applicable=True,
                    semgrep_skipped=static_skipped,
                    audit_path=audit_path,
                    audit_sha=audit_sha,
                    manifest_path=manifest_path,
                    manifest_sha=manifest_sha,
                    run_id=run_id,
                    session_result=None,
                ),
            )

        audit_sink = ListAuditSink()
        evaluator = DeterministicEvaluator(evidence=evidence, evidence_refs=evidence_refs)
        decomposer = DeterministicDecomposer(
            promise_statement=f"Promise {evaluation.promise_id} holds for {repo_root}",
            slot_statements={},
        )
        session = SessionRequest(
            claim=f"Commit at {repo_root} satisfies promise {evaluation.promise_id}",
            roots=[
                RootSpec(
                    root_id=evaluation.promise_id,
                    statement=f"Promise {evaluation.promise_id} is satisfied",
                    exclusion_clause="Not explained by other hypotheses",
                )
            ],
            config=SessionConfig(
                tau=evaluation.abductio_tau,
                epsilon=evaluation.abductio_epsilon,
                gamma=evaluation.abductio_gamma,
                alpha=evaluation.abductio_alpha,
            ),
            credits=evaluation.abductio_credits,
            required_slots=evaluation.abductio_required_slots,
            run_mode="until_credits_exhausted",
        )
        result = run_session(session, RunSessionDeps(evaluator=evaluator, decomposer=decomposer, audit_sink=audit_sink))

        audit_path = run_root / "audit.json"
        audit_text = json.dumps(result.audit, indent=2, sort_keys=True)
        audit_bytes = audit_text.encode("utf-8")
        audit_path.write_bytes(audit_bytes)
        audit_sha = hashlib.sha256(audit_bytes).hexdigest()
        evidence_store.record_external("audit", audit_path, audit_sha)

        manifest_path, manifest_sha = evidence_store.write_manifest(metadata=manifest_metadata)

        credence = float(result.ledger.get(evaluation.promise_id, 0.0))
        root_view = result.roots.get(evaluation.promise_id, {})
        k_root = float(root_view.get("k_root", 0.0))
        gates = {
            "credence>=threshold": credence >= evaluation.threshold,
            "k_root>=tau": k_root >= evaluation.abductio_tau,
        }
        verdict = "green" if all(gates.values()) else "red"

        return EvaluationResult(
            credence=credence,
            verdict=verdict,
            details=self._details(
                evaluation=evaluation,
                evidence=evidence,
                evidence_refs=evidence_refs,
                applicable=True,
                semgrep_skipped=static_skipped,
                audit_path=audit_path,
                audit_sha=audit_sha,
                manifest_path=manifest_path,
                manifest_sha=manifest_sha,
                run_id=run_id,
                session_result=result.to_dict_view(),
                gates=gates,
                k_root=k_root,
            ),
        )

    @staticmethod
    def _build_analyzer(
        evaluation: EvaluationConfig,
        analyzer_override: StaticAnalyzer | None,
    ) -> Tuple[StaticAnalyzer | None, str]:
        semgrep_rules_path = evaluation.semgrep_rules_path
        if analyzer_override is not None:
            return analyzer_override, semgrep_rules_path
        if not semgrep_rules_path:
            return None, ""
        if not evaluation.semgrep_callsite_rule_id or not evaluation.semgrep_violation_rule_id:
            return None, semgrep_rules_path
        analyzer = SemgrepStaticAnalyzer(
            rules_path=Path(semgrep_rules_path),
            callsite_rule_id=evaluation.semgrep_callsite_rule_id,
            violation_rule_id=evaluation.semgrep_violation_rule_id,
        )
        return analyzer, semgrep_rules_path

    def _run_tests(
        self, path: str, evaluation: EvaluationConfig
    ) -> tuple[bool | None, bool, int | None, str | None]:
        if not evaluation.pytest_targets:
            return None, True, None, None
        try:
            test_result_code = self._test_runner.run(
                path, [*evaluation.pytest_targets, *evaluation.pytest_args]
            )
            return test_result_code == 0, False, test_result_code, None
        except Exception as exc:  # pragma: no cover - defensive
            return False, False, None, str(exc)

    @staticmethod
    def _details(
        evaluation: EvaluationConfig,
        evidence: Dict[str, Any],
        evidence_refs: Dict[str, List[str]],
        applicable: bool,
        semgrep_skipped: bool,
        audit_path: Path | None,
        audit_sha: str | None,
        manifest_path: Path | None,
        manifest_sha: str | None,
        run_id: str,
        session_result: Dict[str, Any] | None,
        gates: Dict[str, bool] | None = None,
        k_root: float | None = None,
    ) -> Dict[str, Any]:
        return {
            "promise_id": evaluation.promise_id,
            "threshold": evaluation.threshold,
            "severity": evaluation.severity,
            "applicable": applicable,
            "semgrep_skipped": semgrep_skipped,
            "semgrep_error": evidence.get("semgrep_error"),
            "test_error": evidence.get("test_error"),
            "evidence": dict(evidence),
            "evidence_refs": dict(evidence_refs),
            "audit_path": str(audit_path) if audit_path else None,
            "audit_sha256": audit_sha,
            "manifest_path": str(manifest_path) if manifest_path else None,
            "manifest_sha256": manifest_sha,
            "run_id": run_id,
            "session": session_result,
            "gates": gates,
            "k_root": k_root,
        }

    @staticmethod
    def _praevisio_version() -> str:
        try:
            from .. import __version__ as version
            return version
        except Exception:
            return "unknown"
