"""
Unified configuration management for Claux.

Provides a single entry point for all configuration access with hierarchical
resolution, lazy loading, and validation support.
"""

import os
from typing import Any, Dict, List, Optional
import time


class ConfigManager:
    """
    Unified configuration manager providing access to all config types.

    Properties:
        orchestrator: Project-level config (.claude/ directory)
        user: Global user config (~/.claux/config.yaml)
        profiles: Agent profile manager
        mcp: MCP server configuration manager

    Examples:
        >>> manager = get_manager()
        >>> manager.orchestrator.repo_root
        Path('/home/user/project')

        >>> manager.get("language")
        'ru'

        >>> manager.get("mcp.default", "base")
        'base'
    """

    def __init__(self):
        """Initialize ConfigManager with lazy-loaded components."""
        # Lazy-loaded config components
        self._orchestrator: Optional[Any] = None
        self._user: Optional[Any] = None
        self._profiles: Optional[Any] = None
        self._mcp: Optional[Any] = None

        # Cache management
        self._cache_ttl = 60  # seconds
        self._cache_timestamps: Dict[str, float] = {}

    @property
    def orchestrator(self):
        """
        Get project-level configuration (.claude/ directory).

        Returns:
            OrchestratorConfig: Project configuration instance

        Raises:
            ProjectNotFoundError: If .claude directory not found
        """
        if self._orchestrator is None or not self._is_cache_valid("orchestrator"):
            from claux.core.config import OrchestratorConfig

            self._orchestrator = OrchestratorConfig.from_repo_root()
            self._cache_timestamps["orchestrator"] = time.time()

        return self._orchestrator

    @property
    def user(self):
        """
        Get global user configuration (~/.claux/config.yaml).

        Returns:
            UserConfig: User configuration instance
        """
        if self._user is None or not self._is_cache_valid("user"):
            from claux.core.user_config import UserConfig

            self._user = UserConfig()
            self._cache_timestamps["user"] = time.time()

        return self._user

    @property
    def profiles(self):
        """
        Get agent profile manager.

        Returns:
            ProfileManager: Agent profile manager instance
        """
        if self._profiles is None or not self._is_cache_valid("profiles"):
            from claux.core.profiles import ProfileManager

            self._profiles = ProfileManager(self.orchestrator)
            self._cache_timestamps["profiles"] = time.time()

        return self._profiles

    @property
    def mcp(self):
        """
        Get MCP server configuration manager.

        Returns:
            MCPManager: MCP configuration manager instance
        """
        if self._mcp is None or not self._is_cache_valid("mcp"):
            from claux.core.mcp import MCPManager

            self._mcp = MCPManager(self.orchestrator)
            self._cache_timestamps["mcp"] = time.time()

        return self._mcp

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value with hierarchical resolution.

        Resolution order:
        1. Environment variables (CLAUX_<KEY>)
        2. Project settings (.claude/settings.local.json)
        3. User settings (~/.claux/config.yaml)
        4. Default value

        Args:
            key: Configuration key (supports dot notation: "mcp.default")
            default: Default value if key not found

        Returns:
            Configuration value or default

        Examples:
            >>> manager.get("language")
            'ru'

            >>> manager.get("mcp.default", "base")
            'base'

            >>> manager.get("agents.default_profile")
            'development'
        """
        # 1. Check environment variables
        env_key = f"CLAUX_{key.upper().replace('.', '_')}"
        env_value = os.getenv(env_key)
        if env_value is not None:
            return env_value

        # 2. Check project settings (if in a project)
        try:
            project_settings = self.orchestrator.settings
            value = self._get_nested(project_settings, key)
            if value is not None:
                return value
        except Exception:
            # Not in a project, continue to user settings
            pass

        # 3. Check user settings
        try:
            user_config = self.user.load()
            value = self._get_nested(user_config, key)
            if value is not None:
                return value
        except Exception:
            pass

        # 4. Return default
        return default

    def _get_nested(self, data: Dict[str, Any], key: str) -> Any:
        """
        Get nested dictionary value using dot notation.

        Args:
            data: Dictionary to search
            key: Key with optional dots (e.g., "mcp.default")

        Returns:
            Value if found, None otherwise

        Examples:
            >>> data = {"mcp": {"default": "base"}}
            >>> _get_nested(data, "mcp.default")
            'base'
        """
        keys = key.split(".")
        current = data

        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None

        return current

    def validate_all(self) -> Dict[str, List[str]]:
        """
        Validate all configuration files using JSON schemas.

        Returns:
            Dictionary mapping config types to error lists
            Empty dict if all configs are valid

        Examples:
            >>> errors = manager.validate_all()
            >>> if errors:
            ...     print(f"Found {len(errors)} config errors")
            >>> for config_type, error_list in errors.items():
            ...     print(f"{config_type}: {error_list}")
        """
        from claux.core.validation import ConfigValidator

        errors: Dict[str, List[str]] = {}

        # Initialize validator (will use orchestrator's schemas_dir)
        try:
            schemas_dir = self.orchestrator.schemas_dir
            validator = ConfigValidator(schemas_dir)
        except Exception as e:
            # If we can't load validator, return early
            return {"validator": [f"Failed to initialize validator: {str(e)}"]}

        # Validate project settings (.claude/settings.local.json)
        try:
            settings = self.orchestrator.settings
            settings_errors = validator.validate(settings, "settings")
            if settings_errors:
                errors["settings"] = settings_errors
        except Exception as e:
            errors["settings"] = [f"Failed to load settings: {str(e)}"]

        # Validate user config (~/.claux/config.yaml)
        try:
            user_config = self.user.load()
            user_errors = validator.validate(user_config, "user-config")
            if user_errors:
                errors["user"] = user_errors
        except Exception as e:
            errors["user"] = [f"Failed to load user config: {str(e)}"]

        # Validate MCP configs (.mcp.*.json files)
        try:
            mcp_configs = self.mcp.list_configs()
            for config_name in mcp_configs:
                try:
                    config_data = self.mcp.load_config(config_name)
                    mcp_errors = validator.validate(config_data, "mcp-config")
                    if mcp_errors:
                        errors[f"mcp/{config_name}"] = mcp_errors
                except Exception as e:
                    errors[f"mcp/{config_name}"] = [
                        f"Failed to load MCP config: {str(e)}"
                    ]
        except Exception as e:
            errors["mcp"] = [f"Failed to list MCP configs: {str(e)}"]

        # Note: Profile validation not implemented yet (no schema defined)
        # Agent profiles will be validated when profile.schema.json is created

        return errors

    def reload(self):
        """
        Clear all caches and reload configurations from disk.

        Use this when config files have been modified externally.

        Examples:
            >>> manager.reload()
            >>> # All configs will be re-read on next access
        """
        self._orchestrator = None
        self._user = None
        self._profiles = None
        self._mcp = None
        self._cache_timestamps.clear()

    def _is_cache_valid(self, key: str) -> bool:
        """
        Check if cached value is still valid based on TTL.

        Args:
            key: Cache key to check

        Returns:
            True if cache is valid, False otherwise
        """
        if key not in self._cache_timestamps:
            return False

        elapsed = time.time() - self._cache_timestamps[key]
        return elapsed < self._cache_ttl

    def _invalidate_cache(self, key: Optional[str] = None):
        """
        Invalidate specific cache key or all caches.

        Args:
            key: Specific key to invalidate, or None for all caches
        """
        if key:
            self._cache_timestamps.pop(key, None)
            setattr(self, f"_{key}", None)
        else:
            self.reload()


# Singleton instance
_config_manager: Optional[ConfigManager] = None


def get_manager(force_reload: bool = False) -> ConfigManager:
    """
    Get singleton ConfigManager instance.

    Args:
        force_reload: If True, create new instance even if one exists

    Returns:
        ConfigManager instance

    Examples:
        >>> manager = get_manager()
        >>> manager.get("language")
        'ru'

        >>> # Force reload all configs
        >>> manager = get_manager(force_reload=True)
    """
    global _config_manager

    if _config_manager is None or force_reload:
        _config_manager = ConfigManager()

    return _config_manager


def reset_manager():
    """
    Reset singleton instance (useful for testing).

    Examples:
        >>> reset_manager()
        >>> manager = get_manager()  # Creates fresh instance
    """
    global _config_manager
    _config_manager = None
