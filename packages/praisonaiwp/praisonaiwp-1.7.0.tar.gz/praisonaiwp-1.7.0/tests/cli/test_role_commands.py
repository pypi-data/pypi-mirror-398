"""Tests for role CLI commands"""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from praisonaiwp.cli.commands.role import role_command


@pytest.fixture
def mock_role_wp_client():
    """Mock WPClient for role tests"""
    with patch('praisonaiwp.cli.commands.role.WPClient') as mock_client:
        client_instance = Mock()
        mock_client.return_value = client_instance
        yield client_instance


@pytest.fixture
def mock_role_ssh():
    """Mock SSHManager for role tests"""
    with patch('praisonaiwp.cli.commands.role.SSHManager') as mock_ssh:
        ssh_instance = Mock()
        mock_ssh.from_config.return_value = ssh_instance
        yield ssh_instance


@pytest.fixture
def mock_role_config():
    """Mock Config for role tests"""
    with patch('praisonaiwp.cli.commands.role.Config') as mock_config:
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


class TestRoleList:
    """Test role list command"""

    def test_role_list_success(self, mock_role_wp_client, mock_role_ssh, mock_role_config):
        """Test successful role list"""
        runner = CliRunner()

        mock_role_wp_client.list_roles.return_value = [
            {'name': 'administrator', 'display_name': 'Administrator'},
            {'name': 'editor', 'display_name': 'Editor'},
            {'name': 'author', 'display_name': 'Author'}
        ]

        result = runner.invoke(role_command, ['list'])

        assert result.exit_code == 0
        assert 'administrator' in result.output
        assert 'editor' in result.output
        assert 'author' in result.output
        mock_role_wp_client.list_roles.assert_called_once()

    def test_role_list_empty(self, mock_role_wp_client, mock_role_ssh, mock_role_config):
        """Test role list when no roles found"""
        runner = CliRunner()

        mock_role_wp_client.list_roles.return_value = []

        result = runner.invoke(role_command, ['list'])

        assert result.exit_code == 0
        assert 'no roles' in result.output.lower()

    def test_role_list_with_server(self, mock_role_wp_client, mock_role_ssh, mock_role_config):
        """Test role list with specific server"""
        runner = CliRunner()

        mock_role_wp_client.list_roles.return_value = [{'name': 'administrator', 'display_name': 'Administrator'}]

        result = runner.invoke(role_command, ['list', '--server', 'staging'])

        assert result.exit_code == 0
        mock_role_config.get_server.assert_called_once_with('staging')

    def test_role_list_error(self, mock_role_wp_client, mock_role_ssh, mock_role_config):
        """Test role list with error"""
        runner = CliRunner()

        mock_role_wp_client.list_roles.side_effect = Exception('Connection error')

        result = runner.invoke(role_command, ['list'])

        assert result.exit_code == 1
        assert 'error' in result.output.lower()


class TestRoleGet:
    """Test role get command"""

    def test_role_get_success(self, mock_role_wp_client, mock_role_ssh, mock_role_config):
        """Test successful role get"""
        runner = CliRunner()

        mock_role_wp_client.get_role.return_value = {
            'name': 'editor',
            'display_name': 'Editor',
            'capabilities': ['edit_posts', 'edit_pages']
        }

        result = runner.invoke(role_command, ['get', 'editor'])

        assert result.exit_code == 0
        assert 'Editor' in result.output
        assert 'edit_posts' in result.output
        mock_role_wp_client.get_role.assert_called_once_with('editor')

    def test_role_get_not_found(self, mock_role_wp_client, mock_role_ssh, mock_role_config):
        """Test role get when role not found"""
        runner = CliRunner()

        mock_role_wp_client.get_role.return_value = None

        result = runner.invoke(role_command, ['get', 'nonexistent'])

        assert result.exit_code == 0
        assert 'not found' in result.output.lower()

    def test_role_get_with_server(self, mock_role_wp_client, mock_role_ssh, mock_role_config):
        """Test role get with specific server"""
        runner = CliRunner()

        mock_role_wp_client.get_role.return_value = {'name': 'editor', 'display_name': 'Editor'}

        result = runner.invoke(role_command, ['get', 'editor', '--server', 'staging'])

        assert result.exit_code == 0
        mock_role_config.get_server.assert_called_once_with('staging')

    def test_role_get_error(self, mock_role_wp_client, mock_role_ssh, mock_role_config):
        """Test role get with error"""
        runner = CliRunner()

        mock_role_wp_client.get_role.side_effect = Exception('Connection error')

        result = runner.invoke(role_command, ['get', 'editor'])

        assert result.exit_code == 1
        assert 'error' in result.output.lower()


class TestRoleCreate:
    """Test role create command"""

    def test_role_create_success(self, mock_role_wp_client, mock_role_ssh, mock_role_config):
        """Test successful role create"""
        runner = CliRunner()

        mock_role_wp_client.create_role.return_value = True

        result = runner.invoke(role_command, ['create', 'custom_role', 'Custom Role'])

        assert result.exit_code == 0
        assert 'success' in result.output.lower()
        assert 'Custom Role' in result.output
        mock_role_wp_client.create_role.assert_called_once_with('custom_role', 'Custom Role', None)

    def test_role_create_with_capabilities(self, mock_role_wp_client, mock_role_ssh, mock_role_config):
        """Test role create with capabilities"""
        runner = CliRunner()

        mock_role_wp_client.create_role.return_value = True

        result = runner.invoke(role_command, ['create', 'custom_role', 'Custom Role', '--capabilities', 'edit_posts,edit_pages'])

        assert result.exit_code == 0
        mock_role_wp_client.create_role.assert_called_once_with('custom_role', 'Custom Role', 'edit_posts,edit_pages')

    def test_role_create_with_server(self, mock_role_wp_client, mock_role_ssh, mock_role_config):
        """Test role create with specific server"""
        runner = CliRunner()

        mock_role_wp_client.create_role.return_value = True

        result = runner.invoke(role_command, ['create', 'custom_role', 'Custom Role', '--server', 'staging'])

        assert result.exit_code == 0
        mock_role_config.get_server.assert_called_once_with('staging')

    def test_role_create_failure(self, mock_role_wp_client, mock_role_ssh, mock_role_config):
        """Test role create when operation fails"""
        runner = CliRunner()

        mock_role_wp_client.create_role.return_value = False

        result = runner.invoke(role_command, ['create', 'custom_role', 'Custom Role'])

        assert result.exit_code == 1
        assert 'failed' in result.output.lower()

    def test_role_create_error(self, mock_role_wp_client, mock_role_ssh, mock_role_config):
        """Test role create with error"""
        runner = CliRunner()

        mock_role_wp_client.create_role.side_effect = Exception('Creation error')

        result = runner.invoke(role_command, ['create', 'custom_role', 'Custom Role'])

        assert result.exit_code == 1
        assert 'error' in result.output.lower()


class TestRoleDelete:
    """Test role delete command"""

    def test_role_delete_success(self, mock_role_wp_client, mock_role_ssh, mock_role_config):
        """Test successful role delete"""
        runner = CliRunner()

        mock_role_wp_client.delete_role.return_value = True

        result = runner.invoke(role_command, ['delete', 'custom_role'])

        assert result.exit_code == 0
        assert 'success' in result.output.lower()
        mock_role_wp_client.delete_role.assert_called_once_with('custom_role')

    def test_role_delete_with_server(self, mock_role_wp_client, mock_role_ssh, mock_role_config):
        """Test role delete with specific server"""
        runner = CliRunner()

        mock_role_wp_client.delete_role.return_value = True

        result = runner.invoke(role_command, ['delete', 'custom_role', '--server', 'staging'])

        assert result.exit_code == 0
        mock_role_config.get_server.assert_called_once_with('staging')

    def test_role_delete_failure(self, mock_role_wp_client, mock_role_ssh, mock_role_config):
        """Test role delete when operation fails"""
        runner = CliRunner()

        mock_role_wp_client.delete_role.return_value = False

        result = runner.invoke(role_command, ['delete', 'custom_role'])

        assert result.exit_code == 1
        assert 'failed' in result.output.lower()

    def test_role_delete_error(self, mock_role_wp_client, mock_role_ssh, mock_role_config):
        """Test role delete with error"""
        runner = CliRunner()

        mock_role_wp_client.delete_role.side_effect = Exception('Deletion error')

        result = runner.invoke(role_command, ['delete', 'custom_role'])

        assert result.exit_code == 1
        assert 'error' in result.output.lower()
