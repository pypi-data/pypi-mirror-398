"""Tests for core functionality."""

from unittest.mock import Mock, patch


from transmission_unlinked.core import filter_torrents, get_torrents_without_hardlinks, is_hardlink, process_torrents


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

    @patch("transmission_unlinked.core.is_hardlink")
    def test_excludes_torrents_with_hardlinks(self, mock_is_hardlink, tmp_path):
        """Torrents with any hardlinked files should be excluded."""
        mock_is_hardlink.return_value = True
        torrent = self.create_mock_torrent("test", str(tmp_path), ["file.txt"])

        result = get_torrents_without_hardlinks([torrent])

        assert result == []

    @patch("transmission_unlinked.core.is_hardlink")
    def test_includes_torrents_without_hardlinks(self, mock_is_hardlink, tmp_path):
        """Torrents without any hardlinks should be included."""
        mock_is_hardlink.return_value = False
        torrent = self.create_mock_torrent("test", str(tmp_path), ["file.txt"])

        result = get_torrents_without_hardlinks([torrent])

        assert len(result) == 1
        assert result[0].name == "test"

    @patch("builtins.print")
    @patch("transmission_unlinked.core.is_hardlink")
    def test_handles_missing_files(self, mock_is_hardlink, mock_print, tmp_path):
        """Missing files should be logged and torrent excluded."""
        mock_is_hardlink.side_effect = FileNotFoundError()
        torrent = self.create_mock_torrent("test", str(tmp_path), ["missing.txt"])

        result = get_torrents_without_hardlinks([torrent])

        assert result == []
        mock_print.assert_called()


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
    def test_filters_by_min_days(self, mock_print):
        """Should filter by minimum seeding days."""
        torrents = [
            self.create_mock_torrent("t1", "seeding", "/data", ["http://t.com"], 10 * 24 * 60 * 60),
            self.create_mock_torrent("t2", "seeding", "/data", ["http://t.com"], 5 * 24 * 60 * 60),
        ]

        result = filter_torrents(torrents, None, None, 7)

        assert len(result) == 1
        assert result[0].name == "t1"


class TestProcessTorrents:
    """Tests for torrent processing actions."""

    def create_mock_torrent(self, name, torrent_id):
        """Helper to create a mock torrent."""
        torrent = Mock()
        torrent.name = name
        torrent.id = torrent_id
        return torrent

    @patch("builtins.print")
    def test_list_action(self, mock_print):
        """List action should not remove torrents."""
        client = Mock()
        client.remove_torrent = Mock()
        torrents = [self.create_mock_torrent("t1", 1)]

        process_torrents(client, torrents, "list")

        client.remove_torrent.assert_not_called()

    @patch("builtins.print")
    def test_delete_action(self, mock_print):
        """Delete action should remove with data."""
        client = Mock()
        client.remove_torrent = Mock()
        torrents = [self.create_mock_torrent("t1", 1)]

        process_torrents(client, torrents, "d")

        client.remove_torrent.assert_called_once_with(1, delete_data=True)

    @patch("builtins.print")
    def test_remove_action(self, mock_print):
        """Remove action should remove without data."""
        client = Mock()
        client.remove_torrent = Mock()
        torrents = [self.create_mock_torrent("t1", 1)]

        process_torrents(client, torrents, "r")

        client.remove_torrent.assert_called_once_with(1, delete_data=False)

    @patch("builtins.print")
    @patch("builtins.input")
    def test_interactive_mode(self, mock_input, mock_print):
        """Interactive mode should respect user input."""
        client = Mock()
        client.remove_torrent = Mock()
        torrents = [self.create_mock_torrent("t1", 1)]
        mock_input.return_value = "y"

        process_torrents(client, torrents, None)

        client.remove_torrent.assert_called_once_with(1, delete_data=False)
