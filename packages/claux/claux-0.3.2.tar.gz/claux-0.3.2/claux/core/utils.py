"""
Utility functions for Claude Code Orchestrator Kit.

Provides common file operations, path resolution, and agent file parsing.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple


def find_git_root(start_path: Optional[Path] = None) -> Path:
    """
    Find git repository root by searching upwards for .git directory.

    Args:
        start_path: Starting path for search. Defaults to current directory.

    Returns:
        Path to repository root.

    Raises:
        FileNotFoundError: If no git repository found.
    """
    if start_path is None:
        start_path = Path.cwd()
    else:
        start_path = Path(start_path).resolve()

    current = start_path
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent

    raise FileNotFoundError(
        f"No git repository found from {start_path}. " "Make sure you're inside a git repository."
    )


def load_json_file(
    file_path: Union[str, Path], default: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Load JSON file with error handling.

    Args:
        file_path: Path to JSON file.
        default: Default value to return if file doesn't exist or is invalid.

    Returns:
        Parsed JSON data as dict.

    Raises:
        json.JSONDecodeError: If default is None and file contains invalid JSON.
        FileNotFoundError: If default is None and file doesn't exist.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        if default is not None:
            return default
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        if default is not None:
            return default
        raise json.JSONDecodeError(f"Invalid JSON in {file_path}: {e.msg}", e.doc, e.pos)


def save_json_file(
    file_path: Union[str, Path], data: Dict[str, Any], indent: int = 2, ensure_parents: bool = True
) -> None:
    """
    Save data as JSON file with proper formatting.

    Args:
        file_path: Path to save JSON file.
        data: Data to serialize as JSON.
        indent: Indentation level for JSON formatting.
        ensure_parents: Create parent directories if they don't exist.

    Raises:
        OSError: If file cannot be written.
    """
    file_path = Path(file_path)

    if ensure_parents:
        file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)
        f.write("\n")  # Add trailing newline


def parse_agent_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Parse agent markdown file and extract metadata.

    Extracts frontmatter (if present) and content from agent files.

    Args:
        file_path: Path to agent markdown file.

    Returns:
        Dict with keys:
            - name: Agent file name (without extension)
            - path: Full path to file
            - content: Full file content
            - frontmatter: Parsed frontmatter (if present)
            - description: First paragraph or empty string

    Raises:
        FileNotFoundError: If file doesn't exist.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Agent file not found: {file_path}")

    content = file_path.read_text(encoding="utf-8")

    # Extract frontmatter (YAML between --- markers)
    frontmatter = {}
    description = ""

    frontmatter_match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if frontmatter_match:
        # Parse simple YAML frontmatter (key: value pairs)
        fm_text = frontmatter_match.group(1)
        for line in fm_text.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                frontmatter[key.strip()] = value.strip()

        # Content after frontmatter
        content_after_fm = content[frontmatter_match.end() :]
    else:
        content_after_fm = content

    # Extract first paragraph as description
    lines = content_after_fm.strip().split("\n")
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#"):
            description = line
            break

    return {
        "name": file_path.stem,
        "path": str(file_path),
        "content": content,
        "frontmatter": frontmatter,
        "description": description,
    }


def expand_glob_patterns(
    base_dir: Union[str, Path], patterns: List[str], exclude_patterns: Optional[List[str]] = None
) -> List[Path]:
    """
    Expand glob patterns to list of files.

    Args:
        base_dir: Base directory for glob expansion.
        patterns: List of glob patterns (e.g., ['agents/**/*.md']).
        exclude_patterns: Optional list of glob patterns to exclude.

    Returns:
        List of resolved file paths matching patterns.

    Examples:
        >>> expand_glob_patterns(
        ...     Path(".claude"),
        ...     ["agents/**/*.md"],
        ...     ["agents/health/**/*.md"]
        ... )
        [Path('.claude/agents/meta/orchestrator.md'), ...]
    """
    base_dir = Path(base_dir)
    matched_files = set()

    # Expand include patterns
    for pattern in patterns:
        for file_path in base_dir.glob(pattern):
            if file_path.is_file():
                matched_files.add(file_path.resolve())

    # Remove exclude patterns
    if exclude_patterns:
        excluded_files = set()
        for pattern in exclude_patterns:
            for file_path in base_dir.glob(pattern):
                if file_path.is_file():
                    excluded_files.add(file_path.resolve())

        matched_files -= excluded_files

    return sorted(matched_files)


def validate_json_schema(
    data: Dict[str, Any], schema_path: Union[str, Path]
) -> Tuple[bool, Optional[str]]:
    """
    Validate JSON data against a JSON Schema.

    Args:
        data: Data to validate.
        schema_path: Path to JSON Schema file.

    Returns:
        Tuple of (is_valid, error_message).
        If valid, returns (True, None).
        If invalid, returns (False, error_message).

    Note:
        Requires jsonschema package to be installed.
        If jsonschema not available, returns (True, None) with warning.
    """
    try:
        import jsonschema
    except ImportError:
        return True, None  # Skip validation if jsonschema not installed

    schema_path = Path(schema_path)
    if not schema_path.exists():
        return False, f"Schema file not found: {schema_path}"

    try:
        schema = load_json_file(schema_path)
        jsonschema.validate(data, schema)
        return True, None
    except jsonschema.ValidationError as e:
        return False, f"Validation error: {e.message}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: File size in bytes.

    Returns:
        Formatted string (e.g., '1.5 KB', '2.3 MB').

    Examples:
        >>> format_file_size(1024)
        '1.0 KB'
        >>> format_file_size(1536)
        '1.5 KB'
        >>> format_file_size(1048576)
        '1.0 MB'
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def truncate_string(text: str, max_length: int = 80, suffix: str = "...") -> str:
    """
    Truncate string to maximum length with suffix.

    Args:
        text: String to truncate.
        max_length: Maximum length (including suffix).
        suffix: Suffix to add when truncated.

    Returns:
        Truncated string.

    Examples:
        >>> truncate_string("Hello World", 8)
        'Hello...'
        >>> truncate_string("Short", 20)
        'Short'
    """
    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def count_tokens_estimate(text: str) -> int:
    """
    Estimate token count for text (rough approximation).

    Uses simple heuristic: ~4 characters per token for English text.

    Args:
        text: Text to estimate tokens for.

    Returns:
        Estimated token count.

    Note:
        This is a rough approximation. For accurate counts,
        use a tokenizer from transformers or tiktoken.
    """
    # Simple heuristic: average 4 characters per token
    return len(text) // 4
