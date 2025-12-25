"""Constants and configuration values for transmission-cleaner.

Centralizes magic numbers, file size conversions, and system configuration
to improve maintainability and consistency.
"""

from typing import Final

# File size constants (bytes)
BYTES_PER_KB: Final[int] = 1024
BYTES_PER_MB: Final[int] = 1024 * 1024
BYTES_PER_GB: Final[int] = 1024 * 1024 * 1024
BYTES_PER_TB: Final[int] = 1024 * 1024 * 1024 * 1024

# Time constants (seconds)
SECONDS_PER_MINUTE: Final[int] = 60
SECONDS_PER_HOUR: Final[int] = 60 * 60
SECONDS_PER_DAY: Final[int] = 60 * 60 * 24

# Default values
DEFAULT_MIN_SEEDING_DAYS: Final[int] = 7
DEFAULT_HOST: Final[str] = "127.0.0.1"
DEFAULT_PORT: Final[int] = 9091
DEFAULT_RPC_PATH: Final[str] = "/transmission/rpc"
DEFAULT_PROTOCOL: Final[str] = "http"

# System files to exclude from scans
SYSTEM_FILES: Final[frozenset[str]] = frozenset(
    {
        ".DS_Store",  # macOS
        "Thumbs.db",  # Windows
        "desktop.ini",  # Windows
        ".directory",  # KDE
        "folder.jpg",  # Media folder images
        "folder.png",
        ".@__thumb",  # Synology NAS thumbnails
        "@eaDir",  # Synology NAS metadata
    }
)

# File extensions to exclude
EXCLUDED_EXTENSIONS: Final[frozenset[str]] = frozenset(
    {
        ".torrent",
        ".part",  # Partial downloads
        ".crdownload",  # Chrome partial downloads
        ".tmp",  # Temporary files
    }
)

# Action types
ACTION_LIST: Final[str] = "list"
ACTION_LIST_SHORT: Final[str] = "l"
ACTION_INTERACTIVE: Final[str] = "interactive"
ACTION_INTERACTIVE_SHORT: Final[str] = "i"
ACTION_DELETE: Final[str] = "delete"
ACTION_DELETE_SHORT: Final[str] = "d"
ACTION_REMOVE: Final[str] = "remove"
ACTION_REMOVE_SHORT: Final[str] = "r"

# Action sets for validation
LIST_ACTIONS: Final[frozenset[str]] = frozenset({ACTION_LIST, ACTION_LIST_SHORT})
INTERACTIVE_ACTIONS: Final[frozenset[str]] = frozenset({ACTION_INTERACTIVE, ACTION_INTERACTIVE_SHORT})
DELETE_ACTIONS: Final[frozenset[str]] = frozenset({ACTION_DELETE, ACTION_DELETE_SHORT})
REMOVE_ACTIONS: Final[frozenset[str]] = frozenset({ACTION_REMOVE, ACTION_REMOVE_SHORT})

# Torrent status values
STATUS_SEEDING: Final[str] = "seeding"
STATUS_STOPPED: Final[str] = "stopped"

# Output formatting
PROGRESS_BAR_WIDTH: Final[int] = 50
MAX_FILENAME_DISPLAY_LENGTH: Final[int] = 80

# Limits and thresholds
MAX_CONCURRENT_FILE_CHECKS: Final[int] = 100
CROSS_SEED_CACHE_SIZE: Final[int] = 1000

# User prompts
PROMPT_DELETE_FILE: Final[str] = "Delete file? [y/N] "
PROMPT_DELETE_TORRENT: Final[str] = "Remove torrent? [N(o)/r(emove)/d(ata)] "
PROMPT_CONTINUE: Final[str] = "Continue? [y/N] "

# Exit codes
EXIT_SUCCESS: Final[int] = 0
EXIT_GENERAL_ERROR: Final[int] = 1
EXIT_CONNECTION_ERROR: Final[int] = 2
EXIT_AUTH_ERROR: Final[int] = 3
EXIT_CONFIG_ERROR: Final[int] = 4
EXIT_FILESYSTEM_ERROR: Final[int] = 5
EXIT_KEYBOARD_INTERRUPT: Final[int] = 130


def format_bytes(bytes_count: int, precision: int = 2) -> str:
    """Format bytes into human-readable string.

    Args:
        bytes_count: Number of bytes
        precision: Decimal places to show

    Returns:
        Formatted string (e.g., "1.23 GB")
    """
    if bytes_count < BYTES_PER_KB:
        return f"{bytes_count} B"
    elif bytes_count < BYTES_PER_MB:
        return f"{bytes_count / BYTES_PER_KB:.{precision}f} KB"
    elif bytes_count < BYTES_PER_GB:
        return f"{bytes_count / BYTES_PER_MB:.{precision}f} MB"
    elif bytes_count < BYTES_PER_TB:
        return f"{bytes_count / BYTES_PER_GB:.{precision}f} GB"
    else:
        return f"{bytes_count / BYTES_PER_TB:.{precision}f} TB"


def format_seconds(seconds: int) -> str:
    """Format seconds into human-readable duration string.

    Args:
        seconds: Number of seconds

    Returns:
        Formatted string (e.g., "2d 3h 15m")
    """
    if seconds < SECONDS_PER_MINUTE:
        return f"{seconds}s"

    parts = []
    days, remainder = divmod(seconds, SECONDS_PER_DAY)
    hours, remainder = divmod(remainder, SECONDS_PER_HOUR)
    minutes, secs = divmod(remainder, SECONDS_PER_MINUTE)

    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 and not parts:  # Only show seconds if no larger units
        parts.append(f"{secs}s")

    return " ".join(parts)


def is_action_type(action: str | None, action_type: str) -> bool:
    """Check if action matches a specific action type.

    Args:
        action: Action string to check
        action_type: Type to check against ('list', 'interactive', 'delete', 'remove')

    Returns:
        True if action matches the type
    """
    if action is None:
        return action_type == ACTION_INTERACTIVE

    action_lower = action.lower()

    match action_type:
        case "list":
            return action_lower in LIST_ACTIONS
        case "interactive":
            return action_lower in INTERACTIVE_ACTIONS
        case "delete":
            return action_lower in DELETE_ACTIONS
        case "remove":
            return action_lower in REMOVE_ACTIONS
        case _:
            return False
