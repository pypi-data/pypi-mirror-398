"""Codex platform implementation.

This module provides platform-specific logic for Codex, including
configuration paths, installation strategies, and validation.

Codex supports:
- Global config only: ~/.codex/config.toml
- TOML format (not JSON)
- TOML manipulation strategy
"""

from pathlib import Path

from ..command_builder import CommandBuilder
from ..installation_strategy import (
    InstallationStrategy,
    TOMLManipulationStrategy,
)
from ..types import InstallMethod, MCPServerConfig, Platform, Scope
from ..utils import resolve_command_path


class CodexStrategy:
    """Codex platform implementation.

    Provides configuration paths and installation strategies for Codex.

    Note: Codex uses TOML format instead of JSON, and only supports
    global-level configuration.

    Example:
        >>> strategy = CodexStrategy()
        >>> config_path = strategy.get_config_path(Scope.GLOBAL)
        >>> installer = strategy.get_strategy(Scope.GLOBAL)
        >>> result = installer.install(server, Scope.GLOBAL)
    """

    def __init__(self) -> None:
        """Initialize Codex strategy."""
        self.platform = Platform.CODEX
        self.config_format = "toml"

    def get_config_path(self, scope: Scope) -> Path:
        """Get configuration path for scope.

        Codex only supports global configuration.

        Args:
            scope: Installation scope (only GLOBAL supported)

        Returns:
            Path to TOML configuration file

        Example:
            >>> strategy = CodexStrategy()
            >>> path = strategy.get_config_path(Scope.GLOBAL)
            >>> print(path)
            /home/user/.codex/config.toml
        """
        # Codex only has global config
        return Path.home() / ".codex" / "config.toml"

    def get_strategy(self, scope: Scope) -> InstallationStrategy:
        """Get appropriate installation strategy for scope.

        Codex only supports TOML manipulation.

        Args:
            scope: Installation scope

        Returns:
            TOML manipulation strategy

        Example:
            >>> strategy = CodexStrategy()
            >>> installer = strategy.get_strategy(Scope.GLOBAL)
            >>> result = installer.install(server, Scope.GLOBAL)
        """
        config_path = self.get_config_path(scope)
        return TOMLManipulationStrategy(self.platform, config_path)

    def validate_installation(self) -> bool:
        """Validate Codex is available.

        Checks for config directory or codex CLI.

        Returns:
            True if Codex appears to be installed

        Example:
            >>> strategy = CodexStrategy()
            >>> if strategy.validate_installation():
            ...     print("Codex is available")
        """
        # Check for config directory
        codex_dir = Path.home() / ".codex"
        has_config_dir = codex_dir.exists() and codex_dir.is_dir()

        # Check for codex CLI
        has_cli = resolve_command_path("codex") is not None

        return has_config_dir or has_cli

    def build_server_config(
        self,
        package: str,
        install_method: InstallMethod | None = None,
        env: dict[str, str] | None = None,
        description: str = "",
    ) -> MCPServerConfig:
        """Build server configuration for Codex.

        Uses CommandBuilder to auto-detect best installation method.

        Note: Codex uses TOML format with snake_case keys.

        Args:
            package: Package name (e.g., "mcp-ticketer")
            install_method: Installation method (auto-detected if None)
            env: Environment variables
            description: Server description

        Returns:
            Complete server configuration

        Example:
            >>> strategy = CodexStrategy()
            >>> config = strategy.build_server_config(
            ...     "mcp-ticketer",
            ...     env={"LINEAR_API_KEY": "..."}
            ... )
            >>> print(f"{config.command} {' '.join(config.args)}")
            uv run mcp-ticketer mcp
        """
        builder = CommandBuilder(self.platform)
        return builder.to_server_config(
            package=package,
            install_method=install_method,
            env=env,
            description=description,
        )

    def get_platform_info(self) -> dict[str, str]:
        """Get platform information.

        Returns:
            Dict with platform details

        Example:
            >>> strategy = CodexStrategy()
            >>> info = strategy.get_platform_info()
            >>> print(info["name"])
            Codex
        """
        return {
            "name": "Codex",
            "platform": self.platform.value,
            "config_format": "toml",
            "scope_support": "global_only",
            "cli_available": str(resolve_command_path("codex") is not None),
            "config_key": "mcp_servers",  # TOML uses snake_case
        }

    def get_toml_specific_notes(self) -> dict[str, str]:
        """Get TOML-specific configuration notes.

        Returns:
            Dict with TOML-specific guidance

        Example:
            >>> strategy = CodexStrategy()
            >>> notes = strategy.get_toml_specific_notes()
            >>> print(notes["key_format"])
            snake_case
        """
        return {
            "key_format": "snake_case",
            "section_name": "mcp_servers",
            "env_handling": "May require special quoting for environment variables",
            "config_location": str(Path.home() / ".codex" / "config.toml"),
        }
