"""
MCP (Model Context Protocol) configuration management.

Handles loading, switching, and validating MCP server configurations
stored in the mcp/ directory.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from claux.core.config import OrchestratorConfig


# Known MCP configurations metadata
MCP_CONFIGS = {
    "base": {
        "display_name": "BASE",
        "description": "Context7 + Sequential Thinking",
        "estimated_tokens": 600,
    },
    "supabase-only": {
        "display_name": "SUPABASE",
        "description": "Base + Supabase MegaCampusAI",
        "estimated_tokens": 2500,
    },
    "supabase-full": {
        "display_name": "SUPABASE + LEGACY",
        "description": "Base + Supabase + Legacy project",
        "estimated_tokens": 3000,
    },
    "n8n": {
        "display_name": "N8N",
        "description": "Base + n8n-workflows + n8n-mcp",
        "estimated_tokens": 2500,
    },
    "frontend": {
        "display_name": "FRONTEND",
        "description": "Base + Playwright + ShadCN",
        "estimated_tokens": 2000,
    },
    "serena": {
        "display_name": "SERENA",
        "description": "Base + Serena LSP semantic search",
        "estimated_tokens": 2500,
    },
    "full": {
        "display_name": "FULL",
        "description": "All servers including Serena",
        "estimated_tokens": 6500,
    },
}


@dataclass
class MCPConfig:
    """
    Represents an MCP configuration.

    Attributes:
        name: Configuration name (e.g., 'base', 'frontend').
        display_name: Display name for UI (e.g., 'BASE', 'FRONTEND').
        description: Human-readable description.
        estimated_tokens: Estimated token count for prompt context.
        servers: List of server names (mcpServers keys).
        file_path: Path to .mcp.<name>.json file.
    """

    name: str
    display_name: str
    description: str
    estimated_tokens: int
    servers: List[str]
    file_path: Path

    @staticmethod
    def from_file(file_path: Path) -> "MCPConfig":
        """
        Load MCP config from JSON file.

        Parses .mcp.<name>.json to extract:
        - name (from filename)
        - servers (top-level keys in mcpServers object)
        - Infer display_name, description, estimated_tokens from known configs

        Args:
            file_path: Path to .mcp.<name>.json file.

        Returns:
            MCPConfig instance.

        Raises:
            FileNotFoundError: If file doesn't exist.
            json.JSONDecodeError: If file contains invalid JSON.
            ValueError: If file doesn't have expected structure.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"MCP config file not found: {file_path}")

        # Parse JSON
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON in {file_path}: {e.msg}", e.doc, e.pos)

        # Extract name from filename (.mcp.<name>.json)
        filename = file_path.name
        if not filename.startswith(".mcp.") or not filename.endswith(".json"):
            raise ValueError(
                f"Invalid MCP config filename: {filename}. " "Expected format: .mcp.<name>.json"
            )

        name = filename[5:-5]  # Remove ".mcp." prefix and ".json" suffix

        # Extract servers from mcpServers object
        if "mcpServers" not in data:
            raise ValueError(f"MCP config {file_path} missing 'mcpServers' key")

        servers = list(data["mcpServers"].keys())

        # Get metadata from known configs, or use defaults
        metadata = MCP_CONFIGS.get(name, {})
        display_name = metadata.get("display_name", name.upper())
        description = metadata.get("description", "Custom configuration")
        estimated_tokens = metadata.get("estimated_tokens", 0)

        return MCPConfig(
            name=name,
            display_name=display_name,
            description=description,
            estimated_tokens=estimated_tokens,
            servers=servers,
            file_path=file_path,
        )


class MCPManager:
    """
    High-level MCP configuration management.

    Provides methods for listing, switching, and validating MCP configurations.
    """

    def __init__(self, config: OrchestratorConfig):
        """
        Initialize MCP manager.

        Args:
            config: Orchestrator configuration instance.
        """
        self.config = config
        self.mcp_dir = config.repo_root / "mcp"
        self.active_file = config.repo_root / ".mcp.json"

    def list_configs(self) -> List[MCPConfig]:
        """
        List all available MCP configurations from mcp/ directory.

        Returns:
            List of MCPConfig instances, sorted by name.

        Raises:
            FileNotFoundError: If mcp/ directory doesn't exist.
        """
        if not self.mcp_dir.exists():
            raise FileNotFoundError(
                f"MCP directory not found: {self.mcp_dir}. "
                "Are you in a Claude Code Orchestrator Kit project?"
            )

        configs = []
        for config_file in self.mcp_dir.glob(".mcp.*.json"):
            # Skip example files
            if config_file.name.endswith(".example.json"):
                continue

            try:
                config = MCPConfig.from_file(config_file)
                configs.append(config)
            except Exception:
                # Skip invalid configs
                pass

        # Sort by name
        configs.sort(key=lambda c: c.name)

        return configs

    def get_config(self, name: str) -> Optional[MCPConfig]:
        """
        Get specific MCP configuration by name.

        Args:
            name: Configuration name (e.g., 'base', 'frontend').

        Returns:
            MCPConfig instance if found, None otherwise.
        """
        config_file = self.mcp_dir / f".mcp.{name}.json"

        if not config_file.exists():
            return None

        try:
            return MCPConfig.from_file(config_file)
        except Exception:
            return None

    def get_active_config(self) -> Optional[MCPConfig]:
        """
        Get currently active MCP configuration.

        Parses .mcp.json to determine which config it matches.

        Returns:
            MCPConfig instance if active config matches a known config,
            None otherwise.
        """
        if not self.active_file.exists():
            return None

        try:
            # Load active config
            with open(self.active_file, "r", encoding="utf-8") as f:
                active_data = json.load(f)

            active_servers = set(active_data.get("mcpServers", {}).keys())

            # Try to match against known configs
            for config in self.list_configs():
                config_servers = set(config.servers)
                if config_servers == active_servers:
                    return config

            # No match found - might be custom
            return None

        except Exception:
            return None

    def switch_config(self, name: str) -> None:
        """
        Switch to a different MCP configuration.

        Copies mcp/.mcp.<name>.json to .mcp.json in repo root.

        Args:
            name: Configuration name to switch to.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            IOError: If copy operation fails.
        """
        source_file = self.mcp_dir / f".mcp.{name}.json"

        if not source_file.exists():
            raise FileNotFoundError(f"MCP configuration '{name}' not found at {source_file}")

        # Validate config before switching
        errors = self.validate_config(name)
        if errors:
            raise ValueError(f"Invalid MCP configuration '{name}':\n" + "\n".join(errors))

        # Copy file
        try:
            with open(source_file, "r", encoding="utf-8") as f:
                config_data = f.read()

            with open(self.active_file, "w", encoding="utf-8") as f:
                f.write(config_data)

        except IOError as e:
            raise IOError(f"Failed to copy config file: {e}")

    def validate_config(self, name: str) -> List[str]:
        """
        Validate MCP configuration JSON.

        Args:
            name: Configuration name to validate.

        Returns:
            List of error messages. Empty list means valid.
        """
        errors = []

        config_file = self.mcp_dir / f".mcp.{name}.json"

        if not config_file.exists():
            errors.append(f"Config file not found: {config_file}")
            return errors

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON: {e.msg} at line {e.lineno}")
            return errors

        # Check for required top-level key
        if "mcpServers" not in data:
            errors.append("Missing required key: 'mcpServers'")

        # Check mcpServers is an object
        if not isinstance(data.get("mcpServers"), dict):
            errors.append("'mcpServers' must be an object")
            return errors

        # Validate each server config
        for server_name, server_config in data["mcpServers"].items():
            if not isinstance(server_config, dict):
                errors.append(f"Server '{server_name}' config must be an object")
                continue

            # Check required fields
            if "command" not in server_config:
                errors.append(f"Server '{server_name}' missing 'command' field")

            if "args" not in server_config:
                errors.append(f"Server '{server_name}' missing 'args' field")

            # Validate args is a list
            if "args" in server_config and not isinstance(server_config["args"], list):
                errors.append(f"Server '{server_name}' 'args' must be an array")

        return errors

    def get_active_servers(self) -> List[str]:
        """
        Get list of active server names from .mcp.json.

        Returns:
            List of server names, or empty list if .mcp.json doesn't exist.
        """
        if not self.active_file.exists():
            return []

        try:
            with open(self.active_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            return list(data.get("mcpServers", {}).keys())

        except Exception:
            return []

    def detect_profile_from_active(self, settings: dict) -> Optional[str]:
        """
        Detect which MCP profile is currently active based on server configuration.

        Compares the active MCP servers against known profile signatures to identify
        which profile is currently in use.

        Args:
            settings: Settings dict containing mcpServers configuration

        Returns:
            Name of detected MCP profile ('base', 'frontend', 'full'), or None if no match
        """
        if "mcpServers" not in settings:
            return None

        mcp_servers = set(settings["mcpServers"].keys())

        # Define MCP profile signatures
        profiles = {
            "base": {"context7", "sequential-thinking"},
            "frontend": {"context7", "sequential-thinking", "playwright", "shadcn"},
            "full": {"context7", "sequential-thinking", "playwright", "shadcn", "supabase", "n8n"},
        }

        # Find best match
        for profile_name, servers in profiles.items():
            if servers == mcp_servers:
                return profile_name

        return None


# Convenience functions for easy access without creating MCPManager instance


def list_configs() -> List[str]:
    """
    List all available MCP configuration names.

    Returns:
        List of configuration names (e.g., ['base', 'full', 'frontend']).
        Returns empty list if not in a valid project or no configs found.
    """
    try:
        from claux.core.config import OrchestratorConfig

        config = OrchestratorConfig.from_repo_root()
        manager = MCPManager(config)
        configs = manager.list_configs()
        return [c.name for c in configs]
    except Exception:
        return []


def get_active_config() -> Optional[str]:
    """
    Get the name of the currently active MCP configuration.

    Returns:
        Configuration name if found (e.g., 'base'), None otherwise.
    """
    try:
        from claux.core.config import OrchestratorConfig

        config = OrchestratorConfig.from_repo_root()
        manager = MCPManager(config)
        active = manager.get_active_config()
        return active.name if active else None
    except Exception:
        return None


def switch_config(name: str) -> None:
    """
    Switch to a different MCP configuration.

    Args:
        name: Configuration name to switch to (e.g., 'base', 'full').

    Raises:
        FileNotFoundError: If configuration doesn't exist.
        ValueError: If configuration is invalid.
        IOError: If copy operation fails.
    """
    from claux.core.config import OrchestratorConfig

    config = OrchestratorConfig.from_repo_root()
    manager = MCPManager(config)
    manager.switch_config(name)
