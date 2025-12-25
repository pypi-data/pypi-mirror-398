"""Tests for transient CLI commands"""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from praisonaiwp.cli.commands.transient import transient_command


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_wp_client():
    with patch("praisonaiwp.cli.commands.transient.WPClient") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


@pytest.fixture
def mock_ssh():
    with patch("praisonaiwp.cli.commands.transient.SSHManager") as mock:
        yield mock


@pytest.fixture
def mock_config():
    with patch("praisonaiwp.cli.commands.transient.Config") as mock:
        config = MagicMock()
        config.get_server.return_value = {
            "hostname": "test.com",
            "username": "testuser",
            "wp_path": "/var/www/html",
            "php_bin": "php",
            "wp_cli": "/usr/local/bin/wp",
        }
        mock.return_value = config
        yield config


class TestTransientGet:
    def test_transient_get_success(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test getting transient value"""
        mock_wp_client.get_transient.return_value = "test_value"

        result = runner.invoke(transient_command, ["get", "cache_key"])

        assert result.exit_code == 0
        assert "test_value" in result.output
        mock_wp_client.get_transient.assert_called_once_with("cache_key")

    def test_transient_get_not_found(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test getting non-existent transient"""
        mock_wp_client.get_transient.return_value = None

        result = runner.invoke(transient_command, ["get", "nonexistent"])

        assert result.exit_code == 0
        assert "not found" in result.output or "None" in result.output


class TestTransientSet:
    def test_transient_set_success(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test setting transient value"""
        mock_wp_client.set_transient.return_value = True

        result = runner.invoke(transient_command, ["set", "cache_key", "test_value"])

        assert result.exit_code == 0
        assert "Set" in result.output or "✓" in result.output
        mock_wp_client.set_transient.assert_called_once_with("cache_key", "test_value", 3600)

    def test_transient_set_with_server(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test setting transient with specific server"""
        mock_wp_client.set_transient.return_value = True

        result = runner.invoke(
            transient_command, ["set", "cache_key", "test_value", "--server", "production"]
        )

        assert result.exit_code == 0
        mock_config.get_server.assert_called_with("production")

    def test_transient_set_with_expiration(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test setting transient with custom expiration"""
        mock_wp_client.set_transient.return_value = True

        result = runner.invoke(
            transient_command, ["set", "cache_key", "test_value", "--expire", "7200"]
        )

        assert result.exit_code == 0
        mock_wp_client.set_transient.assert_called_once_with("cache_key", "test_value", 7200)


class TestTransientDelete:
    def test_transient_delete_success(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test deleting transient"""
        mock_wp_client.delete_transient.return_value = True

        result = runner.invoke(transient_command, ["delete", "cache_key"])

        assert result.exit_code == 0
        assert "Deleted" in result.output or "✓" in result.output
        mock_wp_client.delete_transient.assert_called_once_with("cache_key")

    def test_transient_delete_not_found(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test deleting non-existent transient"""
        mock_wp_client.delete_transient.return_value = False

        result = runner.invoke(transient_command, ["delete", "nonexistent"])

        assert result.exit_code == 1
        assert "not found" in result.output or "Failed" in result.output
