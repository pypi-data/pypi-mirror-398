"""
Configuration validation using JSON schemas.

Provides schema-based validation for all configuration types with
user-friendly error messages.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import jsonschema
    from jsonschema import ValidationError as JsonSchemaValidationError
    from jsonschema import SchemaError

    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    JsonSchemaValidationError = Exception
    SchemaError = Exception


class ConfigValidator:
    """
    JSON schema validator for configuration files.

    Loads schemas from .claude/schemas/ directory and validates configs
    against them. Provides user-friendly error messages.

    Examples:
        >>> validator = ConfigValidator(Path(".claude/schemas"))
        >>> errors = validator.validate(config_data, "settings")
        >>> if errors:
        ...     print(f"Validation failed: {errors}")
    """

    def __init__(self, schemas_dir: Optional[Path] = None):
        """
        Initialize validator with schemas directory.

        Args:
            schemas_dir: Path to directory containing JSON schemas
                        Defaults to .claude/schemas in current project
        """
        if schemas_dir is None:
            # Try to find schemas in current project
            from claux.core.config import OrchestratorConfig

            try:
                config = OrchestratorConfig.from_repo_root()
                schemas_dir = config.schemas_dir
            except Exception:
                # Fallback to None, will check on validation
                schemas_dir = None

        self.schemas_dir = schemas_dir
        self._schemas: Dict[str, Dict[str, Any]] = {}
        self._jsonschema_available = JSONSCHEMA_AVAILABLE

    def load_schema(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Load and cache schema by name.

        Args:
            name: Schema name (without .schema.json extension)

        Returns:
            Schema dictionary or None if not found

        Examples:
            >>> schema = validator.load_schema("settings")
            >>> if schema:
            ...     print(f"Loaded schema with {len(schema)} properties")
        """
        # Return cached if available
        if name in self._schemas:
            return self._schemas[name]

        # Check if schemas directory exists
        if self.schemas_dir is None or not self.schemas_dir.exists():
            return None

        # Load schema file
        schema_file = self.schemas_dir / f"{name}.schema.json"
        if not schema_file.exists():
            return None

        try:
            with open(schema_file, "r", encoding="utf-8") as f:
                schema = json.load(f)
                self._schemas[name] = schema
                return schema
        except Exception as e:
            # Log error but don't fail
            print(f"Warning: Failed to load schema {name}: {e}")
            return None

    def validate(self, data: Dict[str, Any], schema_name: str) -> List[str]:
        """
        Validate data against schema.

        Args:
            data: Configuration data to validate
            schema_name: Name of schema to validate against

        Returns:
            List of error messages (empty list = valid)

        Examples:
            >>> errors = validator.validate(config, "settings")
            >>> if not errors:
            ...     print("Configuration is valid")
        """
        # Check if jsonschema is available
        if not self._jsonschema_available:
            return [
                "jsonschema library not installed. "
                "Install with: pip install jsonschema"
            ]

        # Load schema
        schema = self.load_schema(schema_name)
        if schema is None:
            return [f"Schema not found: {schema_name}"]

        # Validate
        try:
            jsonschema.validate(data, schema)
            return []  # Valid - no errors
        except JsonSchemaValidationError as e:
            return [self._format_validation_error(e)]
        except SchemaError as e:
            return [f"Invalid schema '{schema_name}': {e.message}"]
        except Exception as e:
            return [f"Validation error: {str(e)}"]

    def validate_with_details(
        self, data: Dict[str, Any], schema_name: str
    ) -> tuple[bool, List[str]]:
        """
        Validate and return both success status and errors.

        Args:
            data: Configuration data to validate
            schema_name: Name of schema to validate against

        Returns:
            Tuple of (is_valid, error_list)

        Examples:
            >>> valid, errors = validator.validate_with_details(config, "settings")
            >>> if not valid:
            ...     for error in errors:
            ...         print(f"  - {error}")
        """
        errors = self.validate(data, schema_name)
        return (len(errors) == 0, errors)

    def _format_validation_error(self, error: JsonSchemaValidationError) -> str:
        """
        Format jsonschema validation error for user readability.

        Args:
            error: ValidationError from jsonschema

        Returns:
            Formatted error message

        Examples:
            Error: "Failed validating 'enum' in schema['properties']['language']"
            Formatted: "language: must be one of ['en', 'ru']"
        """
        # Build path to error location
        if error.path:
            path_parts = [str(p) for p in error.path]
            path = ".".join(path_parts)
        else:
            path = "root"

        # Format message based on error type
        message = error.message

        # Add constraint info for common validation types
        if error.validator == "enum":
            if "enum" in error.schema:
                valid_values = ", ".join(f"'{v}'" for v in error.schema["enum"])
                message = f"must be one of [{valid_values}]"
        elif error.validator == "type":
            expected_type = error.schema.get("type", "unknown")
            message = f"must be of type '{expected_type}'"
        elif error.validator == "required":
            missing = error.message.split("'")[1] if "'" in error.message else "unknown"
            message = f"missing required property '{missing}'"
        elif error.validator == "pattern":
            pattern = error.schema.get("pattern", "")
            message = f"must match pattern: {pattern}"
        elif error.validator == "minimum":
            minimum = error.schema.get("minimum")
            message = f"must be >= {minimum}"
        elif error.validator == "maximum":
            maximum = error.schema.get("maximum")
            message = f"must be <= {maximum}"

        return f"{path}: {message}"

    def list_available_schemas(self) -> List[str]:
        """
        List all available schema names.

        Returns:
            List of schema names (without .schema.json extension)

        Examples:
            >>> schemas = validator.list_available_schemas()
            >>> print(f"Available schemas: {', '.join(schemas)}")
        """
        if self.schemas_dir is None or not self.schemas_dir.exists():
            return []

        schemas = []
        for schema_file in self.schemas_dir.glob("*.schema.json"):
            name = schema_file.stem.replace(".schema", "")
            schemas.append(name)

        return sorted(schemas)

    def validate_all(
        self, configs: Dict[str, tuple[Dict[str, Any], str]]
    ) -> Dict[str, List[str]]:
        """
        Validate multiple configurations at once.

        Args:
            configs: Dict mapping config names to (data, schema_name) tuples

        Returns:
            Dict mapping config names to error lists (only includes configs with errors)

        Examples:
            >>> configs = {
            ...     "settings": (settings_data, "settings"),
            ...     "user": (user_data, "user-config")
            ... }
            >>> errors = validator.validate_all(configs)
            >>> for name, err_list in errors.items():
            ...     print(f"{name}: {len(err_list)} errors")
        """
        all_errors: Dict[str, List[str]] = {}

        for config_name, (data, schema_name) in configs.items():
            errors = self.validate(data, schema_name)
            if errors:
                all_errors[config_name] = errors

        return all_errors

    def is_jsonschema_available(self) -> bool:
        """
        Check if jsonschema library is available.

        Returns:
            True if jsonschema is installed, False otherwise
        """
        return self._jsonschema_available


# Convenience function
def validate_config(
    data: Dict[str, Any], schema_name: str, schemas_dir: Optional[Path] = None
) -> List[str]:
    """
    Validate configuration data against schema (convenience function).

    Args:
        data: Configuration data to validate
        schema_name: Schema name to validate against
        schemas_dir: Optional path to schemas directory

    Returns:
        List of error messages (empty = valid)

    Examples:
        >>> from claux.core.validation import validate_config
        >>> errors = validate_config(settings, "settings")
        >>> if errors:
        ...     print(f"Invalid: {errors}")
    """
    validator = ConfigValidator(schemas_dir)
    return validator.validate(data, schema_name)
