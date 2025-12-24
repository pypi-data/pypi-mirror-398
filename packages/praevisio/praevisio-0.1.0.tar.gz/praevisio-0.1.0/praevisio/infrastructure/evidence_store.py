from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple


@dataclass(frozen=True)
class EvidenceArtifact:
    kind: str
    path: str
    sha256: str
    size_bytes: int


class EvidenceStore:
    """Persist evidence artifacts and return stable reference strings."""

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir
        self._artifacts: List[EvidenceArtifact] = []
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def write_text(self, name: str, content: str, kind: str) -> str:
        path = self._base_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        data = content.encode("utf-8")
        path.write_bytes(data)
        sha = self._sha256_bytes(data)
        self._record(kind, path, sha)
        return f"{kind}:sha256:{sha}"

    def write_json(self, name: str, payload: Dict[str, Any], kind: str) -> str:
        text = json.dumps(payload, indent=2, sort_keys=True)
        return self.write_text(name, text, kind=kind)

    def write_manifest(self, name: str = "manifest.json", metadata: Dict[str, Any] | None = None) -> Tuple[Path, str]:
        manifest = {
            "artifacts": [
                {
                    "kind": a.kind,
                    "path": a.path,
                    "sha256": a.sha256,
                    "size_bytes": a.size_bytes,
                }
                for a in self._artifacts
            ]
        }
        if metadata:
            manifest["metadata"] = dict(metadata)
        path = self._base_dir / name
        text = json.dumps(manifest, indent=2, sort_keys=True)
        data = text.encode("utf-8")
        path.write_bytes(data)
        sha = self._sha256_bytes(data)
        return path, sha

    def record_external(self, kind: str, path: Path, sha256: str) -> None:
        self._record(kind, path, sha256)

    def artifacts(self) -> List[EvidenceArtifact]:
        return list(self._artifacts)

    def _record(self, kind: str, path: Path, sha: str) -> None:
        rel_path = str(path.relative_to(self._base_dir))
        size_bytes = path.stat().st_size
        self._artifacts.append(
            EvidenceArtifact(kind=kind, path=rel_path, sha256=sha, size_bytes=size_bytes)
        )

    @staticmethod
    def _sha256_bytes(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()
