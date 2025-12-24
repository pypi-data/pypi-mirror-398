"""
Menu building utilities for dynamic context-aware menus.

Provides functions to build menu choices based on project context.
"""

from InquirerPy.base.control import Choice
from InquirerPy.separator import Separator

from claux.ui.industrial_theme import IndustrialIcons as Icons


def build_quick_actions(context):
    """
    Build Quick Actions menu items based on project context.

    Args:
        context: ProjectContext with current directory status

    Returns:
        List of Choice objects for Quick Actions
    """
    if not context.is_git:
        return []  # No quick actions for non-git directories

    if not context.has_claux:
        # Git repo without Claux - offer installation
        return [Choice("install", f"{Icons.LAUNCH}  Install Claux in this project")]

    # Claux installed - show management actions
    actions = []

    # Change agent profile
    profile = context.agent_profile or "none"
    actions.append(
        Choice("change_profile", f"{Icons.AGENT}  Change agent profile (current: {profile})")
    )

    # Switch MCP config
    mcp = context.mcp_config or "none"
    actions.append(Choice("switch_mcp", f"{Icons.MCP}  Switch MCP config (current: {mcp})"))

    # Update Claux files
    actions.append(Choice("update_claux", f"{Icons.ARROW_RIGHT}  Update Claux files"))

    return actions


def build_menu_choices(context):
    """
    Build complete menu based on project context.

    Args:
        context: ProjectContext with current directory status

    Returns:
        List of Choice objects for the complete menu
    """
    choices = []

    # Quick Actions (context-dependent)
    quick_actions = build_quick_actions(context)
    if quick_actions:
        choices.extend(quick_actions)
        choices.append(Separator())

    # Launch Claude Code (only if Claux installed)
    if context.has_claux:
        choices.append(Choice("launch", f"{Icons.LAUNCH}  Launch Claude Code"))
        choices.append(Separator())

    # Configuration (only if git repo)
    if context.is_git:
        choices.append(Choice("mcp", f"{Icons.MCP}  MCP Configurations"))
        choices.append(Choice("agents", f"{Icons.AGENT}  Agent Profiles"))

    # Settings (always available)
    choices.append(Choice("config", f"{Icons.CONFIG}  Settings"))
    choices.append(Separator())

    # Tools & Utilities
    if context.has_claux:
        choices.append(Choice("backups", f"{Icons.DOCS}  Backups"))
    choices.append(Choice("doctor", f"{Icons.INFO}  Doctor"))
    choices.append(Separator())

    # Help & Exit
    choices.append(Choice("help", f"{Icons.HELP}  Help"))
    choices.append(Choice("exit", f"{Icons.ARROW_LEFT}  Exit (q)"))

    return choices
