#!/usr/bin/env python3
"""
RTLViz Setup - Auto-configure MCP servers for AI IDEs.

Usage:
    rtlviz setup                # Configure ALL detected IDEs
    rtlviz setup --all          # Force configure ALL IDEs
    rtlviz setup --antigravity  # Configure Antigravity only
    rtlviz setup --claude       # Configure Claude Desktop only
    rtlviz setup --cursor       # Configure Cursor only
    rtlviz setup --vscode       # Configure VS Code Copilot only
    rtlviz setup --windsurf     # Configure Windsurf only
"""

import os
import sys
import json
import shutil
from pathlib import Path

# Import telemetry
try:
    from .telemetry import ping_cli_setup
except ImportError:
    def ping_cli_setup(ide): pass  # Fallback if telemetry not available

# MCP server configuration
MCP_CONFIG = {
    "command": "rtlviz-server"
}


# =============================================================================
# Config Path Helpers
# =============================================================================

def get_claude_desktop_config_path() -> Path:
    """Get Claude Desktop config path based on OS."""
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", "")) / "Claude" / "claude_desktop_config.json"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    else:  # Linux
        return Path.home() / ".config" / "claude" / "claude_desktop_config.json"


def get_claude_code_config_path() -> Path:
    """Get Claude Code (VS Code extension) config path."""
    return Path.home() / ".claude" / "settings.json"


def get_vscode_config_path() -> Path:
    """Get VS Code Copilot MCP config path (workspace-level)."""
    return Path.cwd() / ".vscode" / "mcp.json"


def get_cursor_config_path() -> Path:
    """Get Cursor global MCP config path."""
    return Path.home() / ".cursor" / "mcp.json"


def get_windsurf_config_path() -> Path:
    """Get Windsurf MCP config path."""
    return Path.home() / ".codeium" / "windsurf" / "mcp_config.json"


def get_antigravity_config_path() -> Path:
    """Get Antigravity (Google DeepMind) MCP config path."""
    return Path.home() / ".gemini" / "antigravity" / "mcp_config.json"


# =============================================================================
# Configuration Functions
# =============================================================================

def _configure_mcp_servers_key(config_path: Path, ide_name: str, restart_msg: str) -> bool:
    """Generic helper for IDEs that use 'mcpServers' key."""
    print(f"📍 {ide_name} config: {config_path}")
    
    # Load existing config or create new
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            try:
                config = json.load(f)
            except json.JSONDecodeError:
                config = {}
    else:
        config = {}
        config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Ensure mcpServers exists
    if "mcpServers" not in config:
        config["mcpServers"] = {}
    
    # Check if already configured
    if "rtlviz" in config["mcpServers"]:
        print(f"✅ RTLViz already configured for {ide_name}")
        return True
    
    # Backup existing file
    if config_path.exists():
        backup_path = config_path.with_suffix(".json.backup")
        shutil.copy(config_path, backup_path)
        print(f"📦 Backed up existing config to: {backup_path}")
    
    # Add rtlviz
    config["mcpServers"]["rtlviz"] = MCP_CONFIG
    
    # Write new config
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    
    # Telemetry
    ping_cli_setup(ide_name)
    
    print(f"✅ RTLViz configured for {ide_name}")
    print(f"   {restart_msg}")
    return True


def _configure_servers_key(config_path: Path, ide_name: str, restart_msg: str) -> bool:
    """Generic helper for IDEs that use 'servers' key (VS Code Copilot)."""
    print(f"📍 {ide_name} config: {config_path}")
    
    # Load existing config or create new
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            try:
                config = json.load(f)
            except json.JSONDecodeError:
                config = {}
    else:
        config = {}
        config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Ensure servers exists
    if "servers" not in config:
        config["servers"] = {}
    
    # Check if already configured
    if "rtlviz" in config["servers"]:
        print(f"✅ RTLViz already configured for {ide_name}")
        return True
    
    # Add rtlviz
    config["servers"]["rtlviz"] = MCP_CONFIG
    
    # Write new config
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ RTLViz configured for {ide_name} (current workspace)")
    print(f"   {restart_msg}")
    return True


def configure_claude_desktop() -> bool:
    """Add rtlviz to Claude Desktop configuration."""
    return _configure_mcp_servers_key(
        get_claude_desktop_config_path(),
        "Claude Desktop",
        "Restart Claude Desktop to activate"
    )


def configure_claude_code() -> bool:
    """Add rtlviz to Claude Code (VS Code extension) configuration."""
    return _configure_mcp_servers_key(
        get_claude_code_config_path(),
        "Claude Code",
        "Restart VS Code to activate"
    )


def configure_vscode() -> bool:
    """Add rtlviz to VS Code Copilot MCP configuration."""
    return _configure_servers_key(
        get_vscode_config_path(),
        "VS Code Copilot",
        "Reload VS Code window to activate"
    )


def configure_cursor() -> bool:
    """Add rtlviz to Cursor configuration."""
    return _configure_mcp_servers_key(
        get_cursor_config_path(),
        "Cursor",
        "Restart Cursor to activate"
    )


def configure_windsurf() -> bool:
    """Add rtlviz to Windsurf configuration."""
    return _configure_mcp_servers_key(
        get_windsurf_config_path(),
        "Windsurf",
        "Restart Windsurf to activate"
    )


def configure_antigravity() -> bool:
    """Add rtlviz to Antigravity (Google DeepMind) configuration."""
    return _configure_mcp_servers_key(
        get_antigravity_config_path(),
        "Antigravity",
        "Restart Antigravity to activate"
    )


# =============================================================================
# IDE Detection
# =============================================================================

def detect_and_configure_all() -> bool:
    """Auto-detect installed IDEs and configure them."""
    print("Auto-detecting IDEs...\n")
    
    configured = []
    
    # Claude Desktop - check if config dir exists or on supported OS
    claude_path = get_claude_desktop_config_path()
    if claude_path.parent.exists() or sys.platform in ("win32", "darwin"):
        print("🔍 Found Claude Desktop")
        configure_claude_desktop()
        configured.append("Claude Desktop")
        print()
    
    # Claude Code - check if ~/.claude exists
    claude_code_path = get_claude_code_config_path()
    if claude_code_path.parent.exists():
        print("🔍 Found Claude Code")
        configure_claude_code()
        configured.append("Claude Code")
        print()
    
    # VS Code Copilot - check for .vscode or .git in current directory
    if (Path.cwd() / ".vscode").exists() or (Path.cwd() / ".git").exists():
        print("🔍 Found VS Code workspace")
        configure_vscode()
        configured.append("VS Code Copilot")
        print()
    
    # Cursor - check if ~/.cursor exists
    cursor_path = get_cursor_config_path()
    if cursor_path.parent.exists():
        print("🔍 Found Cursor")
        configure_cursor()
        configured.append("Cursor")
        print()
    
    # Windsurf - check if ~/.codeium/windsurf exists
    windsurf_path = get_windsurf_config_path()
    if windsurf_path.parent.exists():
        print("🔍 Found Windsurf")
        configure_windsurf()
        configured.append("Windsurf")
        print()
    
    # Antigravity - check if ~/.gemini/antigravity exists
    antigravity_path = get_antigravity_config_path()
    if antigravity_path.parent.exists():
        print("🔍 Found Antigravity")
        configure_antigravity()
        configured.append("Antigravity")
        print()
    
    if not configured:
        print("⚠️  No supported IDEs detected.")
        print("   Use --all to force configure all IDEs, or specify one:")
        print("   --antigravity, --claude, --cursor, --vscode, --windsurf")
        return False
    
    return True


def configure_all_forced() -> bool:
    """Force configure all IDEs regardless of detection."""
    print("Configuring all IDEs...\n")
    
    print("1/6 Antigravity")
    configure_antigravity()
    print()
    
    print("2/6 Claude Desktop")
    configure_claude_desktop()
    print()
    
    print("3/6 Claude Code")
    configure_claude_code()
    print()
    
    print("4/6 VS Code Copilot")
    configure_vscode()
    print()
    
    print("5/6 Cursor")
    configure_cursor()
    print()
    
    print("6/6 Windsurf")
    configure_windsurf()
    print()
    
    return True


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    """Main entry point."""
    print("🔧 RTLViz Setup")
    print("=" * 50)
    
    args = sys.argv[1:]
    
    if "--help" in args or "-h" in args:
        print(__doc__)
        print("\nSupported IDEs:")
        print("  • Antigravity     - Google DeepMind's Antigravity")
        print("  • Claude Desktop  - Anthropic's desktop app")
        print("  • Claude Code     - Anthropic's VS Code extension")
        print("  • VS Code Copilot - GitHub Copilot in VS Code")
        print("  • Cursor          - Cursor IDE")
        print("  • Windsurf        - Codeium's Windsurf IDE")
        return 0
    
    success = True
    
    if "--antigravity" in args:
        success = configure_antigravity()
    elif "--claude" in args:
        success = configure_claude_desktop()
    elif "--claude-code" in args:
        success = configure_claude_code()
    elif "--vscode" in args:
        success = configure_vscode()
    elif "--cursor" in args:
        success = configure_cursor()
    elif "--windsurf" in args:
        success = configure_windsurf()
    elif "--all" in args:
        success = configure_all_forced()
    else:
        # Default: auto-detect and configure found IDEs
        success = detect_and_configure_all()
    
    print("=" * 50)
    if success:
        print("🚀 Setup complete! You can now use RTLViz.")
        print("   Just ask your AI: 'Generate an RTL diagram for CPU.v'")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
