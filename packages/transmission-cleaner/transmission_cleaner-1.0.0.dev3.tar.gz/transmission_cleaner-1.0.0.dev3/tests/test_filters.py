"""Tests for torrent filtering functionality."""

from unittest.mock import Mock, patch

from transmission_cleaner.filters import filter_torrents


class TestFilterTorrents:
    """Tests for filtering torrents by various criteria."""

    def create_mock_torrent(self, name, status, download_dir, trackers, seconds_seeding):
        """Helper to create a mock torrent."""
        torrent = Mock()
        torrent.name = name
        torrent.status = status
        torrent.download_dir = download_dir
        torrent.seconds_seeding = seconds_seeding
        mock_trackers = []
        for url in trackers:
            tracker = Mock()
            tracker.announce = url
            mock_trackers.append(tracker)
        torrent.trackers = mock_trackers
        return torrent

    @patch("builtins.print")
    def test_filters_by_status(self, mock_print):
        """Only seeding and stopped torrents should pass."""
        torrents = [
            self.create_mock_torrent("t1", "seeding", "/data", ["http://t.com"], 8 * 24 * 60 * 60),
            self.create_mock_torrent("t2", "downloading", "/data", ["http://t.com"], 8 * 24 * 60 * 60),
        ]

        result = filter_torrents(torrents, None, None, 7)

        assert len(result) == 1
        assert result[0].name == "t1"

    @patch("builtins.print")
    def test_filters_by_directory(self, mock_print):
        """Should filter by directory substring."""
        torrents = [
            self.create_mock_torrent("t1", "seeding", "/data/movies", ["http://t.com"], 8 * 24 * 60 * 60),
            self.create_mock_torrent("t2", "seeding", "/data/tv", ["http://t.com"], 8 * 24 * 60 * 60),
        ]

        result = filter_torrents(torrents, "movies", None, 7)

        assert len(result) == 1
        assert result[0].name == "t1"

    @patch("builtins.print")
    def test_filters_by_tracker(self, mock_print):
        """Should filter by tracker substring."""
        torrents = [
            self.create_mock_torrent("t1", "seeding", "/data", ["http://tracker1.com"], 8 * 24 * 60 * 60),
            self.create_mock_torrent("t2", "seeding", "/data", ["http://tracker2.com"], 8 * 24 * 60 * 60),
        ]

        result = filter_torrents(torrents, None, "tracker1", 7)

        assert len(result) == 1
        assert result[0].name == "t1"

    @patch("builtins.print")
    def test_filters_by_min_days(self, mock_print):
        """Should filter by minimum seeding days."""
        torrents = [
            self.create_mock_torrent("t1", "seeding", "/data", ["http://t.com"], 10 * 24 * 60 * 60),
            self.create_mock_torrent("t2", "seeding", "/data", ["http://t.com"], 5 * 24 * 60 * 60),
        ]

        result = filter_torrents(torrents, None, None, 7)

        assert len(result) == 1
        assert result[0].name == "t1"
