"""Tests for config CLI commands"""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from praisonaiwp.cli.commands.config import config_command


@pytest.fixture
def mock_config_wp_client():
    """Mock WPClient for config tests"""
    with patch('praisonaiwp.cli.commands.config.WPClient') as mock_client:
        client_instance = Mock()
        mock_client.return_value = client_instance
        yield client_instance


@pytest.fixture
def mock_config_ssh():
    """Mock SSHManager for config tests"""
    with patch('praisonaiwp.cli.commands.config.SSHManager') as mock_ssh:
        ssh_instance = Mock()
        mock_ssh.from_config.return_value = ssh_instance
        yield ssh_instance


@pytest.fixture
def mock_config_config():
    """Mock Config for config tests"""
    with patch('praisonaiwp.cli.commands.config.Config') as mock_config:
        config_instance = Mock()
        config_instance.get_server.return_value = {
            'hostname': 'test.com',
            'username': 'testuser',
            'key_filename': '/path/to/key',
            'wp_path': '/var/www/html'
        }
        config_instance.get_default_server.return_value = {
            'hostname': 'test.com',
            'username': 'testuser',
            'key_filename': '/path/to/key',
            'wp_path': '/var/www/html'
        }
        mock_config.return_value = config_instance
        yield config_instance


class TestConfigGet:
    """Test config get command"""

    def test_config_get_success(self, mock_config_wp_client, mock_config_ssh, mock_config_config):
        """Test successful config get"""
        runner = CliRunner()

        # Mock the config get response
        mock_config_wp_client.get_config_param.return_value = 'test_value'

        result = runner.invoke(config_command, ['get', 'blogname'])

        assert result.exit_code == 0
        assert 'test_value' in result.output
        mock_config_wp_client.get_config_param.assert_called_once_with('blogname')

    def test_config_get_with_server(self, mock_config_wp_client, mock_config_ssh, mock_config_config):
        """Test config get with specific server"""
        runner = CliRunner()

        mock_config_wp_client.get_config_param.return_value = 'staging_value'

        result = runner.invoke(config_command, ['get', 'blogname', '--server', 'staging'])

        assert result.exit_code == 0
        assert 'staging_value' in result.output
        mock_config_config.get_server.assert_called_once_with('staging')

    def test_config_get_not_found(self, mock_config_wp_client, mock_config_ssh, mock_config_config):
        """Test config get when parameter not found"""
        runner = CliRunner()

        mock_config_wp_client.get_config_param.return_value = None

        result = runner.invoke(config_command, ['get', 'nonexistent_param'])

        assert result.exit_code == 0
        assert 'not found' in result.output.lower()

    def test_config_get_error(self, mock_config_wp_client, mock_config_ssh, mock_config_config):
        """Test config get with error"""
        runner = CliRunner()

        mock_config_wp_client.get_config_param.side_effect = Exception('Connection error')

        result = runner.invoke(config_command, ['get', 'blogname'])

        assert result.exit_code == 1
        assert 'error' in result.output.lower()


class TestConfigSet:
    """Test config set command"""

    def test_config_set_success(self, mock_config_wp_client, mock_config_ssh, mock_config_config):
        """Test successful config set"""
        runner = CliRunner()

        mock_config_wp_client.set_config_param.return_value = True

        result = runner.invoke(config_command, ['set', 'blogname', 'New Blog Name'])

        assert result.exit_code == 0
        assert 'success' in result.output.lower()
        mock_config_wp_client.set_config_param.assert_called_once_with('blogname', 'New Blog Name')

    def test_config_set_with_server(self, mock_config_wp_client, mock_config_ssh, mock_config_config):
        """Test config set with specific server"""
        runner = CliRunner()

        mock_config_wp_client.set_config_param.return_value = True

        result = runner.invoke(config_command, ['set', 'blogname', 'Staging Blog', '--server', 'staging'])

        assert result.exit_code == 0
        mock_config_config.get_server.assert_called_once_with('staging')

    def test_config_set_failure(self, mock_config_wp_client, mock_config_ssh, mock_config_config):
        """Test config set when operation fails"""
        runner = CliRunner()

        mock_config_wp_client.set_config_param.return_value = False

        result = runner.invoke(config_command, ['set', 'blogname', 'New Blog'])

        assert result.exit_code == 1
        assert 'failed' in result.output.lower()

    def test_config_set_error(self, mock_config_wp_client, mock_config_ssh, mock_config_config):
        """Test config set with error"""
        runner = CliRunner()

        mock_config_wp_client.set_config_param.side_effect = Exception('Permission denied')

        result = runner.invoke(config_command, ['set', 'blogname', 'New Blog'])

        assert result.exit_code == 1
        assert 'error' in result.output.lower()


class TestConfigList:
    """Test config list command"""

    def test_config_list_success(self, mock_config_wp_client, mock_config_ssh, mock_config_config):
        """Test successful config list"""
        runner = CliRunner()

        # Mock config list response
        mock_config_wp_client.get_all_config.return_value = {
            'blogname': 'My Blog',
            'blogdescription': 'Just another WordPress site',
            'siteurl': 'https://example.com',
            'home': 'https://example.com'
        }

        result = runner.invoke(config_command, ['list'])

        assert result.exit_code == 0
        assert 'blogname' in result.output
        assert 'My Blog' in result.output
        mock_config_wp_client.get_all_config.assert_called_once()

    def test_config_list_empty(self, mock_config_wp_client, mock_config_ssh, mock_config_config):
        """Test config list when no config found"""
        runner = CliRunner()

        mock_config_wp_client.get_all_config.return_value = {}

        result = runner.invoke(config_command, ['list'])

        assert result.exit_code == 0
        assert 'no config' in result.output.lower()

    def test_config_list_with_filter(self, mock_config_wp_client, mock_config_ssh, mock_config_config):
        """Test config list with search filter"""
        runner = CliRunner()

        mock_config_wp_client.get_all_config.return_value = {
            'blogname': 'My Blog',
            'blogdescription': 'Just another WordPress site',
            'admin_email': 'admin@example.com'
        }

        result = runner.invoke(config_command, ['list', '--search', 'blog'])

        assert result.exit_code == 0
        assert 'blogname' in result.output
        assert 'blogdescription' in result.output
        assert 'admin_email' not in result.output

    def test_config_list_error(self, mock_config_wp_client, mock_config_ssh, mock_config_config):
        """Test config list with error"""
        runner = CliRunner()

        mock_config_wp_client.get_all_config.side_effect = Exception('Database error')

        result = runner.invoke(config_command, ['list'])

        assert result.exit_code == 1
        assert 'error' in result.output.lower()


class TestConfigCreate:
    """Test config create command"""

    def test_config_create_success(self, mock_config_wp_client, mock_config_ssh, mock_config_config):
        """Test successful config create"""
        runner = CliRunner()

        mock_config_wp_client.create_config.return_value = True

        result = runner.invoke(config_command, ['create', '--dbhost', 'localhost', '--dbname', 'wordpress', '--dbuser', 'wpuser', '--dbpass', 'wppass'])

        assert result.exit_code == 0
        assert 'success' in result.output.lower()
        mock_config_wp_client.create_config.assert_called_once()

    def test_config_create_with_server(self, mock_config_wp_client, mock_config_ssh, mock_config_config):
        """Test config create with specific server"""
        runner = CliRunner()

        mock_config_wp_client.create_config.return_value = True

        result = runner.invoke(config_command, ['create', '--dbhost', 'localhost', '--dbname', 'wordpress', '--dbuser', 'wpuser', '--dbpass', 'wppass', '--server', 'staging'])

        assert result.exit_code == 0
        mock_config_config.get_server.assert_called_once_with('staging')

    def test_config_create_failure(self, mock_config_wp_client, mock_config_ssh, mock_config_config):
        """Test config create when operation fails"""
        runner = CliRunner()

        mock_config_wp_client.create_config.return_value = False

        result = runner.invoke(config_command, ['create', '--dbhost', 'localhost', '--dbname', 'wordpress', '--dbuser', 'wpuser', '--dbpass', 'wppass'])

        assert result.exit_code == 1
        assert 'failed' in result.output.lower()

    def test_config_create_error(self, mock_config_wp_client, mock_config_ssh, mock_config_config):
        """Test config create with error"""
        runner = CliRunner()

        mock_config_wp_client.create_config.side_effect = Exception('File write error')

        result = runner.invoke(config_command, ['create', '--dbhost', 'localhost', '--dbname', 'wordpress', '--dbuser', 'wpuser', '--dbpass', 'wppass'])

        assert result.exit_code == 1
        assert 'error' in result.output.lower()
