"""
Interactive menu components for MCP, agents, language, and configuration.

Provides submenu handlers for different configuration areas.
"""

import typer
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.separator import Separator
from rich.console import Console
from rich.table import Table
from typing import List, Optional

from claux.i18n import t
from claux.core.user_config import get_config
from claux.ui.industrial_theme import (
    IndustrialIcons as Icons,
    format_status,
    format_number,
    NOTHING_THEME,
)
from claux.ui.menu import MenuItem, BaseMenu, TableMenu

console = Console(force_terminal=True, legacy_windows=False, theme=NOTHING_THEME)


# ============================================================================
# MCP Menu (Migrated to TableMenu)
# ============================================================================

class MCPConfigMenu(TableMenu):
    """MCP configuration menu using new architecture."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._configs = None
        self._current = None
        self._load_configs()

    def _load_configs(self):
        """Load MCP configurations."""
        from claux.core.mcp import list_configs, get_active_config

        self._configs = list_configs()
        self._current = get_active_config()

    def get_items(self) -> List[MenuItem]:
        """Build menu items from MCP configurations."""
        if not self._configs:
            # No configs available - return empty list
            # The show() method will handle this gracefully
            return []

        items = []
        for config_name in self._configs:
            is_active = (config_name == self._current)

            items.append(MenuItem(
                id=config_name,
                label=config_name,
                icon="ACTIVE" if is_active else "INACTIVE",
                enabled=True,
                visible=True,
                metadata={"is_active": is_active}
            ))

        return items

    def handle_selection(self, item_id: str) -> Optional[str]:
        """Handle MCP configuration selection."""
        from claux.core.mcp import switch_config

        # Switch to selected config
        switch_config(item_id)

        # Show success message
        self.console.print(
            f"\n[green]✓[/green] {t('cli.interactive.mcp_switched', config=item_id)}"
        )
        self.console.print(
            f"[yellow]![/yellow] {t('cli.interactive.mcp_restart')}\n"
        )

        # Return None to stay in menu and show pause
        return None

    def get_table_data(self) -> dict:
        """Build table showing MCP configurations."""
        config_details = {
            "base": (format_number(600), t("cli.interactive.mcp_base_desc")),
            "full": (format_number(5000, abbreviated=True), t("cli.interactive.mcp_full_desc")),
        }

        columns = [
            ("", "green", "left", 3),  # (name, style, justify, width)
            (t("cli.interactive.mcp_name"), "cyan", "left"),
            (t("cli.interactive.mcp_tokens"), "yellow", "right"),
            (t("cli.interactive.mcp_description"), "dim", "left"),
        ]

        rows = []
        for config_name in self._configs:
            indicator = format_status(config_name == self._current)
            tokens, desc = config_details.get(
                config_name,
                ("?", t("cli.interactive.mcp_custom_desc"))
            )
            rows.append((indicator, config_name, tokens, desc))

        return {
            "columns": columns,
            "rows": rows,
            "show_header": True
        }


def mcp_menu():
    """MCP configuration submenu (migrated to new architecture)."""
    from claux.core.mcp import list_configs

    # Check if configs exist before showing menu
    configs = list_configs()
    if not configs:
        console.print(f"[yellow]{t('cli.interactive.mcp_no_configs')}[/yellow]")
        console.print(f"[dim]{t('cli.interactive.mcp_invalid_directory')}[/dim]\n")
        typer.pause(t("cli.common.press_enter"))
        return

    # Create and show menu
    menu = MCPConfigMenu()
    result = menu.show(
        title=t("cli.interactive.mcp_title"),
        breadcrumb=f"Main > {t('cli.interactive.mcp_breadcrumb')}"
    )

    # Handle exit if user pressed Ctrl+C
    if result == "exit":
        return "exit"


# ============================================================================
# Agent Profiles Menu (Migrated to TableMenu)
# ============================================================================

class AgentProfilesMenu(TableMenu):
    """Agent profiles menu using new architecture."""

    # Profile metadata (agents count, token savings, description)
    PROFILE_INFO = {
        "base": ("8", "82%", "cli.interactive.agents_minimal"),
        "nextjs-full": ("28", "22%", "cli.interactive.agents_nextjs_full"),
        "health-all": ("15", "56%", "cli.interactive.agents_health_all"),
        "development": ("12", "67%", "cli.interactive.agents_development"),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._profiles = None
        self._current = None
        self._load_profiles()

    def _load_profiles(self):
        """Load agent profiles."""
        from claux.core.profiles import list_profiles, get_active_profile

        self._profiles = list_profiles()
        self._current = get_active_profile()

    def get_items(self) -> List[MenuItem]:
        """Build menu items from agent profiles."""
        if not self._profiles:
            return []

        items = []
        for profile in self._profiles:
            is_active = (profile == self._current)

            items.append(MenuItem(
                id=profile,
                label=profile,
                icon="ACTIVE" if is_active else "INACTIVE",
                enabled=True,
                visible=True,
                metadata={"is_active": is_active}
            ))

        return items

    def handle_selection(self, item_id: str) -> Optional[str]:
        """Handle profile selection."""
        from claux.core.profiles import activate_profile

        # Activate selected profile
        activate_profile(item_id)

        # Get profile info for success message
        agents, savings, _ = self.PROFILE_INFO.get(item_id, ("?", "?", ""))

        # Show success message
        self.console.print(
            f"\n[green]✓[/green] {t('cli.interactive.agents_activated', profile=item_id)}"
        )
        self.console.print(
            f"[dim]  {t('cli.interactive.agents_info', agents=agents, savings=savings)}[/dim]"
        )
        self.console.print(
            f"[yellow]![/yellow] {t('cli.interactive.mcp_restart')}\n"
        )

        return None

    def get_table_data(self) -> dict:
        """Build table showing agent profiles."""
        columns = [
            ("", "green", "left", 3),
            (t("cli.interactive.agents_profile"), "cyan", "left"),
            (t("cli.interactive.agents_agents"), "blue", "right"),
            (t("cli.interactive.agents_savings"), "yellow", "right"),
            (t("cli.interactive.agents_description"), "dim", "left"),
        ]

        rows = []
        for profile in self._profiles:
            indicator = format_status(profile == self._current)
            agents, savings, desc_key = self.PROFILE_INFO.get(
                profile,
                ("?", "?", "cli.interactive.agents_custom")
            )
            desc = t(desc_key)
            rows.append((indicator, profile, agents, savings, desc))

        return {
            "columns": columns,
            "rows": rows,
            "show_header": True
        }


def agent_profiles_menu():
    """Agent profiles submenu (migrated to new architecture)."""
    from claux.core.profiles import list_profiles

    # Check if profiles exist before showing menu
    profiles = list_profiles()
    if not profiles:
        console.print(f"[yellow]{t('cli.interactive.agents_no_profiles')}[/yellow]")
        console.print(f"[dim]{t('cli.interactive.mcp_invalid_directory')}[/dim]\n")
        typer.pause(t("cli.common.press_enter"))
        return

    # Create and show menu
    menu = AgentProfilesMenu()
    result = menu.show(
        title=t("cli.interactive.agents_title"),
        breadcrumb=f"Main > {t('cli.interactive.agents_breadcrumb')}"
    )

    # Handle exit if user pressed Ctrl+C
    if result == "exit":
        return "exit"


# ============================================================================
# Language Menu (Migrated to BaseMenu)
# ============================================================================

class LanguageMenu(BaseMenu):
    """Language selection menu using new architecture."""

    # Language display names
    LANG_NAMES = {
        "en": "English",
        "ru": "Russian (Русский)",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._langs = None
        self._current = None
        self._load_languages()

    def _load_languages(self):
        """Load available languages."""
        from claux.i18n import get_available_languages, get_language

        self._langs = get_available_languages()
        self._current = get_language()

    def get_items(self) -> List[MenuItem]:
        """Build menu items from available languages."""
        items = []
        for lang in self._langs:
            is_active = (lang == self._current)
            display_name = self.LANG_NAMES.get(lang, lang)

            items.append(MenuItem(
                id=lang,
                label=display_name,
                icon="ACTIVE" if is_active else "INACTIVE",
                enabled=True,
                visible=True,
                metadata={"is_active": is_active}
            ))

        return items

    def handle_selection(self, item_id: str) -> Optional[str]:
        """Handle language selection."""
        from claux.i18n import set_language

        # Set new language
        set_language(item_id)

        # Reset banner flag so it shows with new language
        from claux.commands import interactive
        interactive._banner_shown = False

        # Get language display name
        lang_name = self.LANG_NAMES.get(item_id, item_id)

        # Show success message
        self.console.print(
            f"\n[green]✓[/green] {t('cli.interactive.lang_switched', lang=lang_name)}"
        )
        self.console.print(
            f"[dim]  {t('cli.interactive.lang_env_note', lang=item_id)}[/dim]"
        )
        self.console.print(
            f"[dim]  {t('cli.interactive.lang_apply_next')}[/dim]\n"
        )

        return None

    def show_header(self, title: str, breadcrumb: Optional[str] = None):
        """Override to show language selection prompt."""
        super().show_header(title, breadcrumb)
        self.console.print(f"[dim]{t('cli.interactive.lang_select_prompt')}[/dim]\n")


def language_menu():
    """Language settings submenu (migrated to new architecture)."""
    menu = LanguageMenu()
    result = menu.show(
        title=t("cli.interactive.lang_title"),
        breadcrumb=f"Main > {t('cli.interactive.lang_breadcrumb')}"
    )

    if result == "exit":
        return "exit"


# ============================================================================
# Config Menu (Migrated to BaseMenu)
# ============================================================================

class ConfigMenu(BaseMenu):
    """Configuration menu using new architecture."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._config = get_config()

    def get_items(self) -> List[MenuItem]:
        """Build configuration menu items."""
        return [
            MenuItem(
                id="view",
                label=t("cli.interactive.config_view"),
                icon=None,
                enabled=True
            ),
            MenuItem(
                id="language",
                label=t("cli.interactive.config_language"),
                icon=None,
                enabled=True
            ),
            MenuItem(
                id="toggle_claude",
                label=t("cli.interactive.config_toggle_claude_exit"),
                icon=None,
                enabled=True
            ),
            MenuItem(
                id="reset",
                label=t("cli.interactive.config_reset"),
                icon=None,
                enabled=True
            ),
        ]

    def handle_selection(self, item_id: str) -> Optional[str]:
        """Handle configuration action."""
        if item_id == "view":
            self._view_config()
        elif item_id == "language":
            self._change_language()
        elif item_id == "toggle_claude":
            self._toggle_claude_exit()
        elif item_id == "reset":
            self._reset_config()

        # Return None to stay in menu (pause will happen automatically)
        return None

    def _view_config(self):
        """View current configuration."""
        import yaml

        self.console.print()
        self.console.print(f"[bold]{t('cli.interactive.config_current')}[/bold]\n")
        self.console.print(yaml.dump(self._config.load(), default_flow_style=False))

    def _toggle_claude_exit(self):
        """Toggle Claude Code exit behavior."""
        exit_after_close = self._config.get("claude.exit_after_close", True)
        new_value = not exit_after_close
        self._config.set("claude.exit_after_close", new_value)

        behavior = (
            t("cli.interactive.config_claude_exit_enabled")
            if new_value
            else t("cli.interactive.config_claude_exit_disabled")
        )
        self.console.print(
            f"\n[green]✓[/green] {t('cli.interactive.config_claude_exit_changed', behavior=behavior)}"
        )

    def _change_language(self):
        """Change interface language."""
        from claux.i18n import get_available_languages, get_language, set_language

        # Get available languages
        langs = get_available_languages()
        current = get_language()

        # Language display names
        lang_names = {
            "en": "English",
            "ru": "Russian (Русский)",
        }

        # Build choices
        choices = []
        for lang in langs:
            display_name = lang_names.get(lang, lang)
            indicator = "●" if lang == current else "○"
            choices.append(Choice(lang, f"{indicator}  {display_name}"))

        self.console.print()
        selected = inquirer.select(
            message=t("cli.interactive.lang_select_prompt"),
            choices=choices,
            pointer=">",
        ).execute()

        if selected != current:
            # Set new language
            set_language(selected)

            # Reset banner flag so it shows with new language
            from claux.commands import interactive
            interactive._banner_shown = False

            # Get language display name
            lang_name = lang_names.get(selected, selected)

            # Show success message
            self.console.print(
                f"\n[green]✓[/green] {t('cli.interactive.lang_switched', lang=lang_name)}"
            )
            self.console.print(
                f"[dim]  {t('cli.interactive.lang_env_note', lang=selected)}[/dim]"
            )
            self.console.print(
                f"[dim]  {t('cli.interactive.lang_apply_next')}[/dim]"
            )
        else:
            self.console.print(f"\n[dim]{t('cli.interactive.lang_no_change')}[/dim]")

    def _reset_config(self):
        """Reset configuration to defaults."""
        from InquirerPy import inquirer

        confirm = inquirer.confirm(
            message=t("cli.interactive.config_reset_confirm"),
            default=False,
        ).execute()

        if confirm:
            self._config.reset()
            self.console.print(
                f"\n[green]✓[/green] {t('cli.interactive.config_reset_success')}"
            )

    def show_header(self, title: str, breadcrumb: Optional[str] = None):
        """Override to show config management prompt and current setting."""
        super().show_header(title, breadcrumb)
        self.console.print(f"[dim]{t('cli.interactive.config_manage')}[/dim]\n")

        # Show current Claude Code behavior
        exit_after_close = self._config.get("claude.exit_after_close", True)
        behavior_text = (
            t("cli.interactive.config_claude_exit_enabled")
            if exit_after_close
            else t("cli.interactive.config_claude_exit_disabled")
        )
        self.console.print(f"[dim]Current: {behavior_text}[/dim]\n")


def config_menu():
    """Configuration menu (migrated to new architecture)."""
    menu = ConfigMenu()
    result = menu.show(
        title=t("cli.interactive.config_title"),
        breadcrumb=f"Main > {t('cli.interactive.config_breadcrumb')}"
    )

    if result == "exit":
        return "exit"
