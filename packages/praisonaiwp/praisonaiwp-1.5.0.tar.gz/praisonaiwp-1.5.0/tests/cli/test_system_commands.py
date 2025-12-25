"""Tests for system CLI commands"""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from praisonaiwp.cli.commands.system import system_command


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_wp_client():
    with patch('praisonaiwp.cli.commands.system.WPClient') as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


@pytest.fixture
def mock_ssh():
    with patch('praisonaiwp.cli.commands.system.SSHManager') as mock:
        yield mock


@pytest.fixture
def mock_config():
    with patch('praisonaiwp.cli.commands.system.Config') as mock:
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


class TestSystemCacheFlush:
    def test_cache_flush_success(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test flushing cache"""
        mock_wp_client.cache_flush.return_value = True

        result = runner.invoke(system_command, ['cache-flush'])

        assert result.exit_code == 0
        assert "flushed" in result.output or "✓" in result.output
        mock_wp_client.cache_flush.assert_called_once()

    def test_cache_flush_with_server(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test flushing cache with specific server"""
        mock_wp_client.cache_flush.return_value = True

        result = runner.invoke(system_command, ['cache-flush', '--server', 'production'])

        assert result.exit_code == 0
        mock_config.get_server.assert_called_with('production')


class TestSystemCacheType:
    def test_cache_type_success(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test getting cache type"""
        mock_wp_client.get_cache_type.return_value = "redis"

        result = runner.invoke(system_command, ['cache-type'])

        assert result.exit_code == 0
        assert "redis" in result.output
        mock_wp_client.get_cache_type.assert_called_once()


class TestSystemVersion:
    def test_version_success(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test getting WordPress version"""
        mock_wp_client.get_version.return_value = "6.4.2"

        result = runner.invoke(system_command, ['version'])

        assert result.exit_code == 0
        assert "6.4.2" in result.output
        mock_wp_client.get_version.assert_called_once()

    def test_version_detailed(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test getting detailed version info"""
        mock_wp_client.get_version.return_value = "6.4.2"

        result = runner.invoke(system_command, ['version', '--detailed'])

        assert result.exit_code == 0
        mock_wp_client.get_version.assert_called_once()


class TestSystemCheckInstall:
    def test_check_install_success(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test checking WordPress installation"""
        mock_wp_client.check_install.return_value = True

        result = runner.invoke(system_command, ['check-install'])

        assert result.exit_code == 0
        assert "valid" in result.output or "✓" in result.output
        mock_wp_client.check_install.assert_called_once()

    def test_check_install_invalid(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test checking invalid WordPress installation"""
        mock_wp_client.check_install.return_value = False

        result = runner.invoke(system_command, ['check-install'])

        assert result.exit_code == 1
        assert "invalid" in result.output or "✗" in result.output
