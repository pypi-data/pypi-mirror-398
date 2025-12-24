"""
Setup wizard for Claude Code Orchestrator Kit.

Interactive setup with auto-discovery of projects and intelligent configuration.
"""

import typer
from pathlib import Path
from typing import Optional
import shutil

from claux.ui import Console
from claux.commands.init import get_orchestrator_install_path
from claux.core.discovery import find_projects_in_directory


app = typer.Typer(help="Interactive setup wizard")


@app.command()
def setup(
    search_dir: Optional[Path] = typer.Option(
        None,
        "--search-dir",
        "-s",
        help="Directory to search for projects (default: ~/PycharmProjects, ~/projects, ~/Documents)",
    ),
    max_depth: int = typer.Option(
        2, "--max-depth", "-d", help="Maximum depth to search for projects"
    ),
    auto_yes: bool = typer.Option(
        False, "--yes", "-y", help="Automatically answer yes to all prompts"
    ),
):
    """
    Interactive setup wizard with auto-discovery of projects.

    Finds all git repositories in common project directories and offers
    to install orchestrator with recommended configuration for each.

    Examples:
        # Search in default locations
        claux wizard setup

        # Search in specific directory
        claux wizard setup -s ~/my-projects

        # Auto-accept all (useful for CI)
        claux wizard setup -y
    """
    Console.print()
    Console.print_header("🧙 Claude Code Orchestrator - Setup Wizard")
    Console.print()
    Console.print("This wizard will:", style="dim")
    Console.print("  1. Find all your git projects", style="dim")
    Console.print("  2. Detect project types", style="dim")
    Console.print("  3. Recommend optimal configurations", style="dim")
    Console.print("  4. Install and configure orchestrator", style="dim")
    Console.print()

    # Determine search directories
    if search_dir:
        search_dirs = [Path(search_dir)]
    else:
        home = Path.home()
        search_dirs = [
            home / "PycharmProjects",
            home / "projects",
            home / "Documents",
            home / "dev",
            home / "code",
            Path.cwd(),
        ]
        # Only use directories that exist
        search_dirs = [d for d in search_dirs if d.exists()]

    if not search_dirs:
        Console.print_error("No search directories found!")
        raise typer.Exit(1)

    Console.print_info(f"Searching for projects in {len(search_dirs)} location(s)...")
    for d in search_dirs:
        Console.print(f"  * {d}", style="dim")
    Console.print()

    # Find all projects
    all_projects = []
    for search_dir in search_dirs:
        Console.print(f"📂 Scanning {search_dir}...", style="dim")
        projects = find_projects_in_directory(search_dir, max_depth=max_depth)
        all_projects.extend(projects)

    if not all_projects:
        Console.print_warning("No git projects found!")
        Console.print()
        Console.print("Try:", style="dim")
        Console.print("  * Increase search depth: --max-depth 3", style="dim")
        Console.print("  * Specify directory: --search-dir /path/to/projects", style="dim")
        Console.print("  * Or use direct init: claux init /path/to/project", style="dim")
        raise typer.Exit(0)

    Console.print()
    Console.print_success(f"Found {len(all_projects)} project(s)!")
    Console.print()

    # Display projects table
    Console.print_subheader("Projects found:")
    Console.print()

    for i, project in enumerate(all_projects, 1):
        status = "[*] Installed" if project["has_orchestrator"] else "[ ] Not installed"
        status_style = "green" if project["has_orchestrator"] else "yellow"

        type_display = project["type"].value.capitalize()
        Console.print(
            f"  [{i}] {project['name']:<30} "
            f"[dim]{type_display:<12}[/dim] "
            f"[{status_style}]{status}[/{status_style}]"
        )

    Console.print()

    # Ask which projects to setup
    if not auto_yes:
        Console.print("Which projects would you like to setup?", style="prompt")
        Console.print("  Enter numbers (e.g., '1,3,5' or '1-3' or 'all'):", style="dim")
        choice = typer.prompt("", default="all")
    else:
        choice = "all"

    # Parse selection
    selected_indices = set()
    if choice.lower() == "all":
        selected_indices = set(range(len(all_projects)))
    else:
        for part in choice.split(","):
            part = part.strip()
            if "-" in part:
                # Range (e.g., "1-3")
                start, end = part.split("-")
                start_idx = int(start.strip()) - 1
                end_idx = int(end.strip()) - 1
                selected_indices.update(range(start_idx, end_idx + 1))
            else:
                # Single number
                selected_indices.add(int(part) - 1)

    selected_projects = [
        all_projects[i] for i in sorted(selected_indices) if 0 <= i < len(all_projects)
    ]

    if not selected_projects:
        Console.print_warning("No projects selected. Exiting.")
        raise typer.Exit(0)

    Console.print()
    Console.print_info(f"Installing orchestrator in {len(selected_projects)} project(s)...")
    Console.print()

    # Get orchestrator source
    try:
        install_root = get_orchestrator_install_path()
        source_claude_dir = install_root / ".claude"
    except FileNotFoundError as e:
        Console.print_error(str(e))
        raise typer.Exit(1)

    # Install in each selected project
    success_count = 0
    for project in selected_projects:
        project_path = project["path"]
        project_name = project["name"]

        Console.print(f"📦 {project_name}", style="bold")

        # Skip if already installed (unless force)
        if project["has_orchestrator"]:
            Console.print("  ⊙ Already installed, skipping", style="yellow")
            Console.print()
            continue

        try:
            # Copy .claude directory
            target_claude_dir = project_path / ".claude"
            shutil.copytree(source_claude_dir, target_claude_dir)

            # Update .gitignore
            gitignore_path = project_path / ".gitignore"
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

            Console.print("  [*] Installed", style="green")
            Console.print(f"  [*] Detected: {project['type'].value}", style="dim")
            Console.print(f"  [*] Recommended MCP: {project['recommended_mcp']}", style="dim")
            success_count += 1

        except Exception as e:
            Console.print(f"  [X] Failed: {e}", style="red")

        Console.print()

    # Summary
    Console.print()
    Console.print_success(
        f"[*] Setup complete! Installed in {success_count}/{len(selected_projects)} project(s)"
    )
    Console.print()

    # Next steps
    Console.print_subheader("Next steps:")
    Console.print("  1. Navigate to each project", style="dim")
    Console.print("  2. Activate profile: [code]claux agents activate base[/code]", style="dim")
    Console.print("  3. Configure MCP: [code]claux mcp switch <config>[/code]", style="dim")
    Console.print("  4. Restart Claude Code", style="dim")
    Console.print()
    Console.print("For project-specific MCP recommendations, see the output above.", style="dim")
    Console.print()
