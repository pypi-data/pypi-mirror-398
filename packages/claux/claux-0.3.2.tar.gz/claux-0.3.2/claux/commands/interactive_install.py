"""
Smart installation and upgrade functionality with auto-backup.

Handles Claux installation, upgrades, backups, and rollbacks.
"""

import shutil
from pathlib import Path
from datetime import datetime
from rich.console import Console

from claux.core.user_config import get_config
from claux.ui.industrial_theme import NOTHING_THEME

console = Console(force_terminal=True, legacy_windows=False, theme=NOTHING_THEME)


def create_pre_install_backup():
    """
    Create automatic backup before installation/upgrade.

    Returns:
        Backup name if successful, None otherwise
    """
    from claux.commands.backup import BackupManager

    backup_name = datetime.now().strftime("pre-install_%Y-%m-%d_%H-%M-%S")

    try:
        config = get_config()
        manager = BackupManager(config)
        manager.create_backup(name=backup_name, output_dir=None)
        return backup_name
    except Exception as e:
        Console.print_error(f"Failed to create backup: {e}")
        return None


def rollback_installation(backup_name: str) -> bool:
    """
    Rollback installation using backup.

    Args:
        backup_name: Name of backup to restore

    Returns:
        True if rollback successful
    """
    from claux.commands.backup import BackupManager

    try:
        Console.print_info("Rolling back changes...")
        config = get_config()
        manager = BackupManager(config)
        manager.restore_backup(backup_name=backup_name, force=True)
        Console.print_success("Rollback successful")
        return True
    except Exception as e:
        Console.print_error(f"Rollback failed: {e}")
        return False


def perform_installation(upgrade: bool = False):
    """
    Perform actual installation of Claux files.

    Args:
        upgrade: Whether this is an upgrade (preserve custom files)

    Raises:
        Exception: If installation fails
    """
    from claux.commands.init import get_orchestrator_install_path

    # Get target directory (current git repo root)
    from claux.core.utils import find_git_root

    target_dir = find_git_root(Path.cwd())
    claude_dir = target_dir / ".claude"

    # Get source templates
    install_root = get_orchestrator_install_path()
    source_claude_dir = install_root / ".claude"

    if not source_claude_dir.exists():
        raise FileNotFoundError(f"Template directory not found: {source_claude_dir}")

    if upgrade:
        # UPGRADE: Remove old .claude but preserve custom files via backup
        if claude_dir.exists():
            # Remove old installation (backup already created)
            shutil.rmtree(claude_dir)

    # Copy new files
    shutil.copytree(source_claude_dir, claude_dir)

    # Update .gitignore
    gitignore_path = target_dir / ".gitignore"
    gitignore_entries = [
        ".tmp/",
        ".claude/settings.local.json",
        ".claude/.active-agent-profile",
        ".claude/backups/",
    ]

    if gitignore_path.exists():
        existing_content = gitignore_path.read_text(encoding="utf-8")
        new_entries = [e for e in gitignore_entries if e not in existing_content]

        if new_entries:
            with open(gitignore_path, "a", encoding="utf-8") as f:
                f.write("\n# Claude Code Orchestrator\n")
                f.write("\n".join(new_entries))
                f.write("\n")
    else:
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write("# Claude Code Orchestrator\n")
            f.write("\n".join(gitignore_entries))
            f.write("\n")


def smart_install(context) -> bool:
    """
    Smart installation with automatic backup and upgrade detection.

    Flow:
    1. Detect if fresh install or upgrade
    2. If upgrade: auto-create backup (no prompt)
    3. Perform installation
    4. On failure: auto-rollback using backup

    Args:
        context: ProjectContext with current directory status

    Returns:
        True if installation successful, False otherwise
    """
    if context.has_claux:
        # UPGRADE SCENARIO
        Console.print_info("Upgrading Claux installation...")
        console.print()

        # Auto-create backup (user requirement: automatic)
        Console.print_info("Creating automatic backup...")
        backup_name = create_pre_install_backup()

        if not backup_name:
            Console.print_error("Failed to create backup. Aborting upgrade.")
            console.print()
            return False

        Console.print_success(f"Backup created: {backup_name}")
        console.print()

        # Show what will be preserved
        console.print("[dim]Your custom settings will be preserved:[/dim]")
        if context.mcp_config:
            console.print(f"[dim]  • MCP config: {context.mcp_config}[/dim]")
        if context.agent_profile:
            console.print(f"[dim]  • Agent profile: {context.agent_profile}[/dim]")
        if context.has_custom_files:
            console.print("[dim]  • Custom profiles and backups[/dim]")
        console.print()

        try:
            # Perform upgrade
            Console.print_info("Updating Claux files...")
            perform_installation(upgrade=True)

            # Restore custom files from backup
            from claux.commands.backup import BackupManager

            config = get_config()
            manager = BackupManager(config)
            backup_dir = manager.get_backup_dir() / backup_name

            # Restore settings
            settings_backup = backup_dir / "settings.local.json"
            if settings_backup.exists():
                shutil.copy(settings_backup, context.claude_dir / "settings.local.json")

            # Restore profile
            profile_backup = backup_dir / ".active-agent-profile"
            if profile_backup.exists():
                shutil.copy(profile_backup, context.claude_dir / ".active-agent-profile")

            # Restore MCP config
            mcp_backup = backup_dir / ".mcp.json"
            if mcp_backup.exists() and context.git_root:
                shutil.copy(mcp_backup, context.git_root / ".mcp.json")

            console.print()
            Console.print_success("Upgrade complete!")
            console.print("[dim]Your settings and profiles have been preserved.[/dim]")
            console.print(
                f"[dim]You can rollback with: claux backup restore {backup_name}[/dim]"
            )
            console.print()

            return True

        except Exception as e:
            console.print()
            Console.print_error(f"Upgrade failed: {e}")
            rollback_installation(backup_name)
            console.print()
            return False

    else:
        # FRESH INSTALL SCENARIO
        Console.print_info("Installing Claux...")
        console.print()

        try:
            perform_installation(upgrade=False)

            console.print()
            Console.print_success("Installation complete!")
            console.print()

            console.print("[bold]Next steps:[/bold]")
            console.print("  1. Configure MCP: Select from menu → MCP Configurations")
            console.print(
                "  2. Choose agent profile: Select from menu → Agent Profiles"
            )
            console.print("  3. Launch Claude Code: Select from menu → Launch Claude Code")
            console.print()

            return True

        except Exception as e:
            console.print()
            Console.print_error(f"Installation failed: {e}")
            console.print()
            return False
