"""
Initialization command for Claude Code Orchestrator Kit.

Sets up the orchestrator in a new project by copying necessary files and directories.
"""

import typer
import shutil
from pathlib import Path
from typing import Optional

from claux.core.utils import find_git_root
from claux.ui import Console


app = typer.Typer(help="Initialize Claude Code Orchestrator in a project")


def get_orchestrator_install_path() -> Path:
    """
    Find the installation path of the orchestrator (where templates are stored).

    Returns:
        Path to orchestrator installation directory.
    """
    # The orchestrator is installed as a package, so we need to find its location
    # This file is at: <install>/claux/commands/init.py
    # We want: <install>/.claude/ (the templates directory)
    current_file = Path(__file__).resolve()
    package_root = current_file.parent.parent.parent  # Go up to root

    # Check if .claude directory exists in package root (for development)
    template_dir = package_root / ".claude"
    if template_dir.exists():
        return package_root

    raise FileNotFoundError(
        "Could not find orchestrator templates. " "Make sure the package is installed correctly."
    )


@app.command()
def init(
    target_dir: Optional[Path] = typer.Option(
        None, "--target", "-t", help="Target directory (default: current directory)"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing files"),
):
    """
    Initialize orchestrator in a project.

    Creates .claude directory structure and copies:
    - agents/ directory (all agent definitions)
    - agent-profiles/ directory (profile definitions)
    - commands/ directory (slash commands)
    - skills/ directory (reusable skills)
    - schemas/ directory (JSON schemas)
    - settings.local.json.example
    """
    Console.print_info("Initializing Claude Code Orchestrator...")
    Console.print()

    # Determine target directory
    if target_dir is None:
        target_dir = Path.cwd()
    else:
        target_dir = Path(target_dir).resolve()

    # Check if it's a git repository
    try:
        repo_root = find_git_root(target_dir)
        target_dir = repo_root
    except FileNotFoundError:
        Console.print_warning("Not a git repository. Initializing in current directory.")

    # Check if .claude directory already exists
    claude_dir = target_dir / ".claude"
    if claude_dir.exists() and not force:
        Console.print_error(
            f".claude directory already exists at {claude_dir}\n" "Use --force to overwrite."
        )
        raise typer.Exit(1)

    # Get orchestrator installation path
    try:
        install_root = get_orchestrator_install_path()
        source_claude_dir = install_root / ".claude"
    except FileNotFoundError as e:
        Console.print_error(str(e))
        raise typer.Exit(1)

    if not source_claude_dir.exists():
        Console.print_error(
            f"Template directory not found at {source_claude_dir}\n"
            "Make sure the orchestrator is installed correctly."
        )
        raise typer.Exit(1)

    # Copy .claude directory structure
    try:
        if claude_dir.exists():
            Console.print_warning(f"Removing existing {claude_dir}")
            shutil.rmtree(claude_dir)

        Console.print_info(f"Copying orchestrator files to {claude_dir}...")
        shutil.copytree(source_claude_dir, claude_dir)

        # Create .gitignore for temporary files
        gitignore_path = target_dir / ".gitignore"
        gitignore_entries = [
            ".tmp/",
            ".claude/settings.local.json",
            ".claude/.active-agent-profile",
            ".claude/backups/",
        ]

        # Add entries if .gitignore exists, otherwise create it
        if gitignore_path.exists():
            existing_content = gitignore_path.read_text(encoding="utf-8")
            new_entries = []
            for entry in gitignore_entries:
                if entry not in existing_content:
                    new_entries.append(entry)

            if new_entries:
                with open(gitignore_path, "a", encoding="utf-8") as f:
                    f.write("\n# Claude Code Orchestrator\n")
                    f.write("\n".join(new_entries))
                    f.write("\n")
                Console.print_info("Updated .gitignore")
        else:
            with open(gitignore_path, "w", encoding="utf-8") as f:
                f.write("# Claude Code Orchestrator\n")
                f.write("\n".join(gitignore_entries))
                f.write("\n")
            Console.print_info("Created .gitignore")

        # Count installed components
        agents_count = len(list((claude_dir / "agents").rglob("*.md")))
        profiles_count = len(list((claude_dir / "agent-profiles").glob("*.profile.json")))
        commands_count = len(list((claude_dir / "commands").glob("*.md")))
        skills_count = len(list((claude_dir / "skills").glob("**/SKILL.md")))

        Console.print()
        Console.print_success("Installation complete!")
        Console.print()
        Console.print_key_value("Location", str(claude_dir), indent=3)
        Console.print_key_value("Agents", f"{agents_count} agents installed", indent=3)
        Console.print_key_value("Profiles", f"{profiles_count} profiles available", indent=3)
        Console.print_key_value("Commands", f"{commands_count} slash commands installed", indent=3)
        Console.print_key_value("Skills", f"{skills_count} skills available", indent=3)
        Console.print()

        # Show next steps
        Console.print_subheader("Next steps:")
        Console.print("  1. Edit .claude/settings.local.json (copy from .example)", style="dim")
        Console.print(
            "  2. Activate a profile: [code]claux agents activate base[/code]", style="dim"
        )
        Console.print("  3. Choose MCP config: [code]claux mcp switch base[/code]", style="dim")
        Console.print("  4. Restart Claude Code", style="dim")
        Console.print()

    except Exception as e:
        Console.print_error(f"Failed to initialize orchestrator: {e}")
        raise typer.Exit(1)
