"""Configuration file handling for transmission-cleaner.

Supports loading configuration from TOML, JSON, or YAML files,
with validation and merging with CLI arguments.
"""

import json
import pathlib
from typing import Any

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None  # type: ignore


class Config:
    """Configuration container with validation."""

    def __init__(self, config_dict: dict[str, Any] | None = None):
        """Initialize configuration.

        Args:
            config_dict: Dictionary of configuration values
        """
        self.config = config_dict or {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Args:
            key: Configuration key (supports dot notation, e.g., 'transmission.host')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value if value is not None else default

    def set(self, key: str, value: Any) -> None:
        """Set configuration value.

        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split(".")
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def merge(self, other: dict[str, Any]) -> None:
        """Merge another configuration dict into this one.

        Args:
            other: Dictionary to merge (overwrites existing values)
        """
        self._merge_dict(self.config, other)

    def _merge_dict(self, target: dict[str, Any], source: dict[str, Any]) -> None:
        """Recursively merge source dict into target dict.

        Args:
            target: Target dictionary to merge into
            source: Source dictionary to merge from
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_dict(target[key], value)
            else:
                target[key] = value

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary.

        Returns:
            Configuration dictionary
        """
        return self.config.copy()


def load_config_file(config_path: pathlib.Path) -> Config:
    """Load configuration from file.

    Supports TOML (.toml), JSON (.json), and falls back to JSON for no extension.

    Args:
        config_path: Path to configuration file

    Returns:
        Config object

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If file format is not supported or invalid
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    suffix = config_path.suffix.lower()

    try:
        if suffix == ".toml":
            if tomllib is None:
                raise ValueError(
                    "TOML support requires Python 3.11+ or 'tomli' package. Install with: pip install tomli"
                )
            with open(config_path, "rb") as f:
                data = tomllib.load(f)

        elif suffix in {".json", ""}:
            with open(config_path, "r") as f:
                data = json.load(f)

        else:
            raise ValueError(f"Unsupported config file format: {suffix}")

    except (json.JSONDecodeError, Exception) as e:
        raise ValueError(f"Failed to parse config file {config_path}: {e}")

    return Config(data)


def get_default_config_paths() -> list[pathlib.Path]:
    """Get list of default configuration file locations.

    Returns:
        List of paths to check for config files, in order of priority
    """
    paths = []

    # Current directory
    paths.extend(
        [
            pathlib.Path("transmission-cleaner.toml"),
            pathlib.Path("transmission-cleaner.json"),
            pathlib.Path(".transmission-cleaner.toml"),
            pathlib.Path(".transmission-cleaner.json"),
        ]
    )

    # User config directory
    home = pathlib.Path.home()
    config_dir = home / ".config" / "transmission-cleaner"

    paths.extend(
        [
            config_dir / "config.toml",
            config_dir / "config.json",
        ]
    )

    # Legacy location
    paths.extend(
        [
            home / ".transmission-cleaner.toml",
            home / ".transmission-cleaner.json",
        ]
    )

    return paths


def find_config_file() -> pathlib.Path | None:
    """Find configuration file in default locations.

    Returns:
        Path to first found config file, or None if not found
    """
    for path in get_default_config_paths():
        if path.exists():
            return path
    return None


def load_config(config_path: pathlib.Path | None = None) -> Config:
    """Load configuration from file or create default.

    Args:
        config_path: Optional explicit path to config file.
                    If None, searches default locations.

    Returns:
        Config object
    """
    if config_path is not None:
        return load_config_file(config_path)

    # Search for config in default locations
    found_path = find_config_file()
    if found_path is not None:
        return load_config_file(found_path)

    # No config file found, return empty config
    return Config()


def create_example_config(output_path: pathlib.Path) -> None:
    """Create an example configuration file.

    Args:
        output_path: Path where to save the example config
    """
    example_config = {
        "transmission": {
            "protocol": "http",
            "host": "127.0.0.1",
            "port": 9091,
            "rpc_path": "/transmission/rpc",
            "username": None,
            "password": None,
            "settings_file": None,
        },
        "defaults": {
            "min_days": 7,
            "action": "list",
        },
        "filters": {
            "directory": None,
            "tracker": None,
        },
        "errors": {
            "error_pattern": None,
            "skip_cross_seed": False,
        },
        "orphans": {
            "include_hidden": False,
        },
        "output": {
            "quiet": False,
            "log_level": "INFO",
            "use_color": True,
        },
    }

    suffix = output_path.suffix.lower()

    if suffix == ".toml":
        if tomllib is None:
            raise ValueError("TOML support not available. Use .json extension instead.")
        # Write as TOML manually since tomllib only reads
        output_path.write_text(_dict_to_toml(example_config))

    elif suffix in {".json", ""}:
        with open(output_path, "w") as f:
            json.dump(example_config, f, indent=2)
    else:
        raise ValueError(f"Unsupported output format: {suffix}. Use .toml or .json")


def _dict_to_toml(data: dict[str, Any], indent: int = 0) -> str:
    """Convert dictionary to TOML format string.

    Args:
        data: Dictionary to convert
        indent: Current indentation level

    Returns:
        TOML formatted string
    """
    lines = []
    indent_str = "  " * indent

    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"\n[{key}]")
            for k, v in value.items():
                if isinstance(v, bool):
                    v_str = str(v).lower()
                elif v is None:
                    v_str = '""'
                elif isinstance(v, str):
                    v_str = f'"{v}"'
                else:
                    v_str = str(v)
                lines.append(f"{k} = {v_str}")
        else:
            if isinstance(value, bool):
                value_str = str(value).lower()
            elif value is None:
                value_str = '""'
            elif isinstance(value, str):
                value_str = f'"{value}"'
            else:
                value_str = str(value)
            lines.append(f"{indent_str}{key} = {value_str}")

    return "\n".join(lines) + "\n"


def merge_config_with_args(config: Config, args: dict[str, Any]) -> dict[str, Any]:
    """Merge configuration file with command-line arguments.

    Command-line arguments take precedence over config file values.

    Args:
        config: Config object from file
        args: Dictionary of command-line arguments

    Returns:
        Merged configuration dictionary
    """
    result = {}

    # Start with config file values
    result["host"] = config.get("transmission.host", "127.0.0.1")
    result["port"] = config.get("transmission.port", 9091)
    result["protocol"] = config.get("transmission.protocol", "http")
    result["rpc_path"] = config.get("transmission.rpc_path", "/transmission/rpc")
    result["username"] = config.get("transmission.username")
    result["password"] = config.get("transmission.password")
    result["settings_file"] = config.get("transmission.settings_file")

    result["min_days"] = config.get("defaults.min_days", 7)
    result["action"] = config.get("defaults.action", "list")
    result["directory"] = config.get("filters.directory")
    result["tracker"] = config.get("filters.tracker")

    result["quiet"] = config.get("output.quiet", False)
    result["log_level"] = config.get("output.log_level", "INFO")

    # Override with command-line arguments (if provided)
    for key, value in args.items():
        if value is not None:
            result[key] = value

    return result
