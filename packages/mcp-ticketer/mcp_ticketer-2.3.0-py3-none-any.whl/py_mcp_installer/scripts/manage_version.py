#!/usr/bin/env python3
"""Version management for py-mcp-installer-service."""
import re
import sys
from pathlib import Path
from typing import Literal

REPO_ROOT = Path(__file__).parent.parent
VERSION_FILE = REPO_ROOT / "VERSION"
INIT_FILE = REPO_ROOT / "src/py_mcp_installer/__init__.py"


def get_current_version() -> str:
    """Read version from VERSION file."""
    return VERSION_FILE.read_text().strip()


def bump_version(bump_type: Literal["major", "minor", "patch"]) -> str:
    """Bump version and update files."""
    current = get_current_version()
    major, minor, patch = map(int, current.split("."))

    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    else:  # patch
        patch += 1

    new_version = f"{major}.{minor}.{patch}"

    # Update VERSION file
    VERSION_FILE.write_text(f"{new_version}\n")

    # Update __init__.py
    init_content = INIT_FILE.read_text()
    init_content = re.sub(
        r'__version__ = "[^"]+"', f'__version__ = "{new_version}"', init_content
    )
    INIT_FILE.write_text(init_content)

    return new_version


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(get_current_version())
    elif sys.argv[1] == "bump":
        bump_type = sys.argv[2] if len(sys.argv) > 2 else "patch"
        new_version = bump_version(bump_type)
        print(new_version)
