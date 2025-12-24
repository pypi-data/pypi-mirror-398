from __future__ import annotations

from ..domain.ports import FileSystemService


DEFAULT_CONFIG = """
evaluation:
  promise_id: example-promise
  threshold: 0.95
  severity: high
  pytest_targets: []
  semgrep_rules_path: ""
  semgrep_callsite_rule_id: llm-call-site
  semgrep_violation_rule_id: llm-call-must-log
  abductio_credits: 6
  abductio_tau: 0.70
  abductio_epsilon: 0.05
  abductio_gamma: 0.20
  abductio_alpha: 0.40
  abductio_required_slots:
    - slot_key: feasibility
      role: NEC
    - slot_key: availability
      role: NEC
    - slot_key: fit_to_key_features
      role: NEC
    - slot_key: defeater_resistance
      role: NEC
  run_dir: ".praevisio/runs"
  thresholds:
    high: 0.95
hooks:
  - id: example-lint
    name: Example Lint
    type: pre-commit
    command: ["echo", "lint"]
    patterns: ["**/*.py"]
""".lstrip()


class InstallationService:
    """Install a default .praevisio.yaml configuration file.

    Parameters
    - fs: file system adapter used to write the file
    - config_path: target path for the configuration file
    """
    def __init__(self, fs: FileSystemService, config_path: str = ".praevisio.yaml") -> None:
        self._fs = fs
        self._path = config_path

    def install(self) -> str:
        self._fs.write_text(self._path, DEFAULT_CONFIG)
        return self._path
