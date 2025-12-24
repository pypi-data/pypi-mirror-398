"""
User configuration management for Claux.

Manages global user settings stored in ~/.claux/config.yaml
"""

import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime


class UserConfig:
    """Manages global user configuration."""

    def __init__(self):
        """Initialize user config manager."""
        self.config_dir = Path.home() / ".claux"
        self.config_file = self.config_dir / "config.yaml"
        self.bookmarks_file = self.config_dir / "bookmarks.yaml"
        self.history_file = self.config_dir / "history.yaml"
        self._config: Optional[Dict[str, Any]] = None
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        """Ensure config directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> Dict[str, Any]:
        """
        Load configuration from file.

        Returns:
            Configuration dictionary
        """
        if self._config is not None:
            return self._config

        if not self.config_file.exists():
            self._config = self._get_default_config()
            self.save()
            return self._config

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Failed to load config: {e}")
            self._config = self._get_default_config()

        return self._config

    def save(self):
        """Save configuration to file."""
        if self._config is None:
            return

        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(self._config, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            print(f"Error: Failed to save config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.

        Args:
            key: Config key (supports dot notation: "mcp.default")
            default: Default value if key not found

        Returns:
            Configuration value
        """
        config = self.load()
        parts = key.split(".")
        value = config

        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """
        Set configuration value.

        Args:
            key: Config key (supports dot notation)
            value: Value to set
        """
        config = self.load()
        parts = key.split(".")
        target = config

        # Navigate to target dict
        for part in parts[:-1]:
            if part not in target:
                target[part] = {}
            target = target[part]

        # Set value
        target[parts[-1]] = value
        self.save()

    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration.

        Returns:
            Default config dictionary
        """
        return {
            "version": "0.1.0",
            "language": "en",
            "mcp": {
                "default": "base",
                "auto_restart_prompt": True,
            },
            "agents": {
                "default_profile": "base",
                "auto_detect": True,
            },
            "wizard": {
                "search_paths": [
                    str(Path.home() / "PycharmProjects"),
                    str(Path.home() / "projects"),
                    str(Path.home() / "Documents"),
                ],
                "max_depth": 2,
            },
            "ui": {
                "color_scheme": "auto",
                "show_tips": True,
                "confirm_destructive": True,
            },
            "updates": {
                "check_on_start": True,
                "auto_update": False,
            },
            "claude": {
                "exit_after_close": True,  # Exit claux when Claude Code closes
            },
        }

    def reset(self):
        """Reset configuration to defaults."""
        self._config = self._get_default_config()
        self.save()

    # Bookmarks management
    def get_bookmarks(self) -> Dict[str, str]:
        """
        Get project bookmarks.

        Returns:
            Dict of bookmark_name -> project_path
        """
        if not self.bookmarks_file.exists():
            return {}

        try:
            with open(self.bookmarks_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def add_bookmark(self, name: str, path: str):
        """
        Add project bookmark.

        Args:
            name: Bookmark name
            path: Project path
        """
        bookmarks = self.get_bookmarks()
        bookmarks[name] = path

        with open(self.bookmarks_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(bookmarks, f, default_flow_style=False)

    def remove_bookmark(self, name: str):
        """
        Remove project bookmark.

        Args:
            name: Bookmark name
        """
        bookmarks = self.get_bookmarks()
        if name in bookmarks:
            del bookmarks[name]

            with open(self.bookmarks_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(bookmarks, f, default_flow_style=False)

    # History management
    def add_history(self, command: str, success: bool = True):
        """
        Add command to history.

        Args:
            command: Command executed
            success: Whether command succeeded
        """
        history = self._load_history()

        history.append(
            {
                "command": command,
                "timestamp": datetime.now().isoformat(),
                "success": success,
            }
        )

        # Keep last 1000 entries
        if len(history) > 1000:
            history = history[-1000:]

        self._save_history(history)

    def get_history(self, limit: int = 50) -> list:
        """
        Get command history.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of history entries
        """
        history = self._load_history()
        return history[-limit:]

    def _load_history(self) -> list:
        """Load history from file."""
        if not self.history_file.exists():
            return []

        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or []
        except Exception:
            return []

    def _save_history(self, history: list):
        """Save history to file."""
        with open(self.history_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(history, f, default_flow_style=False)


# Global config instance
_config = UserConfig()


def get_config() -> UserConfig:
    """
    Get global config instance.

    Returns:
        UserConfig instance
    """
    return _config


def load_config() -> Dict[str, Any]:
    """
    Load configuration.

    Returns:
        Configuration dictionary
    """
    return _config.load()


def save_config():
    """Save configuration."""
    _config.save()


def get_value(key: str, default: Any = None) -> Any:
    """
    Get configuration value.

    Args:
        key: Config key
        default: Default value

    Returns:
        Configuration value
    """
    return _config.get(key, default)


def set_value(key: str, value: Any):
    """
    Set configuration value.

    Args:
        key: Config key
        value: Value to set
    """
    _config.set(key, value)
