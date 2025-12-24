"""Configuration management for Kaggle projects using OmegaConf.

This module provides a ConfigManager class that handles configuration merging
from base (repository-level) and project-level configuration files.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any, cast

from omegaconf import DictConfig, OmegaConf


class ConfigManager:
    """Manages configuration loading and merging for Kaggle projects.

    Supports hierarchical configuration with:
    - Base configuration at repository root (kef.yaml or kef.toml)
    - Project-local configuration (local kef.yaml/toml override)

    Configurations are automatically merged with project config overriding base config.
    """

    def __init__(self, config_dir: Path | None = None) -> None:
        """Initialize ConfigManager.

        Args:
            config_dir: Optional directory to start searching from for kef.yaml/toml.
                       If None, searches from current working directory.
        """
        self.start_dir = Path(config_dir) if config_dir else Path.cwd()
        self.project_config_path: Path | None = None
        self.base_config_path: Path | None = None
        self.config: DictConfig = OmegaConf.create({})
        self._loaded = False
        self._discovered = False

    def discover(self, force: bool = False) -> None:
        """Discover configuration files without loading them."""
        if self._discovered and not force:
            return
        self.project_config_path = self.find_project_config(self.start_dir)
        self.base_config_path = self.find_base_config()
        self._discovered = True

    def find_git_root(self, start_path: Path | None = None) -> Path | None:
        """Find the git repository root directory.

        Args:
            start_path: Path to start searching from. If None, uses current directory.

        Returns:
            Path to git root, or None if not in a git repository.
        """
        search_path = start_path or Path.cwd()

        # Walk up the directory tree looking for .git
        for path in [search_path, *search_path.parents]:
            if (path / ".git").exists():
                return path

        return None

    def find_base_config(self) -> Path | None:
        """Find base configuration file at repository root.

        Returns:
            Path to kef.yaml or kef.toml at git root, or None if not found.
        """
        git_root = self.find_git_root()
        if git_root:
            for ext in [".yaml", ".toml"]:
                base_config = git_root / f"kef{ext}"
                if base_config.exists():
                    return base_config
        return None

    def find_project_config(self, start_dir: Path | None = None) -> Path | None:
        """Find project-local configuration file.

        Searches upward from start_dir for kef.yaml/toml.
        Prefers yaml over toml if both exist.

        Args:
            start_dir: Directory to start searching from.

        Returns:
            Path to configuration file, or None if not found.
        """
        search_path = start_dir or Path.cwd()
        if not search_path.is_dir():
            search_path = search_path.parent

        for path in [search_path, *search_path.parents]:
            # Priority: kef.yaml, kef.toml
            for ext in [".yaml", ".toml"]:
                cfg_path = path / f"kef{ext}"
                if cfg_path.exists():
                    return cfg_path

        return None

    def _load_file(self, path: Path) -> DictConfig:
        """Load configuration from file based on extension."""
        if path.suffix == ".toml":
            with path.open("rb") as f:
                data = tomllib.load(f)
                return OmegaConf.create(data)
        return OmegaConf.load(path)  # type: ignore[return-value]

    def load_base_config(self) -> None:
        """Load base configuration from repository root.

        Sets self.base_config_path and merges configuration.
        """
        if not self.base_config_path:
            self.base_config_path = self.find_base_config()
        if self.base_config_path:
            base_cfg = self._load_file(self.base_config_path)
            self.config = OmegaConf.merge(self.config, base_cfg)  # type: ignore[assignment]

    def load_project_config(self) -> None:
        """Load project-local configuration.

        Project config overrides base config.
        The project_config_path is auto-discovered in __init__.
        """
        if self.project_config_path:
            project_cfg = self._load_file(self.project_config_path)
            self.config = OmegaConf.merge(self.config, project_cfg)  # type: ignore[assignment]

    def load(self) -> DictConfig:
        """Load and merge all configurations.

        Loads base configuration first, then project configuration.
        Project configuration takes precedence over base configuration.

        Returns:
            Merged configuration as OmegaConf DictConfig object.
        """
        if self._loaded:
            return self.config

        self.discover()

        # Load base if found
        if self.base_config_path:
            base_cfg = self._load_file(self.base_config_path)
            self.config = OmegaConf.merge(self.config, base_cfg)  # type: ignore[assignment]

        # Load project if found and different from base
        if self.project_config_path and self.project_config_path != self.base_config_path:
            project_cfg = self._load_file(self.project_config_path)
            self.config = OmegaConf.merge(self.config, project_cfg)  # type: ignore[assignment]

        self._loaded = True
        return self.config

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key.

        Args:
            key: Configuration key (supports dot notation, e.g., "db.host").
            default: Default value if key not found.

        Returns:
            Configuration value or default.
        """
        try:
            return OmegaConf.select(self.config, key, default=default)
        except Exception:
            return default

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary.

        Returns:
            Configuration as dictionary.
        """
        return self.to_dict_node(self.config)

    def to_dict_node(self, node: Any) -> dict[str, Any]:
        """Convert a specific configuration node to dictionary.

        Args:
            node: Config node to convert.

        Returns:
            Node as dictionary.
        """
        result = OmegaConf.to_container(node, resolve=True)
        return cast(dict[str, Any], result) if isinstance(result, dict) else {}

    def to_yaml(self) -> str:
        """Convert configuration to YAML string.

        Returns:
            Configuration as YAML string.
        """
        return OmegaConf.to_yaml(self.config)

    def __repr__(self) -> str:
        """Return string representation of ConfigManager."""
        return f"ConfigManager(base={self.base_config_path}, project={self.project_config_path})"
