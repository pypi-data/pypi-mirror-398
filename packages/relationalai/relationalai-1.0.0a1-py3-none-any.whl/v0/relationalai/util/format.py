def humanized_duration(ms: int) -> str:
    """Format duration in milliseconds to human-readable format with spaces.

    Converts milliseconds to a human-readable string with up to 3 time components
    (days, hours, minutes, seconds) separated by spaces.

    Args:
        ms: Duration in milliseconds

    Returns:
        Formatted string like '1h 2m 3.5s' (max 3 components).
        Returns empty string for zero duration.

    Examples:
        >>> humanized_duration(1000)
        '1.0s'
        >>> humanized_duration(90000)
        '1m 30.0s'
        >>> humanized_duration(3665000)
        '1h 1m 5.0s'
        >>> humanized_duration(95400000)
        '1d 2h 30m'
    """
    # Convert milliseconds to other time units
    seconds = ms / 1000
    minutes = seconds / 60
    hours = minutes / 60
    days = hours / 24

    # Extract display components using modulo to get remainders
    display_days = int(days)
    display_hours = int(hours % 24)
    display_minutes = int(minutes % 60)
    display_seconds = seconds % 60

    # Build list of non-zero time components
    parts = []
    if display_days > 0:
        parts.append(f"{display_days}d")
    if display_hours > 0:
        parts.append(f"{display_hours}h")
    if display_minutes > 0:
        parts.append(f"{display_minutes}m")
    if display_seconds > 0:
        # Show seconds with one decimal place (no thousand separators for time)
        parts.append(f"{display_seconds:.1f}s")

    # Return up to 3 components, space-separated
    return " ".join(parts[:3])


def format_duration(duration_seconds: float) -> str:
    """Format duration in seconds to human-readable format.

    Args:
        duration_seconds: Duration in seconds

    Returns:
        Formatted string like '500ms', '2.5s', '1m30s', '1h5m'

    Examples:
        >>> format_duration(0.5)
        '500ms'
        >>> format_duration(2.5)
        '2.5s'
        >>> format_duration(90)
        '1m30s'
        >>> format_duration(3665)
        '1h1m'
    """
    # For durations less than 1 second, show milliseconds
    if duration_seconds < 1:
        milliseconds = round(duration_seconds * 1000)
        # Handle edge case where rounding gives us 1000ms
        if milliseconds >= 1000:
            return "1.0s"
        return f"{milliseconds}ms"

    # For durations less than 1 minute, show seconds with one decimal
    elif duration_seconds < 60:
        return f"{round(duration_seconds, 1)}s"

    # For durations less than 1 hour, show minutes and seconds
    elif duration_seconds < 3600:
        minutes = int(duration_seconds // 60)
        seconds = int(duration_seconds % 60)
        if seconds == 0:
            return f"{minutes}m"
        else:
            return f"{minutes}m{seconds}s"
    else:
        hours = int(duration_seconds // 3600)
        minutes = int((duration_seconds % 3600) // 60)
        if minutes == 0:
            return f"{hours}h"
        else:
            return f"{hours}h{minutes}m"

def humanized_bytes(bytes: int) -> str:
    """Format bytes to human-readable format."""
    if bytes < 1024:
        return f"{bytes} B"
    elif bytes < 1024 ** 2:
        return f"{bytes / 1024:.1f} KB"
    elif bytes < 1024 ** 3:
        return f"{bytes / 1024 ** 2:.1f} MB"
    elif bytes < 1024 ** 4:
        return f"{bytes / 1024 ** 3:.1f} GB"
    else:
        return f"{bytes / 1024 ** 4:.1f} TB"

def str_to_bool(s):
    # Adapted from snowflake's convert_str_to_bool
    if s is None:
        return None
    if s.lower() in ("true", "t", "yes", "y", "on", "1"):
        return True
    if s.lower() in ("false", "f", "no", "n", "off", "0"):
        return False
    raise ValueError(f"Invalid boolean value: {s}")

def default_serialize(obj):
    return '<skipped>'
