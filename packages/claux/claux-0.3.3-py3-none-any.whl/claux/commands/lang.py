"""
Language management commands for Claux.
"""

import typer
from rich.console import Console
from rich.table import Table

from claux.i18n import set_language, get_language, get_available_languages

app = typer.Typer(help="Manage language settings")
console = Console()


@app.command("list")
def list_languages():
    """List all available languages."""
    languages = get_available_languages()
    current = get_language()

    table = Table(title="Available Languages")
    table.add_column("Code", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Status", style="yellow")

    lang_names = {
        "en": "English",
        "ru": "Russian",
    }

    for lang in sorted(languages):
        status = "[*] Current" if lang == current else ""
        name = lang_names.get(lang, "Unknown")
        table.add_row(lang, name, status)

    console.print(table)


@app.command("set")
def set_lang(language: str = typer.Argument(..., help="Language code (e.g., 'en', 'ru')")):
    """
    Set the language for Claux CLI.

    This sets the CLAUX_LANG environment variable for the current session.
    To make it permanent, add it to your shell configuration (.bashrc, .zshrc, etc.):

    export CLAUX_LANG=ru
    """
    available = get_available_languages()

    if language not in available:
        console.print(f"[red]ERROR: Language '{language}' not available[/red]")
        console.print(f"\nAvailable languages: {', '.join(available)}")
        raise typer.Exit(1)

    set_language(language)
    console.print(f"[green]OK: Language set to: {language}[/green]")
    console.print("\n[yellow]Note:[/yellow] This only affects the current session.")
    console.print(
        f"\nTo make it permanent, add to your shell configuration:\n"
        f"  export CLAUX_LANG={language}"
    )


@app.command("current")
def show_current():
    """Show current language setting."""
    current = get_language()
    available = get_available_languages()

    console.print(f"[cyan]Current language:[/cyan] {current}")
    console.print(f"[cyan]Available languages:[/cyan] {', '.join(available)}")


if __name__ == "__main__":
    app()
