"""py-mcp-installer-service: Universal MCP server installer for AI coding tools.

This library provides a production-ready, type-safe solution for installing
and configuring MCP (Model Context Protocol) servers across 8 major AI coding
platforms.

Quick Start:
    >>> from py_mcp_installer import PlatformDetector, MCPServerConfig
    >>> detector = PlatformDetector()
    >>> info = detector.detect()
    >>> print(f"Detected {info.platform} with {info.confidence} confidence")

Supported Platforms:
    - Claude Code (claude_code)
    - Claude Desktop (claude_desktop)
    - Cursor (cursor)
    - Auggie (auggie)
    - Codex (codex)
    - Gemini CLI (gemini_cli)
    - Windsurf (windsurf)
    - Antigravity (antigravity) - TBD

Design Principles:
    - Zero external dependencies (except TOML parsing)
    - 100% type coverage (mypy --strict)
    - Cross-platform (macOS, Linux, Windows)
    - Atomic operations with backup/restore
    - Clear error messages with recovery suggestions
"""

__version__ = "0.0.3"

# Core types
from .command_builder import CommandBuilder

# Phase 2 modules
from .config_manager import ConfigManager

# Exceptions
from .exceptions import (
    AtomicWriteError,
    BackupError,
    CommandNotFoundError,
    ConfigurationError,
    InstallationError,
    PlatformDetectionError,
    PlatformNotSupportedError,
    PyMCPInstallerError,
    ValidationError,
)
from .installation_strategy import (
    InstallationStrategy as BaseInstallationStrategy,
)
from .installation_strategy import (
    JSONManipulationStrategy,
    NativeCLIStrategy,
    TOMLManipulationStrategy,
)
from .installer import MCPInstaller

# Phase 3 modules
from .mcp_inspector import InspectionReport, MCPInspector, ValidationIssue

# Platform detection
from .platform_detector import PlatformDetector

# Platform-specific implementations
from .platforms import (
    ClaudeCodeStrategy,
    CodexStrategy,
    CursorStrategy,
)
from .types import (
    ArgsList,
    ConfigFormat,
    EnvDict,
    InstallationResult,
    InstallationStrategy,
    InstallMethod,
    JsonDict,
    MCPServerConfig,
    Platform,
    PlatformInfo,
    Scope,
)

# Utilities
from .utils import (
    atomic_write,
    backup_file,
    mask_credentials,
    parse_json_safe,
    parse_toml_safe,
    resolve_command_path,
    restore_backup,
    validate_json_structure,
    validate_toml_structure,
)

__all__ = [
    # Version
    "__version__",
    # Core Types
    "Platform",
    "InstallMethod",
    "Scope",
    "ConfigFormat",
    "InstallationStrategy",
    "MCPServerConfig",
    "PlatformInfo",
    "InstallationResult",
    "JsonDict",
    "EnvDict",
    "ArgsList",
    # Exceptions
    "PyMCPInstallerError",
    "PlatformDetectionError",
    "ConfigurationError",
    "InstallationError",
    "ValidationError",
    "CommandNotFoundError",
    "BackupError",
    "AtomicWriteError",
    "PlatformNotSupportedError",
    # Platform Detection
    "PlatformDetector",
    # Utilities
    "atomic_write",
    "backup_file",
    "restore_backup",
    "parse_json_safe",
    "parse_toml_safe",
    "mask_credentials",
    "resolve_command_path",
    "validate_json_structure",
    "validate_toml_structure",
    # Phase 2 modules
    "ConfigManager",
    "CommandBuilder",
    "BaseInstallationStrategy",
    "NativeCLIStrategy",
    "JSONManipulationStrategy",
    "TOMLManipulationStrategy",
    # Platform implementations
    "ClaudeCodeStrategy",
    "CursorStrategy",
    "CodexStrategy",
    # Phase 3 modules
    "MCPInstaller",
    "MCPInspector",
    "ValidationIssue",
    "InspectionReport",
]
