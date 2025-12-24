from __future__ import annotations

from typing import List

from ..domain.config import Configuration
from ..domain.entities import HookResult
from ..domain.ports import GitRepository, ProcessExecutor
from ..domain.services import HookSelectionService
from ..domain.value_objects import ExitCode, HookType


class HookOrchestrationService:
    """Coordinates running hooks in correct order and returns results."""

    def __init__(
        self,
        git: GitRepository,
        executor: ProcessExecutor,
        selector: HookSelectionService | None = None,
    ) -> None:
        self._git = git
        self._exec = executor
        self._selector = selector or HookSelectionService()

    def run_hooks(self, hook_type: HookType, config: Configuration) -> List[HookResult]:
        context = self._build_context()
        hooks = self._selector.filter_by_type(config.hooks, hook_type)
        hooks = self._selector.sort_by_dependencies(hooks)

        results: List[HookResult] = []
        for hook in hooks:
            matched = self._selector.matched_files(hook, context)
            if hook.file_scoped and not matched:
                results.append(
                    HookResult(hook_id=hook.id, skipped=True, exit_code=ExitCode(0), matched_files=matched)
                )
                continue
            # For now we don't expand file args; just run the command.
            code = self._exec.run(hook.command)
            results.append(
                HookResult(hook_id=hook.id, skipped=False, exit_code=ExitCode(code), matched_files=matched)
            )

        return results

    def _build_context(self):
        from ..domain.entities import CommitContext

        return CommitContext(staged_files=self._git.get_staged_files(), commit_message=self._git.get_commit_message())
