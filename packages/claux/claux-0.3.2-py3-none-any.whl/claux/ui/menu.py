"""
Base menu system for scalable TUI architecture.

Provides abstract base class for all menus with common behavior,
eliminating boilerplate and ensuring consistency.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Any, Callable
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.separator import Separator
from rich.console import Console
import typer

from claux.i18n import t
from claux.ui.industrial_theme import IndustrialIcons as Icons, NOTHING_THEME


@dataclass
class MenuItem:
    """Configuration for a single menu item.

    Attributes:
        id: Unique identifier for the item
        label: Display text (can be i18n key or direct text)
        icon: Icon name from IndustrialIcons (optional)
        action: Action to perform when selected (callable or string)
        visible: Whether item is visible in menu
        enabled: Whether item can be selected
        metadata: Additional data for custom handling

    Example:
        >>> MenuItem(
        ...     id="launch",
        ...     label="cli.interactive.launch",
        ...     icon="LAUNCH",
        ...     action=launch_claude_code,
        ...     visible=True,
        ...     enabled=True
        ... )
    """
    id: str
    label: str
    icon: Optional[str] = None
    action: Optional[Any] = None
    visible: bool = True
    enabled: bool = True
    metadata: dict = field(default_factory=dict)

    def get_display_name(self, translate: bool = True) -> str:
        """Get formatted display name with icon.

        Args:
            translate: Whether to translate label using i18n

        Returns:
            Formatted string with icon and label

        Example:
            "▶  Launch Claude Code"
        """
        # Translate label if it looks like an i18n key
        label_text = t(self.label) if translate and "." in self.label else self.label

        # Add icon if specified
        if self.icon:
            icon_char = getattr(Icons, self.icon, "")
            return f"{icon_char}  {label_text}" if icon_char else label_text

        return label_text


class BaseMenu(ABC):
    """Abstract base class for all menus.

    Eliminates boilerplate by providing common menu behavior:
    - Clear screen and show header
    - Build choices from MenuItem list
    - Handle selection loop
    - Show help footer
    - Handle back/exit navigation

    Subclasses only need to implement:
    - get_items(): Return list of menu items
    - handle_selection(): Handle selected item

    Example:
        >>> class MCPMenu(BaseMenu):
        ...     def get_items(self) -> List[MenuItem]:
        ...         return [
        ...             MenuItem(id="base", label="Base", icon="ACTIVE"),
        ...             MenuItem(id="full", label="Full", icon="INACTIVE")
        ...         ]
        ...
        ...     def handle_selection(self, item_id: str) -> Optional[str]:
        ...         print(f"Selected: {item_id}")
        ...         return None
        ...
        >>> menu = MCPMenu()
        >>> menu.show(title="MCP Configurations")
    """

    def __init__(self, context=None, console: Optional[Console] = None):
        """Initialize base menu.

        Args:
            context: Project context (optional)
            console: Rich console instance (optional, creates default if None)
        """
        self.context = context
        self.console = console or Console(
            force_terminal=True,
            legacy_windows=False,
            theme=NOTHING_THEME
        )

    @abstractmethod
    def get_items(self) -> List[MenuItem]:
        """Get menu items to display.

        Implemented by subclass to provide menu-specific items.

        Returns:
            List of MenuItem objects

        Example:
            >>> def get_items(self) -> List[MenuItem]:
            ...     return [
            ...         MenuItem(id="option1", label="First Option", icon="LAUNCH"),
            ...         MenuItem(id="option2", label="Second Option", icon="CONFIG")
            ...     ]
        """
        pass

    @abstractmethod
    def handle_selection(self, item_id: str) -> Optional[str]:
        """Handle user selection.

        Implemented by subclass to perform action when item is selected.

        Args:
            item_id: ID of selected menu item

        Returns:
            - "exit": Exit the application completely
            - "back": Return to previous menu (refresh current)
            - None: Stay in current menu (will pause and refresh)

        Example:
            >>> def handle_selection(self, item_id: str) -> Optional[str]:
            ...     if item_id == "option1":
            ...         do_something()
            ...         return None  # Stay in menu
            ...     elif item_id == "option2":
            ...         return "back"  # Go back
        """
        pass

    def build_choices(self, items: List[MenuItem]) -> List[Choice]:
        """Convert MenuItem list to InquirerPy choices.

        Filters out invisible items and adds separator before back option.

        Args:
            items: List of menu items

        Returns:
            List of InquirerPy Choice objects
        """
        choices = []

        # Add visible items
        for item in items:
            if not item.visible:
                continue

            display_name = item.get_display_name(translate=True)
            choices.append(Choice(
                value=item.id,
                name=display_name,
                enabled=item.enabled
            ))

        # Add separator and back option
        if choices:  # Only add separator if there are items
            choices.append(Separator())

        back_label = t("cli.interactive.back")
        choices.append(Choice(value="back", name=back_label))

        return choices

    def show_header(self, title: str, breadcrumb: Optional[str] = None):
        """Show menu header with title and optional breadcrumbs.

        Args:
            title: Menu title (can be i18n key or direct text)
            breadcrumb: Breadcrumb trail (e.g., "Main > Settings > MCP")
        """
        self.console.clear()

        # Show breadcrumbs if provided
        if breadcrumb:
            from claux.commands.interactive_ui import show_breadcrumbs
            show_breadcrumbs(breadcrumb)

        # Translate title if it looks like i18n key
        title_text = t(title) if "." in title else title
        self.console.print(f"[bold cyan]{title_text}[/bold cyan]\n")

        # Show help footer
        from claux.commands.interactive_ui import show_help_footer
        show_help_footer()

    def show(
        self,
        title: str,
        breadcrumb: Optional[str] = None,
        message: Optional[str] = None
    ) -> Optional[str]:
        """Display menu and handle interaction loop.

        Main entry point for displaying the menu. Handles the complete
        interaction cycle: display, select, handle, repeat.

        Args:
            title: Menu title (can be i18n key or direct text)
            breadcrumb: Breadcrumb trail (optional)
            message: Custom selection message (optional, uses default if None)

        Returns:
            - "exit": User wants to exit application
            - "back": User wants to go back
            - None: Menu completed normally

        Example:
            >>> menu = MyMenu()
            >>> result = menu.show(
            ...     title="cli.interactive.settings",
            ...     breadcrumb="Main > Settings"
            ... )
            >>> if result == "exit":
            ...     sys.exit(0)
        """
        while True:
            # Show header (clear screen, title, breadcrumbs, help)
            self.show_header(title, breadcrumb)

            # Get menu items from subclass
            items = self.get_items()

            # Build choices for InquirerPy
            choices = self.build_choices(items)

            # Default message or custom
            select_message = message or t("cli.interactive.select_option")

            # Show menu and get selection
            try:
                selection = inquirer.select(
                    message=select_message,
                    choices=choices,
                    pointer=">",
                ).execute()
            except KeyboardInterrupt:
                # Ctrl+C pressed - exit application
                return "exit"
            except Exception as e:
                # Fallback for incompatible terminals (Cygwin, etc.)
                self.console.print(
                    f"[yellow]!  {t('cli.interactive.unsupported_terminal')}[/yellow]"
                )
                self.console.print(
                    f"[dim]{t('cli.interactive.try_different_terminal')}[/dim]\n"
                )
                typer.pause()
                return "back"

            # Handle back navigation
            if selection == "back" or selection == "b":
                return "back"

            # Let subclass handle the selection
            result = self.handle_selection(selection)

            # Handle result
            if result == "exit":
                return "exit"
            elif result == "back":
                # Subclass wants to refresh menu
                continue

            # Default: pause and refresh menu
            self.console.print()
            typer.pause(t("cli.common.press_enter"))


class TableMenu(BaseMenu):
    """Base menu that displays items in a table format.

    Extends BaseMenu to show items in a Rich table before the menu.
    Useful for displaying detailed information alongside menu choices.

    Subclasses implement:
    - get_items(): Menu items
    - handle_selection(): Selection handler
    - get_table_data(): Table configuration and rows

    Example:
        >>> class MCPConfigMenu(TableMenu):
        ...     def get_table_data(self):
        ...         return {
        ...             "columns": [("Name", "cyan"), ("Tokens", "yellow")],
        ...             "rows": [("base", "≈600"), ("full", "≈5k")]
        ...         }
    """

    @abstractmethod
    def get_table_data(self) -> dict:
        """Get table configuration and data.

        Returns:
            Dictionary with:
            - columns: List of (name, style, justify?) tuples
            - rows: List of row tuples
            - title: Optional table title
            - show_header: Optional bool (default True)

        Example:
            >>> {
            ...     "columns": [
            ...         ("Name", "cyan", "left"),
            ...         ("Status", "green", "center")
            ...     ],
            ...     "rows": [
            ...         ("Item 1", "Active"),
            ...         ("Item 2", "Inactive")
            ...     ],
            ...     "title": "Configuration Status",
            ...     "show_header": True
            ... }
        """
        pass

    def show_table(self):
        """Display table before menu choices."""
        from rich.table import Table

        table_data = self.get_table_data()

        # Create table
        table = Table(
            show_header=table_data.get("show_header", True),
            header_style="bold white",
            border_style="dim",
            padding=(0, 1),
        )

        # Add columns
        for col in table_data["columns"]:
            name = col[0]
            style = col[1] if len(col) > 1 else None
            justify = col[2] if len(col) > 2 else "left"
            width = col[3] if len(col) > 3 else None

            table.add_column(name, style=style, justify=justify, width=width)

        # Add rows
        for row in table_data["rows"]:
            table.add_row(*[str(cell) for cell in row])

        # Print table
        self.console.print(table)
        self.console.print()

    def show(
        self,
        title: str,
        breadcrumb: Optional[str] = None,
        message: Optional[str] = None
    ) -> Optional[str]:
        """Display table and menu."""
        while True:
            # Show header
            self.show_header(title, breadcrumb)

            # Show table
            self.show_table()

            # Get and show menu (rest is same as BaseMenu)
            items = self.get_items()
            choices = self.build_choices(items)
            select_message = message or t("cli.interactive.select_option")

            try:
                selection = inquirer.select(
                    message=select_message,
                    choices=choices,
                    pointer=">",
                ).execute()
            except KeyboardInterrupt:
                return "exit"
            except Exception:
                self.console.print(
                    f"[yellow]!  {t('cli.interactive.unsupported_terminal')}[/yellow]"
                )
                typer.pause()
                return "back"

            if selection == "back" or selection == "b":
                return "back"

            result = self.handle_selection(selection)

            if result == "exit":
                return "exit"
            elif result == "back":
                continue

            self.console.print()
            typer.pause(t("cli.common.press_enter"))
