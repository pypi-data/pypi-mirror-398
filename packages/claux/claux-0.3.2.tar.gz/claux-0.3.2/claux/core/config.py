"""
Configuration management for Claude Code Orchestrator Kit.

Handles loading and caching of configuration from .claude directory structure.
Provides singleton access to orchestrator configuration.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class OrchestratorConfig:
    """
    Main configuration class for Claude Code Orchestrator Kit.

    Attributes:
        repo_root: Path to repository root directory.
        claude_dir: Path to .claude directory.
        agent_profiles_dir: Path to agent profiles directory.
        active_profile_file: Path to active profile marker file.
        settings_file: Path to settings.local.json.
        tmp_dir: Path to temporary files directory.
        reports_dir: Path to reports directory.
        agents_dir: Path to agents directory.
        commands_dir: Path to commands directory.
        skills_dir: Path to skills directory.
        schemas_dir: Path to JSON schemas directory.
        settings: Loaded settings from settings.local.json.
        active_profile: Name of currently active agent profile.
    """

    repo_root: Path
    claude_dir: Path
    agent_profiles_dir: Path
    active_profile_file: Path
    settings_file: Path
    tmp_dir: Path
    reports_dir: Path
    agents_dir: Path
    commands_dir: Path
    skills_dir: Path
    schemas_dir: Path
    settings: Dict[str, Any] = field(default_factory=dict)
    active_profile: Optional[str] = None

    @classmethod
    def from_repo_root(cls, repo_root: Optional[Path] = None) -> "OrchestratorConfig":
        """
        Create configuration from repository root.

        Args:
            repo_root: Path to repository root. If None, searches from current directory.

        Returns:
            OrchestratorConfig instance.

        Raises:
            FileNotFoundError: If .claude directory not found.
        """
        from claux.core.utils import find_git_root

        if repo_root is None:
            repo_root = find_git_root(Path.cwd())
        else:
            repo_root = Path(repo_root).resolve()

        claude_dir = repo_root / ".claude"

        if not claude_dir.exists():
            raise FileNotFoundError(
                f".claude directory not found at {claude_dir}. "
                "Are you in a Claude Code Orchestrator Kit project?"
            )

        # Core directories
        agent_profiles_dir = claude_dir / "agent-profiles"
        active_profile_file = claude_dir / ".active-agent-profile"
        settings_file = claude_dir / "settings.local.json"
        tmp_dir = repo_root / ".tmp" / "current"
        reports_dir = repo_root / "docs" / "reports"
        agents_dir = claude_dir / "agents"
        commands_dir = claude_dir / "commands"
        skills_dir = claude_dir / "skills"
        schemas_dir = claude_dir / "schemas"

        # Load settings
        settings = {}
        if settings_file.exists():
            try:
                with open(settings_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)
            except Exception as e:
                # Non-fatal: use empty settings if load fails
                settings = {"_load_error": str(e)}

        # Load active profile
        active_profile = None
        if active_profile_file.exists():
            try:
                active_profile = active_profile_file.read_text(encoding="utf-8").strip()
            except Exception:
                # Non-fatal: no active profile
                pass

        return cls(
            repo_root=repo_root,
            claude_dir=claude_dir,
            agent_profiles_dir=agent_profiles_dir,
            active_profile_file=active_profile_file,
            settings_file=settings_file,
            tmp_dir=tmp_dir,
            reports_dir=reports_dir,
            agents_dir=agents_dir,
            commands_dir=commands_dir,
            skills_dir=skills_dir,
            schemas_dir=schemas_dir,
            settings=settings,
            active_profile=active_profile,
        )

    def get_profile_path(self, profile_name: str) -> Optional[Path]:
        """
        Get path to profile JSON file.

        Args:
            profile_name: Name of profile (e.g., 'base' or 'custom/myprofile').

        Returns:
            Path to profile file if it exists, None otherwise.
        """
        # Check for custom profile
        if profile_name.startswith("custom/"):
            profile_path = self.agent_profiles_dir / f"{profile_name}.profile.json"
        else:
            profile_path = self.agent_profiles_dir / f"{profile_name}.profile.json"

        return profile_path if profile_path.exists() else None

    def load_profile(self, profile_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Load agent profile configuration.

        Args:
            profile_name: Name of profile to load. If None, uses active profile.

        Returns:
            Profile configuration dict, or None if not found.

        Raises:
            json.JSONDecodeError: If profile file contains invalid JSON.
        """
        if profile_name is None:
            profile_name = self.active_profile

        if profile_name is None:
            return None

        profile_path = self.get_profile_path(profile_name)
        if profile_path is None:
            return None

        with open(profile_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_profiles(self) -> List[Dict[str, Any]]:
        """
        List all available agent profiles.

        Returns:
            List of profile metadata dicts with keys: name, display_name, description, etc.
        """
        profiles = []

        # Standard profiles
        if self.agent_profiles_dir.exists():
            for profile_file in self.agent_profiles_dir.glob("*.profile.json"):
                try:
                    with open(profile_file, "r", encoding="utf-8") as f:
                        profile_data = json.load(f)
                        profiles.append(
                            {
                                "name": profile_file.stem.replace(".profile", ""),
                                "display_name": profile_data.get("displayName", ""),
                                "description": profile_data.get("description", ""),
                                "estimated_tokens": profile_data.get("estimatedTokens", 0),
                                "path": str(profile_file),
                                "is_custom": False,
                            }
                        )
                except Exception:
                    # Skip invalid profiles
                    pass

        # Custom profiles
        custom_dir = self.agent_profiles_dir / "custom"
        if custom_dir.exists():
            for profile_file in custom_dir.glob("*.profile.json"):
                try:
                    with open(profile_file, "r", encoding="utf-8") as f:
                        profile_data = json.load(f)
                        name = profile_file.stem.replace(".profile", "")
                        profiles.append(
                            {
                                "name": f"custom/{name}",
                                "display_name": profile_data.get("displayName", ""),
                                "description": profile_data.get("description", ""),
                                "estimated_tokens": profile_data.get("estimatedTokens", 0),
                                "path": str(profile_file),
                                "is_custom": True,
                            }
                        )
                except Exception:
                    # Skip invalid profiles
                    pass

        return profiles

    def activate_profile(self, profile_name: str) -> bool:
        """
        Activate an agent profile.

        Args:
            profile_name: Name of profile to activate.

        Returns:
            True if activation successful, False otherwise.
        """
        profile_path = self.get_profile_path(profile_name)
        if profile_path is None:
            return False

        # Validate profile is valid JSON
        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                json.load(f)
        except Exception:
            return False

        # Write active profile marker
        try:
            self.active_profile_file.write_text(profile_name, encoding="utf-8")
            self.active_profile = profile_name
            return True
        except Exception:
            return False

    def deactivate_profile(self) -> bool:
        """
        Deactivate current profile (revert to loading all agents).

        Returns:
            True if deactivation successful, False otherwise.
        """
        if self.active_profile_file.exists():
            try:
                self.active_profile_file.unlink()
                self.active_profile = None
                return True
            except Exception:
                return False
        return True  # Already deactivated


# Singleton instance
_config_instance: Optional[OrchestratorConfig] = None


def get_config(repo_root: Optional[Path] = None, force_reload: bool = False) -> OrchestratorConfig:
    """
    Get singleton configuration instance.

    Args:
        repo_root: Path to repository root. If None, searches from current directory.
        force_reload: If True, reload configuration even if already loaded.

    Returns:
        OrchestratorConfig instance.

    Raises:
        FileNotFoundError: If .claude directory not found.
    """
    global _config_instance

    if _config_instance is None or force_reload:
        _config_instance = OrchestratorConfig.from_repo_root(repo_root)

    return _config_instance
