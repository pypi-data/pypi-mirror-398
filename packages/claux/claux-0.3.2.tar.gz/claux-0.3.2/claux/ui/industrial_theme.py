"""
Nothing OS × UNIX Industrial Theme

Minimalist, monochrome TUI with semantic Unicode symbols.
Inspired by Nothing OS and classic UNIX tools.
"""

from typing import Optional
from rich.theme import Theme
from rich.box import Box
from rich.panel import Panel
from rich.table import Table
from rich.console import Console

from claux.ui.theme import get_terminal_width, supports_unicode


# ============================================================================
# Symbol Sets
# ============================================================================

class IndustrialIcons:
    """Semantic Unicode symbols for industrial TUI."""

    # Status & State
    ACTIVE = "●"          # Selected, on, running
    INACTIVE = "○"        # Unselected, off, stopped
    FOCUSED = "◉"         # Primary focus, working
    PROCESSING = "◍"      # Busy, loading, background
    IDLE = "◌"            # Waiting, standby

    # Actions & Navigation
    LAUNCH = "▶"          # Start, execute, run
    PROFILE = "▸"         # Active selection, config
    AGENT = "▷"           # Background worker, process
    ARROW_RIGHT = "→"     # Next, forward, go
    ARROW_LEFT = "←"      # Back, return, exit
    NESTED = "›"          # Child, submenu, indent
    LOCALE = "»"          # Language, region

    # Categories & Functions
    WIZARD = "◆"          # Setup, quickstart
    CONFIG = "≡"          # Settings, menu
    DOCS = "∷"            # Documentation, bookmarks
    HELP = "?"            # Help, unknown, info
    MCP = "⚡"            # MCP, fast, power
    LANGUAGE = "λ"        # Programming language
    GIT = "±"             # Version control, diff
    PATH = "▸"            # Directory, location

    # Selection & Checkboxes
    UNCHECKED = "□"       # Off, unselected
    CHECKED = "■"         # On, selected
    PARTIAL = "▣"         # Mixed, partial

    # Feedback & Alerts
    SUCCESS = "✓"         # Done, ok, passed
    ERROR = "✗"           # Failed, no, error
    WARNING = "!"         # Attention, caution
    CRITICAL = "‼"        # Urgent, severe
    QUESTION = "?"        # Unknown, help
    FAILED = "×"          # Cancelled, failed
    INFO = "i"            # Information, note

    # Numbers & Metrics
    APPROX = "≈"          # Approximately, estimated
    DELTA = "Δ"           # Change, difference
    TIME = "⏱"            # Duration, elapsed

    # Structural
    BULLET = "•"          # List item
    SEPARATOR = "-"       # Range, divider


# ============================================================================
# Color Schemes
# ============================================================================

NOTHING_THEME = Theme({
    # Monochrome base
    "primary": "white",
    "secondary": "bright_black",

    # Nothing red accent
    "accent": "red bold",
    "alert": "bright_red",

    # Minimal status colors
    "success": "green",
    "warning": "yellow",
    "error": "red bold",

    # Utility
    "dim": "bright_black",
    "highlight": "white bold",
})


# ============================================================================
# Box Styles
# ============================================================================

# Nothing Industrial - sharp angles, minimal
NOTHING_BOX = Box(
    "┏━┳┓\n"
    "┃ ┃┃\n"
    "┣━╋┫\n"
    "┃ ┃┃\n"
    "┣━╋┫\n"
    "┃ ┃┃\n"
    "┣━╋┫\n"
    "┗━┻┛"
)

# UNIX Classic - simple ASCII
UNIX_BOX = Box(
    "+-++\n"
    "| ||\n"
    "+-++\n"
    "| ||\n"
    "+-++\n"
    "| ||\n"
    "+-++\n"
    "+-++"
)


# ============================================================================
# ASCII Art
# ============================================================================

CLAUX_LOGO_INDUSTRIAL = """█▀▀ █   ▄▀█ █ █ ▀▄▀
█▄▄ █▄▄ █▀█ █▄█ █ █"""

CLAUX_LOGO_MINIMAL = """╔═╗╦  ╔═╗╦ ╦═╗ ╦
║  ║  ╠═╣║ ║╔╩╦╝
╚═╝╩═╝╩ ╩╚═╝╩ ╚═"""


# ============================================================================
# Helper Functions
# ============================================================================

def get_industrial_box() -> Box:
    """Get appropriate box style for current terminal."""
    return NOTHING_BOX if supports_unicode() else UNIX_BOX


def format_number(value: int, abbreviated: bool = False) -> str:
    """
    Format numbers in industrial style.

    Args:
        value: Number to format
        abbreviated: Use k/M notation for large numbers

    Returns:
        Formatted string with ≈ prefix

    Examples:
        600 → "≈600"
        5000 → "≈5k" (abbreviated)
        5000 → "≈5000" (not abbreviated)
    """
    if not abbreviated:
        return f"{IndustrialIcons.APPROX}{value}"

    if value >= 1_000_000:
        return f"{IndustrialIcons.APPROX}{value / 1_000_000:.1f}M"
    elif value >= 1_000:
        return f"{IndustrialIcons.APPROX}{value / 1_000:.1f}k".replace('.0k', 'k')
    else:
        return f"{IndustrialIcons.APPROX}{value}"


def format_status(active: bool) -> str:
    """
    Format status indicator.

    Args:
        active: Whether item is active

    Returns:
        Formatted status with icon

    Examples:
        True → "●"
        False → "○"
    """
    return IndustrialIcons.ACTIVE if active else IndustrialIcons.INACTIVE


def format_checkbox(checked: bool, partial: bool = False) -> str:
    """
    Format checkbox indicator.

    Args:
        checked: Whether box is checked
        partial: Whether box is partially checked

    Returns:
        Formatted checkbox

    Examples:
        (True, False) → "■"
        (False, False) → "□"
        (True, True) → "▣"
    """
    if partial:
        return IndustrialIcons.PARTIAL
    return IndustrialIcons.CHECKED if checked else IndustrialIcons.UNCHECKED


def create_industrial_banner(
    title: str,
    subtitle: Optional[str] = None,
    version: Optional[str] = None,
    use_ascii_art: bool = True,
) -> Panel:
    """
    Create Nothing-style banner with optional ASCII art logo.

    Args:
        title: Main title (or use ASCII art if enabled)
        subtitle: Optional subtitle
        version: Optional version string
        use_ascii_art: Use ASCII art logo instead of text title

    Returns:
        Rich Panel with industrial styling
    """
    width = min(get_terminal_width() - 4, 60)

    if use_ascii_art:
        content = CLAUX_LOGO_INDUSTRIAL.strip()
        if version:
            # Add version on same line as logo
            lines = content.split('\n')
            if len(lines) > 0:
                lines[0] += f"  v{version}"
            content = '\n'.join(lines)
        if subtitle:
            content += f"\n{subtitle}"
    else:
        content = f"[primary]{title}[/primary]"
        if version:
            content += f" [dim]v{version}[/dim]"
        if subtitle:
            content += f"\n[dim]{subtitle}[/dim]"

    return Panel(
        content,
        box=get_industrial_box(),
        border_style="primary",
        width=width,
        padding=(1, 2),
    )


def create_industrial_table(
    title: str,
    columns: list[tuple],
    rows: list[tuple],
    show_header: bool = True,
) -> Table:
    """
    Create industrial-style table.

    Args:
        title: Table title
        columns: List of (name, style, justify) tuples
        rows: List of row tuples
        show_header: Whether to show header

    Returns:
        Rich Table with industrial styling
    """
    width = get_terminal_width()

    table = Table(
        title=f"╔═ {title.upper()} " + "═" * (width - len(title) - 10) + "╗",
        box=None,  # No box - clean lines only
        show_header=show_header,
        show_edge=False,
        padding=(0, 2),
        collapse_padding=True,
    )

    # Add columns
    for col in columns:
        name, style = col[0], col[1] if len(col) > 1 else None
        justify = col[2] if len(col) > 2 else "left"
        table.add_column(name, style=style, justify=justify)

    # Add separator after header
    if show_header and rows:
        separator_row = ["━" * 10] * len(columns)
        table.add_row(*separator_row)

    # Add data rows
    for row in rows:
        table.add_row(*[str(cell) for cell in row])

    return table


def create_status_bar(
    state: str = "READY",
    mcp: Optional[str] = None,
    profile: Optional[str] = None,
    python_version: Optional[str] = None,
    time: Optional[str] = None,
) -> str:
    """
    Create UNIX-style status bar.

    Args:
        state: Current state (READY, BUSY, IDLE)
        mcp: MCP config name
        profile: Agent profile name
        python_version: Python version
        time: Current time

    Returns:
        Formatted status bar string

    Example:
        "[●] READY   ⚡ base   ▸ development   λ 3.14   12:34:56"
    """
    parts = []

    # State indicator
    state_icon = {
        "READY": IndustrialIcons.ACTIVE,
        "BUSY": IndustrialIcons.PROCESSING,
        "IDLE": IndustrialIcons.IDLE,
    }.get(state.upper(), IndustrialIcons.QUESTION)

    parts.append(f"[{state_icon}] {state}")

    # MCP
    if mcp:
        parts.append(f"{IndustrialIcons.MCP} {mcp}")

    # Profile
    if profile:
        parts.append(f"{IndustrialIcons.PROFILE} {profile}")

    # Python
    if python_version:
        parts.append(f"{IndustrialIcons.LANGUAGE} {python_version}")

    # Time
    if time:
        parts.append(time)

    return "   ".join(parts)


# ============================================================================
# Console Instance
# ============================================================================

industrial_console = Console(theme=NOTHING_THEME)


# ============================================================================
# Print Helpers
# ============================================================================

def print_success(message: str, console: Optional[Console] = None):
    """Print success message with industrial icon."""
    c = console or industrial_console
    c.print(f"{IndustrialIcons.SUCCESS} {message}")


def print_error(message: str, console: Optional[Console] = None):
    """Print error message with industrial icon."""
    c = console or industrial_console
    c.print(f"{IndustrialIcons.ERROR} {message}")


def print_warning(message: str, console: Optional[Console] = None):
    """Print warning message with industrial icon."""
    c = console or industrial_console
    c.print(f"{IndustrialIcons.WARNING} {message}")


def print_info(message: str, console: Optional[Console] = None):
    """Print info message with industrial icon."""
    c = console or industrial_console
    c.print(f"{IndustrialIcons.INFO} {message}")
