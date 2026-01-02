"""Installation strategies for different MCP platforms.

This module provides Strategy pattern implementations for installing MCP servers
across different platforms using native CLIs, JSON manipulation, or TOML manipulation.

Design Philosophy:
- Strategy pattern for platform-specific installation
- Fallback mechanisms (CLI → JSON for Claude)
- Dry-run support for testing
- Atomic operations with backup/restore

Strategies:
- NativeCLIStrategy: Use platform CLI (claude mcp add)
- JSONManipulationStrategy: Direct JSON config modification
- TOMLManipulationStrategy: Direct TOML config modification
"""

import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

from .config_manager import ConfigManager
from .exceptions import InstallationError, ValidationError
from .types import (
    ConfigFormat,
    InstallationResult,
    InstallMethod,
    MCPServerConfig,
    Platform,
    Scope,
)
from .utils import mask_credentials, resolve_command_path


class InstallationStrategy(ABC):
    """Abstract base class for installation strategies.

    Each platform may support multiple installation strategies with
    different priorities (e.g., CLI first, JSON fallback).

    Example:
        >>> strategy = NativeCLIStrategy(Platform.CLAUDE_CODE, "claude")
        >>> result = strategy.install(server, Scope.PROJECT)
    """

    @abstractmethod
    def install(self, server: MCPServerConfig, scope: Scope) -> InstallationResult:
        """Install MCP server with this strategy.

        Args:
            server: Server configuration to install
            scope: Installation scope (project or global)

        Returns:
            InstallationResult with status and details

        Raises:
            InstallationError: If installation fails
        """
        pass

    @abstractmethod
    def uninstall(self, name: str, scope: Scope) -> InstallationResult:
        """Uninstall MCP server.

        Args:
            name: Server name to uninstall
            scope: Installation scope

        Returns:
            InstallationResult with status

        Raises:
            InstallationError: If uninstall fails
        """
        pass

    @abstractmethod
    def list_servers(self, scope: Scope) -> list[MCPServerConfig]:
        """List installed servers.

        Args:
            scope: Installation scope

        Returns:
            List of installed server configurations
        """
        pass

    @abstractmethod
    def validate(self) -> bool:
        """Validate this strategy can be used.

        Returns:
            True if strategy is available, False otherwise

        Example:
            >>> strategy = NativeCLIStrategy(Platform.CLAUDE_CODE, "claude")
            >>> if strategy.validate():
            ...     result = strategy.install(server, Scope.PROJECT)
        """
        pass


class NativeCLIStrategy(InstallationStrategy):
    """Installation via platform's native CLI.

    Uses commands like:
    - `claude mcp add {name} --command "{command}" --scope {scope}`
    - `auggie mcp install {name}`

    Falls back to JSON strategy if CLI command fails.

    Example:
        >>> strategy = NativeCLIStrategy(Platform.CLAUDE_CODE, "claude")
        >>> if strategy.validate():
        ...     result = strategy.install(server, Scope.PROJECT)
        ... else:
        ...     # Fallback to JSON strategy
        ...     fallback = JSONManipulationStrategy(Platform.CLAUDE_CODE, config_path)
        ...     result = fallback.install(server, Scope.PROJECT)
    """

    def __init__(self, platform: Platform, cli_command: str) -> None:
        """Initialize with platform and CLI command.

        Args:
            platform: Target platform
            cli_command: CLI command name (e.g., "claude", "auggie")

        Example:
            >>> strategy = NativeCLIStrategy(Platform.CLAUDE_CODE, "claude")
        """
        self.platform = platform
        self.cli_command = cli_command

    def install(self, server: MCPServerConfig, scope: Scope) -> InstallationResult:
        """Install server using native CLI.

        Executes CLI command to add server. Falls back to JSON strategy
        if CLI fails.

        Args:
            server: Server configuration
            scope: Installation scope

        Returns:
            InstallationResult with installation status

        Example:
            >>> server = MCPServerConfig(
            ...     name="mcp-ticketer",
            ...     command="uv",
            ...     args=["run", "mcp-ticketer", "mcp"]
            ... )
            >>> result = strategy.install(server, Scope.PROJECT)
        """
        # Build CLI command
        cmd = self._build_cli_command(server, scope)

        try:
            # Execute CLI command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                return InstallationResult(
                    success=True,
                    platform=self.platform,
                    server_name=server.name,
                    method=InstallMethod.DIRECT,
                    message=f"Successfully installed '{server.name}' via CLI",
                    config_path=None,  # CLI doesn't expose config path
                )
            else:
                raise InstallationError(
                    f"CLI command failed: {result.stderr}",
                    recovery_suggestion="Check CLI installation and permissions",
                )

        except (subprocess.TimeoutExpired, FileNotFoundError, InstallationError) as e:
            # CLI failed, raise error for caller to try fallback
            raise InstallationError(
                f"Native CLI installation failed: {e}",
                recovery_suggestion="Try JSON manipulation strategy as fallback",
            ) from e

    def uninstall(self, name: str, scope: Scope) -> InstallationResult:
        """Uninstall server using native CLI.

        Args:
            name: Server name
            scope: Installation scope

        Returns:
            InstallationResult with uninstall status
        """
        cmd = self._build_cli_remove_command(name, scope)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                return InstallationResult(
                    success=True,
                    platform=self.platform,
                    server_name=name,
                    method=InstallMethod.DIRECT,
                    message=f"Successfully uninstalled '{name}' via CLI",
                )
            else:
                raise InstallationError(
                    f"CLI remove failed: {result.stderr}",
                    recovery_suggestion="Check if server exists",
                )

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            raise InstallationError(
                f"CLI uninstall failed: {e}",
                recovery_suggestion="Try JSON manipulation strategy",
            ) from e

    def list_servers(self, scope: Scope) -> list[MCPServerConfig]:
        """List servers using native CLI.

        Note: Most CLIs don't provide list functionality,
        so this falls back to JSON reading.

        Args:
            scope: Installation scope

        Returns:
            List of server configurations
        """
        # Most CLIs don't support listing, would need config path
        raise NotImplementedError("Native CLI list not supported, use JSON strategy")

    def validate(self) -> bool:
        """Check if CLI command is available.

        Returns:
            True if CLI is in PATH, False otherwise

        Example:
            >>> strategy = NativeCLIStrategy(Platform.CLAUDE_CODE, "claude")
            >>> if strategy.validate():
            ...     print("Claude CLI available")
        """
        return resolve_command_path(self.cli_command) is not None

    def _build_cli_command(self, server: MCPServerConfig, scope: Scope) -> list[str]:
        """Build CLI command for installation.

        Args:
            server: Server configuration
            scope: Installation scope

        Returns:
            Command as list of strings
        """
        # Platform-specific command building
        if self.platform in (Platform.CLAUDE_CODE, Platform.CLAUDE_DESKTOP):
            # Claude CLI: claude mcp add [options] <name> -e KEY=val -- <cmd>
            scope_str = "project" if scope == Scope.PROJECT else "user"
            cmd = [
                self.cli_command,
                "mcp",
                "add",
                "--scope",
                scope_str,
                "--transport",
                "stdio",
                server.name,  # Name MUST come before -e flags
            ]

            # Add env vars (MUST come after server name)
            if server.env:
                for key, value in server.env.items():
                    cmd.extend(["-e", f"{key}={value}"])

            # Command separator and server command
            cmd.append("--")
            cmd.append(server.command)

            # Add args after the command
            if server.args:
                cmd.extend(server.args)

            return cmd

        else:
            raise NotImplementedError(
                f"CLI command building not implemented for {self.platform}"
            )

    def _build_cli_remove_command(self, name: str, scope: Scope) -> list[str]:
        """Build CLI command for removal.

        Args:
            name: Server name
            scope: Installation scope

        Returns:
            Command as list of strings
        """
        if self.platform in (Platform.CLAUDE_CODE, Platform.CLAUDE_DESKTOP):
            scope_str = "project" if scope == Scope.PROJECT else "user"
            return [
                self.cli_command,
                "mcp",
                "remove",
                name,
                "--scope",
                scope_str,
            ]
        else:
            raise NotImplementedError(f"CLI remove not implemented for {self.platform}")

    def _mask_command(self, cmd: list[str]) -> list[str]:
        """Mask sensitive values in command for logging.

        Args:
            cmd: Command list

        Returns:
            Command with masked credentials
        """
        masked = []
        mask_next = False

        for part in cmd:
            if mask_next:
                # Mask environment variable value
                if "=" in part:
                    key, _ = part.split("=", 1)
                    masked_dict = mask_credentials({key: "value"})
                    masked.append(f"{key}={list(masked_dict.values())[0]}")
                else:
                    masked.append("***")
                mask_next = False
            elif part == "-e":
                masked.append(part)
                mask_next = True
            else:
                masked.append(part)

        return masked


class JSONManipulationStrategy(InstallationStrategy):
    """Installation via direct JSON config file manipulation.

    Safely modifies JSON configuration files using ConfigManager.
    Creates backups before modifications.

    Supported platforms:
    - Claude Code (fallback from CLI)
    - Claude Desktop (fallback from CLI)
    - Cursor
    - Auggie
    - Windsurf
    - Gemini CLI

    Example:
        >>> strategy = JSONManipulationStrategy(
        ...     Platform.CURSOR,
        ...     Path.home() / ".cursor/mcp.json"
        ... )
        >>> result = strategy.install(server, Scope.GLOBAL)
    """

    def __init__(self, platform: Platform, config_path: Path) -> None:
        """Initialize with platform and config path.

        Args:
            platform: Target platform
            config_path: Path to JSON config file

        Example:
            >>> strategy = JSONManipulationStrategy(
            ...     Platform.CURSOR,
            ...     Path.home() / ".cursor/mcp.json"
            ... )
        """
        self.platform = platform
        self.config_path = config_path
        self.config_manager = ConfigManager(config_path, ConfigFormat.JSON)

    def install(self, server: MCPServerConfig, scope: Scope) -> InstallationResult:
        """Install server by modifying JSON config.

        Args:
            server: Server configuration
            scope: Installation scope (unused for JSON, config_path determines scope)

        Returns:
            InstallationResult with installation status

        Raises:
            InstallationError: If installation fails
        """
        try:
            # Add server using config manager
            self.config_manager.add_server(server)

            return InstallationResult(
                success=True,
                platform=self.platform,
                server_name=server.name,
                method=InstallMethod.DIRECT,
                message=f"Successfully installed '{server.name}' to {self.config_path}",
                config_path=self.config_path,
            )

        except ValidationError as e:
            # Server already exists
            raise InstallationError(
                f"Server '{server.name}' already exists",
                recovery_suggestion="Use update operation or remove existing server first",
            ) from e
        except Exception as e:
            raise InstallationError(
                f"Failed to install server: {e}",
                recovery_suggestion="Check config file permissions and syntax",
            ) from e

    def uninstall(self, name: str, scope: Scope) -> InstallationResult:
        """Uninstall server by removing from JSON config.

        Args:
            name: Server name
            scope: Installation scope (unused)

        Returns:
            InstallationResult with uninstall status
        """
        try:
            self.config_manager.remove_server(name)

            return InstallationResult(
                success=True,
                platform=self.platform,
                server_name=name,
                method=InstallMethod.DIRECT,
                message=f"Successfully uninstalled '{name}' from {self.config_path}",
                config_path=self.config_path,
            )

        except ValidationError as e:
            raise InstallationError(
                f"Server '{name}' not found",
                recovery_suggestion="Check server name with list_servers()",
            ) from e
        except Exception as e:
            raise InstallationError(
                f"Failed to uninstall server: {e}",
                recovery_suggestion="Check config file permissions",
            ) from e

    def list_servers(self, scope: Scope) -> list[MCPServerConfig]:
        """List servers from JSON config.

        Args:
            scope: Installation scope (unused)

        Returns:
            List of server configurations
        """
        try:
            return self.config_manager.list_servers()
        except Exception as e:
            raise InstallationError(
                f"Failed to list servers: {e}",
                recovery_suggestion="Check config file exists and is readable",
            ) from e

    def validate(self) -> bool:
        """Check if JSON config exists and is valid.

        Returns:
            True if config is accessible, False otherwise
        """
        try:
            # Try to read config
            self.config_manager.read()
            return True
        except Exception:
            # Config doesn't exist or is invalid
            # This is OK - we can create it
            return True


class TOMLManipulationStrategy(InstallationStrategy):
    """Installation via direct TOML config file manipulation.

    Used by Codex platform which uses TOML instead of JSON.

    Example:
        >>> strategy = TOMLManipulationStrategy(
        ...     Platform.CODEX,
        ...     Path.home() / ".codex/config.toml"
        ... )
        >>> result = strategy.install(server, Scope.GLOBAL)
    """

    def __init__(self, platform: Platform, config_path: Path) -> None:
        """Initialize with platform and config path.

        Args:
            platform: Target platform
            config_path: Path to TOML config file

        Example:
            >>> strategy = TOMLManipulationStrategy(
            ...     Platform.CODEX,
            ...     Path.home() / ".codex/config.toml"
            ... )
        """
        self.platform = platform
        self.config_path = config_path
        self.config_manager = ConfigManager(config_path, ConfigFormat.TOML)

    def install(self, server: MCPServerConfig, scope: Scope) -> InstallationResult:
        """Install server by modifying TOML config.

        Args:
            server: Server configuration
            scope: Installation scope (unused)

        Returns:
            InstallationResult with installation status
        """
        try:
            self.config_manager.add_server(server)

            return InstallationResult(
                success=True,
                platform=self.platform,
                server_name=server.name,
                method=InstallMethod.DIRECT,
                message=f"Successfully installed '{server.name}' to {self.config_path}",
                config_path=self.config_path,
            )

        except ValidationError as e:
            raise InstallationError(
                f"Server '{server.name}' already exists",
                recovery_suggestion="Use update operation or remove existing server first",
            ) from e
        except Exception as e:
            raise InstallationError(
                f"Failed to install server: {e}",
                recovery_suggestion="Check TOML file permissions and syntax",
            ) from e

    def uninstall(self, name: str, scope: Scope) -> InstallationResult:
        """Uninstall server by removing from TOML config.

        Args:
            name: Server name
            scope: Installation scope (unused)

        Returns:
            InstallationResult with uninstall status
        """
        try:
            self.config_manager.remove_server(name)

            return InstallationResult(
                success=True,
                platform=self.platform,
                server_name=name,
                method=InstallMethod.DIRECT,
                message=f"Successfully uninstalled '{name}' from {self.config_path}",
                config_path=self.config_path,
            )

        except ValidationError as e:
            raise InstallationError(
                f"Server '{name}' not found",
                recovery_suggestion="Check server name with list_servers()",
            ) from e
        except Exception as e:
            raise InstallationError(
                f"Failed to uninstall server: {e}",
                recovery_suggestion="Check TOML file permissions",
            ) from e

    def list_servers(self, scope: Scope) -> list[MCPServerConfig]:
        """List servers from TOML config.

        Args:
            scope: Installation scope (unused)

        Returns:
            List of server configurations
        """
        try:
            return self.config_manager.list_servers()
        except Exception as e:
            raise InstallationError(
                f"Failed to list servers: {e}",
                recovery_suggestion="Check TOML file exists and is readable",
            ) from e

    def validate(self) -> bool:
        """Check if TOML config exists and is valid.

        Returns:
            True if config is accessible, False otherwise
        """
        try:
            self.config_manager.read()
            return True
        except Exception:
            # Config doesn't exist or is invalid
            # This is OK - we can create it
            return True
