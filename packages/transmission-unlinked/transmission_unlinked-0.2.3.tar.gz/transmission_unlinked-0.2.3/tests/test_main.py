"""Tests for main module functionality."""

import json
from unittest.mock import Mock, mock_open, patch

import pytest

from transmission_unlinked.main import get_client_config, load_settings_from_file, parse_args


class TestLoadSettingsFromFile:
    """Tests for loading settings from file."""

    def test_load_settings(self):
        """Should load settings from JSON file."""
        settings_content = json.dumps({"rpc-port": 9091, "rpc-username": "user", "rpc-url": "/transmission/rpc"})

        with patch("builtins.open", mock_open(read_data=settings_content)):
            result = load_settings_from_file("settings.json", "pass")

        assert result["port"] == 9091
        assert result["username"] == "user"
        assert result["password"] == "pass"
        assert result["path"] == "/transmission/rpc"

    def test_load_settings_with_defaults(self):
        """Should use defaults for missing settings."""
        settings_content = json.dumps({})

        with patch("builtins.open", mock_open(read_data=settings_content)):
            result = load_settings_from_file("settings.json", "pass")

        assert result["port"] == 9091
        assert result["path"] == "/transmission/rpc"


class TestGetClientConfig:
    """Tests for client configuration."""

    def test_config_from_args(self):
        """Should build config from command line args."""
        args = Mock()
        args.settings_file = None
        args.protocol = "https"
        args.host = "192.168.1.1"
        args.port = 8080
        args.username = "user"
        args.password = "pass"
        args.path = "/rpc"

        result = get_client_config(args)

        assert result["protocol"] == "https"
        assert result["host"] == "192.168.1.1"
        assert result["port"] == 8080

    def test_config_from_settings_file(self):
        """Should prefer settings file over args."""
        args = Mock()
        args.settings_file = "settings.json"
        args.password = "pass"

        settings_content = json.dumps({"rpc-port": 9091})

        with patch("builtins.open", mock_open(read_data=settings_content)):
            result = get_client_config(args)

        assert result["port"] == 9091


class TestParseArgs:
    """Tests for argument parsing."""

    @patch("sys.argv", ["transmission-unlinked", "--password", "pass"])
    def test_minimal_args(self):
        """Should parse with just password."""
        args = parse_args()

        assert args.password == "pass"
        assert args.host == "127.0.0.1"
        assert args.port == 9091
        assert args.min_days == 7

    @patch("sys.argv", ["transmission-unlinked", "--password", "pass", "--dir", "/data/movies", "--min-days", "14"])
    def test_with_filters(self):
        """Should parse filter arguments."""
        args = parse_args()

        assert args.directory == "/data/movies"
        assert args.min_days == 14

    @patch("sys.argv", ["transmission-unlinked"])
    def test_missing_password(self):
        """Should require password."""
        with pytest.raises(SystemExit):
            parse_args()
