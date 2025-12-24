"""
Backup and restore commands for Claude Code Orchestrator Kit.

Provides backup/restore functionality for configuration files.
"""

import typer
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from rich.table import Table

from claux.core.config import get_config
from claux.ui import Console


app = typer.Typer(help="Backup and restore orchestrator configuration")


def get_backup_dir(config) -> Path:
    """Get the backup directory path."""
    backup_dir = config.claude_dir / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


@app.command("create")
def create_backup(
    name: Optional[str] = typer.Option(
        None, "--name", "-n", help="Backup name (default: timestamp)"
    ),
    output_dir: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output directory (default: .claude/backups)"
    ),
):
    """
    Create a backup of current configuration.

    Backs up:
    - .claude/settings.local.json (if exists)
    - .claude/.active-agent-profile (if exists)
    - .mcp.json (active MCP config)
    - .claude/agent-profiles/custom/ (custom profiles)

    Creates timestamped backup directory with metadata.json
    """
    try:
        config = get_config()
    except FileNotFoundError as e:
        Console.print_error(str(e))
        raise typer.Exit(1)

    Console.print_info("Creating backup...")
    Console.print()

    # Generate backup name
    if name is None:
        name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Determine output directory
    if output_dir is None:
        backup_root = get_backup_dir(config)
    else:
        backup_root = Path(output_dir).resolve()
        backup_root.mkdir(parents=True, exist_ok=True)

    backup_path = backup_root / name

    # Check if backup already exists
    if backup_path.exists():
        Console.print_error(f"Backup already exists: {backup_path}")
        raise typer.Exit(1)

    # Create backup directory
    backup_path.mkdir(parents=True, exist_ok=True)

    # Track backed up files
    backed_up_files = []

    try:
        # Backup settings.local.json
        if config.settings_file.exists():
            dest = backup_path / "settings.local.json"
            shutil.copy2(config.settings_file, dest)
            backed_up_files.append("settings.local.json")

        # Backup active profile marker
        if config.active_profile_file.exists():
            dest = backup_path / ".active-agent-profile"
            shutil.copy2(config.active_profile_file, dest)
            backed_up_files.append(".active-agent-profile")

        # Backup .mcp.json
        mcp_file = config.repo_root / ".mcp.json"
        if mcp_file.exists():
            dest = backup_path / ".mcp.json"
            shutil.copy2(mcp_file, dest)
            backed_up_files.append(".mcp.json")

        # Backup custom profiles
        custom_profiles_dir = config.agent_profiles_dir / "custom"
        if custom_profiles_dir.exists():
            custom_profiles = list(custom_profiles_dir.glob("*.profile.json"))
            if custom_profiles:
                dest_custom = backup_path / "custom-profiles"
                dest_custom.mkdir(parents=True, exist_ok=True)
                for profile_file in custom_profiles:
                    shutil.copy2(profile_file, dest_custom / profile_file.name)
                backed_up_files.append(f"{len(custom_profiles)} custom profiles")

        # Create metadata
        metadata = {
            "name": name,
            "created": datetime.now().isoformat(),
            "files": backed_up_files,
            "repo_root": str(config.repo_root),
        }

        metadata_file = backup_path / "metadata.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
            f.write("\n")

        # Show success
        Console.print_success(f"Backup created: {name}")
        Console.print()
        Console.print_path("  Location", str(backup_path), indent=2)
        Console.print_subheader("  Files backed up:")
        for file_name in backed_up_files:
            Console.print(f"    [green]{file_name}[/green]")
        Console.print()
        Console.print_info(f"Restore with: [code]claux backup restore {name}[/code]")
        Console.print()

    except Exception as e:
        # Clean up partial backup
        if backup_path.exists():
            shutil.rmtree(backup_path)
        Console.print_error(f"Failed to create backup: {e}")
        raise typer.Exit(1)


@app.command("list")
def list_backups():
    """List all available backups."""
    try:
        config = get_config()
    except FileNotFoundError as e:
        Console.print_error(str(e))
        raise typer.Exit(1)

    backup_root = get_backup_dir(config)

    # Find all backups
    backups = []
    for backup_dir in backup_root.iterdir():
        if not backup_dir.is_dir():
            continue

        metadata_file = backup_dir / "metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                backups.append(
                    {
                        "name": metadata.get("name", backup_dir.name),
                        "created": metadata.get("created", "Unknown"),
                        "files": len(metadata.get("files", [])),
                    }
                )
            except Exception:
                # Skip invalid metadata
                pass

    if not backups:
        Console.print_warning("No backups found")
        Console.print()
        Console.print_info("Create a backup with:")
        Console.print("  [code]claux backup create[/code]", style="dim")
        Console.print()
        return

    # Sort by creation date (newest first)
    backups.sort(key=lambda b: b["created"], reverse=True)

    # Create table
    table = Table(
        title="Available Backups",
        show_header=True,
        header_style="bold blue",
        border_style="dim",
    )
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Date", style="white")
    table.add_column("Files", style="green", justify="right")

    for backup in backups:
        # Format date
        try:
            created_dt = datetime.fromisoformat(backup["created"])
            date_str = created_dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            date_str = backup["created"]

        table.add_row(backup["name"], date_str, str(backup["files"]))

    Console.print()
    Console.get_console().print(table)
    Console.print()
    Console.print_info("Restore with: [code]claux backup restore <name>[/code]")
    Console.print()


@app.command("restore")
def restore_backup(
    backup_name: str = typer.Argument(..., help="Backup name to restore"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite without confirmation"),
):
    """
    Restore configuration from a backup.

    Restores:
    - settings.local.json
    - .active-agent-profile
    - .mcp.json
    - custom profiles
    """
    try:
        config = get_config()
    except FileNotFoundError as e:
        Console.print_error(str(e))
        raise typer.Exit(1)

    backup_root = get_backup_dir(config)
    backup_path = backup_root / backup_name

    # Check if backup exists
    if not backup_path.exists():
        Console.print_error(f"Backup not found: {backup_name}")
        Console.print()
        Console.print_info("List available backups with:")
        Console.print("  [code]claux backup list[/code]", style="dim")
        Console.print()
        raise typer.Exit(1)

    # Load metadata
    metadata_file = backup_path / "metadata.json"
    if not metadata_file.exists():
        Console.print_error("Invalid backup: metadata.json not found")
        raise typer.Exit(1)

    try:
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    except Exception as e:
        Console.print_error(f"Failed to load backup metadata: {e}")
        raise typer.Exit(1)

    # Show what will be restored
    Console.print_info(f"Restoring backup: {backup_name}")
    Console.print()
    Console.print_subheader("  Files to restore:")
    for file_name in metadata.get("files", []):
        Console.print(f"    [cyan]{file_name}[/cyan]")
    Console.print()

    # Confirm restore
    if not force:
        if not Console.confirm("Proceed with restore?", default=False):
            Console.print_warning("Restore cancelled")
            raise typer.Exit(0)

    # Restore files
    restored_files = []

    try:
        # Restore settings.local.json
        source = backup_path / "settings.local.json"
        if source.exists():
            shutil.copy2(source, config.settings_file)
            restored_files.append("settings.local.json")

        # Restore active profile marker
        source = backup_path / ".active-agent-profile"
        if source.exists():
            shutil.copy2(source, config.active_profile_file)
            restored_files.append(".active-agent-profile")

        # Restore .mcp.json
        source = backup_path / ".mcp.json"
        if source.exists():
            dest = config.repo_root / ".mcp.json"
            shutil.copy2(source, dest)
            restored_files.append(".mcp.json")

        # Restore custom profiles
        source_custom = backup_path / "custom-profiles"
        if source_custom.exists():
            dest_custom = config.agent_profiles_dir / "custom"
            dest_custom.mkdir(parents=True, exist_ok=True)

            profile_files = list(source_custom.glob("*.profile.json"))
            for profile_file in profile_files:
                shutil.copy2(profile_file, dest_custom / profile_file.name)

            restored_files.append(f"{len(profile_files)} custom profiles")

        # Show success
        Console.print()
        Console.print_success("Restore completed!")
        Console.print()
        Console.print_subheader("  Restored files:")
        for file_name in restored_files:
            Console.print(f"    [green]{file_name}[/green]")
        Console.print()
        Console.print_warning("Restart Claude Code for changes to take effect")
        Console.print()

    except Exception as e:
        Console.print_error(f"Failed to restore backup: {e}")
        raise typer.Exit(1)


@app.command("delete")
def delete_backup(
    backup_name: str = typer.Argument(..., help="Backup name to delete"),
):
    """Delete a backup."""
    try:
        config = get_config()
    except FileNotFoundError as e:
        Console.print_error(str(e))
        raise typer.Exit(1)

    backup_root = get_backup_dir(config)
    backup_path = backup_root / backup_name

    # Check if backup exists
    if not backup_path.exists():
        Console.print_error(f"Backup not found: {backup_name}")
        raise typer.Exit(1)

    # Confirm deletion
    Console.print_warning(f"Delete backup: {backup_name}?")
    if not Console.confirm("This cannot be undone", default=False):
        Console.print_info("Deletion cancelled")
        raise typer.Exit(0)

    # Delete backup
    try:
        shutil.rmtree(backup_path)
        Console.print_success(f"Backup deleted: {backup_name}")
        Console.print()
    except Exception as e:
        Console.print_error(f"Failed to delete backup: {e}")
        raise typer.Exit(1)
