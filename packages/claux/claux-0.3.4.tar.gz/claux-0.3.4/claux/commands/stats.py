"""
Token usage statistics commands.

Provides CLI commands for viewing TOON format token savings and usage metrics.
"""

import typer
from pathlib import Path
from typing import Optional

from claux.core.metrics import get_tracker
from claux.ui import Console

app = typer.Typer(help="View token usage statistics and TOON format savings")


@app.command("show")
def show_stats(
    week: bool = typer.Option(False, "--week", "-w", help="Show last 7 days"),
    month: bool = typer.Option(False, "--month", "-m", help="Show last 30 days"),
    export: Optional[str] = typer.Option(
        None,
        "--export",
        "-e",
        help="Export to CSV file (e.g., stats.csv)",
    ),
):
    """Show token usage statistics and savings."""
    try:
        from rich.table import Table
        from rich.panel import Panel
        from rich.text import Text

        tracker = get_tracker()
        console = Console.get_console()

        # Export to CSV if requested
        if export:
            days = 30 if month else (7 if week else 1)
            export_path = Path(export)
            tracker.export_csv(export_path, days=days)
            Console.print_success(f"Exported {days} days of metrics to {export_path}")
            return

        # Get summary statistics
        summary = tracker.get_summary()

        # Create summary panel
        summary_text = Text()
        summary_text.append("Total Operations: ", style="bold cyan")
        summary_text.append(f"{summary['total_operations']}\n")

        summary_text.append("Total JSON Tokens: ", style="bold yellow")
        summary_text.append(f"{summary['total_json_tokens']:,}\n")

        summary_text.append("Total TOON Tokens: ", style="bold green")
        summary_text.append(f"{summary['total_toon_tokens']:,}\n")

        summary_text.append("Total Savings: ", style="bold magenta")
        summary_text.append(f"{summary['total_savings_tokens']:,} tokens ")
        summary_text.append(
            f"({summary['average_savings_percent']:.1f}%)\n",
            style="bold magenta",
        )

        summary_text.append("\nLast Updated: ", style="dim")
        summary_text.append(f"{summary['last_updated']}", style="dim italic")

        summary_panel = Panel(
            summary_text,
            title="[bold]Overall Token Usage Statistics[/bold]",
            border_style="cyan",
        )
        console.print(summary_panel)

        # Get daily/weekly stats
        if month:
            days = 30
            title = "Last 30 Days"
        elif week:
            days = 7
            title = "Last 7 Days"
        else:
            days = 1
            title = "Today"

        daily_stats = tracker.get_weekly_stats(weeks=(days + 6) // 7)

        if not daily_stats:
            Console.print_warning(f"No metrics recorded for {title.lower()}")
            Console.print()
            Console.print("[dim]Metrics are automatically logged when using TOON format.[/dim]")
            Console.print("[dim]Run examples or health workflows to generate metrics.[/dim]")
            return

        # Create daily stats table
        table = Table(
            title=f"[bold]{title} - Token Savings[/bold]",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Date", style="cyan", no_wrap=True)
        table.add_column("Operations", justify="right", style="yellow")
        table.add_column("JSON Tokens", justify="right", style="yellow")
        table.add_column("TOON Tokens", justify="right", style="green")
        table.add_column("Savings", justify="right", style="magenta")
        table.add_column("Savings %", justify="right", style="bold magenta")

        # Show most recent days first
        for daily in daily_stats[:days]:
            table.add_row(
                daily.date,
                str(daily.total_operations),
                f"{daily.total_json_tokens:,}",
                f"{daily.total_toon_tokens:,}",
                f"{daily.total_savings_tokens:,}",
                f"{daily.average_savings_percent:.1f}%",
            )

        console.print()
        console.print(table)

        # Show breakdown by data type if available
        if daily_stats and daily_stats[0].operations_by_type:
            console.print()
            type_table = Table(
                title="[bold]Operations by Type[/bold]",
                show_header=True,
                header_style="bold cyan",
            )
            type_table.add_column("Data Type", style="cyan")
            type_table.add_column("Count", justify="right", style="yellow")

            for data_type, count in sorted(
                daily_stats[0].operations_by_type.items(),
                key=lambda x: x[1],
                reverse=True,
            ):
                type_table.add_row(data_type, str(count))

            console.print(type_table)

        # Show breakdown by agent pair if available
        if daily_stats and daily_stats[0].operations_by_agent_pair:
            console.print()
            agent_table = Table(
                title="[bold]Operations by Agent Communication[/bold]",
                show_header=True,
                header_style="bold cyan",
            )
            agent_table.add_column("Agent Pair", style="cyan")
            agent_table.add_column("Count", justify="right", style="yellow")

            for pair, count in sorted(
                daily_stats[0].operations_by_agent_pair.items(),
                key=lambda x: x[1],
                reverse=True,
            ):
                agent_table.add_row(pair, str(count))

            console.print(agent_table)

        # Show usage hints
        console.print()
        console.print("[dim]Options:[/dim]")
        console.print("[dim]  --week     Show last 7 days[/dim]")
        console.print("[dim]  --month    Show last 30 days[/dim]")
        console.print("[dim]  --export   Export to CSV file[/dim]")
        console.print()
        console.print("[dim]Metrics location: .claude/metrics/[/dim]")

    except FileNotFoundError:
        Console.print_warning("No metrics found")
        Console.print()
        Console.print("[dim]Metrics are automatically logged when using TOON format.[/dim]")
        Console.print("[dim]Run examples or health workflows to generate metrics.[/dim]")
        raise typer.Exit(0)
    except Exception as e:
        Console.print_error(f"Failed to show stats: {e}")
        import traceback

        traceback.print_exc()
        raise typer.Exit(1)


@app.command("clear")
def clear_stats(
    confirm: bool = typer.Option(
        False,
        "--confirm",
        "-y",
        help="Confirm deletion without prompting",
    ),
):
    """Clear all token usage statistics."""
    try:
        if not confirm:
            Console.print_warning("This will delete all metrics data.")
            response = typer.confirm("Are you sure?")
            if not response:
                Console.print("Cancelled")
                raise typer.Exit(0)

        tracker = get_tracker()
        metrics_dir = tracker.metrics_dir

        # Delete all metric files
        import shutil

        if metrics_dir.exists():
            shutil.rmtree(metrics_dir)
            metrics_dir.mkdir(parents=True, exist_ok=True)
            tracker._ensure_summary_exists()

        Console.print_success("All metrics cleared")

    except Exception as e:
        Console.print_error(f"Failed to clear stats: {e}")
        raise typer.Exit(1)


# Default command
@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Show token usage statistics (default command)."""
    if ctx.invoked_subcommand is None:
        # No subcommand specified, run show_stats with defaults
        show_stats(week=False, month=False, export=None)
