from __future__ import annotations

import subprocess
import sys
from typing import Iterable

from ..domain.ports import TestRunner


class SubprocessPytestRunner(TestRunner):
    """Run pytest via subprocess to avoid pytest.main side effects."""

    def run(self, path: str, args: Iterable[str]) -> int:
        command = [sys.executable, "-m", "pytest", *args]
        result = subprocess.run(command, cwd=path)
        return result.returncode
