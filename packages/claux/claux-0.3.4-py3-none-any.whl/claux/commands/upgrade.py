"""
Upgrade command for Claux.

Provides automatic update checking and upgrading functionality.
"""

import typer
from rich.console import Console
from rich.panel import Panel

from claux import __version__
from claux.core.updater import check_for_updates, perform_upgrade, clear_update_cache
from claux.i18n import t

app = typer.Typer(help="Check for updates and upgrade Claux")
console = Console()


@app.command()
def check(
    no_cache: bool = typer.Option(False, "--no-cache", help="Bypass cache and check PyPI directly")
):
    """
    Check for available updates without installing.
    """
    console.print(f"\n[bold cyan]{t('cli.upgrade.checking')}[/bold cyan]")
    console.print(f"{t('cli.upgrade.current_version', version=__version__)}\n")

    # Check for updates
    has_update, latest_version, error = check_for_updates(use_cache=not no_cache)

    if error:
        console.print(f"[red]{t('cli.upgrade.check_failed', error=error)}[/red]\n")
        raise typer.Exit(1)

    if has_update and latest_version:
        # Show update available
        panel = Panel(
            f"[green]{t('cli.upgrade.update_available')}[/green]\n\n"
            f"{t('cli.upgrade.current')}: [yellow]{__version__}[/yellow]\n"
            f"{t('cli.upgrade.latest')}: [green]{latest_version}[/green]\n\n"
            f"{t('cli.upgrade.upgrade_hint')}",
            title=f"[bold green]{t('cli.upgrade.new_version_title')}[/bold green]",
            border_style="green",
        )
        console.print(panel)
    else:
        console.print(f"[green]{t('cli.upgrade.up_to_date')}[/green]\n")


@app.command()
def install(yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt")):
    """
    Install the latest version of Claux.
    """
    console.print(f"\n[bold cyan]{t('cli.upgrade.checking')}[/bold cyan]")

    # Check for updates
    has_update, latest_version, error = check_for_updates(use_cache=False)

    if error:
        console.print(f"[red]{t('cli.upgrade.check_failed', error=error)}[/red]\n")
        raise typer.Exit(1)

    if not has_update:
        console.print(f"[green]{t('cli.upgrade.up_to_date')}[/green]\n")
        return

    # Show what will be upgraded
    console.print(f"\n{t('cli.upgrade.current')}: [yellow]{__version__}[/yellow]")
    console.print(f"{t('cli.upgrade.latest')}: [green]{latest_version}[/green]\n")

    # Confirm upgrade
    if not yes:
        confirm = typer.confirm(t("cli.upgrade.confirm"))
        if not confirm:
            console.print(f"\n[yellow]{t('cli.common.cancel')}[/yellow]\n")
            raise typer.Exit(0)

    # Perform upgrade
    console.print(f"\n[bold cyan]{t('cli.upgrade.upgrading')}[/bold cyan]")

    success, message = perform_upgrade()

    if success:
        console.print(f"[green]{t('cli.upgrade.success', version=latest_version)}[/green]")
        console.print(f"\n[dim]{t('cli.upgrade.restart_hint')}[/dim]\n")
    else:
        console.print(f"[red]{t('cli.upgrade.failed', error=message)}[/red]\n")
        raise typer.Exit(1)


@app.command()
def clear_cache():
    """
    Clear the update check cache.
    """
    clear_update_cache()
    console.print(f"[green]{t('cli.upgrade.cache_cleared')}[/green]\n")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    Update management commands.

    Check for updates and install the latest version of Claux.

    Running 'claux upgrade' without a subcommand will check and install updates.
    """
    # If no subcommand is invoked, run install (most common use case)
    if ctx.invoked_subcommand is None:
        ctx.invoke(install)


if __name__ == "__main__":
    app()
