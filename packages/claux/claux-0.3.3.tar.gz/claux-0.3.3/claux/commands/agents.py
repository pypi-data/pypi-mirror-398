"""
Agent profile management commands.

Provides CLI commands for listing, activating, and managing agent profiles.
"""

import typer

from claux.core.config import get_config
from claux.core.profiles import ProfileManager
from claux.ui import Console
from claux.ui.tables import (
    create_profiles_list_table,
    create_profile_detail_table,
    create_status_table,
    format_agent_list,
)

app = typer.Typer(help="Manage agent profiles for selective loading")


@app.command("list")
def list_profiles():
    """List all available agent profiles."""
    try:
        config = get_config()
        manager = ProfileManager(config)

        profiles = manager.list_profiles()

        if not profiles:
            Console.print_warning("No profiles found")
            return

        # Get active profile name
        active_name = config.active_profile

        # Calculate agent counts for display
        agent_counts = {}
        for profile in profiles:
            agent_counts[profile.name] = manager.get_agent_count(profile)

        # Create and print table with agent counts
        table = create_profiles_list_table(profiles, active_name, agent_counts)
        Console.get_console().print(table)

        # Show usage hint
        Console.print()
        Console.get_console().print("[dim][*] = Active profile[/dim]")
        Console.get_console().print("[dim]Activate a profile: claux agents activate <name>[/dim]")

    except FileNotFoundError as e:
        Console.print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        Console.print_error(f"Failed to list profiles: {e}")
        raise typer.Exit(1)


@app.command("status")
def show_status():
    """Show current active profile and MCP configuration."""
    try:
        config = get_config()
        manager = ProfileManager(config)

        # Get active profile
        active_profile = manager.get_active_profile()
        agent_count = 0
        if active_profile:
            agent_count = manager.get_agent_count(active_profile)

        # Load MCP servers from settings.local.json
        mcp_servers = []
        settings = config.settings
        if "mcpServers" in settings:
            mcp_servers = list(settings["mcpServers"].keys())

        # Create and print status table
        table = create_status_table(active_profile, mcp_servers, agent_count)
        Console.get_console().print()
        Console.get_console().print(table)
        Console.get_console().print()

        # Show MCP mismatch warning if applicable
        if active_profile and active_profile.mcp_profile:
            # Check if MCP profile matches recommendation
            from claux.core.mcp import MCPManager
            mcp_manager = MCPManager(config)
            current_mcp = mcp_manager.detect_profile_from_active(config.settings)
            if current_mcp != active_profile.mcp_profile:
                Console.print_warning(f"Profile recommends MCP: {active_profile.mcp_profile}")
                Console.get_console().print(
                    f"   Run: [bold]claux mcp switch {active_profile.mcp_profile}[/bold]"
                )
                Console.print()

    except FileNotFoundError as e:
        Console.print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        Console.print_error(f"Failed to get status: {e}")
        raise typer.Exit(1)


@app.command("activate")
def activate_profile(
    profile_name: str = typer.Argument(
        ..., help="Profile name to activate (e.g., 'base', 'nextjs-full')"
    )
):
    """Activate an agent profile."""
    try:
        config = get_config()
        manager = ProfileManager(config)

        # Validate profile exists
        profile = manager.get_profile(profile_name)
        if profile is None:
            Console.print_error(f"Profile not found: {profile_name}")
            Console.print()
            Console.get_console().print("Available profiles: [cyan]claux agents list[/cyan]")
            raise typer.Exit(1)

        # Activate profile
        manager.activate_profile(profile_name)

        # Get agent count
        agent_count = manager.get_agent_count(profile)

        # Show success message
        Console.print()
        Console.print_success(f"Activated profile: {profile.display_name}")
        Console.print()

        # Show profile info
        Console.get_console().print("[info][INFO][/info] This profile includes:")
        Console.get_console().print(
            f"   * {agent_count} agents (~{profile.estimated_tokens} tokens)"
        )

        # Calculate savings
        total_tokens = 4500
        if profile.estimated_tokens < total_tokens:
            savings_pct = ((total_tokens - profile.estimated_tokens) / total_tokens) * 100
            Console.get_console().print(f"   * [green]{savings_pct:.0f}% token savings[/green]")

        if profile.tags:
            tags_str = ", ".join(profile.tags)
            Console.get_console().print(f"   * Tags: {tags_str}")

        Console.print()

        # Show MCP recommendation
        if profile.mcp_profile:
            Console.print_warning(f"Recommended MCP profile: {profile.mcp_profile}")
            Console.get_console().print(
                f"   Run: [bold]claux mcp switch {profile.mcp_profile}[/bold]"
            )
            Console.print()

        # Restart reminder
        Console.print_warning("IMPORTANT: Restart Claude Code to apply changes!")

    except FileNotFoundError as e:
        Console.print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        Console.print_error(f"Failed to activate profile: {e}")
        raise typer.Exit(1)


@app.command("detect")
def detect_profile():
    """Auto-detect best profile for current project."""
    try:
        config = get_config()
        manager = ProfileManager(config)

        Console.print()
        Console.get_console().print("[info][INFO][/info] Analyzing project structure...")

        # Run auto-detection
        detected = manager.detect_profile()

        if detected:
            agent_count = manager.get_agent_count(detected)

            Console.print()
            Console.print_success(f"Detected profile: {detected.display_name}")
            Console.print()
            Console.get_console().print(f"   Name: [cyan]{detected.name}[/cyan]")
            Console.get_console().print(f"   Description: {detected.description}")
            Console.get_console().print(
                f"   Agents: {agent_count} (~{detected.estimated_tokens} tokens)"
            )

            # Ask to activate
            Console.print()
            should_activate = Console.confirm(f"Activate profile '{detected.name}'?", default=True)

            if should_activate:
                manager.activate_profile(detected.name)
                Console.print()
                Console.print_success("Profile activated!")
                Console.print_warning("IMPORTANT: Restart Claude Code to apply changes!")
            else:
                Console.print()
                Console.get_console().print(
                    f"To activate later: [bold]claux agents activate {detected.name}[/bold]"
                )
        else:
            Console.print()
            Console.print_warning("No matching profile found for this project")
            Console.print()
            Console.get_console().print(
                "Suggestion: Use the [cyan]base[/cyan] profile for universal support"
            )
            Console.get_console().print("   [bold]claux agents activate base[/bold]")

    except FileNotFoundError as e:
        Console.print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        Console.print_error(f"Failed to detect profile: {e}")
        raise typer.Exit(1)


@app.command("reset")
def reset_profile():
    """Deactivate profile (load all 41 agents)."""
    try:
        config = get_config()
        manager = ProfileManager(config)

        # Check if any profile is active
        if config.active_profile is None:
            Console.print_warning("No profile is currently active")
            return

        # Deactivate profile
        manager.deactivate_profile()

        Console.print()
        Console.print_success("Profile deactivated - all agents will be loaded")
        Console.print()
        Console.get_console().print("   Claude Code will now load all 41 agents (~4500 tokens)")
        Console.print()
        Console.print_warning("IMPORTANT: Restart Claude Code to apply changes!")

    except FileNotFoundError as e:
        Console.print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        Console.print_error(f"Failed to reset profile: {e}")
        raise typer.Exit(1)


@app.command("info")
def show_info(profile_name: str = typer.Argument(..., help="Profile name to show details for")):
    """Show detailed information about a profile."""
    try:
        config = get_config()
        manager = ProfileManager(config)

        # Load profile
        profile = manager.get_profile(profile_name)
        if profile is None:
            Console.print_error(f"Profile not found: {profile_name}")
            Console.print()
            Console.get_console().print("Available profiles: [cyan]claux agents list[/cyan]")
            raise typer.Exit(1)

        # Get agent count and files
        agent_count = manager.get_agent_count(profile)
        agent_files = profile.get_all_agents(config.claude_dir)

        # Create and print detail table
        Console.print()
        table = create_profile_detail_table(profile, agent_count)
        Console.get_console().print(table)

        # Show agent list (truncated)
        Console.print()
        Console.get_console().print("[bold]Included Agents:[/bold]")
        Console.print()

        if agent_files:
            formatted_list = format_agent_list(
                agent_files, max_display=10, base_path=config.claude_dir
            )
            Console.get_console().print(formatted_list)
        else:
            Console.get_console().print("[dim]No agents matched[/dim]")

        Console.print()

        # Show activation command if not active
        if config.active_profile != profile_name:
            Console.get_console().print(
                f"To activate: [bold]claux agents activate {profile_name}[/bold]"
            )
            Console.print()

    except FileNotFoundError as e:
        Console.print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        Console.print_error(f"Failed to get profile info: {e}")
        raise typer.Exit(1)


@app.command("validate")
def validate_profile(profile_name: str = typer.Argument(..., help="Profile name to validate")):
    """Validate profile JSON structure and content."""
    try:
        config = get_config()
        manager = ProfileManager(config)

        Console.print()
        Console.get_console().print(f"[info][INFO][/info] Validating profile: {profile_name}")

        # Run validation
        errors = manager.validate_profile(profile_name)

        if errors:
            Console.print()
            Console.print_error(f"Profile validation failed ({len(errors)} errors)")
            Console.print()
            for i, error in enumerate(errors, 1):
                Console.get_console().print(f"   {i}. {error}")
            Console.print()
            raise typer.Exit(1)
        else:
            Console.print()
            Console.print_success("Profile is valid")

            # Show additional info
            profile = manager.get_profile(profile_name)
            if profile:
                agent_count = manager.get_agent_count(profile)
                Console.print()
                Console.get_console().print(f"   * Display Name: {profile.display_name}")
                Console.get_console().print(f"   * Agents: {agent_count}")
                Console.get_console().print(f"   * Tokens: ~{profile.estimated_tokens}")

                # Check for warnings
                warnings = []
                if not profile.tags:
                    warnings.append("No tags defined")
                if not profile.mcp_profile:
                    warnings.append("No MCP profile recommendation")
                if agent_count == 0:
                    warnings.append("No agents matched by patterns")

                if warnings:
                    Console.print()
                    Console.print_warning(f"Warnings ({len(warnings)}):")
                    for warning in warnings:
                        Console.get_console().print(f"   * {warning}")

            Console.print()

    except FileNotFoundError as e:
        Console.print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        Console.print_error(f"Failed to validate profile: {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
