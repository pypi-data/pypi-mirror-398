"""Tests for theme CLI commands"""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from praisonaiwp.cli.commands.theme import theme_command


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_wp_client():
    with patch("praisonaiwp.cli.commands.theme.WPClient") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


@pytest.fixture
def mock_ssh():
    with patch("praisonaiwp.cli.commands.theme.SSHManager") as mock:
        yield mock


@pytest.fixture
def mock_config():
    with patch("praisonaiwp.cli.commands.theme.Config") as mock:
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


class TestThemeList:
    def test_theme_list_success(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test listing themes"""
        mock_wp_client.list_themes.return_value = [
            {
                "name": "Twenty Twenty-Three",
                "slug": "twentytwentythree",
                "status": "active",
                "version": "1.2",
                "author": "WordPress Team",
            },
            {
                "name": "Twenty Twenty-Two",
                "slug": "twentytwentytwo",
                "status": "inactive",
                "version": "1.1",
                "author": "WordPress Team",
            },
        ]

        result = runner.invoke(theme_command, ["list"])

        assert result.exit_code == 0
        mock_wp_client.list_themes.assert_called_once()

    def test_theme_list_empty(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test listing when no themes found"""
        mock_wp_client.list_themes.return_value = []

        result = runner.invoke(theme_command, ["list"])

        assert result.exit_code == 0
        assert "No themes found" in result.output


class TestThemeActivate:
    def test_theme_activate_success(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test activating a theme"""
        mock_wp_client.activate_theme.return_value = True

        result = runner.invoke(theme_command, ["activate", "twentytwentythree"])

        assert result.exit_code == 0
        assert "activated" in result.output or "✓" in result.output
        mock_wp_client.activate_theme.assert_called_once_with("twentytwentythree")

    def test_theme_activate_with_server(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test activating theme with specific server"""
        mock_wp_client.activate_theme.return_value = True

        result = runner.invoke(
            theme_command, ["activate", "twentytwentythree", "--server", "production"]
        )

        assert result.exit_code == 0
        mock_config.get_server.assert_called_with("production")

    def test_theme_activate_failure(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test theme activation failure"""
        mock_wp_client.activate_theme.return_value = False

        result = runner.invoke(theme_command, ["activate", "nonexistent"])

        assert result.exit_code == 1
        assert "Failed" in result.output or "✗" in result.output
