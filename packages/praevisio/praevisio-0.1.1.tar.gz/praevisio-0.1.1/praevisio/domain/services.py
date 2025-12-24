from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

from .entities import Hook, HookResult, CommitContext
from .value_objects import HookType, ExitCode


class HookSelectionService:
    """Selects and orders hooks based on type, file patterns, and dependencies."""

    def filter_by_type(self, hooks: Iterable[Hook], hook_type: HookType) -> List[Hook]:
        return [h for h in hooks if h.enabled and h.type == hook_type]

    def sort_by_dependencies(self, hooks: List[Hook]) -> List[Hook]:
        # Simple topological sort (Kahn's algorithm)
        graph: Dict[str, List[str]] = {h.id: list(h.depends_on) for h in hooks}
        id_to_hook = {h.id: h for h in hooks}
        incoming = {h.id: set(graph[h.id]) for h in hooks}
        ready = [hid for hid, deps in incoming.items() if not deps]
        order: List[Hook] = []
        while ready:
            hid = ready.pop(0)
            order.append(id_to_hook[hid])
            # remove edges
            for k, deps in incoming.items():
                if hid in deps:
                    deps.remove(hid)
                    if not deps and k not in [h.id for h in order] and k in id_to_hook and id_to_hook[k] not in order and k not in ready:
                        ready.append(k)
        # Append any remaining hooks (in case of cycles, keep original order)
        remaining = [h for h in hooks if h.id not in [o.id for o in order]]
        return order + remaining

    def matched_files(self, hook: Hook, context: CommitContext) -> List[str]:
        if not hook.file_scoped:
            return context.staged_files
        if not hook.patterns:
            return context.staged_files
        matched = []
        for f in context.staged_files:
            if any(p.matches(f) for p in hook.patterns):
                matched.append(f)
        return matched

