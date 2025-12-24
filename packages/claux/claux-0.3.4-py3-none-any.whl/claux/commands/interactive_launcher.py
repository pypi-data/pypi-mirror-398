"""
Claude Code launcher functionality.

Handles launching Claude Code with current configuration and exit behavior.
"""

import os
import shutil
import subprocess
import typer
from InquirerPy import inquirer
from rich.console import Console
from rich.table import Table

from claux.i18n import t
from claux.core.user_config import get_config
from claux.ui.industrial_theme import (
    IndustrialIcons as Icons,
    NOTHING_THEME,
)

console = Console(force_terminal=True, legacy_windows=False, theme=NOTHING_THEME)


def launch_claude_code():
    """Launch Claude Code with current configuration.

    Returns:
        str: "exit_all" if should exit claux after Claude Code closes, None otherwise
    """
    from claux.core.mcp import get_active_config
    from claux.core.profiles import get_active_profile

    console.clear()
    console.print(
        f"[bold cyan]{t('cli.interactive.launch_title')}[/bold cyan] [dim]({t('cli.interactive.launch_breadcrumb')})[/dim]\n"
    )
    from claux.commands.interactive_ui import show_help_footer
    show_help_footer()

    # Check if claude command exists
    claude_path = shutil.which("claude")
    if not claude_path:
        console.print(f"[red]✗[/red] {t('cli.interactive.launch_not_found')}")
        console.print(f"[dim]{t('cli.interactive.launch_install_hint')}[/dim]\n")
        typer.pause(t("cli.common.press_enter"))
        return None

    # Get current configuration
    mcp_config = get_active_config() or "none"
    profile = get_active_profile() or "all agents"

    # Show current configuration
    console.print(f"[bold]{t('cli.interactive.launch_current_config')}[/bold]\n")

    config_table = Table(
        show_header=False,
        border_style="dim",
        padding=(0, 1),
    )
    config_table.add_column(style="cyan", width=20)
    config_table.add_column(style="white")

    config_table.add_row(f"{Icons.MCP} MCP Config:", f"[yellow]{mcp_config}[/yellow]")
    config_table.add_row(f"{Icons.AGENT} Agent Profile:", f"[green]{profile}[/green]")
    config_table.add_row(f"{Icons.PATH} Directory:", f"[dim]{os.getcwd()}[/dim]")
    config_table.add_row(f"{Icons.CONFIG} Claude CLI:", f"[dim]{claude_path}[/dim]")

    console.print(config_table)
    console.print()

    # Confirm launch
    try:
        confirm = inquirer.confirm(
            message=t("cli.interactive.launch_confirm"),
            default=True,
        ).execute()

        if not confirm:
            return None

        console.print(f"\n[cyan]{t('cli.interactive.launch_starting')}[/cyan]")
        console.print()

        # Launch Claude Code
        try:
            # Check user preference for exit behavior
            config = get_config()
            exit_after_close = config.get("claude.exit_after_close", True)

            # On Windows, use the current console
            if os.name == "nt":
                subprocess.run([claude_path], check=False)
                # After Claude Code exits, check if should exit claux too
                if exit_after_close:
                    return "exit_all"
                else:
                    return None
            else:
                # On Unix-like systems
                if exit_after_close:
                    # Replace the current process completely
                    os.execvp(claude_path, [claude_path])
                else:
                    # Run as subprocess to return to menu
                    subprocess.run([claude_path], check=False)
                    return None
        except Exception as e:
            console.print(f"\n[red]✗[/red] {t('cli.interactive.launch_error', error=str(e))}\n")
            typer.pause(t("cli.common.press_enter"))
            return None

    except KeyboardInterrupt:
        console.print()
        return None
