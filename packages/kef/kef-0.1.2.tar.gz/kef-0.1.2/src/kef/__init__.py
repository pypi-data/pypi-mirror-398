"""kef - Kaggle Efficient Framework.

Configuration management for Kaggle projects.
"""

from typing import Any

from omegaconf import DictConfig

from .config import ConfigManager

__version__ = "0.1.1"

_manager: ConfigManager | None = None


def get_config() -> DictConfig:
    """Get the merged configuration singleton."""
    global _manager
    if _manager is None:
        _manager = ConfigManager()
    return _manager.load()


def reload_config() -> DictConfig:
    """Reload the configuration from disk."""
    global _manager
    _manager = ConfigManager()
    return _manager.load()


# Lazy singleton
class ConfigProxy:
    """A proxy object that loads the configuration only when accessed."""

    def __getattr__(self, name: str) -> Any:
        return getattr(get_config(), name)

    def __getitem__(self, key: str) -> Any:
        return get_config()[key]

    def __repr__(self) -> str:
        return repr(get_config())

    def __dir__(self):
        return dir(get_config())


# Expose cfg as the primary entry point
cfg: DictConfig = ConfigProxy()  # type: ignore

__all__ = ["cfg", "get_config", "reload_config", "ConfigManager"]
