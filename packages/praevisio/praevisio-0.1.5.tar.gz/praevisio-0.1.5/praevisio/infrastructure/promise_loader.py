from __future__ import annotations

from pathlib import Path

import yaml

from ..domain.models import Promise
from ..domain.ports import PromiseLoader


class YamlPromiseLoader(PromiseLoader):
    """Load promise definitions from governance/promises/*.yaml."""

    def __init__(self, base_path: Path | None = None) -> None:
        self._base_path = base_path or Path("governance/promises")

    def load(self, promise_id: str) -> Promise:
        promise_file = self._base_path / f"{promise_id}.yaml"
        if not promise_file.exists():
            raise FileNotFoundError(
                f"Promise file not found: {promise_file}\n"
                f"Expected location: governance/promises/{promise_id}.yaml"
            )
        data = yaml.safe_load(promise_file.read_text(encoding="utf-8")) or {}
        return Promise(
            id=data["id"],
            statement=data["statement"],
            version=data.get("version", "0.1.0"),
            domain=data.get("domain", ""),
            critical=bool(data.get("critical", True)),
            credence_threshold=float(
                (data.get("success_criteria") or {}).get("credence_threshold", 0.95)
            ),
        )
