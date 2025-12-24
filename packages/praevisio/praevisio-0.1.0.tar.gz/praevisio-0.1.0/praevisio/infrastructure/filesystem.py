from __future__ import annotations

from ..domain.ports import FileSystemService


class LocalFileSystemService(FileSystemService):
    """FileSystemService adapter that uses the local filesystem."""
    def read_text(self, path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def write_text(self, path: str, content: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
