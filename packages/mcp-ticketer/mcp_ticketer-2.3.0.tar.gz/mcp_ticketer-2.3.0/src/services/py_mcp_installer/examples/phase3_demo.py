#!/usr/bin/env python3
"""Phase 3 Demo: MCPInstaller and MCPInspector usage examples.

This script demonstrates the main API features of py-mcp-installer Phase 3.
"""

import sys
from pathlib import Path

# Add src to path for local development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from py_mcp_installer import (
    MCPInstaller,
    Scope,
)


def demo_auto_detection() -> None:
    """Demo: Auto-detect platform and show info."""
    print("\n" + "=" * 60)
    print("Demo 1: Auto-Detection")
    print("=" * 60)

    try:
        installer = MCPInstaller.auto_detect(verbose=True)
        info = installer.platform_info

        print(f"\n✅ Detected Platform: {info.platform.value}")
        print(f"   Confidence: {info.confidence:.2%}")
        print(f"   Config Path: {info.config_path}")
        print(f"   CLI Available: {info.cli_available}")
        print(f"   Scope Support: {info.scope_support.value}")

    except Exception as e:
        print(f"\n❌ Detection failed: {e}")


def demo_inspection() -> None:
    """Demo: Run inspection and show results."""
    print("\n" + "=" * 60)
    print("Demo 2: Installation Inspection")
    print("=" * 60)

    try:
        installer = MCPInstaller.auto_detect()
        report = installer.inspect_installation()

        print(f"\n{report.summary()}")

        if report.issues:
            print("\nIssues Found:")
            for issue in report.issues:
                icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}[issue.severity]
                print(f"\n  {icon} [{issue.severity.upper()}] {issue.message}")
                if issue.server_name:
                    print(f"     Server: {issue.server_name}")
                print(f"     Fix: {issue.fix_suggestion}")
                if issue.auto_fixable:
                    print("     (Auto-fixable)")

        if report.recommendations:
            print("\nRecommendations:")
            for rec in report.recommendations:
                print(f"  • {rec}")

    except Exception as e:
        print(f"\n❌ Inspection failed: {e}")


def demo_list_servers() -> None:
    """Demo: List installed servers."""
    print("\n" + "=" * 60)
    print("Demo 3: List Installed Servers")
    print("=" * 60)

    try:
        installer = MCPInstaller.auto_detect()
        servers = installer.list_servers(scope=Scope.PROJECT)

        if servers:
            print(f"\n✅ Found {len(servers)} server(s):\n")
            for server in servers:
                print(f"  📦 {server.name}")
                print(f"     Command: {server.command}")
                if server.args:
                    print(f"     Args: {' '.join(server.args)}")
                if server.env:
                    print(f"     Env Vars: {', '.join(server.env.keys())}")
                if server.description:
                    print(f"     Description: {server.description}")
                print()
        else:
            print("\n⚠️  No servers installed")

    except Exception as e:
        print(f"\n❌ Failed to list servers: {e}")


def demo_dry_run_install() -> None:
    """Demo: Dry-run installation (safe preview)."""
    print("\n" + "=" * 60)
    print("Demo 4: Dry-Run Installation")
    print("=" * 60)

    try:
        installer = MCPInstaller.auto_detect(dry_run=True, verbose=True)

        print("\n🔍 Previewing installation (no actual changes)...\n")

        result = installer.install_server(
            name="demo-server",
            command="uv",
            args=["run", "demo-server", "mcp"],
            description="Demo server for testing",
        )

        if result.success:
            print(f"\n✅ {result.message}")
            print(f"   Would install to: {result.config_path}")
        else:
            print(f"\n❌ {result.message}")

    except Exception as e:
        print(f"\n❌ Dry-run failed: {e}")


def demo_get_server() -> None:
    """Demo: Get specific server details."""
    print("\n" + "=" * 60)
    print("Demo 5: Get Server Details")
    print("=" * 60)

    try:
        installer = MCPInstaller.auto_detect()
        servers = installer.list_servers()

        if servers:
            # Get first server as example
            server_name = servers[0].name
            server = installer.get_server(server_name)

            if server:
                print(f"\n✅ Server Details: {server.name}\n")
                print(f"   Command: {server.command}")
                print(f"   Args: {server.args}")
                print(f"   Env Vars: {list(server.env.keys())}")
                print(f"   Description: {server.description or '(none)'}")
            else:
                print(f"\n⚠️  Server '{server_name}' not found")
        else:
            print("\n⚠️  No servers installed to query")

    except Exception as e:
        print(f"\n❌ Failed to get server: {e}")


def main() -> None:
    """Run all demos."""
    print("\n╔══════════════════════════════════════════════════════════╗")
    print("║  py-mcp-installer Phase 3 Demo                          ║")
    print("║  MCPInstaller & MCPInspector API Examples               ║")
    print("╚══════════════════════════════════════════════════════════╝")

    # Run demos
    demo_auto_detection()
    demo_inspection()
    demo_list_servers()
    demo_get_server()
    demo_dry_run_install()

    print("\n" + "=" * 60)
    print("✅ All demos completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
