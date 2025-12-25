"""Custom exceptions for transmission-cleaner.

Provides a hierarchy of exceptions for different error conditions
to enable better error handling and user feedback.
"""


class TransmissionCleanerError(Exception):
    """Base exception for all transmission-cleaner errors."""

    def __init__(self, message: str, details: str | None = None):
        """Initialize exception.

        Args:
            message: Error message
            details: Additional error details
        """
        self.message = message
        self.details = details
        super().__init__(message)

    def __str__(self) -> str:
        """Return formatted error message."""
        if self.details:
            return f"{self.message}\nDetails: {self.details}"
        return self.message


class ConnectionError(TransmissionCleanerError):
    """Raised when connection to Transmission fails."""

    def __init__(self, host: str, port: int, reason: str | None = None):
        """Initialize connection error.

        Args:
            host: Transmission host
            port: Transmission port
            reason: Connection failure reason
        """
        message = f"Failed to connect to Transmission at {host}:{port}"
        super().__init__(message, details=reason)
        self.host = host
        self.port = port


class AuthenticationError(TransmissionCleanerError):
    """Raised when authentication with Transmission fails."""

    def __init__(self, username: str | None = None):
        """Initialize authentication error.

        Args:
            username: Username that failed authentication
        """
        message = "Authentication failed"
        if username:
            message += f" for user '{username}'"
        super().__init__(message)
        self.username = username


class ConfigurationError(TransmissionCleanerError):
    """Raised when configuration is invalid."""

    def __init__(self, parameter: str, reason: str):
        """Initialize configuration error.

        Args:
            parameter: Configuration parameter that is invalid
            reason: Why the configuration is invalid
        """
        message = f"Invalid configuration for '{parameter}'"
        super().__init__(message, details=reason)
        self.parameter = parameter


class FileSystemError(TransmissionCleanerError):
    """Raised when filesystem operations fail."""

    def __init__(self, path: str, operation: str, reason: str | None = None):
        """Initialize filesystem error.

        Args:
            path: File or directory path
            operation: Operation that failed (read, write, delete, etc.)
            reason: Failure reason
        """
        message = f"Failed to {operation} '{path}'"
        super().__init__(message, details=reason)
        self.path = path
        self.operation = operation


class PermissionError(FileSystemError):
    """Raised when permission is denied for filesystem operations."""

    def __init__(self, path: str, operation: str):
        """Initialize permission error.

        Args:
            path: File or directory path
            operation: Operation that was denied
        """
        super().__init__(path, operation, reason="Permission denied")


class PathNotFoundError(FileSystemError):
    """Raised when a path does not exist."""

    def __init__(self, path: str):
        """Initialize path not found error.

        Args:
            path: Path that doesn't exist
        """
        super().__init__(path, operation="access", reason="Path does not exist")


class TorrentNotFoundError(TransmissionCleanerError):
    """Raised when a torrent cannot be found."""

    def __init__(self, torrent_id: int | str):
        """Initialize torrent not found error.

        Args:
            torrent_id: ID or name of the torrent
        """
        message = f"Torrent not found: {torrent_id}"
        super().__init__(message)
        self.torrent_id = torrent_id


class ValidationError(TransmissionCleanerError):
    """Raised when input validation fails."""

    def __init__(self, field: str, value: str | None, reason: str):
        """Initialize validation error.

        Args:
            field: Field that failed validation
            value: Invalid value
            reason: Why validation failed
        """
        message = f"Invalid value for '{field}'"
        if value is not None:
            message += f": {value}"
        super().__init__(message, details=reason)
        self.field = field
        self.value = value


class DiskSpaceError(TransmissionCleanerError):
    """Raised when there's insufficient disk space."""

    def __init__(self, required_bytes: int, available_bytes: int):
        """Initialize disk space error.

        Args:
            required_bytes: Bytes required
            available_bytes: Bytes available
        """
        required_gb = required_bytes / (1024**3)
        available_gb = available_bytes / (1024**3)
        message = f"Insufficient disk space: need {required_gb:.2f} GB, have {available_gb:.2f} GB"
        super().__init__(message)
        self.required_bytes = required_bytes
        self.available_bytes = available_bytes


class CrossSeedError(TransmissionCleanerError):
    """Raised when cross-seed operation encounters an issue."""

    def __init__(self, torrent_name: str, cross_seeders: list[str]):
        """Initialize cross-seed error.

        Args:
            torrent_name: Name of the torrent
            cross_seeders: Names of torrents that cross-seed this one
        """
        message = f"Torrent '{torrent_name}' is cross-seeded by {len(cross_seeders)} other torrent(s)"
        details = "Cross-seeders: " + ", ".join(cross_seeders)
        super().__init__(message, details=details)
        self.torrent_name = torrent_name
        self.cross_seeders = cross_seeders
