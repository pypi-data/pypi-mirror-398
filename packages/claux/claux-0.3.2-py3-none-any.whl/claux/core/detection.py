"""
Project type detection and MCP configuration recommendations.

This module provides utilities for automatically detecting project types
based on files present in a directory and recommending appropriate MCP
configurations for each project type.
"""

from pathlib import Path
from enum import Enum


class ProjectType(str, Enum):
    """Detected project types."""

    PYTHON = "python"
    NODEJS = "nodejs"
    NEXTJS = "nextjs"
    REACT = "react"
    DJANGO = "django"
    FASTAPI = "fastapi"
    UNKNOWN = "unknown"


def detect_project_type(project_path: Path) -> ProjectType:
    """
    Detect project type based on files present.

    Args:
        project_path: Path to project directory.

    Returns:
        Detected ProjectType.
    """
    # Check for Next.js
    if (
        (project_path / "next.config.js").exists()
        or (project_path / "next.config.ts").exists()
        or (project_path / "next.config.mjs").exists()
    ):
        return ProjectType.NEXTJS

    # Check for React (package.json with react dependency)
    package_json = project_path / "package.json"
    if package_json.exists():
        try:
            import json

            with open(package_json) as f:
                data = json.load(f)
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                if "react" in deps:
                    return ProjectType.REACT
                if "next" in deps:
                    return ProjectType.NEXTJS
        except Exception:
            pass

    # Check for Django
    if (project_path / "manage.py").exists():
        manage_py = project_path / "manage.py"
        if manage_py.exists():
            content = manage_py.read_text()
            if "django" in content.lower():
                return ProjectType.DJANGO

    # Check for FastAPI
    requirements = project_path / "requirements.txt"
    if requirements.exists():
        content = requirements.read_text()
        if "fastapi" in content.lower():
            return ProjectType.FASTAPI

    pyproject = project_path / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text()
        if "fastapi" in content.lower():
            return ProjectType.FASTAPI

    # Check for Python (generic)
    if (
        (project_path / "setup.py").exists()
        or (project_path / "pyproject.toml").exists()
        or (project_path / "requirements.txt").exists()
        or list(project_path.glob("*.py"))
    ):
        return ProjectType.PYTHON

    # Check for Node.js (generic)
    if (project_path / "package.json").exists():
        return ProjectType.NODEJS

    return ProjectType.UNKNOWN


def recommend_mcp_config(project_type: ProjectType) -> str:
    """
    Recommend MCP configuration based on project type.

    Args:
        project_type: Detected project type.

    Returns:
        Recommended MCP config name (e.g., "base", "frontend", "supabase").
    """
    recommendations = {
        ProjectType.NEXTJS: "frontend",
        ProjectType.REACT: "frontend",
        ProjectType.DJANGO: "supabase",
        ProjectType.FASTAPI: "supabase",
        ProjectType.PYTHON: "base",
        ProjectType.NODEJS: "base",
        ProjectType.UNKNOWN: "base",
    }
    return recommendations.get(project_type, "base")
