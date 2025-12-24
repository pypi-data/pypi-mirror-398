"""
Unified UI theme and styling for Claux CLI.

Provides consistent, cross-platform, adaptive terminal UI.
"""

import os
import sys
import shutil
from typing import Optional, List
from rich.console import Console
from rich.theme import Theme
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.box import ROUNDED, ASCII

from claux.i18n import t


# Detect terminal capabilities
def get_terminal_width() -> int:
    """Get terminal width with fallback."""
    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return 80


def supports_unicode() -> bool:
    """Check if terminal supports Unicode."""
    # Check encoding
    encoding = sys.stdout.encoding or ""
    if "utf" in encoding.lower():
        return True

    # Windows specific check
    if sys.platform == "win32":
        # Windows Terminal and modern terminals support UTF-8
        if os.environ.get("WT_SESSION") or os.environ.get("TERM_PROGRAM"):
            return True
        return False

    return True


def get_box_style():
    """Get appropriate box style for terminal."""
    if supports_unicode():
        return ROUNDED
    return ASCII


# Unified color scheme
CLAUX_THEME = Theme(
    {
        "primary": "cyan bold",
        "secondary": "blue",
        "success": "green bold",
        "warning": "yellow",
        "error": "red bold",
        "info": "cyan",
        "dim": "dim",
        "highlight": "bold white",
        "accent": "magenta",
    }
)


# Icon sets (cross-platform compatible)
class Icons:
    """Cross-platform icon sets."""

    def __init__(self):
        self.unicode = supports_unicode()

    @property
    def success(self) -> str:
        return "[green]OK[/green]" if not self.unicode else "[green][*][/green]"

    @property
    def error(self) -> str:
        return "[red]FAIL[/red]" if not self.unicode else "[red][X][/red]"

    @property
    def warning(self) -> str:
        return "[yellow]WARN[/yellow]" if not self.unicode else "[yellow]![/yellow]"

    @property
    def info(self) -> str:
        return "[cyan]INFO[/cyan]" if not self.unicode else "[cyan]i[/cyan]"

    @property
    def arrow(self) -> str:
        return "->" if not self.unicode else "->"

    @property
    def bullet(self) -> str:
        return "*" if not self.unicode else "*"

    @property
    def check(self) -> str:
        return "[*]" if not self.unicode else "[*]"


# Global instances
icons = Icons()
console = Console(theme=CLAUX_THEME)


def create_banner(
    title: str, subtitle: Optional[str] = None, version: Optional[str] = None
) -> Panel:
    """
    Create a beautiful banner.

    Args:
        title: Main title
        subtitle: Optional subtitle
        version: Optional version string

    Returns:
        Rich Panel with banner
    """
    width = min(get_terminal_width() - 4, 60)

    content = f"[primary]{title}[/primary]"
    if version:
        content += f" [dim]v{version}[/dim]"
    if subtitle:
        content += f"\n[dim]{subtitle}[/dim]"

    return Panel(
        content,
        box=get_box_style(),
        border_style="primary",
        width=width,
    )


def create_table(
    title: str,
    columns: List[tuple],
    rows: List[tuple],
    show_header: bool = True,
) -> Table:
    """
    Create adaptive table.

    Args:
        title: Table title
        columns: List of (name, style, justify) tuples
        rows: List of row tuples
        show_header: Whether to show header

    Returns:
        Rich Table
    """
    width = get_terminal_width()

    table = Table(
        title=title,
        box=get_box_style(),
        show_header=show_header,
        width=min(width - 4, 120),
    )

    for col in columns:
        name, style = col[0], col[1] if len(col) > 1 else None
        justify = col[2] if len(col) > 2 else "left"
        table.add_column(name, style=style, justify=justify)

    for row in rows:
        table.add_row(*[str(cell) for cell in row])

    return table


def create_menu_panel(title: str, items: List[str]) -> Panel:
    """
    Create menu panel.

    Args:
        title: Menu title
        items: List of menu items

    Returns:
        Rich Panel
    """
    content = "\n".join(f"{icons.bullet} {item}" for item in items)

    return Panel(
        content,
        title=f"[primary]{title}[/primary]",
        box=get_box_style(),
        border_style="primary",
    )


def print_success(message: str):
    """Print success message."""
    console.print(f"{icons.success} {message}")


def print_error(message: str):
    """Print error message."""
    console.print(f"{icons.error} {message}")


def print_warning(message: str):
    """Print warning message."""
    console.print(f"{icons.warning} {message}")


def print_info(message: str):
    """Print info message."""
    console.print(f"{icons.info} {message}")


def print_section(title: str):
    """Print section header."""
    console.print(f"\n[primary]{title}[/primary]", style="bold")


def create_progress() -> Progress:
    """Create progress bar."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    )


def prompt_confirm(message: str, default: bool = False) -> bool:
    """
    Cross-platform confirm prompt.

    Args:
        message: Prompt message
        default: Default value

    Returns:
        User's choice
    """
    try:
        from InquirerPy import inquirer

        return inquirer.confirm(message=message, default=default).execute()
    except ImportError:
        # Fallback to simple input
        suffix = " [Y/n]" if default else " [y/N]"
        response = input(f"{message}{suffix}: ").lower().strip()
        if not response:
            return default
        return response in ("y", "yes", "да", "д")


def prompt_select(message: str, choices: List[tuple], default: Optional[str] = None):
    """
    Cross-platform select prompt.

    Args:
        message: Prompt message
        choices: List of (value, name) tuples
        default: Default value

    Returns:
        Selected value
    """
    try:
        from InquirerPy import inquirer
        from InquirerPy.base.control import Choice

        choice_objects = [Choice(value=v, name=n) for v, n in choices]
        return inquirer.select(
            message=message,
            choices=choice_objects,
            default=default,
        ).execute()
    except ImportError:
        # Fallback to numbered menu
        console.print(f"\n[primary]{message}[/primary]")
        for i, (value, name) in enumerate(choices, 1):
            console.print(f"  {i}. {name}")

        while True:
            try:
                choice = input(f"\nSelect (1-{len(choices)}): ").strip()
                idx = int(choice) - 1
                if 0 <= idx < len(choices):
                    return choices[idx][0]
            except (ValueError, IndexError):
                print_error("Invalid choice. Try again.")


def clear_screen():
    """Clear terminal screen (cross-platform)."""
    os.system("cls" if sys.platform == "win32" else "clear")


def pause(message: Optional[str] = None):
    """
    Pause and wait for user input.

    Args:
        message: Custom pause message
    """
    msg = message or t("cli.common.press_enter")
    try:
        input(f"\n{msg}")
    except KeyboardInterrupt:
        pass


# Color helpers
def colorize(text: str, color: str) -> str:
    """
    Colorize text.

    Args:
        text: Text to colorize
        color: Color name (success, error, warning, info, primary)

    Returns:
        Colored text
    """
    color_map = {
        "success": "green",
        "error": "red",
        "warning": "yellow",
        "info": "cyan",
        "primary": "cyan bold",
        "dim": "dim",
    }

    style = color_map.get(color, color)
    return f"[{style}]{text}[/{style}]"
