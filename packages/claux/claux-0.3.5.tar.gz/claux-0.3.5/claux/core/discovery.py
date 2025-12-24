"""
Project discovery utilities.

This module provides functionality for discovering git repositories
in directory trees and gathering metadata about detected projects.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional

from claux.core.detection import detect_project_type, recommend_mcp_config


def find_projects_in_directory(
    search_dir: Path, max_depth: int = 3, exclude_dirs: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Find all git repositories in directory tree.

    Args:
        search_dir: Directory to search.
        max_depth: Maximum depth to search.
        exclude_dirs: Directory names to exclude (e.g., ["node_modules", ".venv"]).

    Returns:
        List of project dicts with keys: path, name, type, has_orchestrator.
    """
    if exclude_dirs is None:
        exclude_dirs = [
            "node_modules",
            ".venv",
            "venv",
            ".git",
            "__pycache__",
            "dist",
            "build",
            ".next",
            "target",
            ".cache",
            ".pytest_cache",
        ]

    projects = []

    def search_recursive(current_dir: Path, current_depth: int):
        if current_depth > max_depth:
            return

        # Check if current directory is a git repo
        if (current_dir / ".git").exists():
            project_type = detect_project_type(current_dir)
            has_orchestrator = (current_dir / ".claude").exists()

            projects.append(
                {
                    "path": current_dir,
                    "name": current_dir.name,
                    "type": project_type,
                    "has_orchestrator": has_orchestrator,
                    "recommended_mcp": recommend_mcp_config(project_type),
                }
            )
            # Don't search deeper if we found a git repo
            return

        # Search subdirectories
        try:
            for item in current_dir.iterdir():
                if item.is_dir() and item.name not in exclude_dirs:
                    search_recursive(item, current_depth + 1)
        except PermissionError:
            pass

    search_recursive(search_dir, 0)
    return projects
