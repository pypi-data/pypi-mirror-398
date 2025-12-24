"""
UI components for Claude Code Orchestrator Kit.

Provides rich console output with colors, formatting, and progress indicators.
"""

from rich.console import Console as RichConsole
from rich.theme import Theme
from typing import Optional


# Custom theme for Claude Code Orchestrator Kit
ORCHESTRATOR_THEME = Theme(
    {
        "info": "cyan",
        "success": "bold green",
        "warning": "bold yellow",
        "error": "bold red",
        "highlight": "bold blue",
        "dim": "dim",
        "prompt": "bold cyan",
        "header": "bold blue",
        "subheader": "blue",
        "code": "yellow",
        "path": "cyan",
        "value": "green",
    }
)


class Console:
    """
    Singleton console wrapper for consistent output formatting.

    Provides methods for common output patterns with proper styling.

    Examples:
        >>> from claux.ui import console
        >>> console.print_success("Operation completed!")
        >>> console.print_error("Something went wrong")
        >>> console.print_header("Agent Profiles")
    """

    _instance: Optional[RichConsole] = None

    @classmethod
    def get_console(cls) -> RichConsole:
        """
        Get singleton console instance.

        Returns:
            Rich Console instance with custom theme.
        """
        if cls._instance is None:
            # Use legacy_windows=False to avoid Unicode issues on Windows
            cls._instance = RichConsole(theme=ORCHESTRATOR_THEME, legacy_windows=False)
        return cls._instance

    @classmethod
    def print(cls, *args, **kwargs) -> None:
        """Print message to console."""
        cls.get_console().print(*args, **kwargs)

    @classmethod
    def print_success(cls, message: str) -> None:
        """
        Print success message in green.

        Args:
            message: Success message to display.
        """
        cls.get_console().print(f"[success][OK][/success] {message}")

    @classmethod
    def print_error(cls, message: str) -> None:
        """
        Print error message in red.

        Args:
            message: Error message to display.
        """
        cls.get_console().print(f"[error][ERROR][/error] {message}")

    @classmethod
    def print_warning(cls, message: str) -> None:
        """
        Print warning message in yellow.

        Args:
            message: Warning message to display.
        """
        cls.get_console().print(f"[warning][WARN][/warning] {message}")

    @classmethod
    def print_info(cls, message: str) -> None:
        """
        Print info message in cyan.

        Args:
            message: Info message to display.
        """
        cls.get_console().print(f"[info][INFO][/info] {message}")

    @classmethod
    def print_header(cls, title: str) -> None:
        """
        Print header with separator line.

        Args:
            title: Header title to display.
        """
        console = cls.get_console()
        console.print()
        console.rule(title, style="header")
        console.print()

    @classmethod
    def print_subheader(cls, title: str) -> None:
        """
        Print subheader without separator.

        Args:
            title: Subheader title to display.
        """
        cls.get_console().print(f"\n[subheader]{title}[/subheader]")

    @classmethod
    def print_key_value(cls, key: str, value: str, indent: int = 0) -> None:
        """
        Print key-value pair with formatting.

        Args:
            key: Key name to display.
            value: Value to display.
            indent: Number of spaces to indent (default: 0).
        """
        indent_str = " " * indent
        cls.get_console().print(f"{indent_str}[dim]{key}:[/dim] [value]{value}[/value]")

    @classmethod
    def print_path(cls, label: str, path: str, indent: int = 0) -> None:
        """
        Print path with formatting.

        Args:
            label: Label for the path.
            path: Path to display.
            indent: Number of spaces to indent (default: 0).
        """
        indent_str = " " * indent
        cls.get_console().print(f"{indent_str}[dim]{label}:[/dim] [path]{path}[/path]")

    @classmethod
    def print_separator(cls) -> None:
        """Print horizontal separator line."""
        cls.get_console().rule(style="dim")

    @classmethod
    def confirm(cls, message: str, default: bool = False) -> bool:
        """
        Prompt user for yes/no confirmation.

        Args:
            message: Confirmation message to display.
            default: Default value if user presses Enter.

        Returns:
            True if user confirms, False otherwise.
        """
        from rich.prompt import Confirm

        return Confirm.ask(message, default=default, console=cls.get_console())

    @classmethod
    def prompt(cls, message: str, default: str = "") -> str:
        """
        Prompt user for text input.

        Args:
            message: Prompt message to display.
            default: Default value if user presses Enter.

        Returns:
            User input string.
        """
        from rich.prompt import Prompt

        return Prompt.ask(message, default=default, console=cls.get_console())


# Singleton instance for easy import
console = Console()


__all__ = ["Console", "console", "ORCHESTRATOR_THEME"]
