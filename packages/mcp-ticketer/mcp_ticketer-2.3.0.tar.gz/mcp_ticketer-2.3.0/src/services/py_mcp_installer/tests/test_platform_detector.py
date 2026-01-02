"""Tests for platform detector."""


from py_mcp_installer.platform_detector import PlatformDetector
from py_mcp_installer.types import Platform


def test_detect_returns_platform():
    """Test that detect returns a valid Platform."""
    result = PlatformDetector.detect()
    assert isinstance(result, Platform)


def test_get_config_path():
    """Test config path retrieval."""
    path = PlatformDetector.get_config_path(Platform.CLAUDE_CODE)
    assert path is not None or Platform.CLAUDE_CODE == Platform.UNKNOWN
