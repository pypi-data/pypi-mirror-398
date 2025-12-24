"""
Claude Code Orchestrator Kit - Python CLI.

Professional automation and orchestration system for Claude Code.
Provides CLI tools for managing agent profiles, workflows, and utilities.
"""

__version__ = "0.3.4"
__author__ = "Ilya Kalinin (Gerrux)"

from claux.core.config import OrchestratorConfig, get_config

__all__ = ["OrchestratorConfig", "get_config", "__version__"]
