"""
MCP configuration management commands.

Provides CLI commands for listing, switching, and validating MCP server
configurations.
"""

import typer
from rich.table import Table
from rich.prompt import Prompt

from claux.core.config import get_config
from claux.core.mcp import MCPManager
from claux.ui import Console


app = typer.Typer(help="Manage MCP server configurations")


@app.command("list")
def list_configs():
    """List all available MCP configurations."""
    try:
        config = get_config()
        manager = MCPManager(config)

        configs = manager.list_configs()

        if not configs:
            Console.print_warning("No MCP configurations found in mcp/ directory")
            return

        # Get active config
        active_config = manager.get_active_config()
        active_name = active_config.name if active_config else None

        # Create table
        Console.print_header("Available MCP Configurations")

        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="dim")
        table.add_column("Servers", style="green", justify="right")
        table.add_column("Tokens", style="yellow", justify="right")

        for cfg in configs:
            # Mark active config
            name = f"{cfg.name} *" if cfg.name == active_name else cfg.name

            table.add_row(
                name,
                cfg.description,
                str(len(cfg.servers)),
                f"~{cfg.estimated_tokens}",
            )

        Console.get_console().print(table)

        # Show legend
        Console.print()
        Console.get_console().print("[dim]* = Active configuration[/dim]")

        # Show usage hint
        Console.print()
        Console.get_console().print(
            "[dim]Use 'claux mcp switch <name>' to change configuration[/dim]"
        )

    except FileNotFoundError as e:
        Console.print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        Console.print_error(f"Failed to list MCP configurations: {e}")
        raise typer.Exit(1)


@app.command("status")
def show_status():
    """Show current active MCP configuration."""
    try:
        config = get_config()
        manager = MCPManager(config)

        # Get active config
        active_config = manager.get_active_config()
        active_servers = manager.get_active_servers()

        if not active_servers:
            Console.print_warning("No active MCP configuration (.mcp.json not found)")
            return

        # Create status table
        Console.print_header("MCP Configuration Status")

        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Setting", style="cyan", width=20)
        table.add_column("Value", style="green")

        # Active config row
        if active_config:
            config_name = f"{active_config.display_name} (~{active_config.estimated_tokens} tokens)"
        else:
            config_name = "Custom (unknown)"

        table.add_row("Active Config", config_name)

        # Servers row
        servers_str = ", ".join(active_servers)
        table.add_row("Servers", servers_str)

        Console.get_console().print(table)

        # Show detailed server list
        if len(active_servers) > 3:
            Console.print()
            Console.print_subheader("Active Servers:")
            for i, server in enumerate(active_servers, 1):
                Console.get_console().print(f"  {i}. [cyan]{server}[/cyan]")

    except Exception as e:
        Console.print_error(f"Failed to get MCP status: {e}")
        raise typer.Exit(1)


@app.command("switch")
def switch_config(
    config_name: str = typer.Argument(..., help="Config name (base, frontend, full, etc.)")
):
    """Switch to a different MCP configuration."""
    try:
        config = get_config()
        manager = MCPManager(config)

        # Get config details
        mcp_config = manager.get_config(config_name)
        if not mcp_config:
            Console.print_error(f"MCP configuration '{config_name}' not found")
            Console.print()
            Console.get_console().print(
                "[dim]Run 'claux mcp list' to see available configurations[/dim]"
            )
            raise typer.Exit(1)

        # Switch config
        manager.switch_config(config_name)

        # Show success message
        Console.print()
        Console.print_success(f"Switched to: {mcp_config.display_name} ({mcp_config.description})")
        Console.print_path("   Source", str(mcp_config.file_path), indent=0)
        Console.get_console().print(
            f"   [dim]Servers:[/dim] [cyan]{', '.join(mcp_config.servers)}[/cyan]"
        )
        Console.print()

        # Show restart reminder
        Console.print_warning("IMPORTANT: Restart Claude Code to apply changes!")
        Console.print()

    except FileNotFoundError as e:
        Console.print_error(str(e))
        raise typer.Exit(1)
    except ValueError as e:
        Console.print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        Console.print_error(f"Failed to switch MCP configuration: {e}")
        raise typer.Exit(1)


@app.command("validate")
def validate_config(config_name: str = typer.Argument(..., help="Config name to validate")):
    """Validate MCP configuration JSON."""
    try:
        config = get_config()
        manager = MCPManager(config)

        # Run validation
        errors = manager.validate_config(config_name)

        if errors:
            Console.print_error(f"MCP configuration '{config_name}' is invalid:")
            Console.print()
            for error in errors:
                Console.get_console().print(f"  [red]*[/red] {error}")
            Console.print()
            raise typer.Exit(1)
        else:
            Console.print_success(f"MCP configuration '{config_name}' is valid")

    except Exception as e:
        Console.print_error(f"Failed to validate MCP configuration: {e}")
        raise typer.Exit(1)


@app.command("interactive")
def interactive_menu():
    """Interactive menu for switching MCP configurations (like bash script)."""
    try:
        config = get_config()
        manager = MCPManager(config)

        # Get available configs
        all_configs = manager.list_configs()
        config_map = {cfg.name: cfg for cfg in all_configs}

        # Print header
        console = Console.get_console()
        console.print()
        console.print("=" * 67, style="bold blue")
        console.print("  MCP Configuration Switcher", style="bold blue")
        console.print("=" * 67, style="bold blue")
        console.print()

        # Print menu
        console.print("Select MCP configuration:")
        console.print()

        # Define menu options in order matching bash script
        menu_options = [
            ("base", "1", "BASE", "Context7 + Sequential Thinking", "~600 tokens"),
            ("supabase-only", "2", "SUPABASE", "Base + Supabase MegaCampusAI", "~2500 tokens"),
            (
                "supabase-full",
                "3",
                "SUPABASE + LEGACY",
                "Base + Supabase + Legacy project",
                "~3000 tokens",
            ),
            ("n8n", "4", "N8N", "Base + n8n-workflows + n8n-mcp", "~2500 tokens"),
            ("frontend", "5", "FRONTEND", "Base + Playwright + ShadCN", "~2000 tokens"),
            ("serena", "6", "SERENA", "Base + Serena LSP semantic search", "~2500 tokens"),
            ("full", "7", "FULL", "All servers including Serena", "~6500 tokens"),
        ]

        # Display menu options (only if config exists)
        available_options = []
        for cfg_name, number, display, desc, tokens in menu_options:
            if cfg_name in config_map:
                console.print(f"[green]{number}[/green] - {display:16} ({desc:45}) {tokens}")
                available_options.append(number)

        console.print()
        console.print("[yellow]0[/yellow] - STATUS           (Show current configuration)")
        console.print()

        # Get user choice
        choice = Prompt.ask(
            "Your choice",
            console=console,
            choices=["0"] + available_options,
        )

        # Handle choice
        if choice == "0":
            # Show status
            console.print()
            show_status()
            return

        # Map choice to config name
        choice_map = {
            "1": "base",
            "2": "supabase-only",
            "3": "supabase-full",
            "4": "n8n",
            "5": "frontend",
            "6": "serena",
            "7": "full",
        }

        config_name = choice_map.get(choice)
        if not config_name:
            Console.print_error(f"Invalid choice: {choice}")
            raise typer.Exit(1)

        # Get config details
        mcp_config = config_map.get(config_name)
        if not mcp_config:
            Console.print_error(f"Configuration '{config_name}' not found")
            raise typer.Exit(1)

        # Switch config
        manager.switch_config(config_name)

        # Show success message
        console.print()
        Console.print_success(f"Switched to: {mcp_config.display_name} ({mcp_config.description})")
        Console.print_path("   Source", str(mcp_config.file_path), indent=0)
        console.print()

        # Show restart reminder
        Console.print_warning("IMPORTANT: Restart Claude Code to apply changes!")
        console.print()

    except KeyboardInterrupt:
        Console.print()
        Console.print_warning("Operation cancelled by user")
        raise typer.Exit(0)
    except Exception as e:
        Console.print_error(f"Failed to switch MCP configuration: {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
