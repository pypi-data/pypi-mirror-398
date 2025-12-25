"""Transmission client configuration and connection management."""

import json

from transmission_rpc import Client


def load_settings_from_file(settings_file: str, password: str) -> dict[str, str | int | None]:
    """Load Transmission settings from settings.json file.

    Args:
        settings_file: Path to the Transmission settings.json file
        password: RPC password to use

    Returns:
        Dictionary with client configuration parameters
    """
    with open(settings_file, "r") as f:
        settings = json.load(f)

    return {
        "host": "127.0.0.1",
        "port": settings.get("rpc-port", 9091),
        "username": settings.get("rpc-username"),
        "password": password,
        "path": settings.get("rpc-url", "/transmission/rpc"),
    }


def get_client_config(
    settings_file: str | None = None,
    protocol: str = "http",
    host: str = "127.0.0.1",
    port: int = 9091,
    username: str | None = None,
    password: str | None = None,
    path: str = "/transmission/rpc",
) -> dict[str, str | int | None]:
    """Get client configuration from settings file or individual parameters.

    Args:
        settings_file: Path to Transmission settings.json file (takes precedence)
        protocol: Protocol to use (http or https)
        host: Transmission host
        port: Transmission port
        username: Transmission username
        password: Transmission password (required)
        path: Transmission RPC path

    Returns:
        Dictionary with client configuration parameters
    """
    if settings_file and password:
        return load_settings_from_file(settings_file, password)

    return {
        "protocol": protocol,
        "host": host,
        "port": port,
        "username": username,
        "password": password,
        "path": path,
    }


def create_client(**config: str | int | None) -> Client:
    """Create a Transmission RPC client with the given configuration.

    Args:
        **config: Configuration parameters for the client

    Returns:
        Configured Transmission RPC client
    """
    return Client(**config)
