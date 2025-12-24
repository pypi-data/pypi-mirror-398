"""
Main CLI entry point for Claux.

Token-efficient AI automation toolkit with TOON inter-agent communication.
"""

import os
import sys
import typer

from claux import __version__
from claux.commands import (
    agents,
    mcp,
    init,
    status,
    backup,
    wizard,
    lang,
    interactive,
    doctor,
    upgrade,
    stats,
)
from claux.i18n import t, get_language
from claux.core.updater import check_for_updates

# Fix Windows console encoding for UTF-8 support
if os.name == "nt":
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleOutputCP(65001)  # UTF-8
    except Exception:
        pass

# Ensure Python's stdout uses UTF-8 encoding
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


# Create main app
app = typer.Typer(
    name="claux",
    help="Claux - Token-efficient AI automation with TOON protocol",
    no_args_is_help=False,  # Allow interactive mode
    invoke_without_command=True,
)


# Register subcommands
app.add_typer(agents.app, name="agents")
app.add_typer(mcp.app, name="mcp")
app.add_typer(init.app, name="init")
app.add_typer(status.app, name="status")
app.add_typer(backup.app, name="backup")
app.add_typer(wizard.app, name="wizard")
app.add_typer(lang.app, name="lang")
app.add_typer(interactive.app, name="menu")
app.add_typer(doctor.app, name="doctor")
app.add_typer(upgrade.app, name="upgrade")
app.add_typer(stats.app, name="stats")


@app.callback()
def main(ctx: typer.Context):
    """
    Claux - Token-efficient AI automation with TOON protocol.

    Run without arguments to launch interactive mode.
    Use --help to see available commands.
    """
    # Check for updates (silent, uses cache, once per day)
    _check_for_updates_silently()

    # If no subcommand is invoked, launch interactive mode
    if ctx.invoked_subcommand is None:
        from claux.commands.interactive import menu

        menu()


def _check_for_updates_silently():
    """
    Check for updates silently and show notification if available.
    Uses cache to avoid checking more than once per day.
    """
    try:
        has_update, latest_version, _ = check_for_updates(use_cache=True)

        if has_update and latest_version:
            # Show subtle notification
            typer.echo(f"\n💡 {t('cli.upgrade.notification', version=latest_version)}")
            typer.echo(f"   {t('cli.upgrade.notification_hint')}\n")
    except Exception:
        # Silently ignore any errors during update check
        pass


@app.command()
def version():
    """Show version information."""
    typer.echo(t("cli.version.title", version=__version__))
    typer.echo(
        t(
            "cli.version.python",
            python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        )
    )
    typer.echo(t("cli.version.location", location=__file__))
    typer.echo(f"\nLanguage: {get_language()}")


if __name__ == "__main__":
    app()
