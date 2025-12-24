"""
Interactive menu system for Claux CLI.

Provides a rich, user-friendly terminal interface.
"""

import os
import typer
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.separator import Separator
from rich.console import Console

from claux.i18n import t
from claux.core.context import detect_project_context
from claux.ui.industrial_theme import (
    IndustrialIcons as Icons,
    NOTHING_THEME,
)

# Import all functions from new modules
from claux.commands.interactive_ui import (
    get_system_info,
    show_banner,
    show_help_footer,
    show_breadcrumbs,
)
from claux.commands.interactive_menus import (
    mcp_menu,
    agent_profiles_menu,
    language_menu,
    config_menu,
)
from claux.commands.interactive_launcher import launch_claude_code
from claux.commands.interactive_install import (
    create_pre_install_backup,
    rollback_installation,
    perform_installation,
    smart_install,
)
from claux.commands.interactive_builder import (
    build_quick_actions,
    build_menu_choices,
)

# Fix Windows console encoding
if os.name == "nt":
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleOutputCP(65001)  # UTF-8
    except Exception:
        pass

app = typer.Typer(help="Interactive mode")
console = Console(force_terminal=True, legacy_windows=False, theme=NOTHING_THEME)

# Global flag to show banner only once
_banner_shown = False


# ============================================================================
# Quick Action Handlers
# ============================================================================


def quick_install_claux(context):
    """Install Claux in current project."""
    success = smart_install(context)
    if success:
        console.print()
        typer.pause(t("cli.common.press_enter"))


def quick_change_profile(context):
    """Change agent profile."""
    agent_profiles_menu()


def quick_switch_mcp(context):
    """Switch MCP configuration."""
    mcp_menu()


def quick_update_claux(context):
    """Update Claux files."""
    success = smart_install(context)  # Reuse smart_install for upgrades
    if success:
        console.print()
        typer.pause(t("cli.common.press_enter"))


# ============================================================================
# Setup Wizard for Uninitialized Projects
# ============================================================================


def show_setup_wizard(context):
    """
    Show setup wizard for projects without Claux installation.

    This provides a guided setup experience instead of an empty menu.

    Args:
        context: ProjectContext with current directory status

    Returns:
        str: "exit" to exit the application, None to continue
    """
    console.clear()

    # Show banner with warning
    show_banner(context, force=True)

    # Explain the situation
    console.print(
        f"[bold yellow]{Icons.WARNING}  {t('cli.interactive.setup_title')}[/bold yellow]\n"
    )

    if not context.is_git:
        # Not a git repository - limited functionality
        console.print(f"[dim]{t('cli.interactive.setup_not_git')}[/dim]")
        console.print(f"[dim]{t('cli.interactive.setup_git_required')}[/dim]\n")

        choices = [
            Choice("doctor", f"{Icons.INFO}  {t('cli.interactive.setup_doctor')}"),
            Choice("help", f"{Icons.HELP}  {t('cli.interactive.setup_help')}"),
            Separator(),
            Choice("exit", f"{Icons.ARROW_LEFT}  {t('cli.interactive.exit')} (q)"),
        ]
    else:
        # Git repository without Claux - offer installation
        console.print(f"[dim]{t('cli.interactive.setup_install_prompt')}[/dim]\n")

        choices = [
            Choice("install", f"{Icons.LAUNCH}  {t('cli.interactive.setup_install_claux')}"),
            Separator(),
            Choice("doctor", f"{Icons.INFO}  {t('cli.interactive.setup_doctor')}"),
            Choice("help", f"{Icons.HELP}  {t('cli.interactive.setup_help')}"),
            Separator(),
            Choice("exit", f"{Icons.ARROW_LEFT}  {t('cli.interactive.exit')} (q)"),
        ]

    show_help_footer()

    try:
        action = inquirer.select(
            message=t("cli.interactive.select_option"),
            choices=choices,
            pointer=">",
        ).execute()

        if action == "q":
            action = "exit"

    except KeyboardInterrupt:
        return "exit"

    # Handle actions
    if action == "exit":
        return "exit"
    elif action == "install":
        success = smart_install(context)
        if success:
            console.print()
            console.print(
                f"[bold green]{t('cli.interactive.setup_install_success')}[/bold green]\n"
            )
            console.print(f"[dim]{t('cli.interactive.setup_next_steps')}[/dim]")
            console.print(f"[dim]  1. {t('cli.interactive.setup_step_mcp')}[/dim]")
            console.print(f"[dim]  2. {t('cli.interactive.setup_step_profile')}[/dim]")
            console.print(f"[dim]  3. {t('cli.interactive.setup_step_launch')}[/dim]\n")
            typer.pause(t("cli.common.press_enter"))
            return None  # Return to main menu (now with Claux installed)
        else:
            typer.pause(t("cli.common.press_enter"))
            return None
    elif action == "doctor":
        console.print(f"\n[yellow]{t('cli.interactive.feature_soon')}[/yellow]\n")
        typer.pause(t("cli.common.press_enter"))
        return None
    elif action == "help":
        console.print(
            f"\n[bold]{t('cli.interactive.help_title')}:[/bold] {t('cli.interactive.help_visit')}\n"
        )
        typer.pause(t("cli.common.press_enter"))
        return None

    return None


# ============================================================================
# Main Menu
# ============================================================================


@app.command()
def menu():
    """Launch context-aware interactive menu."""
    while True:
        # Detect context at each iteration
        context = detect_project_context()

        # IMPORTANT: If Claux is not installed, show setup wizard instead of empty menu
        if not context.has_claux:
            result = show_setup_wizard(context)
            if result == "exit":
                console.print(f"\n[bold cyan]{t('cli.interactive.goodbye')}[/bold cyan]\n")
                break
            # If setup wizard returns None, loop again (context may have changed after install)
            continue

        # Show context-aware banner (only for initialized projects)
        console.clear()
        show_banner(context)
        console.print(f"[bold cyan]{t('cli.interactive.menu_title')}[/bold cyan]\n")
        show_help_footer()

        # Build dynamic menu based on context
        choices = build_menu_choices(context)

        # Show menu
        try:
            action = inquirer.select(
                message=t("cli.interactive.select_option"),
                choices=choices,
                pointer=">",
            ).execute()

            # Handle keyboard shortcuts
            if action == "q":
                action = "exit"

        except KeyboardInterrupt:
            console.print(f"\n[bold cyan]{t('cli.interactive.goodbye')}[/bold cyan]\n")
            break
        except Exception:
            # Fallback for Cygwin and other incompatible terminals
            console.print(f"[yellow]!  {t('cli.interactive.unsupported_terminal')}[/yellow]")
            console.print(f"[dim]{t('cli.interactive.try_different_terminal')}[/dim]\n")
            typer.pause()
            continue

        # Route to handlers
        if action == "exit":
            console.print(f"\n[bold cyan]{t('cli.interactive.goodbye')}[/bold cyan]\n")
            break

        # Main actions
        elif action == "launch":
            result = launch_claude_code()
            if result == "exit_all":
                console.print(f"\n[bold cyan]{t('cli.interactive.goodbye')}[/bold cyan]\n")
                break
        elif action == "install":
            quick_install_claux(context)
        elif action == "update_claux":
            quick_update_claux(context)
        elif action == "change_profile":
            quick_change_profile(context)
        elif action == "switch_mcp":
            quick_switch_mcp(context)

        # Configuration
        elif action == "mcp":
            mcp_menu()
        elif action == "agents":
            agent_profiles_menu()

        # Settings
        elif action == "config":
            config_menu()


# ============================================================================
# Re-exports for backward compatibility
# ============================================================================

__all__ = [
    "menu",
    "get_system_info",
    "show_banner",
    "show_help_footer",
    "show_breadcrumbs",
    "mcp_menu",
    "agent_profiles_menu",
    "language_menu",
    "config_menu",
    "launch_claude_code",
    "create_pre_install_backup",
    "rollback_installation",
    "perform_installation",
    "smart_install",
    "build_quick_actions",
    "build_menu_choices",
    "show_setup_wizard",
]


if __name__ == "__main__":
    app()
