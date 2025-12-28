"""Tests for error detection and cross-seed checking functionality."""

from unittest.mock import Mock, patch

from transmission_cleaner.checkers.errors import check_cross_seeding, get_torrents_with_errors, is_cross_seeded


class TestGetTorrentsWithErrors:
    """Tests for error detection."""

    def create_mock_torrent(self, name, error_string=""):
        """Helper to create a mock torrent."""
        torrent = Mock()
        torrent.name = name
        torrent.error_string = error_string
        torrent.error = error_string  # Some versions use 'error' instead
        return torrent

    def test_finds_torrents_with_errors(self):
        """Should find torrents with error strings."""
        torrents = [
            self.create_mock_torrent("t1", "Unregistered torrent"),
            self.create_mock_torrent("t2", ""),
            self.create_mock_torrent("t3", "Tracker returned error"),
        ]

        result = get_torrents_with_errors(torrents)

        assert len(result) == 2
        assert result[0].name == "t1"
        assert result[1].name == "t3"

    def test_filters_by_error_pattern(self):
        """Should filter errors by pattern when provided."""
        torrents = [
            self.create_mock_torrent("t1", "Unregistered torrent"),
            self.create_mock_torrent("t2", "Tracker not responding"),
            self.create_mock_torrent("t3", "Unregistered tracker"),
        ]

        result = get_torrents_with_errors(torrents, "Unregistered")

        assert len(result) == 2
        assert result[0].name == "t1"
        assert result[1].name == "t3"

    def test_pattern_is_case_insensitive(self):
        """Should match patterns case-insensitively."""
        torrents = [
            self.create_mock_torrent("t1", "UNREGISTERED TORRENT"),
            self.create_mock_torrent("t2", "unregistered tracker"),
        ]

        result = get_torrents_with_errors(torrents, "UnReGiStErEd")

        assert len(result) == 2

    def test_no_errors_returns_empty_list(self):
        """Should return empty list when no errors found."""
        torrents = [
            self.create_mock_torrent("t1", ""),
            self.create_mock_torrent("t2", ""),
        ]

        result = get_torrents_with_errors(torrents)

        assert result == []

    def test_empty_torrent_list(self):
        """Should handle empty torrent list."""
        result = get_torrents_with_errors([])

        assert result == []


class TestCheckCrossSeeding:
    """Tests for cross-seed detection."""

    def create_mock_torrent(self, torrent_id, name, download_dir, file_names):
        """Helper to create a mock torrent with files."""
        torrent = Mock()
        torrent.id = torrent_id
        torrent.name = name
        torrent.download_dir = download_dir

        mock_files = []
        for file_name in file_names:
            mock_file = Mock()
            mock_file.name = file_name
            mock_files.append(mock_file)
        torrent.get_files.return_value = mock_files

        return torrent

    def test_detects_cross_seeded_torrent(self):
        """Should detect when another torrent shares files."""
        target = self.create_mock_torrent(1, "target", "/data", ["movie.mkv"])
        other1 = self.create_mock_torrent(2, "other1", "/data", ["movie.mkv"])
        other2 = self.create_mock_torrent(3, "other2", "/data", ["different.mkv"])

        client = Mock()
        client.get_torrents.return_value = [target, other1, other2]

        result = check_cross_seeding(client, target)

        assert len(result) == 1
        assert result[0].name == "other1"

    def test_no_cross_seeding(self):
        """Should return empty list when no files are shared."""
        target = self.create_mock_torrent(1, "target", "/data", ["movie1.mkv"])
        other = self.create_mock_torrent(2, "other", "/data", ["movie2.mkv"])

        client = Mock()
        client.get_torrents.return_value = [target, other]

        result = check_cross_seeding(client, target)

        assert result == []

    def test_detects_multiple_cross_seeders(self):
        """Should detect when multiple torrents share files."""
        target = self.create_mock_torrent(1, "target", "/data", ["movie.mkv"])
        other1 = self.create_mock_torrent(2, "other1", "/data", ["movie.mkv"])
        other2 = self.create_mock_torrent(3, "other2", "/data", ["movie.mkv"])

        client = Mock()
        client.get_torrents.return_value = [target, other1, other2]

        result = check_cross_seeding(client, target)

        assert len(result) == 2


class TestIsCrossSeeded:
    """Tests for is_cross_seeded convenience function."""

    def test_returns_true_when_cross_seeded(self):
        """Should return True when cross-seeders exist."""
        torrent = Mock()
        torrent.id = 1
        torrent.name = "test"

        client = Mock()

        with patch("transmission_cleaner.checkers.errors.check_cross_seeding") as mock_check:
            mock_check.return_value = [Mock(), Mock()]  # Two cross-seeders

            result = is_cross_seeded(client, torrent)

            assert result is True

    def test_returns_false_when_not_cross_seeded(self):
        """Should return False when no cross-seeders exist."""
        torrent = Mock()
        client = Mock()

        with patch("transmission_cleaner.checkers.errors.check_cross_seeding") as mock_check:
            mock_check.return_value = []  # No cross-seeders

            result = is_cross_seeded(client, torrent)

            assert result is False


class TestCrossSeedProtection:
    """Tests for cross-seed protection enforcement during deletion."""

    def create_mock_torrent(self, torrent_id, name, download_dir, file_names):
        """Helper
        to create a mock torrent with files."""
        torrent = Mock()
        torrent.id = torrent_id
        torrent.name = name
        torrent.download_dir = download_dir

        mock_files = []
        for file_name in file_names:
            mock_file = Mock()
            mock_file.name = file_name
            mock_files.append(mock_file)
        torrent.get_files.return_value = mock_files

        return torrent
