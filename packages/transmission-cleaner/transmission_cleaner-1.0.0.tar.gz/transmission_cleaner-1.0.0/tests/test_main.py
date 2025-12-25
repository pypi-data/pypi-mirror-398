"""Tests for main module functionality."""

from unittest.mock import patch

import pytest

from transmission_cleaner.main import parse_args


class TestParseArgsHardlinks:
    """Tests for hardlinks subcommand argument parsing."""

    @patch("sys.argv", ["transmission-cleaner", "hardlinks", "--password", "pass"])
    def test_hardlinks_minimal_args_with_defaults(self):
        """Should parse hardlinks with just password and use default values."""
        args = parse_args()

        assert args.command == "hardlinks"
        assert args.password == "pass"
        assert args.host == "127.0.0.1"
        assert args.port == 9091
        assert args.min_days == 7
        assert args.action == "list"  # Changed default
        assert args.directory is None
        assert args.tracker is None

    @patch(
        "sys.argv",
        [
            "transmission-cleaner",
            "hardlinks",
            "--password",
            "pass",
            "--dir",
            "/data/movies",
            "--tracker",
            "tracker.com",
            "--min-days",
            "30",
            "--action",
            "interactive",
            "--host",
            "192.168.1.100",
            "--port",
            "8080",
        ],
    )
    def test_hardlinks_all_arguments_parsed_correctly(self):
        """Should correctly parse all hardlinks arguments when provided."""
        args = parse_args()

        assert args.command == "hardlinks"
        assert args.password == "pass"
        assert args.directory == "/data/movies"
        assert args.tracker == "tracker.com"
        assert args.min_days == 30
        assert args.action == "interactive"
        assert args.host == "192.168.1.100"
        assert args.port == 8080

    @patch("sys.argv", ["transmission-cleaner", "hardlinks", "--password", "pass", "--action", "list"])
    def test_hardlinks_list_action(self):
        """Should parse list action for hardlinks."""
        args = parse_args()

        assert args.command == "hardlinks"
        assert args.action == "list"

    @patch("sys.argv", ["transmission-cleaner", "hardlinks", "--password", "pass", "--action", "delete"])
    def test_hardlinks_delete_action(self):
        """Should parse delete action for hardlinks."""
        args = parse_args()

        assert args.command == "hardlinks"
        assert args.action == "delete"


class TestParseArgsErrors:
    """Tests for errors subcommand argument parsing."""

    @patch("sys.argv", ["transmission-cleaner", "errors", "--password", "pass"])
    def test_errors_minimal_args_with_defaults(self):
        """Should parse errors with just password and use default values."""
        args = parse_args()

        assert args.command == "errors"
        assert args.password == "pass"
        assert args.action == "list"  # Changed default
        assert args.error_pattern is None
        assert args.skip_cross_seed is False  # Cross-seed check enabled by default

    @patch(
        "sys.argv",
        [
            "transmission-cleaner",
            "errors",
            "--password",
            "pass",
            "--error-pattern",
            "Unregistered",
            "--skip-cross-seed",
            "--action",
            "delete",
            "--dir",
            "/data/tv",
        ],
    )
    def test_errors_with_all_options(self):
        """Should parse all error checking options."""
        args = parse_args()

        assert args.command == "errors"
        assert args.password == "pass"
        assert args.error_pattern == "Unregistered"
        assert args.skip_cross_seed is True
        assert args.action == "delete"
        assert args.directory == "/data/tv"

    @patch("sys.argv", ["transmission-cleaner", "errors", "--password", "pass", "--action", "interactive"])
    def test_errors_interactive_action(self):
        """Should parse interactive action for errors."""
        args = parse_args()

        assert args.command == "errors"
        assert args.action == "interactive"


class TestParseArgsOrphans:
    """Tests for orphans subcommand argument parsing."""

    @patch("sys.argv", ["transmission-cleaner", "orphans", "--password", "pass", "--dir", "/data/downloads"])
    def test_orphans_minimal_args_with_defaults(self):
        """Should parse orphans with required directory."""
        args = parse_args()

        assert args.command == "orphans"
        assert args.password == "pass"
        assert args.directory == "/data/downloads"
        assert args.action == "list"  # Changed default
        assert args.include_hidden is False  # Hidden files excluded by default

    @patch(
        "sys.argv",
        [
            "transmission-cleaner",
            "orphans",
            "--password",
            "pass",
            "--dir",
            "/data/downloads",
            "--include-hidden",
            "--action",
            "delete",
        ],
    )
    def test_orphans_with_all_options(self):
        """Should parse all orphan detection options."""
        args = parse_args()

        assert args.command == "orphans"
        assert args.directory == "/data/downloads"
        assert args.include_hidden is True
        assert args.action == "delete"

    @patch("sys.argv", ["transmission-cleaner", "orphans", "--password", "pass"])
    def test_orphans_missing_required_directory(self):
        """Should require directory argument for orphans."""
        with pytest.raises(SystemExit):
            parse_args()


class TestParseArgsCommon:
    """Tests for common argument parsing behavior."""

    @patch("sys.argv", ["transmission-cleaner"])
    def test_no_subcommand_shows_help(self):
        """Should exit when no subcommand provided."""
        with pytest.raises(SystemExit):
            parse_args()

    @patch("sys.argv", ["transmission-cleaner", "hardlinks"])
    def test_missing_required_password(self):
        """Should require password argument."""
        with pytest.raises(SystemExit):
            parse_args()

    @patch("sys.argv", ["transmission-cleaner", "hardlinks", "--password", "pass", "--action", "invalid"])
    def test_invalid_action_rejected(self):
        """Should reject invalid action choices."""
        with pytest.raises(SystemExit):
            parse_args()

    @patch(
        "sys.argv",
        ["transmission-cleaner", "hardlinks", "--password", "pass", "--settings-file", "/path/to/settings.json"],
    )
    def test_settings_file_option(self):
        """Should parse settings file path for alternate config."""
        args = parse_args()

        assert args.settings_file == "/path/to/settings.json"

    @patch("sys.argv", ["transmission-cleaner", "invalid_command", "--password", "pass"])
    def test_invalid_subcommand_rejected(self):
        """Should reject invalid subcommand."""
        with pytest.raises(SystemExit):
            parse_args()
