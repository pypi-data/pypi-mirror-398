"""Input validation for transmission-cleaner.

Provides validation functions for user inputs, configuration values,
and filesystem paths with clear error messages.
"""

import pathlib
import re
from typing import Any

from transmission_cleaner.constants import (
    DEFAULT_HOST,
    DEFAULT_MIN_SEEDING_DAYS,
    DEFAULT_PORT,
    DEFAULT_PROTOCOL,
    DEFAULT_RPC_PATH,
)
from transmission_cleaner.exceptions import ValidationError


def validate_host(host: str) -> str:
    """Validate hostname or IP address.

    Args:
        host: Hostname or IP address to validate

    Returns:
        Validated host string

    Raises:
        ValidationError: If host is invalid
    """
    if not host or not host.strip():
        raise ValidationError("host", host, "Host cannot be empty")

    host = host.strip()

    # Check for valid characters (alphanumeric, dots, hyphens)
    if not re.match(r"^[a-zA-Z0-9\.\-]+$", host):
        raise ValidationError("host", host, "Host contains invalid characters")

    return host


def validate_port(port: int | str) -> int:
    """Validate port number.

    Args:
        port: Port number to validate

    Returns:
        Validated port as integer

    Raises:
        ValidationError: If port is invalid
    """
    try:
        port_int = int(port)
    except (ValueError, TypeError):
        raise ValidationError("port", str(port), "Port must be a number")

    if port_int < 1 or port_int > 65535:
        raise ValidationError("port", str(port_int), "Port must be between 1 and 65535")

    return port_int


def validate_protocol(protocol: str) -> str:
    """Validate protocol.

    Args:
        protocol: Protocol string to validate

    Returns:
        Validated protocol (lowercase)

    Raises:
        ValidationError: If protocol is invalid
    """
    if not protocol or not protocol.strip():
        raise ValidationError("protocol", protocol, "Protocol cannot be empty")

    protocol = protocol.strip().lower()

    if protocol not in {"http", "https"}:
        raise ValidationError("protocol", protocol, "Protocol must be 'http' or 'https'")

    return protocol


def validate_rpc_path(path: str) -> str:
    """Validate RPC path.

    Args:
        path: RPC path to validate

    Returns:
        Validated path

    Raises:
        ValidationError: If path is invalid
    """
    if not path or not path.strip():
        raise ValidationError("rpc_path", path, "RPC path cannot be empty")

    path = path.strip()

    if not path.startswith("/"):
        raise ValidationError("rpc_path", path, "RPC path must start with '/'")

    return path


def validate_username(username: str | None) -> str | None:
    """Validate username.

    Args:
        username: Username to validate (can be None)

    Returns:
        Validated username or None

    Raises:
        ValidationError: If username is invalid
    """
    if username is None or username == "":
        return None

    username = username.strip()

    if len(username) > 255:
        raise ValidationError("username", username, "Username is too long (max 255 characters)")

    return username


def validate_password(password: str | None, required: bool = True) -> str | None:
    """Validate password.

    Args:
        password: Password to validate
        required: Whether password is required

    Returns:
        Validated password or None

    Raises:
        ValidationError: If password is invalid
    """
    if password is None or password == "":
        if required:
            raise ValidationError("password", None, "Password is required")
        return None

    if len(password) > 1024:
        raise ValidationError("password", "***", "Password is too long (max 1024 characters)")

    return password


def validate_directory(directory: str | pathlib.Path, must_exist: bool = True) -> pathlib.Path:
    """Validate directory path.

    Args:
        directory: Directory path to validate
        must_exist: Whether directory must already exist

    Returns:
        Validated Path object

    Raises:
        ValidationError: If directory is invalid
    """
    if isinstance(directory, str):
        if not directory.strip():
            raise ValidationError("directory", directory, "Directory cannot be empty")
        directory = pathlib.Path(directory.strip())

    # Convert to absolute path
    try:
        directory = directory.resolve()
    except (OSError, RuntimeError) as e:
        raise ValidationError("directory", str(directory), f"Cannot resolve path: {e}")

    if must_exist:
        if not directory.exists():
            raise ValidationError("directory", str(directory), "Directory does not exist")

        if not directory.is_dir():
            raise ValidationError("directory", str(directory), "Path is not a directory")

    return directory


def validate_file(file_path: str | pathlib.Path, must_exist: bool = True) -> pathlib.Path:
    """Validate file path.

    Args:
        file_path: File path to validate
        must_exist: Whether file must already exist

    Returns:
        Validated Path object

    Raises:
        ValidationError: If file is invalid
    """
    if isinstance(file_path, str):
        if not file_path.strip():
            raise ValidationError("file", file_path, "File path cannot be empty")
        file_path = pathlib.Path(file_path.strip())

    # Convert to absolute path
    try:
        file_path = file_path.resolve()
    except (OSError, RuntimeError) as e:
        raise ValidationError("file", str(file_path), f"Cannot resolve path: {e}")

    if must_exist:
        if not file_path.exists():
            raise ValidationError("file", str(file_path), "File does not exist")

        if not file_path.is_file():
            raise ValidationError("file", str(file_path), "Path is not a file")

    return file_path


def validate_min_days(days: int | str) -> int:
    """Validate minimum seeding days.

    Args:
        days: Number of days to validate

    Returns:
        Validated days as integer

    Raises:
        ValidationError: If days is invalid
    """
    try:
        days_int = int(days)
    except (ValueError, TypeError):
        raise ValidationError("min_days", str(days), "Minimum days must be a number")

    if days_int < 0:
        raise ValidationError("min_days", str(days_int), "Minimum days cannot be negative")

    if days_int > 36500:  # ~100 years
        raise ValidationError("min_days", str(days_int), "Minimum days is unreasonably large")

    return days_int


def validate_action(action: str | None) -> str | None:
    """Validate action type.

    Args:
        action: Action to validate

    Returns:
        Validated action (lowercase) or None for interactive

    Raises:
        ValidationError: If action is invalid
    """
    if action is None:
        return None

    action = action.strip().lower()

    valid_actions = {"list", "l", "interactive", "i", "delete", "d", "remove", "r"}

    if action not in valid_actions:
        raise ValidationError(
            "action",
            action,
            f"Invalid action. Must be one of: {', '.join(sorted(valid_actions))}",
        )

    return action


def validate_error_pattern(pattern: str | None) -> str | None:
    """Validate error pattern regex.

    Args:
        pattern: Pattern to validate

    Returns:
        Validated pattern or None

    Raises:
        ValidationError: If pattern is invalid
    """
    if pattern is None or pattern == "":
        return None

    pattern = pattern.strip()

    # Test if it's a valid regex
    try:
        re.compile(pattern, re.IGNORECASE)
    except re.error as e:
        raise ValidationError("error_pattern", pattern, f"Invalid regex pattern: {e}")

    return pattern


def validate_config_dict(config: dict[str, Any]) -> dict[str, Any]:
    """Validate entire configuration dictionary.

    Args:
        config: Configuration dictionary to validate

    Returns:
        Validated configuration dictionary

    Raises:
        ValidationError: If any configuration value is invalid
    """
    validated = {}

    # Transmission settings
    if "host" in config:
        validated["host"] = validate_host(config["host"])
    else:
        validated["host"] = DEFAULT_HOST

    if "port" in config:
        validated["port"] = validate_port(config["port"])
    else:
        validated["port"] = DEFAULT_PORT

    if "protocol" in config:
        validated["protocol"] = validate_protocol(config["protocol"])
    else:
        validated["protocol"] = DEFAULT_PROTOCOL

    if "rpc_path" in config:
        validated["rpc_path"] = validate_rpc_path(config["rpc_path"])
    else:
        validated["rpc_path"] = DEFAULT_RPC_PATH

    if "username" in config:
        validated["username"] = validate_username(config["username"])

    if "password" in config:
        validated["password"] = validate_password(config["password"], required=False)

    if "settings_file" in config and config["settings_file"]:
        validated["settings_file"] = validate_file(config["settings_file"])

    # Filter settings
    if "min_days" in config:
        validated["min_days"] = validate_min_days(config["min_days"])
    else:
        validated["min_days"] = DEFAULT_MIN_SEEDING_DAYS

    if "action" in config:
        validated["action"] = validate_action(config["action"])

    if "directory" in config and config["directory"]:
        # Don't validate existence for filter directory (it's a substring match)
        validated["directory"] = config["directory"]

    if "tracker" in config and config["tracker"]:
        validated["tracker"] = config["tracker"]

    if "error_pattern" in config:
        validated["error_pattern"] = validate_error_pattern(config["error_pattern"])

    # Boolean flags
    for bool_key in ["skip_cross_seed", "include_hidden", "quiet"]:
        if bool_key in config:
            if not isinstance(config[bool_key], bool):
                raise ValidationError(bool_key, str(config[bool_key]), "Must be true or false")
            validated[bool_key] = config[bool_key]

    # Log level
    if "log_level" in config:
        log_level = config["log_level"].upper()
        if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR"}:
            raise ValidationError("log_level", log_level, "Must be DEBUG, INFO, WARNING, or ERROR")
        validated["log_level"] = log_level

    return validated


def validate_transmission_connection(
    host: str,
    port: int,
    protocol: str,
    rpc_path: str,
    username: str | None,
    password: str | None,
) -> dict[str, Any]:
    """Validate all transmission connection parameters.

    Args:
        host: Transmission host
        port: Transmission port
        protocol: Connection protocol
        rpc_path: RPC path
        username: Username (optional)
        password: Password (optional)

    Returns:
        Dictionary of validated connection parameters

    Raises:
        ValidationError: If any parameter is invalid
    """
    return {
        "host": validate_host(host),
        "port": validate_port(port),
        "protocol": validate_protocol(protocol),
        "path": validate_rpc_path(rpc_path),
        "username": validate_username(username),
        "password": validate_password(password, required=False),
    }
