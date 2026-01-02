"""Utility functions for py-mcp-installer-service.

This module provides common utility functions for file operations, command
resolution, credential masking, and safe parsing of configuration files.

Design Philosophy:
- Atomic operations for file writes (temp file + rename)
- Safe parsing with error recovery
- Credential masking for logs
- Cross-platform compatibility
"""

import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from .exceptions import AtomicWriteError, BackupError, ConfigurationError

# ============================================================================
# File Operations (Atomic & Safe)
# ============================================================================


def atomic_write(path: Path, content: str) -> None:
    """Write file atomically using temp file + rename pattern.

    This ensures the file is never in a partially-written state, which is
    critical for configuration files that may be read by other processes.

    Strategy:
    1. Write to temporary file in same directory
    2. Sync to disk (fsync)
    3. Atomic rename to target path

    Args:
        path: Target file path
        content: Content to write

    Raises:
        AtomicWriteError: If write operation fails

    Example:
        >>> atomic_write(Path("/tmp/config.json"), '{"key": "value"}')
    """
    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Create temp file in same directory (required for atomic rename)
    try:
        fd, temp_path = tempfile.mkstemp(
            dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
        )

        try:
            # Write content
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())  # Force write to disk

            # Atomic rename (overwrites existing file atomically)
            os.replace(temp_path, path)

        except Exception as e:
            # Clean up temp file on error
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise AtomicWriteError(f"Failed to write {path}: {e}", str(path)) from e

    except Exception as e:
        raise AtomicWriteError(f"Failed to create temp file: {e}", str(path)) from e


def backup_file(path: Path) -> Path:
    """Create timestamped backup of file.

    Backups are stored in .mcp-installer-backups/ directory next to the
    original file, with timestamp in filename.

    Args:
        path: File to backup

    Returns:
        Path to created backup file

    Raises:
        BackupError: If backup creation fails

    Example:
        >>> backup_path = backup_file(Path("/tmp/config.json"))
        >>> print(backup_path)
        /tmp/.mcp-installer-backups/config.json.20250105_143022.backup
    """
    if not path.exists():
        raise BackupError(f"Cannot backup non-existent file: {path}")

    # Create backup directory
    backup_dir = path.parent / ".mcp-installer-backups"
    try:
        backup_dir.mkdir(exist_ok=True)
    except Exception as e:
        raise BackupError(f"Failed to create backup directory: {e}") from e

    # Generate timestamped backup filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{path.name}.{timestamp}.backup"
    backup_path = backup_dir / backup_name

    # Copy file to backup
    try:
        shutil.copy2(path, backup_path)
    except Exception as e:
        raise BackupError(f"Failed to copy file to backup: {e}") from e

    return backup_path


def restore_backup(backup_path: Path, original_path: Path) -> None:
    """Restore file from backup.

    Args:
        backup_path: Path to backup file
        original_path: Path to restore to

    Raises:
        BackupError: If restore fails

    Example:
        >>> restore_backup(
        ...     Path("/tmp/.mcp-installer-backups/config.json.20250105_143022.backup"),
        ...     Path("/tmp/config.json")
        ... )
    """
    if not backup_path.exists():
        raise BackupError(f"Backup file not found: {backup_path}")

    try:
        shutil.copy2(backup_path, original_path)
    except Exception as e:
        raise BackupError(f"Failed to restore from backup: {e}") from e


# ============================================================================
# Safe Parsing (JSON/TOML with Error Recovery)
# ============================================================================


def parse_json_safe(path: Path) -> dict[str, Any]:
    """Parse JSON file with graceful error handling.

    Returns empty dict if file doesn't exist or is empty.
    Raises ConfigurationError if file is invalid JSON.

    Args:
        path: Path to JSON file

    Returns:
        Parsed JSON as dictionary (empty dict if file doesn't exist)

    Raises:
        ConfigurationError: If file exists but is invalid JSON

    Example:
        >>> config = parse_json_safe(Path("/tmp/config.json"))
        >>> print(config.get("mcpServers", {}))
    """
    if not path.exists():
        return {}

    try:
        with path.open("r", encoding="utf-8") as f:
            content = f.read().strip()

            # Empty file is valid (return empty dict)
            if not content:
                return {}

            result: dict[str, Any] = json.loads(content)
            return result

    except json.JSONDecodeError as e:
        raise ConfigurationError(
            f"Invalid JSON in {path}: {e}", config_path=str(path)
        ) from e
    except Exception as e:
        raise ConfigurationError(
            f"Failed to read {path}: {e}", config_path=str(path)
        ) from e


def parse_toml_safe(path: Path) -> dict[str, Any]:
    """Parse TOML file with graceful error handling.

    Returns empty dict if file doesn't exist or is empty.
    Raises ConfigurationError if file is invalid TOML.

    Args:
        path: Path to TOML file

    Returns:
        Parsed TOML as dictionary (empty dict if file doesn't exist)

    Raises:
        ConfigurationError: If file exists but is invalid TOML

    Example:
        >>> config = parse_toml_safe(Path("/tmp/config.toml"))
        >>> print(config.get("mcp_servers", {}))
    """
    if not path.exists():
        return {}

    try:
        # Python 3.11+ has tomllib in stdlib
        try:
            import tomllib  # type: ignore[import-untyped]
        except ImportError:
            import tomli as tomllib  # type: ignore[import-untyped,unused-ignore]

        with path.open("rb") as f:
            content = f.read()

            # Empty file is valid (return empty dict)
            if not content:
                return {}

            result: dict[str, Any] = tomllib.loads(content.decode("utf-8"))
            return result

    except Exception as e:
        raise ConfigurationError(
            f"Invalid TOML in {path}: {e}", config_path=str(path)
        ) from e


# ============================================================================
# Credential Masking (Security)
# ============================================================================


def mask_credentials(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively mask sensitive values in dictionary for logging.

    Masks any keys containing: API_KEY, TOKEN, SECRET, PASSWORD, CREDENTIALS, AUTH

    Args:
        data: Dictionary potentially containing sensitive data

    Returns:
        New dictionary with sensitive values masked as "***"

    Example:
        >>> masked = mask_credentials({
        ...     "API_KEY": "secret123",
        ...     "DEBUG": "true"
        ... })
        >>> print(masked)
        {'API_KEY': '***', 'DEBUG': 'true'}
    """
    sensitive_keywords = {
        "API_KEY",
        "TOKEN",
        "SECRET",
        "PASSWORD",
        "CREDENTIALS",
        "AUTH",
        "KEY",
    }

    def is_sensitive(key: str) -> bool:
        """Check if key name suggests sensitive data."""
        key_upper = key.upper()
        return any(keyword in key_upper for keyword in sensitive_keywords)

    def mask_value(key: str, value: Any) -> Any:
        """Recursively mask sensitive values."""
        if isinstance(value, dict):
            return {k: mask_value(k, v) for k, v in value.items()}
        elif isinstance(value, list):
            return [mask_value(key, item) for item in value]
        elif is_sensitive(key):
            return "***"
        else:
            return value

    return {k: mask_value(k, v) for k, v in data.items()}


# ============================================================================
# Command Resolution (PATH lookups)
# ============================================================================


def resolve_command_path(command: str) -> Path | None:
    """Find command in PATH and return absolute path.

    Args:
        command: Command name to find (e.g., "uv", "mcp-ticketer")

    Returns:
        Absolute path to command if found, None otherwise

    Example:
        >>> path = resolve_command_path("python")
        >>> print(path)
        /usr/bin/python
    """
    found = shutil.which(command)
    return Path(found) if found else None


def detect_install_method(package: str) -> str:
    """Detect how a Python package is installed.

    Checks in order:
    1. pipx (in ~/.local/bin or ~/.local/pipx/venvs/)
    2. pip (via pip show)
    3. Not installed

    Args:
        package: Package name (e.g., "mcp-ticketer")

    Returns:
        "pipx", "pip", or "not_installed"

    Example:
        >>> method = detect_install_method("mcp-ticketer")
        >>> print(method)
        pipx
    """
    # Check if pipx installed
    pipx_path = Path.home() / ".local" / "pipx" / "venvs" / package
    if pipx_path.exists():
        return "pipx"

    # Check if pip installed
    try:
        import subprocess

        result = subprocess.run(
            ["pip", "show", package],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return "pip"
    except Exception:
        pass

    return "not_installed"


# ============================================================================
# Validation Helpers
# ============================================================================


def validate_json_structure(data: dict[str, Any], path: Path) -> list[str]:
    """Validate MCP config JSON structure.

    Checks for:
    - mcpServers key exists
    - mcpServers is a dictionary
    - Each server has required fields (command)

    Args:
        data: Parsed JSON config
        path: Path to config file (for error messages)

    Returns:
        List of validation errors (empty if valid)

    Example:
        >>> errors = validate_json_structure(
        ...     {"mcpServers": {"test": {"command": "test"}}},
        ...     Path("/tmp/config.json")
        ... )
        >>> print(errors)
        []
    """
    errors: list[str] = []

    # Check for mcpServers key
    if "mcpServers" not in data:
        errors.append("Missing 'mcpServers' key")
        return errors

    servers = data["mcpServers"]
    if not isinstance(servers, dict):
        errors.append("'mcpServers' must be a dictionary")
        return errors

    # Validate each server
    for server_name, server_config in servers.items():
        if not isinstance(server_config, dict):
            errors.append(f"Server '{server_name}' config must be a dictionary")
            continue

        if "command" not in server_config:
            errors.append(f"Server '{server_name}' missing 'command' field")

        if "args" in server_config and not isinstance(server_config["args"], list):
            errors.append(f"Server '{server_name}' 'args' must be a list")

        if "env" in server_config and not isinstance(server_config["env"], dict):
            errors.append(f"Server '{server_name}' 'env' must be a dictionary")

    return errors


def validate_toml_structure(data: dict[str, Any], path: Path) -> list[str]:
    """Validate MCP config TOML structure.

    Checks for:
    - mcp_servers key exists (snake_case for TOML)
    - mcp_servers is a dictionary
    - Each server has required fields (command)

    Args:
        data: Parsed TOML config
        path: Path to config file (for error messages)

    Returns:
        List of validation errors (empty if valid)

    Example:
        >>> errors = validate_toml_structure(
        ...     {"mcp_servers": {"test": {"command": "test"}}},
        ...     Path("/tmp/config.toml")
        ... )
        >>> print(errors)
        []
    """
    errors: list[str] = []

    # Check for mcp_servers key (TOML uses snake_case)
    if "mcp_servers" not in data:
        errors.append("Missing 'mcp_servers' key")
        return errors

    servers = data["mcp_servers"]
    if not isinstance(servers, dict):
        errors.append("'mcp_servers' must be a table")
        return errors

    # Validate each server
    for server_name, server_config in servers.items():
        if not isinstance(server_config, dict):
            errors.append(f"Server '{server_name}' config must be a table")
            continue

        if "command" not in server_config:
            errors.append(f"Server '{server_name}' missing 'command' field")

        if "args" in server_config and not isinstance(server_config["args"], list):
            errors.append(f"Server '{server_name}' 'args' must be an array")

    return errors
