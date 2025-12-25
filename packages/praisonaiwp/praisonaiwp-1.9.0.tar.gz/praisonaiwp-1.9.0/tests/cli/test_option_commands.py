"""Tests for option CLI commands"""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from praisonaiwp.cli.commands.option import option_command


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_wp_client():
    with patch('praisonaiwp.cli.commands.option.WPClient') as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


@pytest.fixture
def mock_ssh():
    with patch('praisonaiwp.cli.commands.option.SSHManager') as mock:
        yield mock


@pytest.fixture
def mock_config():
    with patch('praisonaiwp.cli.commands.option.Config') as mock:
        config = MagicMock()
        config.get_server.return_value = {
            'hostname': 'test.com',
            'username': 'testuser',
            'wp_path': '/var/www/html',
            'php_bin': 'php',
            'wp_cli': '/usr/local/bin/wp'
        }
        mock.return_value = config
        yield config


class TestOptionGet:
    def test_get_option_success(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test getting an option value"""
        mock_wp_client.get_option.return_value = "test_value"

        result = runner.invoke(option_command, ['get', 'site_name'])

        assert result.exit_code == 0
        assert "test_value" in result.output
        mock_wp_client.get_option.assert_called_once_with('site_name')

    def test_get_option_not_found(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test getting a non-existent option"""
        mock_wp_client.get_option.side_effect = Exception("Option not found")

        result = runner.invoke(option_command, ['get', 'nonexistent'])

        assert result.exit_code == 1


class TestOptionSet:
    def test_set_option_success(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test setting an option value"""
        mock_wp_client.set_option.return_value = True

        result = runner.invoke(option_command, ['set', 'site_name', 'New Site Name'])

        assert result.exit_code == 0
        assert "Set option" in result.output or "✓" in result.output
        mock_wp_client.set_option.assert_called_once_with('site_name', 'New Site Name')

    def test_set_option_with_server(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test setting option with specific server"""
        mock_wp_client.set_option.return_value = True

        result = runner.invoke(option_command, ['set', 'blogname', 'Test Blog', '--server', 'production'])

        assert result.exit_code == 0
        mock_config.get_server.assert_called_with('production')


class TestOptionDelete:
    def test_delete_option_success(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test deleting an option"""
        mock_wp_client.delete_option.return_value = True

        result = runner.invoke(option_command, ['delete', 'test_option'], input='y\n')

        assert result.exit_code == 0
        assert "Deleted" in result.output or "✓" in result.output
        mock_wp_client.delete_option.assert_called_once_with('test_option')

    def test_delete_option_cancelled(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test cancelling option deletion"""
        result = runner.invoke(option_command, ['delete', 'important_option'], input='n\n')

        assert result.exit_code == 1
        mock_wp_client.delete_option.assert_not_called()
