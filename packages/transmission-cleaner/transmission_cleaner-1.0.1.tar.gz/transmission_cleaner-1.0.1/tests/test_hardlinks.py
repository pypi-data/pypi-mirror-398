"""Tests for hardlink detection functionality."""

from unittest.mock import Mock, patch

from transmission_cleaner.checkers.hardlinks import get_torrents_without_hardlinks, is_hardlink


class TestIsHardlink:
    """Tests for hardlink detection."""

    def test_file_with_multiple_links(self, tmp_path):
        """Files with multiple hardlinks should return True."""
        original = tmp_path / "original.txt"
        original.write_text("test")
        hardlink = tmp_path / "hardlink.txt"
        hardlink.hardlink_to(original)

        assert is_hardlink(original) is True
        assert is_hardlink(hardlink) is True

    def test_file_with_single_link(self, tmp_path):
        """Files with only one link should return False."""
        single = tmp_path / "single.txt"
        single.write_text("test")

        assert is_hardlink(single) is False


class TestGetTorrentsWithoutHardlinks:
    """Tests for filtering torrents by hardlink status."""

    def create_mock_torrent(self, name, download_dir, files):
        """Helper to create a mock torrent."""
        torrent = Mock()
        torrent.name = name
        torrent.download_dir = download_dir
        mock_files = []
        for file_name in files:
            mock_file = Mock()
            mock_file.name = file_name
            mock_files.append(mock_file)
        torrent.get_files.return_value = mock_files
        return torrent

    @patch("transmission_cleaner.checkers.hardlinks.is_hardlink")
    def test_excludes_torrents_with_hardlinks(self, mock_is_hardlink, tmp_path):
        """Torrents with any hardlinked files should be excluded."""
        mock_is_hardlink.return_value = True
        torrent = self.create_mock_torrent("test", str(tmp_path), ["file.txt"])

        result = get_torrents_without_hardlinks([torrent])

        assert result == []

    @patch("transmission_cleaner.checkers.hardlinks.is_hardlink")
    def test_includes_torrents_without_hardlinks(self, mock_is_hardlink, tmp_path):
        """Torrents without any hardlinks should be included."""
        mock_is_hardlink.return_value = False
        torrent = self.create_mock_torrent("test", str(tmp_path), ["file.txt"])

        result = get_torrents_without_hardlinks([torrent])

        assert len(result) == 1
        assert result[0].name == "test"

    @patch("builtins.print")
    @patch("transmission_cleaner.checkers.hardlinks.is_hardlink")
    def test_handles_missing_files(self, mock_is_hardlink, mock_print, tmp_path):
        """Missing files should be logged and torrent excluded."""
        mock_is_hardlink.side_effect = FileNotFoundError()
        torrent = self.create_mock_torrent("test", str(tmp_path), ["missing.txt"])

        result = get_torrents_without_hardlinks([torrent])

        assert result == []
        mock_print.assert_called()
