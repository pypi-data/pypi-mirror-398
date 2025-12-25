"""Test super-admin CLI commands"""
from unittest.mock import Mock, patch

from click.testing import CliRunner

from praisonaiwp.cli.commands.super_admin import super_admin_command
from praisonaiwp.utils.exceptions import ConfigNotFoundError


class TestSuperAdminCommands:
    """Test super-admin command group"""

    def setup_method(self):
        """Setup test environment"""
        self.runner = CliRunner()
        self.mock_config = Mock()
        self.mock_ssh_manager = Mock()
        self.mock_wp_client = Mock()

    @patch('praisonaiwp.cli.commands.super_admin.Config')
    @patch('praisonaiwp.cli.commands.super_admin.SSHManager')
    @patch('praisonaiwp.cli.commands.super_admin.WPClient')
    def test_super_admin_list_basic(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test basic super-admin list"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.super_admin_list.return_value = {
            "super_admins": [
                {"user_id": "1", "user_email": "admin@example.com", "user_login": "admin"},
                {"user_id": "2", "user_email": "super@example.com", "user_login": "super"}
            ]
        }

        # Execute command
        result = self.runner.invoke(super_admin_command, ['list'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.super_admin_list.assert_called_once_with("table")
        assert "Super Admins" in result.output
        assert "admin@example.com" in result.output

    @patch('praisonaiwp.cli.commands.super_admin.Config')
    @patch('praisonaiwp.cli.commands.super_admin.SSHManager')
    @patch('praisonaiwp.cli.commands.super_admin.WPClient')
    def test_super_admin_list_json_format(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test super-admin list with JSON format"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.super_admin_list.return_value = {
            "super_admins": [
                {"user_id": "1", "user_email": "admin@example.com", "user_login": "admin"}
            ]
        }

        # Execute command
        result = self.runner.invoke(super_admin_command, ['list', '--format', 'json'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.super_admin_list.assert_called_once_with("json")
        assert "admin@example.com" in result.output

    @patch('praisonaiwp.cli.commands.super_admin.Config')
    @patch('praisonaiwp.cli.commands.super_admin.SSHManager')
    @patch('praisonaiwp.cli.commands.super_admin.WPClient')
    def test_super_admin_list_json_output(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test super-admin list with JSON output"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.super_admin_list.return_value = {
            "super_admins": [
                {"user_id": "1", "user_email": "admin@example.com", "user_login": "admin"}
            ]
        }

        # Execute command with JSON output
        result = self.runner.invoke(super_admin_command, ['list', '--json'])

        # Assertions
        assert result.exit_code == 0
        assert '"status": "success"' in result.output
        assert '"super-admin list"' in result.output
        assert '"ai_friendly": true' in result.output

    @patch('praisonaiwp.cli.commands.super_admin.Config')
    def test_super_admin_list_config_not_found(self, mock_config_class):
        """Test super-admin list when config not found"""
        # Setup mock to raise exception
        mock_config_class.side_effect = ConfigNotFoundError("Configuration not found")

        # Execute command
        result = self.runner.invoke(super_admin_command, ['list'])

        # Assertions
        assert result.exit_code == 1
        assert "Configuration not found" in result.output

    @patch('praisonaiwp.cli.commands.super_admin.Config')
    @patch('praisonaiwp.cli.commands.super_admin.SSHManager')
    @patch('praisonaiwp.cli.commands.super_admin.WPClient')
    def test_super_admin_list_empty(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test super-admin list with no super admins"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.super_admin_list.return_value = {"super_admins": []}

        # Execute command
        result = self.runner.invoke(super_admin_command, ['list'])

        # Assertions
        assert result.exit_code == 0
        assert "No super admins found" in result.output

    @patch('praisonaiwp.cli.commands.super_admin.Config')
    @patch('praisonaiwp.cli.commands.super_admin.SSHManager')
    @patch('praisonaiwp.cli.commands.super_admin.WPClient')
    def test_super_admin_add_success(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test super-admin add success"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.super_admin_add.return_value = True

        # Execute command
        result = self.runner.invoke(super_admin_command, ['add', '1'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.super_admin_add.assert_called_once_with('1')
        assert "Super admin '1' added successfully" in result.output

    @patch('praisonaiwp.cli.commands.super_admin.Config')
    @patch('praisonaiwp.cli.commands.super_admin.SSHManager')
    @patch('praisonaiwp.cli.commands.super_admin.WPClient')
    def test_super_admin_add_by_email(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test super-admin add by email"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.super_admin_add.return_value = True

        # Execute command
        result = self.runner.invoke(super_admin_command, ['add', 'admin@example.com'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.super_admin_add.assert_called_once_with('admin@example.com')
        assert "Super admin 'admin@example.com' added successfully" in result.output

    @patch('praisonaiwp.cli.commands.super_admin.Config')
    @patch('praisonaiwp.cli.commands.super_admin.SSHManager')
    @patch('praisonaiwp.cli.commands.super_admin.WPClient')
    def test_super_admin_add_failure(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test super-admin add failure"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.super_admin_add.return_value = False

        # Execute command
        result = self.runner.invoke(super_admin_command, ['add', '1'])

        # Assertions
        assert result.exit_code == 1
        assert "Failed to add super admin" in result.output

    @patch('praisonaiwp.cli.commands.super_admin.Config')
    @patch('praisonaiwp.cli.commands.super_admin.SSHManager')
    @patch('praisonaiwp.cli.commands.super_admin.WPClient')
    def test_super_admin_remove_success(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test super-admin remove success"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.super_admin_remove.return_value = True

        # Execute command
        result = self.runner.invoke(super_admin_command, ['remove', '1'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.super_admin_remove.assert_called_once_with('1')
        assert "Super admin '1' removed successfully" in result.output

    @patch('praisonaiwp.cli.commands.super_admin.Config')
    @patch('praisonaiwp.cli.commands.super_admin.SSHManager')
    @patch('praisonaiwp.cli.commands.super_admin.WPClient')
    def test_super_admin_remove_by_email(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test super-admin remove by email"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.super_admin_remove.return_value = True

        # Execute command
        result = self.runner.invoke(super_admin_command, ['remove', 'admin@example.com'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.super_admin_remove.assert_called_once_with('admin@example.com')
        assert "Super admin 'admin@example.com' removed successfully" in result.output

    @patch('praisonaiwp.cli.commands.super_admin.Config')
    @patch('praisonaiwp.cli.commands.super_admin.SSHManager')
    @patch('praisonaiwp.cli.commands.super_admin.WPClient')
    def test_super_admin_remove_failure(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test super-admin remove failure"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.super_admin_remove.return_value = False

        # Execute command
        result = self.runner.invoke(super_admin_command, ['remove', '1'])

        # Assertions
        assert result.exit_code == 1
        assert "Failed to remove super admin" in result.output

    @patch('praisonaiwp.cli.commands.super_admin.Config')
    @patch('praisonaiwp.cli.commands.super_admin.SSHManager')
    @patch('praisonaiwp.cli.commands.super_admin.WPClient')
    def test_super_admin_add_json_output(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test super-admin add with JSON output"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.super_admin_add.return_value = True

        # Execute command with JSON output
        result = self.runner.invoke(super_admin_command, ['add', '1', '--json'])

        # Assertions
        assert result.exit_code == 0
        assert '"status": "success"' in result.output
        assert '"super-admin add"' in result.output
        assert '"user_id": "1"' in result.output
        assert '"added": true' in result.output

    @patch('praisonaiwp.cli.commands.super_admin.Config')
    @patch('praisonaiwp.cli.commands.super_admin.SSHManager')
    @patch('praisonaiwp.cli.commands.super_admin.WPClient')
    def test_super_admin_command_help(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test super-admin command help"""
        # Execute command
        result = self.runner.invoke(super_admin_command, ['--help'])

        # Assertions
        assert result.exit_code == 0
        assert "Manage WordPress multisite super admins" in result.output
        assert "list" in result.output
        assert "add" in result.output
        assert "remove" in result.output
