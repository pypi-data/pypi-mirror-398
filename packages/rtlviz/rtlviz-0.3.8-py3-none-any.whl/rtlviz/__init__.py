# RTLViz MCP Server
"""
RTLViz - AI-powered RTL diagram generation via MCP.

On first import after installation, we log an 'install' event.
This helps track adoption without collecting any personal data.
"""

import os
from pathlib import Path


def _check_first_use():
    """Check if this is the first time the package is being used.
    
    Creates a marker file in user's config directory on first use.
    This fires an 'install' telemetry event once per machine.
    """
    try:
        # Use user's home directory for the marker
        marker_dir = Path.home() / ".rtlviz"
        marker_file = marker_dir / ".installed"
        
        if not marker_file.exists():
            # First use! Create marker and send telemetry
            marker_dir.mkdir(parents=True, exist_ok=True)
            
            # Import telemetry and ping
            from rtlviz.telemetry import _send_ping_sync, VERSION
            _send_ping_sync("install")
            
            # Write marker with version
            marker_file.write_text(VERSION, encoding="utf-8")
    except Exception:
        # Never break import due to telemetry
        pass


# Run first-use check on import
_check_first_use()
