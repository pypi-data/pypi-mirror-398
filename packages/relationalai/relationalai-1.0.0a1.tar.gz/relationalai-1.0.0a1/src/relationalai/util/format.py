"""Formatting utilities for RelationalAI."""

from __future__ import annotations


def format_duration(seconds: float) -> str:
    """Format a duration in seconds as a human-readable string.

    Args:
        seconds: Duration in seconds (can be fractional)

    Returns:
        Formatted duration string (e.g., "1.2s", "3m 45s", "1h 23m 45s")

    Examples:
        >>> format_duration(0.5)
        '0.5s'
        >>> format_duration(65.5)
        '1m 5s'
        >>> format_duration(3661)
        '1h 1m 1s'
    """
    if seconds < 0:
        return "0s"

    if seconds < 60:
        # Less than a minute: show seconds with appropriate precision
        if seconds < 1:
            # Sub-second: show 2 decimal places
            return f"{seconds:.2f}s".rstrip("0").rstrip(".")
        elif seconds < 10:
            # 1-10 seconds: show 1 decimal place
            return f"{seconds:.1f}s".rstrip("0").rstrip(".")
        else:
            # 10+ seconds: show as integer
            return f"{int(seconds)}s"

    # Calculate hours, minutes, and remaining seconds
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60

    parts = []

    if hours > 0:
        parts.append(f"{hours}h")

    if minutes > 0:
        parts.append(f"{minutes}m")

    # Only show seconds if less than a minute has elapsed, or if it's a significant portion
    if hours == 0 and minutes == 0:
        # Show seconds with decimal if less than a minute
        if secs < 1:
            parts.append(f"{secs:.2f}s".rstrip("0").rstrip("."))
        elif secs < 10:
            parts.append(f"{secs:.1f}s".rstrip("0").rstrip("."))
        else:
            parts.append(f"{int(secs)}s")
    elif secs >= 1:
        # Show seconds as integer if >= 1 second when we have minutes/hours
        parts.append(f"{int(secs)}s")

    return " ".join(parts) if parts else "0s"

