from __future__ import annotations

from ..domain.config import Configuration
from ..domain.entities import Hook
from ..domain.value_objects import HookType


class ConfigurationInvalidException(Exception):
    """Raised when a provided Configuration fails validation."""


class ValidationService:
    """Validate configuration objects before execution."""

    def validate(self, config: Configuration) -> None:
        for hook in config.hooks:
            self._validate_hook(hook)

    def _validate_hook(self, hook: Hook) -> None:
        if not hook.command:
            raise ConfigurationInvalidException(f"Hook {hook.id} has empty command")
        if hook.type not in {HookType.PRE_COMMIT, HookType.COMMIT_MSG, HookType.PRE_PUSH}:
            raise ConfigurationInvalidException(f"Hook {hook.id} has invalid type {hook.type}")
