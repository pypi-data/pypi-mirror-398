from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class EvaluationConfig:
    promise_id: str = "default-promise"
    threshold: float = 0.95
    severity: str | None = None
    pytest_args: List[str] = field(default_factory=lambda: ["-q", "--disable-warnings"])
    pytest_targets: List[str] = field(default_factory=list)
    semgrep_rules_path: str = "governance/evidence/semgrep_rules.yaml"
    semgrep_callsite_rule_id: str = "llm-call-site"
    semgrep_violation_rule_id: str = "llm-call-must-log"
    thresholds: Dict[str, float] = field(default_factory=dict)
    abductio_credits: int = 6
    abductio_tau: float = 0.70
    abductio_epsilon: float = 0.05
    abductio_gamma: float = 0.20
    abductio_alpha: float = 0.40
    abductio_required_slots: List[Dict[str, str]] = field(default_factory=lambda: [
        {"slot_key": "feasibility", "role": "NEC"},
        {"slot_key": "availability", "role": "NEC"},
        {"slot_key": "fit_to_key_features", "role": "NEC"},
        {"slot_key": "defeater_resistance", "role": "NEC"},
    ])
    run_dir: str = ".praevisio/runs"
