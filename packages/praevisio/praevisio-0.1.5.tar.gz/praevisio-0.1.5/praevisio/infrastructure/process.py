from __future__ import annotations

from typing import Iterable, List

from ..domain.ports import ProcessExecutor


class RecordingProcessExecutor(ProcessExecutor):
    """Executes nothing; records commands. Useful for tests."""

    def __init__(self, default_exit_code: int = 0) -> None:
        self.commands: List[List[str]] = []
        self.default_exit_code = default_exit_code

    def run(self, command: Iterable[str]) -> int:
        cmd = list(command)
        self.commands.append(cmd)
        return self.default_exit_code

