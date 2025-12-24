"""
Interactive UI components for banner, help, and breadcrumbs.

Provides system info display and visual elements for the interactive menu.
"""

import sys
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from claux import __version__
from claux.i18n import get_language, t
from claux.ui.industrial_theme import (
    IndustrialIcons as Icons,
    get_industrial_box,
    CLAUX_LOGO_INDUSTRIAL,
    NOTHING_THEME,
)

# Fix Windows console encoding
if os.name == "nt":
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleOutputCP(65001)  # UTF-8
    except Exception:
        pass

console = Console(force_terminal=True, legacy_windows=False, theme=NOTHING_THEME)


def get_system_info():
    """Get system status information."""
    try:
        from claux.core.mcp import get_active_config
        from claux.core.profiles import get_active_profile

        mcp_config = get_active_config()
        profile = get_active_profile()
        py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        return {
            "python": py_version,
            "mcp": mcp_config or "none",
            "profile": profile or "none",
            "language": get_language(),
        }
    except Exception:
        return {
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "mcp": "none",
            "profile": "none",
            "language": get_language(),
        }


def show_banner(context, force=False):
    """Display context-aware welcome banner with project status."""
    # Import _banner_shown from interactive.py to maintain state
    from claux.commands import interactive

    if interactive._banner_shown and not force:
        return

    interactive._banner_shown = True

    # Get system info (for Python version and language)
    info = get_system_info()

    # Build status line based on context
    current_dir = context.git_root if context.git_root else Path.cwd()

    # Build banner content with monochrome orange logo (Claude brand)
    banner_lines = []

    # Industrial ASCII logo in Claude brand orange, version and subtitle in white
    logo_line1 = f"[claude]█▀▀ █   ▄▀█ █ █ ▀▄▀[/claude]  [white]v{__version__}[/white]"
    logo_line2 = f"[claude]█▄▄ █▄▄ █▀█ █▄█ █ █[/claude]"

    banner_lines.append(logo_line1)
    banner_lines.append(logo_line2)
    banner_lines.append(f"[white]{t('cli.interactive.banner_subtitle')}[/white]")
    banner_lines.append("")  # Empty line

    # Project path (styled with path color)
    banner_lines.append(f"[dim]{Icons.PATH}[/dim] [path]{current_dir}[/path]")

    # Status line - show only when there are problems
    if context.is_git and context.has_claux:
        # Everything OK - no status needed (UNIX philosophy: silence is golden)
        pass
    elif context.is_git:
        # Git OK but Claux not installed - show warning
        status = f"{Icons.WARNING} {t('cli.interactive.banner_not_installed')}"
        banner_lines.append(f"[warning]{status}[/warning]")
    else:
        # Not a git repository - show warning
        status = f"{Icons.WARNING} {t('cli.interactive.banner_not_git')}"
        banner_lines.append(f"[warning.soft]{status}[/warning.soft]")

    # Combined info line with adaptive width
    terminal_width = console.width

    # MCP and Profile info (always show when Claux installed)
    if context.is_git and context.has_claux:
        mcp_str = context.mcp_config or "none"
        profile_str = context.agent_profile or "none"

        # Start with MCP and Profile (always shown)
        # Use accent.soft for active config, dim for inactive
        mcp_style = "accent.soft" if mcp_str != "none" else "subdued"
        profile_style = "accent.soft" if profile_str != "none" else "subdued"

        info_parts = [
            f"[{mcp_style}]{Icons.MCP} {mcp_str}[/{mcp_style}]",
            f"[{profile_style}]{Icons.PROFILE} {profile_str}[/{profile_style}]"
        ]

        # Add Python and Language based on terminal width
        if terminal_width > 100:
            # Wide terminal: show full info
            info_parts.append(f"[secondary]{Icons.LANGUAGE} Python {info['python']}[/secondary]")
            info_parts.append(f"[secondary]{Icons.LOCALE} {info['language'].upper()}[/secondary]")
        elif terminal_width > 80:
            # Medium terminal: shorten Python to Py
            py_short = f"{info['python'].rsplit('.', 1)[0]}"  # 3.14.0 -> 3.14
            info_parts.append(f"[secondary]{Icons.LANGUAGE} Py {py_short}[/secondary]")
            info_parts.append(f"[secondary]{Icons.LOCALE} {info['language'].upper()}[/secondary]")
        # else: narrow terminal, don't show Python/Language

        banner_lines.append(f"[dim]{' · '.join(info_parts)}[/dim]")
    else:
        # Not installed - show only system info
        if terminal_width > 80:
            sys_info = f"[secondary]{Icons.LANGUAGE} Python {info['python']}[/secondary]   [secondary]{Icons.LOCALE} {info['language'].upper()}[/secondary]"
        else:
            sys_info = f"[secondary]{Icons.LANGUAGE} Py {info['python'].rsplit('.', 1)[0]}[/secondary]   [secondary]{Icons.LOCALE} {info['language'].upper()}[/secondary]"
        banner_lines.append(f"{sys_info}")

    banner_panel = Panel(
        "\n".join(banner_lines),
        box=get_industrial_box(),
        border_style="primary",
        padding=(1, 2)
    )

    console.print()
    console.print(banner_panel)
    console.print()


def show_help_footer():
    """Show compact help footer with keyboard shortcuts."""
    # Use new color scheme for keys
    help_text = (
        f"[tertiary]{t('cli.interactive.keys_label')}[/tertiary] "
        f"[key]↑↓[/key] [dim]{t('cli.interactive.keys_navigate')}[/dim] · "
        f"[key]↵[/key] [dim]{t('cli.interactive.keys_select')}[/dim] · "
        f"[key]q[/key] [dim]{t('cli.interactive.keys_quit')}[/dim] · "
        f"[key]h[/key] [dim]{t('cli.interactive.keys_help')}[/dim] · "
        f"[key]Ctrl+C[/key] [dim]{t('cli.interactive.keys_exit')}[/dim]"
    )
    console.print(help_text + "\n")


def show_breadcrumbs(path: str):
    """Show navigation breadcrumbs with industrial styling."""
    breadcrumb = Text()
    breadcrumb.append("┌─ ", style="subdued")
    breadcrumb.append(f"{Icons.NESTED} ", style="tertiary")

    parts = path.split(" > ")
    for i, part in enumerate(parts):
        if i > 0:
            breadcrumb.append(" ", style="")
            breadcrumb.append(Icons.ARROW_RIGHT, style="separator")
            breadcrumb.append(" ", style="")

        # Last part is accent (current location), others are dim
        style = "accent.soft" if i == len(parts) - 1 else "tertiary"
        breadcrumb.append(part, style=style)

    console.print(breadcrumb)
    console.print()
