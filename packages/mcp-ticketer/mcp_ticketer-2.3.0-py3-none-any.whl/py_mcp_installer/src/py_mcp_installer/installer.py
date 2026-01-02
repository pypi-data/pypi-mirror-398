"""Main installer orchestrator for MCP servers.

This module provides the primary API facade for installing, managing, and
inspecting MCP server configurations across all supported platforms.

Design Philosophy:
- Simple API with smart defaults (auto-detection)
- Atomic operations with backup/restore
- Comprehensive validation and inspection
- Dry-run support for safe testing
- Platform-agnostic interface

Example:
    >>> from py_mcp_installer import MCPInstaller
    >>> installer = MCPInstaller.auto_detect()
    >>> result = installer.install_server(
    ...     name="mcp-ticketer",
    ...     command="uv",
    ...     args=["run", "mcp-ticketer", "mcp"],
    ...     description="Ticket management MCP server"
    ... )
    >>> print(result.message)
    Successfully installed mcp-ticketer
"""

import logging
from pathlib import Path
from typing import Any

from .command_builder import CommandBuilder
from .exceptions import (
    ConfigurationError,
    InstallationError,
    PlatformDetectionError,
    PlatformNotSupportedError,
    ValidationError,
)
from .installation_strategy import (
    InstallationStrategy as BaseStrategy,
)
from .installation_strategy import (
    JSONManipulationStrategy,
)
from .mcp_inspector import InspectionReport, MCPInspector, ValidationIssue
from .platform_detector import PlatformDetector
from .platforms import ClaudeCodeStrategy, CodexStrategy, CursorStrategy
from .types import (
    InstallationResult,
    InstallMethod,
    MCPServerConfig,
    Platform,
    PlatformInfo,
    Scope,
)
from .utils import detect_install_method, resolve_command_path

logger = logging.getLogger(__name__)


# ============================================================================
# Main Installer API
# ============================================================================


class MCPInstaller:
    """Main API facade for MCP server installation.

    Provides a unified interface for installing, managing, and inspecting
    MCP servers across all supported platforms. Automatically detects platform
    and selects best installation method.

    Attributes:
        platform_info: Detected platform information
        config_path: Path to configuration file
        dry_run: If True, preview changes without applying
        verbose: If True, enable verbose logging

    Example:
        >>> # Auto-detect platform and install
        >>> installer = MCPInstaller.auto_detect()
        >>> result = installer.install_server(
        ...     name="mcp-ticketer",
        ...     command="uv",
        ...     args=["run", "mcp-ticketer", "mcp"]
        ... )
        >>> if result.success:
        ...     print(f"Installed to {result.config_path}")

        >>> # Inspect existing installation
        >>> report = installer.inspect_installation()
        >>> print(report.summary())

        >>> # List all servers
        >>> servers = installer.list_servers()
        >>> for server in servers:
        ...     print(f"- {server.name}: {server.command}")
    """

    def __init__(
        self,
        platform: Platform | None = None,
        dry_run: bool = False,
        verbose: bool = False,
    ) -> None:
        """Initialize installer.

        Args:
            platform: Force specific platform (None = auto-detect)
            dry_run: Preview changes without applying
            verbose: Enable verbose logging

        Raises:
            PlatformDetectionError: If platform cannot be detected
            PlatformNotSupportedError: If platform is not supported

        Example:
            >>> # Auto-detect platform
            >>> installer = MCPInstaller()

            >>> # Force specific platform
            >>> installer = MCPInstaller(platform=Platform.CLAUDE_CODE)

            >>> # Dry-run mode (safe testing)
            >>> installer = MCPInstaller(dry_run=True, verbose=True)
        """
        self.dry_run = dry_run
        self.verbose = verbose

        # Configure logging
        if verbose:
            logging.basicConfig(level=logging.DEBUG)
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

        # Detect or use provided platform
        if platform:
            # For forced platform, we still need to detect but validate it matches
            detector = PlatformDetector()
            detected_info = detector.detect()
            if detected_info.platform != platform:
                raise PlatformNotSupportedError(
                    platform.value,
                    [p.value for p in Platform if p != Platform.UNKNOWN],
                )
            self._platform_info = detected_info
        else:
            self._platform_info = self._detect_platform()

        logger.info(
            f"Initialized for {self._platform_info.platform.value} "
            f"(confidence: {self._platform_info.confidence:.2f})"
        )

        # Initialize components
        self._command_builder = CommandBuilder(self._platform_info.platform)
        self._inspector = MCPInspector(self._platform_info)

        # Select installation strategy
        self._strategy = self._select_strategy()

    @classmethod
    def auto_detect(cls, **kwargs: Any) -> "MCPInstaller":
        """Create installer with auto-detected platform.

        This is the recommended way to create an installer instance.

        Args:
            **kwargs: Additional arguments passed to __init__

        Returns:
            Configured MCPInstaller instance

        Example:
            >>> installer = MCPInstaller.auto_detect()
            >>> print(f"Detected: {installer.platform_info.platform.value}")
        """
        return cls(platform=None, **kwargs)

    def install_server(
        self,
        name: str,
        command: str,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        description: str = "",
        scope: Scope = Scope.PROJECT,
        method: InstallMethod | None = None,
    ) -> InstallationResult:
        """Install MCP server.

        Auto-detects best installation method if not specified. Creates backup
        of existing config before making changes.

        Args:
            name: Unique server identifier (e.g., "mcp-ticketer")
            command: Executable command (e.g., "uv", "/usr/bin/python")
            args: Command arguments (e.g., ["run", "mcp-ticketer", "mcp"])
            env: Environment variables (e.g., {"API_KEY": "..."})
            description: Human-readable description
            scope: Installation scope (PROJECT or GLOBAL)
            method: Installation method (auto-detect if None)

        Returns:
            InstallationResult with success status and details

        Raises:
            ValidationError: If server configuration is invalid
            InstallationError: If installation fails

        Example:
            >>> # Simple installation with auto-detection
            >>> result = installer.install_server(
            ...     name="mcp-ticketer",
            ...     command="uv",
            ...     args=["run", "mcp-ticketer", "mcp"],
            ...     description="Ticket management"
            ... )

            >>> # Install with environment variables
            >>> result = installer.install_server(
            ...     name="github-mcp",
            ...     command="npx",
            ...     args=["-y", "@modelcontextprotocol/server-github"],
            ...     env={"GITHUB_TOKEN": "ghp_..."}
            ... )

            >>> # Force specific method
            >>> result = installer.install_server(
            ...     name="custom-server",
            ...     command="python",
            ...     args=["-m", "my_server"],
            ...     method=InstallMethod.PYTHON_MODULE
            ... )
        """
        logger.info(f"Installing server: {name}")

        # Validate inputs
        if not name:
            raise ValidationError(
                "Server name is required", "Provide a unique server name"
            )

        if not command and not method:
            raise ValidationError(
                "Either command or method must be provided",
                "Provide command parameter or specify installation method",
            )

        # Auto-detect method if not provided
        if method is None:
            # Default to UV_RUN as recommended method
            if command == "uv":
                method = InstallMethod.UV_RUN
            elif resolve_command_path(name):
                # Check if installed method
                install_check = detect_install_method(name)
                if install_check == "pipx":
                    method = InstallMethod.PIPX
                else:
                    method = InstallMethod.DIRECT
            else:
                method = InstallMethod.PYTHON_MODULE
            logger.debug(f"Auto-detected method: {method.value}")

        # Build complete command if needed
        if not command:
            command = self._command_builder.build_command(
                MCPServerConfig(name=name, command="", args=args or []),
                method,
            )

        # Create server config
        server = MCPServerConfig(
            name=name,
            command=command,
            args=args or [],
            env=env or {},
            description=description,
        )

        # Validate server config
        issues = self._inspector.validate_server(server)
        errors = [i for i in issues if i.severity == "error"]
        if errors:
            error_msg = "\n".join(f"- {e.message}" for e in errors)
            raise ValidationError(
                f"Server configuration invalid:\n{error_msg}",
                "Fix validation errors before installing",
            )

        # Log warnings
        warnings = [i for i in issues if i.severity == "warning"]
        for warning in warnings:
            logger.warning(f"{warning.message} - {warning.fix_suggestion}")

        # Install using strategy
        if self.dry_run:
            logger.info(
                f"[DRY RUN] Would install {name} to {self._platform_info.config_path}"
            )
            return InstallationResult(
                success=True,
                platform=self._platform_info.platform,
                server_name=name,
                method=method,
                message=f"[DRY RUN] Would install {name}",
                config_path=self._platform_info.config_path,
            )

        try:
            result = self._strategy.install(server, scope)
            logger.info(f"Successfully installed {name}")
            return result
        except Exception as e:
            logger.error(f"Installation failed: {e}", exc_info=True)
            raise InstallationError(
                f"Failed to install {name}: {e}",
                "Check logs for details and verify permissions",
            ) from e

    def uninstall_server(
        self, name: str, scope: Scope = Scope.PROJECT
    ) -> InstallationResult:
        """Remove MCP server from configuration.

        Creates backup before removing. Server data/packages are not removed,
        only the configuration entry.

        Args:
            name: Server name to uninstall
            scope: Installation scope (PROJECT or GLOBAL)

        Returns:
            InstallationResult with success status

        Raises:
            InstallationError: If uninstallation fails

        Example:
            >>> result = installer.uninstall_server("old-server")
            >>> if result.success:
            ...     print(f"Removed {result.server_name}")
        """
        logger.info(f"Uninstalling server: {name}")

        if self.dry_run:
            logger.info(f"[DRY RUN] Would uninstall {name}")
            return InstallationResult(
                success=True,
                platform=self._platform_info.platform,
                server_name=name,
                method=InstallMethod.DIRECT,  # Not relevant for uninstall
                message=f"[DRY RUN] Would uninstall {name}",
                config_path=self._platform_info.config_path,
            )

        try:
            result = self._strategy.uninstall(name, scope)
            logger.info(f"Successfully uninstalled {name}")
            return result
        except Exception as e:
            logger.error(f"Uninstallation failed: {e}", exc_info=True)
            raise InstallationError(
                f"Failed to uninstall {name}: {e}",
                "Check logs for details and verify permissions",
            ) from e

    def list_servers(self, scope: Scope = Scope.PROJECT) -> list[MCPServerConfig]:
        """List all installed MCP servers.

        Args:
            scope: Installation scope (PROJECT or GLOBAL)

        Returns:
            List of installed server configurations (empty if none)

        Example:
            >>> servers = installer.list_servers()
            >>> for server in servers:
            ...     print(f"{server.name}: {server.command} {' '.join(server.args)}")
            mcp-ticketer: uv run mcp-ticketer mcp
            github-mcp: npx -y @modelcontextprotocol/server-github
        """
        try:
            return self._strategy.list_servers(scope)
        except Exception as e:
            logger.error(f"Failed to list servers: {e}", exc_info=True)
            return []

    def get_server(
        self, name: str, scope: Scope = Scope.PROJECT
    ) -> MCPServerConfig | None:
        """Get specific server configuration.

        Args:
            name: Server name to retrieve
            scope: Installation scope (PROJECT or GLOBAL)

        Returns:
            Server configuration or None if not found

        Example:
            >>> server = installer.get_server("mcp-ticketer")
            >>> if server:
            ...     print(f"Command: {server.command}")
            ...     print(f"Args: {server.args}")
        """
        servers = self.list_servers(scope)
        for server in servers:
            if server.name == name:
                return server
        return None

    def inspect_installation(self) -> InspectionReport:
        """Run comprehensive inspection.

        Validates all servers, checks for legacy format, detects duplicates,
        and provides recommendations for improvements.

        Returns:
            Complete inspection report

        Example:
            >>> report = installer.inspect_installation()
            >>> print(report.summary())
            Inspection PASS: 5/5 servers valid
              Errors: 0, Warnings: 2, Info: 1

            >>> # Fix issues
            >>> if report.has_warnings():
            ...     for issue in report.issues:
            ...         if issue.auto_fixable:
            ...             inspector.auto_fix(issue)
        """
        logger.info("Running installation inspection...")
        report = self._inspector.inspect()

        if self.verbose:
            print("\n" + "=" * 60)
            print(report.summary())
            print("=" * 60)

            if report.issues:
                print("\nIssues:")
                for issue in report.issues:
                    print(f"\n[{issue.severity.upper()}] {issue.message}")
                    if issue.server_name:
                        print(f"  Server: {issue.server_name}")
                    print(f"  Fix: {issue.fix_suggestion}")
                    if issue.auto_fixable:
                        print("  (Auto-fixable)")

            if report.recommendations:
                print("\nRecommendations:")
                for rec in report.recommendations:
                    print(f"  - {rec}")
            print()

        return report

    def fix_issues(self, auto_fix: bool = True) -> list[str]:
        """Fix detected issues.

        Runs inspection and attempts to auto-fix all fixable issues.
        Non-fixable issues are logged as warnings.

        Args:
            auto_fix: If True, actually apply fixes (False = dry run)

        Returns:
            List of fixes applied

        Example:
            >>> fixes = installer.fix_issues()
            >>> for fix in fixes:
            ...     print(f"Fixed: {fix}")
            Fixed: Created default config file
            Fixed: Migrated legacy format to modern format
            Fixed: Removed deprecated args from server 'old-server'
        """
        logger.info("Checking for fixable issues...")
        report = self.inspect_installation()

        fixes: list[str] = []
        auto_fixable = [i for i in report.issues if i.auto_fixable]

        if not auto_fixable:
            logger.info("No auto-fixable issues found")
            return fixes

        logger.info(f"Found {len(auto_fixable)} auto-fixable issues")

        for issue in auto_fixable:
            if self.dry_run or not auto_fix:
                fixes.append(f"[DRY RUN] Would fix: {issue.message}")
                logger.info(f"[DRY RUN] Would fix: {issue.message}")
            else:
                try:
                    if self._inspector.auto_fix(issue):
                        fixes.append(issue.message)
                        logger.info(f"Fixed: {issue.message}")
                    else:
                        logger.warning(f"Could not auto-fix: {issue.message}")
                except Exception as e:
                    logger.error(f"Fix failed for '{issue.message}': {e}")

        return fixes

    def migrate_legacy(self) -> bool:
        """Migrate from legacy line-delimited JSON format.

        Converts old line-delimited JSON format to modern FastMCP SDK format.
        Creates backup before migration.

        Returns:
            True if migration succeeded (or not needed)

        Example:
            >>> if installer.migrate_legacy():
            ...     print("Migration successful")
        """
        logger.info("Checking for legacy format...")

        if not self._inspector.check_legacy_format():
            logger.info("No legacy format detected")
            return True

        if self.dry_run:
            logger.info("[DRY RUN] Would migrate legacy format")
            return True

        logger.info("Migrating from legacy format...")

        try:
            # Auto-fix will handle the migration
            issue = ValidationIssue(
                severity="warning",
                message="Legacy format detected",
                server_name=None,
                fix_suggestion="Migrate to modern format",
                auto_fixable=True,
            )

            success = self._inspector.auto_fix(issue)
            if success:
                logger.info("Migration successful")
            else:
                logger.error("Migration failed")
            return success

        except Exception as e:
            logger.error(f"Migration error: {e}", exc_info=True)
            return False

    @property
    def platform_info(self) -> PlatformInfo:
        """Get detected platform information.

        Returns:
            Platform information including confidence and paths

        Example:
            >>> info = installer.platform_info
            >>> print(f"Platform: {info.platform.value}")
            >>> print(f"Config: {info.config_path}")
            >>> print(f"Confidence: {info.confidence}")
        """
        return self._platform_info

    @property
    def config_path(self) -> Path:
        """Get configuration file path.

        Returns:
            Path to platform's config file

        Example:
            >>> print(installer.config_path)
            /home/user/.config/claude/mcp.json
        """
        return self._platform_info.config_path or Path()

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    def _detect_platform(self) -> PlatformInfo:
        """Detect platform automatically.

        Returns:
            Detected platform info

        Raises:
            PlatformDetectionError: If no platform detected
        """
        detector = PlatformDetector()
        info = detector.detect()

        if info.platform == Platform.UNKNOWN or info.confidence == 0.0:
            raise PlatformDetectionError()

        return info

    def _select_strategy(self) -> BaseStrategy:
        """Select best installation strategy for platform.

        Returns:
            Installation strategy instance

        Raises:
            PlatformNotSupportedError: If platform has no strategy
        """
        platform = self._platform_info.platform

        # Platform-specific strategies (with fallbacks)
        if platform == Platform.CLAUDE_CODE:
            claude_strategy = ClaudeCodeStrategy()
            # Use the strategy's get_strategy method to get actual installer
            return claude_strategy.get_strategy(Scope.PROJECT)

        elif platform == Platform.CLAUDE_DESKTOP:
            # Use same strategy as Claude Code
            desktop_strategy = ClaudeCodeStrategy()
            return desktop_strategy.get_strategy(Scope.GLOBAL)

        elif platform == Platform.CURSOR:
            cursor_strategy = CursorStrategy()
            return cursor_strategy.get_strategy(Scope.PROJECT)

        elif platform == Platform.CODEX:
            codex_strategy = CodexStrategy()
            return codex_strategy.get_strategy(Scope.GLOBAL)

        elif platform in [Platform.AUGGIE, Platform.WINDSURF, Platform.GEMINI_CLI]:
            # Generic JSON manipulation for these platforms
            if not self._platform_info.config_path:
                raise ConfigurationError(
                    f"No config path for {platform.value}",
                    "Ensure platform is installed correctly",
                )

            return JSONManipulationStrategy(
                platform=platform,
                config_path=self._platform_info.config_path,
            )

        else:
            raise PlatformNotSupportedError(
                platform.value,
                [
                    p.value
                    for p in Platform
                    if p not in [Platform.UNKNOWN, Platform.ANTIGRAVITY]
                ],
            )
