"""Format utilities - Duration parsing and formatting."""

import re


def parse_duration(duration: str) -> int:
    """Parse duration string to milliseconds.
    
    Args:
        duration: Duration string like "30s", "5m", "1h"
    
    Returns:
        Duration in milliseconds
    """
    match = re.match(r"^(\d+)(s|m|h)$", duration.strip().lower())
    if not match:
        return 30000  # Default 30s
    
    value = int(match.group(1))
    unit = match.group(2)
    
    if unit == "s":
        return value * 1000
    elif unit == "m":
        return value * 60 * 1000
    elif unit == "h":
        return value * 60 * 60 * 1000
    
    return 30000


def format_duration(ms: int) -> str:
    """Format milliseconds to human readable duration.
    
    Args:
        ms: Duration in milliseconds
    
    Returns:
        Formatted duration string like "1m30s"
    """
    total_seconds = ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    
    if minutes > 0:
        return f"{minutes}m{seconds}s"
    return f"{seconds}s"


def format_bytes(bytes_count: int) -> str:
    """Format bytes to human readable size."""
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_count < 1024:
            return f"{bytes_count:.1f}{unit}"
        bytes_count /= 1024
    return f"{bytes_count:.1f}TB"

