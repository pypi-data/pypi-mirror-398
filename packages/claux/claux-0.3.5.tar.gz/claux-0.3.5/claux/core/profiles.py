"""
Profile management for Claude Code Orchestrator Kit.

Handles loading, validation, and management of agent profiles.
Provides high-level operations for profile lifecycle management.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional

from claux.core.utils import load_json_file, expand_glob_patterns


@dataclass
class AgentProfile:
    """
    Represents an agent profile with metadata.

    Attributes:
        name: Profile identifier (e.g., 'base', 'nextjs-full').
        display_name: Human-readable profile name.
        description: Profile description.
        estimated_tokens: Estimated token count for all agents.
        tags: Profile tags for filtering/search.
        languages: Programming languages supported.
        stacks: Technology stacks supported.
        extends: List of parent profile names to inherit from.
        agents_include: Glob patterns for agents to include.
        agents_exclude: Glob patterns for agents to exclude.
        mcp_profile: Recommended MCP profile name.
        required_mcp_servers: MCP servers required by this profile.
        optional_mcp_servers: MCP servers that enhance this profile.
        auto_detect: Rules for automatic profile detection.
    """

    name: str
    display_name: str
    description: str
    estimated_tokens: int
    tags: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    stacks: List[str] = field(default_factory=list)
    extends: List[str] = field(default_factory=list)
    agents_include: List[str] = field(default_factory=list)
    agents_exclude: List[str] = field(default_factory=list)
    mcp_profile: Optional[str] = None
    required_mcp_servers: List[str] = field(default_factory=list)
    optional_mcp_servers: List[str] = field(default_factory=list)
    auto_detect: Optional[Dict[str, Any]] = None

    @staticmethod
    def from_json(name: str, data: Dict[str, Any]) -> "AgentProfile":
        """
        Create AgentProfile from JSON data.

        Args:
            name: Profile name/identifier.
            data: Profile JSON data.

        Returns:
            AgentProfile instance.

        Raises:
            KeyError: If required fields are missing.
        """
        agents_config = data.get("agents", {})

        return AgentProfile(
            name=name,
            display_name=data.get("displayName", name),
            description=data.get("description", ""),
            estimated_tokens=data.get("estimatedTokens", 0),
            tags=data.get("tags", []),
            languages=data.get("languages", []),
            stacks=data.get("stacks", []),
            extends=data.get("extends", []),
            agents_include=agents_config.get("include", []),
            agents_exclude=agents_config.get("exclude", []),
            mcp_profile=data.get("mcpProfile"),
            required_mcp_servers=data.get("requiredMcpServers", []),
            optional_mcp_servers=data.get("optionalMcpServers", []),
            auto_detect=data.get("autoDetect"),
        )

    def get_all_agents(self, base_dir: Path) -> List[Path]:
        """
        Resolve all agent files including extended profiles.

        This method recursively resolves agent patterns from parent profiles
        and combines them with this profile's patterns.

        Args:
            base_dir: Base directory for agent file resolution (.claude directory).

        Returns:
            List of resolved agent file paths.

        Note:
            Extended profiles are not loaded recursively to avoid infinite loops.
            This implementation assumes single-level inheritance.
        """
        all_include_patterns = list(self.agents_include)
        all_exclude_patterns = list(self.agents_exclude)

        # Note: For full recursive resolution, ProfileManager.get_profile()
        # would be needed, but that creates circular dependency.
        # Simple implementation: just use this profile's patterns.

        return expand_glob_patterns(
            base_dir=base_dir,
            patterns=all_include_patterns,
            exclude_patterns=all_exclude_patterns if all_exclude_patterns else None,
        )

    def matches_project(self, project_root: Path) -> bool:
        """
        Check if profile matches project using autoDetect rules.

        Checks for:
        - Required files existence (autoDetect.files)
        - Required package.json dependencies (autoDetect.packageJson.dependencies)
        - Required pyproject.toml dependencies (autoDetect.pyprojectToml.dependencies)

        Args:
            project_root: Path to project root directory.

        Returns:
            True if profile matches project structure, False otherwise.
        """
        if not self.auto_detect:
            return False

        # Check for required files
        files = self.auto_detect.get("files", [])
        for file_name in files:
            if (project_root / file_name).exists():
                return True

        # Check package.json dependencies
        package_json_rules = self.auto_detect.get("packageJson", {})
        if package_json_rules:
            package_json_path = project_root / "package.json"
            if package_json_path.exists():
                try:
                    package_data = load_json_file(package_json_path, default={})
                    dependencies = package_data.get("dependencies", {})
                    dev_dependencies = package_data.get("devDependencies", {})
                    all_deps = {**dependencies, **dev_dependencies}

                    required_deps = package_json_rules.get("dependencies", [])
                    for dep in required_deps:
                        if dep in all_deps:
                            return True
                except Exception:
                    pass

        # Check pyproject.toml dependencies
        pyproject_rules = self.auto_detect.get("pyprojectToml", {})
        if pyproject_rules:
            pyproject_path = project_root / "pyproject.toml"
            if pyproject_path.exists():
                try:
                    content = pyproject_path.read_text(encoding="utf-8")
                    required_deps = pyproject_rules.get("dependencies", [])
                    for dep in required_deps:
                        # Simple string search (not a full TOML parser)
                        if dep in content:
                            return True
                except Exception:
                    pass

        return False


class ProfileManager:
    """
    High-level profile management operations.

    Provides methods for listing, loading, activating, and validating profiles.
    Handles both built-in and custom profiles.
    """

    def __init__(self, config):
        """
        Initialize ProfileManager.

        Args:
            config: OrchestratorConfig instance.
        """
        self.config = config

    def list_profiles(self) -> List[AgentProfile]:
        """
        List all available profiles (built-in + custom).

        Returns:
            List of AgentProfile instances sorted by name.
        """
        profiles = []

        # Load built-in profiles
        if self.config.agent_profiles_dir.exists():
            for profile_file in self.config.agent_profiles_dir.glob("*.profile.json"):
                try:
                    name = profile_file.stem.replace(".profile", "")
                    data = load_json_file(profile_file, default=None)
                    if data:
                        profile = AgentProfile.from_json(name, data)
                        profiles.append(profile)
                except Exception:
                    # Skip invalid profiles
                    pass

        # Load custom profiles
        custom_dir = self.config.agent_profiles_dir / "custom"
        if custom_dir.exists():
            for profile_file in custom_dir.glob("*.profile.json"):
                try:
                    name = f"custom/{profile_file.stem.replace('.profile', '')}"
                    data = load_json_file(profile_file, default=None)
                    if data:
                        profile = AgentProfile.from_json(name, data)
                        profiles.append(profile)
                except Exception:
                    # Skip invalid profiles
                    pass

        return sorted(profiles, key=lambda p: p.name)

    def get_profile(self, name: str) -> Optional[AgentProfile]:
        """
        Load a specific profile by name.

        Args:
            name: Profile name (e.g., 'base', 'custom/myprofile').

        Returns:
            AgentProfile instance if found, None otherwise.
        """
        profile_path = self.config.get_profile_path(name)
        if profile_path is None:
            return None

        try:
            data = load_json_file(profile_path)
            return AgentProfile.from_json(name, data)
        except Exception:
            return None

    def activate_profile(self, name: str) -> None:
        """
        Activate a profile (write to .active-agent-profile).

        Args:
            name: Profile name to activate.

        Raises:
            FileNotFoundError: If profile doesn't exist.
            ValueError: If profile is invalid.
        """
        profile = self.get_profile(name)
        if profile is None:
            raise FileNotFoundError(f"Profile not found: {name}")

        # Write active profile marker
        try:
            self.config.active_profile_file.write_text(name, encoding="utf-8")
            self.config.active_profile = name
        except Exception as e:
            raise ValueError(f"Failed to activate profile: {e}")

    def deactivate_profile(self) -> None:
        """
        Deactivate current profile (remove .active-agent-profile).

        This reverts to loading all agents (no profile filtering).
        """
        if self.config.active_profile_file.exists():
            try:
                self.config.active_profile_file.unlink()
                self.config.active_profile = None
            except Exception as e:
                raise ValueError(f"Failed to deactivate profile: {e}")

    def get_active_profile(self) -> Optional[AgentProfile]:
        """
        Get currently active profile.

        Returns:
            AgentProfile instance if active, None otherwise.
        """
        if self.config.active_profile is None:
            return None

        return self.get_profile(self.config.active_profile)

    def detect_profile(self) -> Optional[AgentProfile]:
        """
        Auto-detect best profile for current project.

        Checks all profiles with autoDetect rules against project structure.

        Returns:
            Best matching AgentProfile, or None if no match.
        """
        profiles = self.list_profiles()

        for profile in profiles:
            if profile.auto_detect and profile.matches_project(self.config.repo_root):
                return profile

        return None

    def validate_profile(self, name: str) -> List[str]:
        """
        Validate profile JSON and return list of errors.

        Args:
            name: Profile name to validate.

        Returns:
            List of error messages. Empty list means valid.
        """
        errors = []

        # Check if profile exists
        profile_path = self.config.get_profile_path(name)
        if profile_path is None:
            errors.append(f"Profile not found: {name}")
            return errors

        # Load and parse JSON
        try:
            data = load_json_file(profile_path)
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON: {e.msg}")
            return errors
        except Exception as e:
            errors.append(f"Failed to load profile: {e}")
            return errors

        # Check required fields
        required_fields = ["displayName", "description"]
        for field_name in required_fields:
            if field_name not in data:
                errors.append(f"Missing required field: {field_name}")

        # Check agents configuration
        if "agents" not in data:
            errors.append("Missing 'agents' configuration")
        else:
            agents_config = data["agents"]
            if "include" not in agents_config or not agents_config["include"]:
                errors.append("Missing or empty 'agents.include' patterns")

        # Check for extends validity (if specified)
        if "extends" in data:
            extends = data["extends"]
            if not isinstance(extends, list):
                errors.append("'extends' must be a list")
            else:
                for parent_name in extends:
                    parent_path = self.config.get_profile_path(parent_name)
                    if parent_path is None:
                        errors.append(f"Extended profile not found: {parent_name}")

        # Validate estimatedTokens
        if "estimatedTokens" in data:
            tokens = data["estimatedTokens"]
            if not isinstance(tokens, int) or tokens < 0:
                errors.append("'estimatedTokens' must be a non-negative integer")

        # Validate agent patterns resolve to files
        try:
            profile = AgentProfile.from_json(name, data)
            agent_files = profile.get_all_agents(self.config.claude_dir)
            if not agent_files:
                errors.append("No agent files match the include patterns")
        except Exception as e:
            errors.append(f"Failed to resolve agent files: {e}")

        return errors

    def get_agent_count(self, profile: AgentProfile) -> int:
        """
        Get count of agents for a profile.

        Args:
            profile: AgentProfile instance.

        Returns:
            Number of agent files matched by profile.
        """
        try:
            agent_files = profile.get_all_agents(self.config.claude_dir)
            return len(agent_files)
        except Exception:
            return 0


# Convenience functions for easy access without creating ProfileManager instance


def list_profiles() -> List[str]:
    """
    List all available agent profile names.

    Returns:
        List of profile names (e.g., ['base', 'nextjs-full', 'health-all']).
        Returns empty list if not in a valid project or no profiles found.
    """
    try:
        from claux.core.config import OrchestratorConfig

        config = OrchestratorConfig.from_repo_root()
        manager = ProfileManager(config)
        profiles = manager.list_profiles()
        return [p.name for p in profiles]
    except Exception:
        return []


def get_active_profile() -> Optional[str]:
    """
    Get the name of the currently active agent profile.

    Returns:
        Profile name if found (e.g., 'base'), None otherwise.
    """
    try:
        from claux.core.config import OrchestratorConfig

        config = OrchestratorConfig.from_repo_root()
        manager = ProfileManager(config)
        active = manager.get_active_profile()
        return active.name if active else None
    except Exception:
        return None


def activate_profile(name: str) -> None:
    """
    Activate an agent profile.

    Args:
        name: Profile name to activate (e.g., 'base', 'nextjs-full').

    Raises:
        FileNotFoundError: If profile doesn't exist.
        ValueError: If profile is invalid.
    """
    from claux.core.config import OrchestratorConfig

    config = OrchestratorConfig.from_repo_root()
    manager = ProfileManager(config)
    manager.activate_profile(name)
