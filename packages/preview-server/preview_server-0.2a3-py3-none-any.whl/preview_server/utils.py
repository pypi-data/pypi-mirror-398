"""Utility functions for preview server."""

import re
import socket
from pathlib import Path
from typing import Optional


def parse_duration(duration_str: str) -> int:
    """Parse a duration string to seconds.

    Supports formats like:
    - "5s" -> 5 seconds
    - "5m" -> 300 seconds
    - "1h" -> 3600 seconds
    - "1h5m30s" -> 3930 seconds
    - "1 h 5 m 30 s" -> 3930 seconds (with spaces)

    Args:
        duration_str: Duration string in human-readable format

    Returns:
        Duration in seconds

    Raises:
        ValueError: If the duration string is invalid or cannot be parsed
    """
    if not duration_str:
        raise ValueError("Duration string cannot be empty")

    # Remove spaces for easier parsing
    duration_str = duration_str.replace(" ", "")

    # Pattern to match number + unit pairs
    pattern = r"(\d+)([smh])"
    matches = re.findall(pattern, duration_str)

    if not matches:
        raise ValueError(f"Invalid duration format: {duration_str}")

    # Ensure we matched the entire string (no leftover characters)
    matched_chars = sum(len(match[0]) + 1 for match in matches)
    if matched_chars != len(duration_str):
        raise ValueError(f"Invalid duration format: {duration_str}")

    total_seconds = 0
    unit_map = {
        "s": 1,
        "m": 60,
        "h": 3600,
    }

    for value_str, unit in matches:
        value = int(value_str)
        total_seconds += value * unit_map[unit]

    return total_seconds


def find_unused_port(preferred_port: Optional[int] = None) -> int:
    """Find an unused port (legacy wrapper, prefer reserve_port).

    Args:
        preferred_port: Port number to try first (default: None)

    Returns:
        An available port number
    """
    port, sock = reserve_port(preferred_port)
    sock.close()
    return port


def reserve_port(preferred_port: Optional[int] = None) -> tuple[int, socket.socket]:
    """Reserve an unused port by keeping the socket open.

    This avoids the race condition where another process could grab the port
    between when we check availability and when the subprocess binds to it.
    The caller should close the socket after the subprocess has started and
    bound to the port (or failed).

    Args:
        preferred_port: Port number to try first (default: None)

    Returns:
        Tuple of (port_number, socket). Caller must close the socket.

    Raises:
        OSError: If no port can be found (very unlikely)
    """
    if preferred_port is not None:
        # Try the preferred port first
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("127.0.0.1", preferred_port))
            sock.listen(1)  # Put in listen mode to fully reserve
            return preferred_port, sock
        except OSError:
            # Preferred port is in use, fall through to automatic selection
            pass

    # Let the OS choose an unused port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 0))
    sock.listen(1)  # Put in listen mode to fully reserve
    port = sock.getsockname()[1]
    return port, sock


def get_serve_command(worktree_path: str) -> str:
    """Get the serve command from server.sh.

    Looks for a server.sh script in the worktree root. The script will be
    executed with the PORT environment variable set to the assigned port.

    Args:
        worktree_path: Path to the worktree containing server.sh

    Returns:
        The serve command string (path to server.sh)

    Raises:
        RuntimeError: If server.sh is missing or not executable
    """
    server_script = Path(worktree_path) / "server.sh"

    if not server_script.exists():
        raise RuntimeError(
            f"server.sh not found in {worktree_path}. "
            "Please create a server.sh script that starts your server on $PORT.\n\n"
            "Example server.sh:\n"
            "#!/bin/bash\n"
            "npm run dev -- --port $PORT"
        )

    # Return the command to execute the script
    # Use bash explicitly to avoid permission issues
    return f"bash {server_script}"
