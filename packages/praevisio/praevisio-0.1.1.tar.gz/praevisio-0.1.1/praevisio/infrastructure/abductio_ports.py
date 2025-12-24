from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from abductio_core.domain.audit import AuditEvent


@dataclass
class ListAuditSink:
    events: List[AuditEvent] = field(default_factory=list)

    def append(self, event: AuditEvent) -> None:
        self.events.append(event)

    def to_dicts(self) -> List[Dict[str, Any]]:
        return [{"event_type": e.event_type, "payload": dict(e.payload)} for e in self.events]


@dataclass
class DeterministicDecomposer:
    promise_statement: str
    slot_statements: Dict[str, str]

    def decompose(self, root_id: str) -> Dict[str, Any]:
        if ":" in root_id:
            return {}
        return {
            "ok": True,
            "feasibility_statement": self.slot_statements.get("feasibility", self.promise_statement),
            "availability_statement": self.slot_statements.get("availability", ""),
            "fit_statement": self.slot_statements.get("fit_to_key_features", ""),
            "defeater_statement": self.slot_statements.get("defeater_resistance", ""),
        }


@dataclass
class DeterministicEvaluator:
    evidence: Dict[str, Any]
    evidence_refs: Dict[str, List[str]]

    def evaluate(self, node_key: str) -> Dict[str, Any]:
        if ":" not in node_key:
            return {}
        _, slot_key = node_key.split(":", 1)
        if slot_key == "feasibility":
            return self._evaluate_static_feasibility()
        if slot_key == "defeater_resistance":
            return self._evaluate_static_defeater()
        if slot_key == "availability":
            return self._evaluate_tests()
        if slot_key == "fit_to_key_features":
            return self._evaluate_fit()
        return {}

    def _evaluate_static_feasibility(self) -> Dict[str, Any]:
        coverage = float(self.evidence.get("semgrep_coverage", 0.0))
        error = self.evidence.get("semgrep_error")
        rules_ok = bool(self.evidence.get("semgrep_rules_configured", True))
        no_call_sites = bool(self.evidence.get("no_call_sites", False))

        p = 1.0 if no_call_sites else coverage
        A = 2 if error is None else 0
        B = 2 if rules_ok else 0
        if coverage >= 0.99:
            C = 2
        elif coverage >= 0.95:
            C = 1
        else:
            C = 0
        D = 2 if no_call_sites else (1 if coverage > 0.0 else 0)

        return {
            "p": p,
            "A": A,
            "B": B,
            "C": C,
            "D": D,
            "evidence_refs": self.evidence_refs.get("semgrep", []),
        }

    def _evaluate_static_defeater(self) -> Dict[str, Any]:
        violations = int(self.evidence.get("violations_found", 0))
        error = self.evidence.get("semgrep_error")
        rules_ok = bool(self.evidence.get("semgrep_rules_configured", True))
        no_call_sites = bool(self.evidence.get("no_call_sites", False))

        if no_call_sites:
            p = 1.0
        else:
            p = 1.0 if violations == 0 else 0.0
        A = 2 if error is None else 0
        B = 2 if rules_ok else 0
        C = 2 if (no_call_sites or violations == 0) else 0
        D = 2 if (no_call_sites or violations == 0) else 0

        return {
            "p": p,
            "A": A,
            "B": B,
            "C": C,
            "D": D,
            "evidence_refs": self.evidence_refs.get("semgrep", []),
        }

    def _evaluate_tests(self) -> Dict[str, Any]:
        test_passes = self.evidence.get("test_passes")
        tests_skipped = bool(self.evidence.get("tests_skipped", False))
        if tests_skipped:
            p = 0.2
            A = 0
            B = 0
        else:
            p = 1.0 if test_passes else 0.0
            A = 2 if test_passes else 0
            B = 2 if test_passes else 0
        C = 1 if not tests_skipped else 0
        D = 1 if not tests_skipped else 0

        return {
            "p": p,
            "A": A,
            "B": B,
            "C": C,
            "D": D,
            "evidence_refs": self.evidence_refs.get("pytest", []),
        }

    def _evaluate_fit(self) -> Dict[str, Any]:
        has_tests = bool(self.evidence.get("tests_configured", False))
        has_rules = bool(self.evidence.get("semgrep_rules_configured", False))
        p = 1.0 if (has_tests or has_rules) else 0.5
        A = 2 if (has_tests or has_rules) else 1
        B = 2 if has_rules else 1
        C = 1 if has_tests else 0
        D = 1 if has_rules else 0

        refs = self.evidence_refs.get("pytest", []) + self.evidence_refs.get("semgrep", [])
        return {
            "p": p,
            "A": A,
            "B": B,
            "C": C,
            "D": D,
            "evidence_refs": refs,
        }
