from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import List

from ..domain.entities import StaticAnalysisResult, StaticFinding
from ..domain.ports import StaticAnalyzer


class SemgrepStaticAnalyzer(StaticAnalyzer):
    """StaticAnalyzer implementation using Semgrep."""

    def __init__(
        self,
        rules_path: Path | None = None,
        callsite_rule_id: str = "llm-call-site",
        violation_rule_id: str = "llm-call-must-log",
    ) -> None:
        self._rules_path = rules_path or Path("governance/evidence/semgrep_rules.yaml")
        self._callsite_rule_id = callsite_rule_id
        self._violation_rule_id = violation_rule_id

    def analyze(self, path: str) -> StaticAnalysisResult:
        # Ensure rules file exists in the target project
        root = Path(path)
        rules_path = self._rules_path
        if not rules_path.is_absolute():
            rules_path = root / rules_path
        if not rules_path.exists():
            return StaticAnalysisResult(
                total_llm_calls=0,
                violations=0,
                coverage=0.0,
                findings=[],
                error=f"semgrep rules file not found at {rules_path}",
            )

        # First: run Semgrep with JSON output using our governance rules
        result = subprocess.run(
            ["semgrep", "--config", str(rules_path), "--json", "."],
            capture_output=True,
            text=True,
            cwd=path,
        )

        if result.returncode >= 2:
            raise RuntimeError(f"Semgrep failed: {result.stderr}")

        try:
            output = json.loads(result.stdout or "{}")
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Could not parse Semgrep output: {exc}") from exc

        findings = output.get("results", [])

        llm_violations = [
            f for f in findings if f.get("check_id") == self._violation_rule_id
        ]
        llm_call_sites = [
            f for f in findings if f.get("check_id") == self._callsite_rule_id
        ]

        total_calls = len(llm_call_sites)
        num_violations = len(llm_violations)
        if total_calls == 0 and num_violations > 0:
            total_calls = num_violations

        if total_calls == 0:
            coverage = 0.0
        else:
            coverage = (total_calls - num_violations) / total_calls

        findings_struct: List[StaticFinding] = []
        for f in llm_violations:
            path_str = f.get("path", "")
            start = f.get("start") or {}
            line = start.get("line")
            code = (f.get("extra") or {}).get("lines", "")
            findings_struct.append(StaticFinding(file=path_str, line=line, code=code))

        return StaticAnalysisResult(
            total_llm_calls=total_calls,
            violations=num_violations,
            coverage=coverage,
            findings=findings_struct,
            error=None,
        )
