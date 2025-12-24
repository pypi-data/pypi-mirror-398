"""
Configuration management commands for Claux.

Provides commands to view, validate, and modify configuration settings.
"""

import typer
import json
import yaml
from typing import Optional
from rich.table import Table
from rich.syntax import Syntax

from claux.core.config_manager import get_manager
from claux.core.exceptions import ConfigError
from claux.ui import Console


app = typer.Typer(help="Manage Claux configuration")


@app.command()
def show(
    section: Optional[str] = typer.Argument(
        None,
        help="Configuration section to display (orchestrator, user, mcp, profiles)",
    )
):
    """
    Display configuration settings.

    Shows all configurations or a specific section if provided.

    Examples:
        claux config show              # Show all configurations
        claux config show user         # Show user config only
        claux config show mcp          # Show MCP config only
    """
    try:
        manager = get_manager()

        if section is None:
            # Show all configurations
            _show_all_configs(manager)
        elif section == "orchestrator":
            _show_orchestrator_config(manager)
        elif section == "user":
            _show_user_config(manager)
        elif section == "mcp":
            _show_mcp_config(manager)
        elif section == "profiles":
            _show_profiles_config(manager)
        else:
            Console.print_error(f"Unknown section: {section}")
            Console.print_info(
                "Valid sections: orchestrator, user, mcp, profiles"
            )
            raise typer.Exit(1)

    except ConfigError as e:
        Console.print_error(str(e))
        if e.suggestion:
            Console.print_info(e.suggestion)
        raise typer.Exit(1)
    except Exception as e:
        Console.print_error(f"Failed to load configuration: {str(e)}")
        raise typer.Exit(1)


@app.command()
def validate():
    """
    Validate all configuration files.

    Checks all configuration files against their JSON schemas and reports
    any validation errors.

    Examples:
        claux config validate          # Validate all configs
    """
    try:
        manager = get_manager()
        Console.print()
        Console.print_header("Validating Configurations")
        Console.print()

        # Run validation
        errors = manager.validate_all()

        if not errors:
            # All valid
            Console.print_success("All configurations are valid")
            Console.print()
            return

        # Show errors
        Console.print_error(f"Found validation errors in {len(errors)} configuration(s):")
        Console.print()

        for config_name, error_list in errors.items():
            Console.print_subheader(f"{config_name}:")
            for error in error_list:
                Console.print(f"  [red]✗[/red] {error}")
            Console.print()

        # Show suggestion
        Console.print_info(
            "Fix the errors above and run 'claux config validate' again."
        )
        Console.print()
        raise typer.Exit(1)

    except Exception as e:
        Console.print_error(f"Validation failed: {str(e)}")
        raise typer.Exit(1)


@app.command()
def get(
    key: str = typer.Argument(..., help="Configuration key (supports dot notation)"),
    default: Optional[str] = typer.Option(
        None, "--default", "-d", help="Default value if key not found"
    ),
):
    """
    Get a configuration value.

    Supports hierarchical resolution (environment → project → user → default).
    Use dot notation for nested keys.

    Examples:
        claux config get language              # Get language setting
        claux config get mcp.default           # Get default MCP config
        claux config get ui.color_scheme -d auto  # With default value
    """
    try:
        manager = get_manager()
        value = manager.get(key, default)

        if value is None:
            Console.print_warning(f"Configuration key not found: {key}")
            if default is None:
                Console.print_info(
                    "Tip: Use --default to specify a fallback value"
                )
            raise typer.Exit(1)

        # Display value
        Console.print()
        Console.print_key_value(key, str(value))
        Console.print()

    except ConfigError as e:
        Console.print_error(str(e))
        if e.suggestion:
            Console.print_info(e.suggestion)
        raise typer.Exit(1)
    except Exception as e:
        Console.print_error(f"Failed to get configuration: {str(e)}")
        raise typer.Exit(1)


@app.command()
def set(
    key: str = typer.Argument(..., help="Configuration key (supports dot notation)"),
    value: str = typer.Argument(..., help="Value to set"),
):
    """
    Set a user configuration value.

    Modifies the global user config (~/.claux/config.yaml).
    Use dot notation for nested keys.

    Examples:
        claux config set language ru           # Set language to Russian
        claux config set mcp.default full      # Set default MCP config
        claux config set ui.color_scheme dark  # Set dark color scheme
    """
    try:
        manager = get_manager()

        # Load current user config
        user_config = manager.user.load()

        # Parse value (try to detect type)
        parsed_value = _parse_value(value)

        # Set nested value
        _set_nested_value(user_config, key, parsed_value)

        # Save user config
        manager.user.save(user_config)

        # Reload manager to pick up changes
        manager.reload()

        Console.print()
        Console.print_success(f"Set {key} = {parsed_value}")
        Console.print()
        Console.print_info("Configuration updated in ~/.claux/config.yaml")
        Console.print()

    except ConfigError as e:
        Console.print_error(str(e))
        if e.suggestion:
            Console.print_info(e.suggestion)
        raise typer.Exit(1)
    except Exception as e:
        Console.print_error(f"Failed to set configuration: {str(e)}")
        raise typer.Exit(1)


@app.command()
def reset():
    """
    Reset user configuration to defaults.

    Removes all custom settings from ~/.claux/config.yaml and restores
    default values.

    Examples:
        claux config reset             # Reset to defaults
    """
    # Ask for confirmation
    confirmed = typer.confirm(
        "This will reset all user configuration to defaults. Continue?",
        default=False,
    )

    if not confirmed:
        Console.print_info("Reset cancelled")
        raise typer.Exit(0)

    try:
        manager = get_manager()

        # Create default config
        default_config = {"version": "0.1.3"}

        # Save default config
        manager.user.save(default_config)

        # Reload manager
        manager.reload()

        Console.print()
        Console.print_success("User configuration reset to defaults")
        Console.print()
        Console.print_info("Configuration file: ~/.claux/config.yaml")
        Console.print()

    except Exception as e:
        Console.print_error(f"Failed to reset configuration: {str(e)}")
        raise typer.Exit(1)


# Helper functions


def _show_all_configs(manager):
    """Display all configurations."""
    Console.print()
    Console.print_header("Claux Configuration")
    Console.print()

    # Orchestrator config
    Console.print_subheader("Project Configuration (.claude/):")
    try:
        config = manager.orchestrator
        Console.print_path("  Location", str(config.claude_dir))
        Console.print_key_value("  Repository Root", str(config.repo_root), indent=2)
        Console.print()
    except Exception as e:
        Console.print(f"  [red]Not available: {str(e)}[/red]")
        Console.print()

    # User config
    Console.print_subheader("User Configuration (~/.claux/config.yaml):")
    try:
        user_config = manager.user.load()
        for key, value in user_config.items():
            Console.print_key_value(f"  {key}", str(value), indent=2)
        Console.print()
    except Exception as e:
        Console.print(f"  [red]Not available: {str(e)}[/red]")
        Console.print()

    # MCP config
    Console.print_subheader("MCP Configuration:")
    try:
        active_mcp = manager.mcp.get_active_config()
        if active_mcp:
            Console.print_key_value("  Active", active_mcp.display_name, indent=2)
            Console.print_key_value(
                "  Servers", f"{len(active_mcp.servers)} configured", indent=2
            )
        else:
            Console.print("  [dim]No active MCP configuration[/dim]")
        Console.print()
    except Exception as e:
        Console.print(f"  [red]Not available: {str(e)}[/red]")
        Console.print()

    # Profiles
    Console.print_subheader("Agent Profiles:")
    try:
        active_profile = manager.profiles.get_active_profile()
        if active_profile:
            agent_count = manager.profiles.get_agent_count(active_profile)
            Console.print_key_value("  Active", active_profile.display_name, indent=2)
            Console.print_key_value("  Agents", f"{agent_count} loaded", indent=2)
        else:
            profiles = manager.profiles.list_profiles()
            Console.print_key_value(
                "  Available", f"{len(profiles)} profiles", indent=2
            )
        Console.print()
    except Exception as e:
        Console.print(f"  [red]Not available: {str(e)}[/red]")
        Console.print()


def _show_orchestrator_config(manager):
    """Display orchestrator (project) configuration."""
    Console.print()
    Console.print_header("Project Configuration")
    Console.print()

    try:
        config = manager.orchestrator

        # Basic info
        table = Table(show_header=False, border_style="dim")
        table.add_column("Property", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")

        table.add_row("Installation", str(config.claude_dir))
        table.add_row("Repository Root", str(config.repo_root))

        # Directory structure
        table.add_row("Agents", str(config.agents_dir))
        table.add_row("Profiles", str(config.agent_profiles_dir))
        table.add_row("Commands", str(config.commands_dir))
        table.add_row("Skills", str(config.skills_dir))
        table.add_row("Schemas", str(config.schemas_dir))

        Console.get_console().print(table)
        Console.print()

        # Settings
        if config.settings_file.exists():
            Console.print_subheader("Settings (.claude/settings.local.json):")
            settings_json = json.dumps(config.settings, indent=2)
            syntax = Syntax(settings_json, "json", theme="monokai", line_numbers=True)
            Console.get_console().print(syntax)
            Console.print()

    except Exception as e:
        Console.print_error(f"Failed to load project configuration: {str(e)}")
        raise typer.Exit(1)


def _show_user_config(manager):
    """Display user configuration."""
    Console.print()
    Console.print_header("User Configuration")
    Console.print()

    try:
        config_path = manager.user.config_path
        user_config = manager.user.load()

        Console.print_path("Location", str(config_path))
        Console.print()

        # Show as YAML
        yaml_str = yaml.dump(user_config, default_flow_style=False, sort_keys=False)
        syntax = Syntax(yaml_str, "yaml", theme="monokai", line_numbers=True)
        Console.get_console().print(syntax)
        Console.print()

    except Exception as e:
        Console.print_error(f"Failed to load user configuration: {str(e)}")
        raise typer.Exit(1)


def _show_mcp_config(manager):
    """Display MCP configuration."""
    Console.print()
    Console.print_header("MCP Configuration")
    Console.print()

    try:
        # List all configs
        configs = manager.mcp.list_configs()
        active_config = manager.mcp.get_active_config()

        Console.print_subheader(f"Available Configurations ({len(configs)}):")
        Console.print()

        for config_name in configs:
            is_active = active_config and active_config.name == config_name
            marker = "[green]●[/green]" if is_active else "[dim]○[/dim]"
            Console.print(f"  {marker} {config_name}")

        Console.print()

        # Show active config details
        if active_config:
            Console.print_subheader(f"Active: {active_config.display_name}")
            Console.print_key_value("  Servers", len(active_config.servers), indent=2)
            Console.print()

            for server_name, server_config in active_config.servers.items():
                Console.print(f"  [cyan]{server_name}[/cyan]")
                Console.print(f"    Command: {server_config.get('command', 'N/A')}")
                args = server_config.get("args", [])
                if args:
                    Console.print(f"    Args: {' '.join(args)}")
            Console.print()

    except Exception as e:
        Console.print_error(f"Failed to load MCP configuration: {str(e)}")
        raise typer.Exit(1)


def _show_profiles_config(manager):
    """Display profiles configuration."""
    Console.print()
    Console.print_header("Agent Profiles")
    Console.print()

    try:
        profiles = manager.profiles.list_profiles()
        active_profile = manager.profiles.get_active_profile()

        Console.print_subheader(f"Available Profiles ({len(profiles)}):")
        Console.print()

        for profile in profiles:
            is_active = active_profile and active_profile.name == profile.name
            marker = "[green]●[/green]" if is_active else "[dim]○[/dim]"
            agent_count = manager.profiles.get_agent_count(profile)
            Console.print(f"  {marker} {profile.display_name} ({agent_count} agents)")

        Console.print()

    except Exception as e:
        Console.print_error(f"Failed to load profiles: {str(e)}")
        raise typer.Exit(1)


def _parse_value(value_str: str):
    """
    Parse string value to appropriate type.

    Tries to detect booleans, numbers, and JSON structures.
    Falls back to string.
    """
    # Boolean
    if value_str.lower() in ("true", "yes", "1", "on"):
        return True
    if value_str.lower() in ("false", "no", "0", "off"):
        return False

    # Number
    try:
        if "." in value_str:
            return float(value_str)
        else:
            return int(value_str)
    except ValueError:
        pass

    # JSON (array or object)
    if value_str.startswith("[") or value_str.startswith("{"):
        try:
            return json.loads(value_str)
        except json.JSONDecodeError:
            pass

    # String
    return value_str


def _set_nested_value(config: dict, key: str, value):
    """
    Set nested dictionary value using dot notation.

    Creates intermediate dictionaries as needed.
    """
    keys = key.split(".")
    current = config

    # Navigate to parent
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        elif not isinstance(current[k], dict):
            raise ValueError(f"Cannot set nested value: {k} is not a dictionary")
        current = current[k]

    # Set value
    current[keys[-1]] = value
