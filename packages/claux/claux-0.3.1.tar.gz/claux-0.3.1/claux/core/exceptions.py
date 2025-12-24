"""
Custom exception classes for Claux configuration management.

Provides contextual error messages with actionable suggestions to help users
resolve configuration issues.
"""

from pathlib import Path
from typing import List, Optional


class ConfigError(Exception):
    """
    Base exception for configuration errors with helpful suggestions.

    Attributes:
        message: Error description
        suggestion: Actionable advice for resolving the error
    """

    def __init__(self, message: str, suggestion: Optional[str] = None):
        """
        Initialize configuration error.

        Args:
            message: Error description
            suggestion: Optional suggestion for resolution
        """
        self.message = message
        self.suggestion = suggestion
        super().__init__(self.format_message())

    def format_message(self) -> str:
        """
        Format error message with suggestion.

        Returns:
            Formatted error message string
        """
        msg = f"Configuration Error: {self.message}"
        if self.suggestion:
            msg += f"\n\nSuggestion: {self.suggestion}"
        return msg


class ProjectNotFoundError(ConfigError):
    """
    Raised when .claude directory is not found.

    This usually means the user is not in a Claux project directory.
    """

    def __init__(self, path: Optional[Path] = None):
        """
        Initialize project not found error.

        Args:
            path: Path where .claude directory was expected
        """
        if path:
            message = f".claude directory not found at {path}"
        else:
            message = ".claude directory not found in current directory or parent directories"

        suggestion = (
            "Run 'claux init' to initialize a new project, "
            "or 'claux wizard' to select an existing project."
        )

        super().__init__(message, suggestion)


class ProfileNotFoundError(ConfigError):
    """
    Raised when specified agent profile doesn't exist.

    Provides list of available profiles to help user choose a valid one.
    """

    def __init__(self, name: str, available: Optional[List[str]] = None):
        """
        Initialize profile not found error.

        Args:
            name: Name of profile that wasn't found
            available: Optional list of available profile names
        """
        message = f"Agent profile '{name}' not found"

        if available:
            profiles_list = ", ".join(f"'{p}'" for p in available)
            suggestion = (
                f"Available profiles: {profiles_list}\n"
                f"Use 'claux agents list' to see all profiles."
            )
        else:
            suggestion = "Use 'claux agents list' to see available profiles."

        super().__init__(message, suggestion)


class MCPConfigNotFoundError(ConfigError):
    """
    Raised when specified MCP configuration doesn't exist.

    Provides list of available MCP configs to help user choose a valid one.
    """

    def __init__(self, name: str, available: Optional[List[str]] = None):
        """
        Initialize MCP config not found error.

        Args:
            name: Name of MCP config that wasn't found
            available: Optional list of available config names
        """
        message = f"MCP configuration '{name}' not found"

        if available:
            configs_list = ", ".join(f"'{c}'" for c in available)
            suggestion = (
                f"Available configurations: {configs_list}\n"
                f"Use 'claux mcp list' to see all MCP configurations."
            )
        else:
            suggestion = "Use 'claux mcp list' to see available MCP configurations."

        super().__init__(message, suggestion)


class ValidationError(ConfigError):
    """
    Raised when configuration validation fails.

    Aggregates multiple validation errors and provides guidance on fixing them.
    """

    def __init__(self, config_type: str, errors: List[str]):
        """
        Initialize validation error.

        Args:
            config_type: Type of config that failed validation
            errors: List of specific validation error messages
        """
        if not errors:
            errors = ["Unknown validation error"]

        error_list = "\n  - ".join(errors)
        message = f"Invalid {config_type} configuration:\n  - {error_list}"

        suggestion = (
            "Fix the validation errors listed above.\n"
            "Use 'claux config validate' to check all configurations."
        )

        super().__init__(message, suggestion)


class SettingsNotFoundError(ConfigError):
    """
    Raised when settings file is missing or unreadable.

    Suggests creating default settings or re-initializing project.
    """

    def __init__(self, file_path: Path, reason: Optional[str] = None):
        """
        Initialize settings not found error.

        Args:
            file_path: Path to settings file
            reason: Optional reason why settings couldn't be loaded
        """
        if reason:
            message = f"Settings file not found or unreadable: {file_path}\nReason: {reason}"
        else:
            message = f"Settings file not found: {file_path}"

        suggestion = (
            "Settings will be created with defaults on next save.\n"
            "Use 'claux init' to re-initialize project settings."
        )

        super().__init__(message, suggestion)


class UserConfigNotFoundError(ConfigError):
    """
    Raised when user configuration file is missing or unreadable.

    Suggests creating default user config.
    """

    def __init__(self, file_path: Path, reason: Optional[str] = None):
        """
        Initialize user config not found error.

        Args:
            file_path: Path to user config file
            reason: Optional reason why config couldn't be loaded
        """
        if reason:
            message = f"User config not found or unreadable: {file_path}\nReason: {reason}"
        else:
            message = f"User config not found: {file_path}"

        suggestion = (
            "Default configuration will be created automatically.\n"
            "Use 'claux config reset' to recreate with defaults."
        )

        super().__init__(message, suggestion)


class InvalidConfigValueError(ConfigError):
    """
    Raised when configuration value is invalid or out of range.

    Provides expected value format or range.
    """

    def __init__(
        self,
        key: str,
        value: any,
        expected: str,
        valid_values: Optional[List[str]] = None,
    ):
        """
        Initialize invalid config value error.

        Args:
            key: Configuration key
            value: Invalid value that was provided
            expected: Description of expected value format
            valid_values: Optional list of valid values
        """
        message = f"Invalid value for '{key}': {value}\nExpected: {expected}"

        if valid_values:
            values_list = ", ".join(f"'{v}'" for v in valid_values)
            suggestion = f"Valid values: {values_list}"
        else:
            suggestion = f"Use 'claux config get {key}' to see current value."

        super().__init__(message, suggestion)


class ConfigPermissionError(ConfigError):
    """
    Raised when configuration file permissions prevent read/write.

    Suggests checking file permissions and ownership.
    """

    def __init__(self, file_path: Path, operation: str = "access"):
        """
        Initialize config permission error.

        Args:
            file_path: Path to file with permission issue
            operation: Operation that failed (read, write, access)
        """
        message = f"Permission denied: cannot {operation} {file_path}"

        suggestion = (
            f"Check file permissions and ownership:\n"
            f"  chmod 644 {file_path}  # Make readable/writable\n"
            f"  chown $USER {file_path}  # Set correct owner"
        )

        super().__init__(message, suggestion)


class ConfigFormatError(ConfigError):
    """
    Raised when configuration file has invalid format (e.g., malformed JSON/YAML).

    Provides line/column information if available.
    """

    def __init__(
        self,
        file_path: Path,
        format_type: str,
        details: Optional[str] = None,
    ):
        """
        Initialize config format error.

        Args:
            file_path: Path to file with format error
            format_type: Expected format (JSON, YAML, etc.)
            details: Optional error details (line/column info)
        """
        message = f"Invalid {format_type} format in {file_path}"

        if details:
            message += f"\n{details}"

        suggestion = (
            f"Check {format_type} syntax in {file_path}\n"
            f"Use a validator or linter to identify syntax errors."
        )

        super().__init__(message, suggestion)
