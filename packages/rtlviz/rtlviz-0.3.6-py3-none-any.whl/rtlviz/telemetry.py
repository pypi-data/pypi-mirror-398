"""
RTLViz Telemetry - Privacy-Protected Usage Analytics

This module sends anonymous usage pings to help improve RTLViz.
NO personal data, file contents, or identifying information is collected.

What IS collected:
- Event type (session_start, resource_read, tool_call, render)
- RTLViz version
- Random session ID (not tied to user)

What is NOT collected:
- IP addresses
- File paths or contents
- User names or machine names
- Any RTL/Verilog code
- Operating system details

Users can opt-out by setting: RTLVIZ_TELEMETRY=0
"""

import os
import uuid
import threading
from typing import Optional

# Telemetry endpoint - Google Apps Script webhook
TELEMETRY_ENDPOINT = os.environ.get(
    "RTLVIZ_TELEMETRY_URL",
    "https://script.google.com/macros/s/AKfycbxJiF7kJuUNYXwJbsn2x8jTlXW-w3-nhoh4y344U2YtCm9y4yCSiptVq1rPkLbqzjOC7Q/exec"
)

# Version
VERSION = "0.3.3"

# Persistent session ID for this run (regenerated each server start)
_SESSION_ID: Optional[str] = None


def _get_session_id() -> str:
    """Get or create a session ID for this run."""
    global _SESSION_ID
    if _SESSION_ID is None:
        _SESSION_ID = str(uuid.uuid4())[:8]  # Short random ID
    return _SESSION_ID


def is_telemetry_enabled() -> bool:
    """Check if telemetry is enabled (opt-out via env var)."""
    return os.environ.get("RTLVIZ_TELEMETRY", "1").lower() not in ("0", "false", "no", "off")


def _send_ping_sync(event: str, extra: dict = None) -> bool:
    """Send a telemetry ping SYNCHRONOUSLY. Returns True if successful."""
    if not is_telemetry_enabled():
        return False
    
    # Skip if using placeholder URL
    if "YOUR_DEPLOYMENT_ID" in TELEMETRY_ENDPOINT:
        return False
    
    try:
        import urllib.request
        import json
        
        payload = {
            "event": event,
            "version": VERSION,
            "session_id": _get_session_id(),
            "token": "rtlviz-analytics-v1-keep-safe"
        }
        if extra:
            payload.update(extra)
        
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            TELEMETRY_ENDPOINT,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        # Short timeout but wait for completion
        urllib.request.urlopen(req, timeout=3)
        return True
    except Exception:
        # Silently ignore all errors - telemetry should never break the app
        return False


def _send_ping_async(event: str, extra: dict = None) -> None:
    """Send a telemetry ping in background thread (for non-critical events)."""
    if not is_telemetry_enabled():
        return
    
    if "YOUR_DEPLOYMENT_ID" in TELEMETRY_ENDPOINT:
        return
    
    def _do_send():
        _send_ping_sync(event, extra)
    
    # Run in background thread - NOT daemon so it survives script exit
    thread = threading.Thread(target=_do_send, daemon=False)
    thread.start()


# ============ Public API ============

def ping_session_start() -> None:
    """Ping when the server starts. SYNCHRONOUS - logs before server responds."""
    _send_ping_sync("session_start")


def ping_resource_read(resource_name: str) -> None:
    """Ping when a resource is read. SYNCHRONOUS - logs before response."""
    _send_ping_sync("resource_read", {"resource": resource_name})


def ping_tool_call(tool_name: str) -> None:
    """Ping when a tool is called. SYNCHRONOUS - logs before tool executes."""
    _send_ping_sync("tool_call", {"tool": tool_name})


def ping_diagram_rendered(success: bool = True) -> None:
    """Ping when a diagram is rendered (async, happens after file write)."""
    _send_ping_async("render", {"success": success})


def ping_cli_generate(module_count: int, use_llm: bool) -> None:
    """Ping when CLI generate command is used."""
    _send_ping_sync("cli_generate", {"modules": module_count, "llm": use_llm})


def ping_cli_setup(ide: str) -> None:
    """Ping when CLI setup command is used."""
    _send_ping_sync("cli_setup", {"ide": ide})
