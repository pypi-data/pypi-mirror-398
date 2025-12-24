from __future__ import annotations

from ..domain.config import Configuration
from ..domain.ports import ConfigLoader, FileSystemService


class ConfigurationService:
    """Load and return the effective Configuration.

    This thin application service delegates parsing to a ConfigLoader port and
    isolates future concerns like merging user config with defaults.

    Parameters
    - loader: adapter that knows how to parse configuration files
    - fs: file system port (reserved for future composition/merging)
    - config_path: path to the configuration file (default: .praevisio.yaml)
    """
    def __init__(self, loader: ConfigLoader, fs: FileSystemService, config_path: str = ".praevisio.yaml") -> None:
        self._loader = loader
        self._fs = fs
        self._path = config_path

    def load(self) -> Configuration:
        # Future: merge defaults here
        return self._loader.load(self._path)
