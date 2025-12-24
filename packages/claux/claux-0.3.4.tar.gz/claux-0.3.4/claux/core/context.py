"""
Project context detection for Claux.

Provides context-aware functionality by detecting current directory status:
- Git repository detection
- Claux installation status
- Active MCP configuration
- Active agent profile
- Custom files and settings
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from claux.core.utils import find_git_root
from claux.core.mcp import get_active_config
from claux.core.profiles import get_active_profile


@dataclass
class ProjectContext:
    """
    Current project/directory context information.

    Attributes:
        is_git: Whether current directory is in a git repository
        git_root: Path to git root directory (None if not a git repo)
        has_claux: Whether .claude directory exists in the git repo
        claude_dir: Path to .claude directory (None if not installed)
        mcp_config: Active MCP configuration name (e.g., "base", "full", None)
        agent_profile: Active agent profile name (e.g., "base", "development", None)
        has_custom_files: Whether custom files exist (profiles, backups, settings)
        is_upgradeable: Whether existing installation can be upgraded
    """

    is_git: bool
    git_root: Optional[Path]
    has_claux: bool
    claude_dir: Optional[Path]
    mcp_config: Optional[str]
    agent_profile: Optional[str]
    has_custom_files: bool
    is_upgradeable: bool


def detect_project_context(current_dir: Optional[Path] = None) -> ProjectContext:
    """
    Detect complete context for current directory.

    Args:
        current_dir: Directory to check (defaults to current working directory)

    Returns:
        ProjectContext with all detection results

    Example:
        >>> context = detect_project_context()
        >>> if context.is_git and not context.has_claux:
        ...     print("Git repo without Claux - can install")
    """
    if current_dir is None:
        current_dir = Path.cwd()

    # Detect git repository
    is_git = False
    git_root = None
    try:
        git_root = find_git_root(current_dir)
        is_git = git_root is not None
    except Exception:
        pass

    # Detect Claux installation
    # Check for .claude directory AND required components (agents, agent-profiles)
    has_claux = False
    claude_dir = None
    if is_git:
        claude_dir = git_root / ".claude"
        if claude_dir.exists() and claude_dir.is_dir():
            # Require at least agents/ and agent-profiles/ for valid installation
            agents_dir = claude_dir / "agents"
            profiles_dir = claude_dir / "agent-profiles"
            has_claux = agents_dir.exists() and profiles_dir.exists()

    # Detect MCP configuration
    mcp_config = None
    if has_claux:
        try:
            active_mcp = get_active_config()
            if active_mcp:
                mcp_config = active_mcp.name
        except Exception:
            pass

    # Detect agent profile
    agent_profile = None
    if has_claux:
        try:
            active_profile = get_active_profile()
            if active_profile:
                agent_profile = active_profile.name
        except Exception:
            pass

    # Detect custom files
    has_custom_files = False
    if has_claux:
        has_custom_files = has_custom_configuration(claude_dir)

    # Check if upgradeable (always True if installed for now)
    is_upgradeable = has_claux

    return ProjectContext(
        is_git=is_git,
        git_root=git_root,
        has_claux=has_claux,
        claude_dir=claude_dir,
        mcp_config=mcp_config,
        agent_profile=agent_profile,
        has_custom_files=has_custom_files,
        is_upgradeable=is_upgradeable,
    )


def has_custom_configuration(claude_dir: Path) -> bool:
    """
    Check if user has custom files that should be preserved.

    Checks for:
    - Backups directory with actual backups
    - Custom agent profiles
    - Modified settings.local.json
    - Active agent profile set
    - Active MCP config set

    Args:
        claude_dir: Path to .claude directory

    Returns:
        True if any custom files/settings exist

    Example:
        >>> claude_dir = Path(".claude")
        >>> if has_custom_configuration(claude_dir):
        ...     print("User has customizations - preserve them")
    """
    if not claude_dir or not claude_dir.exists():
        return False

    # Check for backups
    backups_dir = claude_dir / "backups"
    if backups_dir.exists() and any(backups_dir.iterdir()):
        return True

    # Check for custom profiles
    custom_profiles_dir = claude_dir / "agent-profiles" / "custom"
    if custom_profiles_dir.exists() and any(custom_profiles_dir.glob("*.json")):
        return True

    # Check for settings.local.json
    settings_file = claude_dir / "settings.local.json"
    if settings_file.exists():
        return True

    # Check for active profile
    active_profile_file = claude_dir / ".active-agent-profile"
    if active_profile_file.exists():
        return True

    # Check for .mcp.json in git root
    if claude_dir.parent.exists():
        mcp_file = claude_dir.parent / ".mcp.json"
        if mcp_file.exists():
            return True

    return False
