"""
Status command for Claude Code Orchestrator Kit.

Shows installation health and configuration status.
"""

import typer
from rich.table import Table

from claux.core.config import get_config
from claux.core.profiles import ProfileManager
from claux.core.mcp import MCPManager
from claux.ui import Console


app = typer.Typer(help="Show installation status and health")


@app.command()
def status():
    """
    Show orchestrator installation status.

    Displays:
    - Installation location (.claude/ directory)
    - Active agent profile (if any)
    - Active MCP configuration
    - Agent count (loaded vs total)
    - Health checks:
      - .claude/agents/ exists
      - .claude/agent-profiles/ exists
      - .claude/schemas/ exists
      - settings.local.json exists
      - pyproject.toml exists
    """
    try:
        config = get_config()
    except FileNotFoundError as e:
        Console.print_error(str(e))
        Console.print()
        Console.print_info("To initialize orchestrator in current project:")
        Console.print("  [code]claux init[/code]", style="dim")
        Console.print()
        raise typer.Exit(1)

    # Create status table
    table = Table(
        title="Claude Code Orchestrator Status",
        show_header=True,
        header_style="bold blue",
        border_style="dim",
    )
    table.add_column("Component", style="cyan", no_wrap=True)
    table.add_column("Status", style="white")

    # Check installation
    table.add_row(
        "Installation",
        "[green]Installed[/green]" if config.claude_dir.exists() else "[red]Not found[/red]",
    )

    # Check agent profile
    profile_manager = ProfileManager(config)
    active_profile = profile_manager.get_active_profile()
    if active_profile:
        agent_count = profile_manager.get_agent_count(active_profile)
        profile_status = f"{active_profile.display_name} ([green]{agent_count} agents[/green])"
    else:
        # Count all agents
        all_agents = list(config.agents_dir.rglob("*.md"))
        agent_count = len(all_agents)
        profile_status = f"[dim]None (all {agent_count} agents)[/dim]"

    table.add_row("Agent Profile", profile_status)

    # Check MCP configuration
    mcp_manager = MCPManager(config)
    active_mcp = mcp_manager.get_active_config()
    if active_mcp:
        server_count = len(active_mcp.servers)
        mcp_status = f"{active_mcp.display_name} ([green]{server_count} servers[/green])"
    else:
        mcp_status = "[dim]None[/dim]"

    table.add_row("MCP Config", mcp_status)

    # Health checks
    health_checks = []
    health_status = "[green]All systems OK[/green]"

    # Check directory structure
    checks = [
        (config.claude_dir, ".claude directory"),
        (config.agents_dir, "agents directory"),
        (config.agent_profiles_dir, "agent-profiles directory"),
        (config.schemas_dir, "schemas directory"),
        (config.commands_dir, "commands directory"),
        (config.skills_dir, "skills directory"),
    ]

    for path, name in checks:
        if not path.exists():
            health_checks.append(f"[red]{name} not found[/red]")

    # Check settings file
    if config.settings_file.exists():
        settings_check = "[green]settings.local.json exists[/green]"
    else:
        settings_check = "[yellow]settings.local.json missing (optional)[/yellow]"
        health_checks.append(settings_check)

    # Overall health
    if health_checks:
        health_status = f"[yellow]{len(health_checks)} warning(s)[/yellow]"

    table.add_row("Health Check", health_status)

    # Print table
    Console.print()
    Console.get_console().print(table)
    Console.print()

    # Show details
    Console.print_subheader("Details:")
    Console.print_path("  Installation", str(config.claude_dir))

    # Count components
    try:
        total_agents = len(list(config.agents_dir.rglob("*.md")))
        total_profiles = len(profile_manager.list_profiles())
        total_commands = len(list(config.commands_dir.glob("*.md")))
        total_skills = len(list(config.skills_dir.glob("**/SKILL.md")))

        Console.print_key_value("  Agents", f"{total_agents} available", indent=2)
        Console.print_key_value("  Profiles", f"{total_profiles} configured", indent=2)
        Console.print_key_value("  Commands", f"{total_commands} slash commands", indent=2)
        Console.print_key_value("  Skills", f"{total_skills} skills", indent=2)
    except Exception:
        pass

    # Show health warnings
    if health_checks:
        Console.print()
        Console.print_subheader("Warnings:")
        for warning in health_checks:
            Console.print(f"  {warning}")

    Console.print()

    # Show helpful hints
    if not active_profile:
        Console.print_info("Tip: Activate a profile to reduce token usage")
        Console.print("  [code]claux agents list[/code]", style="dim")
        Console.print("  [code]claux agents activate <name>[/code]", style="dim")
        Console.print()

    if not active_mcp:
        Console.print_info("Tip: Switch to an MCP configuration")
        Console.print("  [code]claux mcp list[/code]", style="dim")
        Console.print("  [code]claux mcp switch <name>[/code]", style="dim")
        Console.print()
