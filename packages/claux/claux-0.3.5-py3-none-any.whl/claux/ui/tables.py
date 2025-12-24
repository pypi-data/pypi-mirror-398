"""
Rich table generators for agent profile display.

Provides formatted tables for listing profiles, showing details, and status information.
"""

from rich.table import Table
from typing import List, Optional

from claux.core.profiles import AgentProfile


def create_profiles_list_table(
    profiles: List[AgentProfile],
    active_name: Optional[str] = None,
    agent_counts: Optional[dict] = None,
) -> Table:
    """
    Create table for 'claux agents list' command.

    Displays profiles in a compact list view with key information:
    - Name (with checkmark if active)
    - Display Name
    - Agent count
    - Estimated tokens
    - Tags (comma-separated)

    Args:
        profiles: List of AgentProfile instances to display.
        active_name: Name of currently active profile (will be highlighted).
        agent_counts: Dict mapping profile names to agent counts (optional).

    Returns:
        Rich Table instance ready to print.

    Example:
        >>> counts = {"base": 8, "nextjs-full": 28}
        >>> table = create_profiles_list_table(profiles, active_name="base", agent_counts=counts)
        >>> console.print(table)
    """
    table = Table(title="Available Agent Profiles", show_header=True, header_style="bold blue")

    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Display Name", style="white")
    table.add_column("Agents", justify="right", style="yellow")
    table.add_column("Tokens", justify="right", style="magenta")
    table.add_column("Tags", style="dim")

    for profile in profiles:
        # Add checkmark if active
        name_display = profile.name
        if active_name and profile.name == active_name:
            name_display = f"[green]{profile.name} [*][/green]"

        # Format tokens with ~ prefix
        tokens_display = f"~{profile.estimated_tokens}"

        # Format tags (truncate if too long)
        tags_display = ", ".join(profile.tags[:3])
        if len(profile.tags) > 3:
            tags_display += f" +{len(profile.tags) - 3}"

        # Get agent count from dict if provided
        if agent_counts and profile.name in agent_counts:
            agents_display = str(agent_counts[profile.name])
        else:
            agents_display = "?"

        table.add_row(
            name_display,
            profile.display_name,
            agents_display,
            tokens_display,
            tags_display,
        )

    return table


def create_profile_detail_table(profile: AgentProfile, agent_count: int = 0) -> Table:
    """
    Create detailed table for 'claux agents info <name>' command.

    Shows comprehensive profile metadata including:
    - Display Name
    - Description
    - Estimated Tokens
    - Extends (if any)
    - Tags, Languages, Stacks
    - MCP Profile recommendation
    - Required/Optional MCP Servers
    - Auto-detect rules (if any)

    Args:
        profile: AgentProfile instance to display.
        agent_count: Number of agents in profile (optional).

    Returns:
        Rich Table instance ready to print.

    Example:
        >>> table = create_profile_detail_table(profile, agent_count=8)
        >>> console.print(table)
    """
    table = Table(
        title=f"Profile: {profile.display_name}",
        show_header=False,
        box=None,
        padding=(0, 2),
    )

    table.add_column("Field", style="dim", no_wrap=True)
    table.add_column("Value", style="white")

    # Basic info
    table.add_row("Name", f"[cyan]{profile.name}[/cyan]")
    table.add_row("Display Name", f"[bold]{profile.display_name}[/bold]")
    table.add_row("Description", profile.description)

    # Agent and token info
    if agent_count > 0:
        table.add_row("Agents", f"[yellow]{agent_count}[/yellow] agent files")
    table.add_row("Estimated Tokens", f"[magenta]~{profile.estimated_tokens}[/magenta]")

    # Calculate token savings (assuming 4500 tokens for all 41 agents)
    if profile.estimated_tokens > 0:
        total_tokens = 4500
        savings_pct = ((total_tokens - profile.estimated_tokens) / total_tokens) * 100
        if savings_pct > 0:
            table.add_row("Token Savings", f"[green]{savings_pct:.0f}%[/green] vs. all agents")

    # Inheritance
    if profile.extends:
        extends_str = ", ".join(profile.extends)
        table.add_row("Extends", f"[blue]{extends_str}[/blue]")

    # Tags and categories
    if profile.tags:
        tags_str = ", ".join(profile.tags)
        table.add_row("Tags", tags_str)

    if profile.languages and profile.languages != ["any"]:
        langs_str = ", ".join(profile.languages)
        table.add_row("Languages", langs_str)

    if profile.stacks and profile.stacks != ["any"]:
        stacks_str = ", ".join(profile.stacks)
        table.add_row("Stacks", stacks_str)

    # MCP configuration
    if profile.mcp_profile:
        table.add_row("MCP Profile", f"[bold cyan]{profile.mcp_profile}[/bold cyan]")

    if profile.required_mcp_servers:
        servers_str = ", ".join(profile.required_mcp_servers)
        table.add_row("Required MCP", servers_str)

    if profile.optional_mcp_servers:
        servers_str = ", ".join(profile.optional_mcp_servers)
        table.add_row("Optional MCP", f"[dim]{servers_str}[/dim]")

    # Auto-detect rules
    if profile.auto_detect:
        rules = []
        if "files" in profile.auto_detect:
            files = profile.auto_detect["files"]
            if files:
                rules.append(f"Files: {', '.join(files[:3])}")
        if "packageJson" in profile.auto_detect:
            deps = profile.auto_detect["packageJson"].get("dependencies", [])
            if deps:
                rules.append(f"NPM deps: {', '.join(deps[:3])}")
        if "pyprojectToml" in profile.auto_detect:
            deps = profile.auto_detect["pyprojectToml"].get("dependencies", [])
            if deps:
                rules.append(f"Python deps: {', '.join(deps[:3])}")

        if rules:
            table.add_row("Auto-detect", "\n".join(rules))

    return table


def create_status_table(
    active_profile: Optional[AgentProfile],
    mcp_servers: List[str],
    agent_count: int = 0,
) -> Table:
    """
    Create status table for 'claux agents status' command.

    Shows current configuration:
    - Active profile (or "All agents" if none)
    - MCP profile in use
    - Enabled MCP servers

    Args:
        active_profile: Currently active AgentProfile, or None if all agents loaded.
        mcp_servers: List of enabled MCP server names from settings.local.json.
        agent_count: Number of agents in active profile (optional).

    Returns:
        Rich Table instance ready to print.

    Example:
        >>> table = create_status_table(profile, ["context7"], agent_count=8)
        >>> console.print(table)
    """
    table = Table(
        title="Agent Profile Status",
        show_header=True,
        header_style="bold blue",
        box=None,
        padding=(0, 2),
    )

    table.add_column("Setting", style="dim", no_wrap=True)
    table.add_column("Value", style="white")

    # Active profile
    if active_profile:
        profile_display = f"[bold cyan]{active_profile.name}[/bold cyan]"
        if agent_count > 0:
            profile_display += f" ({agent_count} agents, ~{active_profile.estimated_tokens} tokens)"
        else:
            profile_display += f" (~{active_profile.estimated_tokens} tokens)"
    else:
        # Assuming 41 total agents when no profile active
        profile_display = "[dim]None - All agents loaded (41 agents, ~4500 tokens)[/dim]"

    table.add_row("Active Profile", profile_display)

    # MCP servers
    if mcp_servers:
        servers_display = ", ".join(mcp_servers)
        table.add_row("MCP Servers", servers_display)
    else:
        table.add_row("MCP Servers", "[dim]None configured[/dim]")

    # MCP profile recommendation (if active profile specifies one)
    if active_profile and active_profile.mcp_profile:
        table.add_row("Recommended MCP", f"[yellow]{active_profile.mcp_profile}[/yellow]")

    return table


def format_agent_list(agent_paths: List, max_display: int = 10, base_path: Optional = None) -> str:
    """
    Format agent file list for display.

    Args:
        agent_paths: List of agent file paths.
        max_display: Maximum number of agents to display before truncating.
        base_path: Base path to make paths relative (optional).

    Returns:
        Formatted string with agent list.

    Example:
        >>> paths = [Path(".claude/agents/meta/orchestrator.md"), ...]
        >>> print(format_agent_list(paths, max_display=5, base_path=claude_dir))
        * agents/meta/orchestrator.md
        * agents/meta/worker.md
        ... and 3 more
    """
    from pathlib import Path

    if not agent_paths:
        return "[dim]No agents[/dim]"

    # Convert to relative paths if base_path provided
    display_paths = []
    for path in agent_paths[:max_display]:
        path_obj = Path(path)
        if base_path:
            try:
                rel_path = path_obj.relative_to(Path(base_path))
                display_paths.append(str(rel_path))
            except ValueError:
                display_paths.append(path_obj.name)
        else:
            display_paths.append(path_obj.name)

    # Format as bullet list
    formatted = "\n".join(f"* {path}" for path in display_paths)

    # Add truncation indicator
    remaining = len(agent_paths) - max_display
    if remaining > 0:
        formatted += f"\n[dim]... and {remaining} more[/dim]"

    return formatted
