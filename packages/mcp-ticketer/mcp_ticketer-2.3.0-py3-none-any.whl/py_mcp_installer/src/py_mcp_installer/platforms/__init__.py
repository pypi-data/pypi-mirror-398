"""Platform-specific implementations for MCP installation.

This module provides platform-specific strategies and configurations
for different AI coding tools.

Supported platforms:
- Claude Code (claude_code.py)
- Cursor (cursor.py)
- Codex (codex.py)

Each platform module provides:
- Configuration path detection
- Installation strategy selection
- Platform-specific validation
- Command building utilities
"""

from .claude_code import ClaudeCodeStrategy
from .codex import CodexStrategy
from .cursor import CursorStrategy

__all__ = [
    "ClaudeCodeStrategy",
    "CursorStrategy",
    "CodexStrategy",
]
