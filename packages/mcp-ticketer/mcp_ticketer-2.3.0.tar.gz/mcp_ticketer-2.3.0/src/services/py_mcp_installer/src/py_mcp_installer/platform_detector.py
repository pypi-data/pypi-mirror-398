"""Platform detection logic for all supported AI coding tools.

This module implements comprehensive platform detection with confidence scoring
and multi-layered validation.

Detection Strategy:
1. Check for config file existence (+0.4 confidence)
2. Validate config format (JSON/TOML parsing) (+0.3 confidence)
3. Check CLI availability (+0.2 confidence)
4. Check environment variables (+0.1 confidence)

Supported Platforms:
- Claude Code (claude_code)
- Claude Desktop (claude_desktop)
- Cursor (cursor)
- Auggie (auggie)
- Codex (codex)
- Gemini CLI (gemini_cli)
- Windsurf (windsurf)
- Antigravity (antigravity) - TBD
"""

import os
import sys
from pathlib import Path

from .exceptions import PlatformDetectionError
from .types import Platform, PlatformInfo, Scope
from .utils import parse_json_safe, parse_toml_safe, resolve_command_path


class PlatformDetector:
    """Detect which AI coding tool platform is currently running.

    This class provides methods to detect all supported platforms with
    confidence scoring, allowing intelligent selection in multi-platform
    environments.

    Example:
        >>> detector = PlatformDetector()
        >>> info = detector.detect()
        >>> print(f"{info.platform}: {info.confidence}")
        Platform.CLAUDE_CODE: 1.0
    """

    def __init__(self) -> None:
        """Initialize platform detector."""
        pass

    def detect(self) -> PlatformInfo:
        """Auto-detect current platform with highest confidence.

        Runs all platform-specific detectors and returns the one with
        highest confidence score.

        Returns:
            PlatformInfo for detected platform

        Raises:
            PlatformDetectionError: If no platforms detected

        Example:
            >>> detector = PlatformDetector()
            >>> info = detector.detect()
            >>> if info.confidence > 0.8:
            ...     print(f"Detected {info.platform} with high confidence")
        """
        # Run all detectors
        detectors = [
            self.detect_claude_code,
            self.detect_claude_desktop,
            self.detect_cursor,
            self.detect_auggie,
            self.detect_codex,
            self.detect_gemini_cli,
            self.detect_windsurf,
            self.detect_antigravity,
        ]

        results: list[tuple[float, Path | None]] = []
        for detector_func in detectors:
            confidence, config_path = detector_func()
            results.append((confidence, config_path))

        # Find platform with highest confidence
        max_confidence = max(r[0] for r in results)

        if max_confidence == 0.0:
            raise PlatformDetectionError("No supported platforms detected")

        # Map results back to platforms
        platform_results = list(
            zip(
                [
                    Platform.CLAUDE_CODE,
                    Platform.CLAUDE_DESKTOP,
                    Platform.CURSOR,
                    Platform.AUGGIE,
                    Platform.CODEX,
                    Platform.GEMINI_CLI,
                    Platform.WINDSURF,
                    Platform.ANTIGRAVITY,
                ],
                results,
            )
        )

        # Get platform with max confidence
        for platform, (confidence, config_path) in platform_results:
            if confidence == max_confidence:
                # Determine CLI availability
                cli_available = False
                if platform in (Platform.CLAUDE_CODE, Platform.CLAUDE_DESKTOP):
                    cli_available = resolve_command_path("claude") is not None
                elif platform == Platform.CURSOR:
                    cli_available = resolve_command_path("cursor") is not None

                return PlatformInfo(
                    platform=platform,
                    confidence=confidence,
                    config_path=config_path,
                    cli_available=cli_available,
                    scope_support=Scope.BOTH,
                )

        # Should never reach here, but fallback to unknown
        return PlatformInfo(
            platform=Platform.UNKNOWN,
            confidence=0.0,
            config_path=None,
            cli_available=False,
            scope_support=Scope.BOTH,
        )

    # ========================================================================
    # Platform-Specific Detectors
    # ========================================================================

    def detect_claude_code(self) -> tuple[float, Path | None]:
        """Detect Claude Code installation.

        Config locations (in priority order):
        1. ~/.config/claude/mcp.json (new location)
        2. .claude.json (legacy project-level)
        3. ~/.claude.json (legacy global)

        Returns:
            Tuple of (confidence, config_path)
            - confidence: 0.0-1.0
            - config_path: Path if found, None otherwise

        Example:
            >>> detector = PlatformDetector()
            >>> confidence, path = detector.detect_claude_code()
            >>> if confidence > 0.5:
            ...     print(f"Found Claude Code config at {path}")
        """
        confidence = 0.0
        config_path: Path | None = None

        # Priority 1: New location (~/.config/claude/mcp.json)
        new_config = Path.home() / ".config" / "claude" / "mcp.json"
        if new_config.exists():
            config_path = new_config
            confidence += 0.4

            # Validate JSON
            try:
                parse_json_safe(new_config)
                confidence += 0.3
            except Exception:
                pass  # Invalid JSON reduces confidence

        # Priority 2: Legacy project location (.claude.json)
        elif Path(".claude.json").exists():
            config_path = Path(".claude.json")
            confidence += 0.4

            try:
                parse_json_safe(config_path)
                confidence += 0.3
            except Exception:
                pass

        # Priority 3: Legacy global location (~/.claude.json)
        elif (Path.home() / ".claude.json").exists():
            config_path = Path.home() / ".claude.json"
            confidence += 0.4

            try:
                parse_json_safe(config_path)
                confidence += 0.3
            except Exception:
                pass

        # Check CLI availability
        if resolve_command_path("claude") is not None:
            confidence += 0.2

        # Check environment variables
        if os.getenv("CLAUDE_CODE_ENV"):
            confidence += 0.1

        return (min(confidence, 1.0), config_path)

    def detect_claude_desktop(self) -> tuple[float, Path | None]:
        """Detect Claude Desktop installation.

        Config locations (platform-specific):
        - macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
        - Linux: ~/.config/Claude/claude_desktop_config.json
        - Windows: %APPDATA%/Claude/claude_desktop_config.json

        Returns:
            Tuple of (confidence, config_path)
        """
        confidence = 0.0
        config_path: Path | None = None

        # Determine platform-specific config path
        if sys.platform == "darwin":
            # macOS
            config_path = (
                Path.home()
                / "Library"
                / "Application Support"
                / "Claude"
                / "claude_desktop_config.json"
            )
        elif sys.platform == "win32":
            # Windows
            appdata = os.environ.get("APPDATA", "")
            if appdata:
                config_path = Path(appdata) / "Claude" / "claude_desktop_config.json"
        else:
            # Linux
            config_path = (
                Path.home() / ".config" / "Claude" / "claude_desktop_config.json"
            )

        # Check if config exists
        if config_path and config_path.exists():
            confidence += 0.4

            # Validate JSON
            try:
                parse_json_safe(config_path)
                confidence += 0.3
            except Exception:
                pass

        # Check CLI availability (Claude Desktop uses same CLI as Claude Code)
        if resolve_command_path("claude") is not None:
            confidence += 0.2

        # Check for Claude Desktop process
        if sys.platform == "darwin":
            # Check if Claude.app exists
            claude_app = Path("/Applications/Claude.app")
            if claude_app.exists():
                confidence += 0.1

        return (min(confidence, 1.0), config_path)

    def detect_cursor(self) -> tuple[float, Path | None]:
        """Detect Cursor installation.

        Config location: ~/.cursor/mcp.json

        Returns:
            Tuple of (confidence, config_path)
        """
        confidence = 0.0
        config_path = Path.home() / ".cursor" / "mcp.json"

        # Check if config exists
        if config_path.exists():
            confidence += 0.4

            # Validate JSON
            try:
                parse_json_safe(config_path)
                confidence += 0.3
            except Exception:
                pass

        # Check CLI availability
        if resolve_command_path("cursor") is not None:
            confidence += 0.2

        # Check for Cursor directory
        if (Path.home() / ".cursor").exists():
            confidence += 0.1

        return (min(confidence, 1.0), config_path if config_path.exists() else None)

    def detect_auggie(self) -> tuple[float, Path | None]:
        """Detect Auggie installation.

        Config location: ~/.augment/settings.json

        Returns:
            Tuple of (confidence, config_path)
        """
        confidence = 0.0
        config_path = Path.home() / ".augment" / "settings.json"

        # Check if config exists
        if config_path.exists():
            confidence += 0.4

            # Validate JSON
            try:
                parse_json_safe(config_path)
                confidence += 0.3
            except Exception:
                pass

        # Check for Auggie directory
        if (Path.home() / ".augment").exists():
            confidence += 0.2

        # Check environment
        if os.getenv("AUGGIE_HOME"):
            confidence += 0.1

        return (min(confidence, 1.0), config_path if config_path.exists() else None)

    def detect_codex(self) -> tuple[float, Path | None]:
        """Detect Codex installation.

        Config location: ~/.codex/config.toml

        Returns:
            Tuple of (confidence, config_path)
        """
        confidence = 0.0
        config_path = Path.home() / ".codex" / "config.toml"

        # Check if config exists
        if config_path.exists():
            confidence += 0.4

            # Validate TOML
            try:
                parse_toml_safe(config_path)
                confidence += 0.3
            except Exception:
                pass

        # Check for Codex directory
        if (Path.home() / ".codex").exists():
            confidence += 0.2

        # Check CLI
        if resolve_command_path("codex") is not None:
            confidence += 0.1

        return (min(confidence, 1.0), config_path if config_path.exists() else None)

    def detect_gemini_cli(self) -> tuple[float, Path | None]:
        """Detect Gemini CLI installation.

        Config locations (in priority order):
        1. .gemini/settings.json (project-level)
        2. ~/.gemini/settings.json (user-level)

        Returns:
            Tuple of (confidence, config_path)
        """
        confidence = 0.0
        config_path: Path | None = None

        # Priority 1: Project-level config
        project_config = Path(".gemini") / "settings.json"
        if project_config.exists():
            config_path = project_config
            confidence += 0.4

            try:
                parse_json_safe(config_path)
                confidence += 0.3
            except Exception:
                pass

        # Priority 2: User-level config
        elif (Path.home() / ".gemini" / "settings.json").exists():
            config_path = Path.home() / ".gemini" / "settings.json"
            confidence += 0.4

            try:
                parse_json_safe(config_path)
                confidence += 0.3
            except Exception:
                pass

        # Check for Gemini directory
        if (Path.home() / ".gemini").exists() or Path(".gemini").exists():
            confidence += 0.2

        # Check CLI
        if resolve_command_path("gemini") is not None:
            confidence += 0.1

        return (min(confidence, 1.0), config_path)

    def detect_windsurf(self) -> tuple[float, Path | None]:
        """Detect Windsurf installation.

        Config location: ~/.codeium/windsurf/mcp_config.json

        Returns:
            Tuple of (confidence, config_path)
        """
        confidence = 0.0
        config_path = Path.home() / ".codeium" / "windsurf" / "mcp_config.json"

        # Check if config exists
        if config_path.exists():
            confidence += 0.4

            # Validate JSON
            try:
                parse_json_safe(config_path)
                confidence += 0.3
            except Exception:
                pass

        # Check for Windsurf directory
        if (Path.home() / ".codeium" / "windsurf").exists():
            confidence += 0.2

        # Check for Windsurf app (macOS)
        if sys.platform == "darwin":
            windsurf_app = Path("/Applications/Windsurf.app")
            if windsurf_app.exists():
                confidence += 0.1

        return (min(confidence, 1.0), config_path if config_path.exists() else None)

    def detect_antigravity(self) -> tuple[float, Path | None]:
        """Detect Antigravity installation.

        Note: Config location not yet documented. This is a placeholder
        implementation that always returns 0.0 confidence.

        Returns:
            Tuple of (confidence=0.0, config_path=None)
        """
        # TODO: Update when Antigravity config location is documented
        return (0.0, None)
