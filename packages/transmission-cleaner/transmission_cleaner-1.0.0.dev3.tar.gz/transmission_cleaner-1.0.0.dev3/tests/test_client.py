"""Tests for client configuration functionality."""

import json
from unittest.mock import mock_open, patch

from transmission_cleaner.client import get_client_config, load_settings_from_file


class TestLoadSettingsFromFile:
    """Tests for loading settings from file."""

    def test_load_settings_from_json(self):
        """Should load settings from JSON file with custom values."""
        settings_content = json.dumps({"rpc-port": 9091, "rpc-username": "user", "rpc-url": "/transmission/rpc"})

        with patch("builtins.open", mock_open(read_data=settings_content)):
            result = load_settings_from_file("settings.json", "pass")

        assert result["port"] == 9091
        assert result["username"] == "user"
        assert result["password"] == "pass"
        assert result["path"] == "/transmission/rpc"
        assert result["host"] == "127.0.0.1"

    def test_load_settings_uses_defaults_for_missing_keys(self):
        """Should use default values for missing settings."""
        settings_content = json.dumps({})

        with patch("builtins.open", mock_open(read_data=settings_content)):
            result = load_settings_from_file("settings.json", "pass")

        assert result["port"] == 9091
        assert result["path"] == "/transmission/rpc"
        assert result["host"] == "127.0.0.1"


class TestGetClientConfig:
    """Tests for client configuration."""

    def test_config_from_individual_parameters(self):
        """Should build config from individual parameters."""
        result = get_client_config(
            settings_file=None,
            protocol="https",
            host="192.168.1.1",
            port=8080,
            username="user",
            password="pass",
            path="/rpc",
        )

        assert result["protocol"] == "https"
        assert result["host"] == "192.168.1.1"
        assert result["port"] == 8080
        assert result["username"] == "user"
        assert result["password"] == "pass"
        assert result["path"] == "/rpc"

    def test_config_prefers_settings_file_over_parameters(self):
        """Should prefer settings file when both provided."""
        settings_content = json.dumps({"rpc-port": 9091, "rpc-username": "fileuser"})

        with patch("builtins.open", mock_open(read_data=settings_content)):
            result = get_client_config(
                settings_file="settings.json",
                password="pass",
                host="192.168.1.1",  # Should be ignored
                username="arguser",  # Should be ignored
            )

        assert result["port"] == 9091
        assert result["username"] == "fileuser"
        assert result["host"] == "127.0.0.1"  # From file loader, not args

    def test_config_without_settings_file_requires_password(self):
        """Should handle None password gracefully when no settings file."""
        result = get_client_config(settings_file=None, password=None)

        assert result["password"] is None
        assert result["protocol"] == "http"
        assert result["host"] == "127.0.0.1"
