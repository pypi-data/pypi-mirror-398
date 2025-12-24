"""
Diagnostic tool for Claux.

Checks installation health and provides troubleshooting.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Tuple

import typer
from rich.console import Console
from rich.table import Table

from claux import __version__
from claux.i18n import get_language, t
from claux.core.updater import check_for_updates

app = typer.Typer(help="Diagnose installation and configuration")
console = Console()


def check_python_version() -> Tuple[bool, str]:
    """Check Python version."""
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    is_ok = sys.version_info >= (3, 8)
    return is_ok, version


def check_claux_installation() -> Tuple[bool, str]:
    """Check Claux installation."""
    try:
        import claux  # noqa: F401

        return True, __version__
    except ImportError:
        return False, "Not installed"


def check_dependencies() -> dict:
    """Check required dependencies."""
    deps = {
        "typer": False,
        "rich": False,
        "inquirerpy": False,
        "pyyaml": False,
        "questionary": False,
    }

    for dep in deps:
        try:
            __import__(dep)
            deps[dep] = True
        except ImportError:
            pass

    return deps


def check_config_files() -> dict:
    """Check configuration files."""
    config_dir = Path.home() / ".claux"
    config_file = config_dir / "config.yaml"

    return {
        "config_dir": config_dir.exists(),
        "config_file": config_file.exists(),
        "writable": (
            config_dir.is_dir() and os.access(config_dir, os.W_OK) if config_dir.exists() else False
        ),
    }


def check_git() -> Tuple[bool, str]:
    """Check git installation."""
    git_path = shutil.which("git")
    if git_path:
        try:
            result = subprocess.run(["git", "--version"], capture_output=True, text=True, timeout=5)
            version = result.stdout.strip()
            return True, version
        except Exception:
            return True, "Installed (version check failed)"
    return False, "Not found"


def check_claude_code() -> Tuple[bool, str]:
    """Check Claude Code CLI."""
    claude_path = shutil.which("claude")
    if claude_path:
        return True, claude_path
    return False, "Not found"


def check_updates() -> Tuple[bool, str]:
    """Check for available updates."""
    has_update, latest_version, error = check_for_updates(use_cache=True)

    if error:
        return False, f"Check failed: {error}"

    if has_update and latest_version:
        return True, f"v{latest_version} available"

    return True, "Up to date"


@app.command()
def check():
    """Run diagnostic checks."""
    console.print("\n[bold cyan]Claux Doctor - System Diagnostic[/bold cyan]\n")

    # Python version
    python_ok, python_ver = check_python_version()
    python_status = "[green]OK[/green]" if python_ok else "[red]FAIL[/red]"

    # Claux installation
    claux_ok, claux_ver = check_claux_installation()
    claux_status = "[green]OK[/green]" if claux_ok else "[red]FAIL[/red]"

    # Dependencies
    deps = check_dependencies()
    deps_ok = all(deps.values())
    deps_status = "[green]OK[/green]" if deps_ok else "[yellow]WARN[/yellow]"

    # Config files
    config = check_config_files()
    config_ok = config["config_dir"]
    config_status = "[green]OK[/green]" if config_ok else "[yellow]WARN[/yellow]"

    # Git
    git_ok, git_ver = check_git()
    git_status = "[green]OK[/green]" if git_ok else "[yellow]WARN[/yellow]"

    # Claude Code
    claude_ok, claude_path = check_claude_code()
    claude_status = "[green]OK[/green]" if claude_ok else "[yellow]WARN[/yellow]"

    # Updates
    update_ok, update_info = check_updates()
    update_status = "[yellow]UPDATE[/yellow]" if "available" in update_info else "[green]OK[/green]"

    # Create results table
    table = Table(title="Diagnostic Results")
    table.add_column("Component", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Details", style="dim")

    table.add_row("Python", python_status, python_ver)
    table.add_row("Claux", claux_status, claux_ver)
    table.add_row("Dependencies", deps_status, f"{sum(deps.values())}/{len(deps)} installed")
    table.add_row("Configuration", config_status, "~/.claux/")
    table.add_row("Git", git_status, git_ver if git_ok else "Not found")
    table.add_row("Claude Code", claude_status, claude_path if claude_ok else "Not found")
    table.add_row(t("cli.doctor.updates"), update_status, update_info)

    console.print(table)

    # Recommendations
    recommendations = []

    if not python_ok:
        recommendations.append("[WARN] Python 3.8+ is required. Please upgrade Python.")

    if not deps_ok:
        missing = [dep for dep, installed in deps.items() if not installed]
        recommendations.append(f"[WARN] Missing dependencies: {', '.join(missing)}")
        recommendations.append("       Run: pip install -e .")

    if not config_ok:
        recommendations.append(
            "[INFO] Configuration directory not found. It will be created on first use."
        )

    if not git_ok:
        recommendations.append("[WARN] Git not found. Some features may not work.")

    if not claude_ok:
        recommendations.append("[INFO] Claude Code CLI not detected. Make sure it's installed.")

    if "available" in update_info:
        version_num = update_info.split("v")[1].split(" ")[0]
        recommendations.append(f"[INFO] {t('cli.doctor.update_available', version=version_num)}")
        recommendations.append(f"       {t('cli.doctor.update_command')}")

    if recommendations:
        console.print("\n[bold yellow]Recommendations:[/bold yellow]\n")
        for rec in recommendations:
            console.print(f"  {rec}")
    else:
        console.print("\n[bold green]All checks passed! Your installation looks good.[/bold green]")

    # System info
    console.print("\n[bold]System Information:[/bold]")
    console.print(f"  OS: {sys.platform}")
    console.print(f"  Language: {get_language()}")
    console.print(f"  Config: {Path.home() / '.claux'}")

    console.print()


if __name__ == "__main__":
    app()
