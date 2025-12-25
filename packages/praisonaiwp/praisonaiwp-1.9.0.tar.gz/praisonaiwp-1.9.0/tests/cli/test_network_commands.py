"""Test network CLI commands"""
from unittest.mock import Mock, patch

from click.testing import CliRunner

from praisonaiwp.cli.commands.network import network_command
from praisonaiwp.utils.exceptions import ConfigNotFoundError


class TestNetworkCommands:
    """Test network command group"""

    def setup_method(self):
        """Setup test environment"""
        self.runner = CliRunner()
        self.mock_config = Mock()
        self.mock_ssh_manager = Mock()
        self.mock_wp_client = Mock()

    @patch('praisonaiwp.cli.commands.network.Config')
    @patch('praisonaiwp.cli.commands.network.SSHManager')
    @patch('praisonaiwp.cli.commands.network.WPClient')
    def test_network_meta_get_success(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test network meta get success"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.network_meta_get.return_value = "My Network"

        # Execute command
        result = self.runner.invoke(network_command, ['meta', 'get', 'site_name'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.network_meta_get.assert_called_once_with('site_name')
        assert "My Network" in result.output

    @patch('praisonaiwp.cli.commands.network.Config')
    @patch('praisonaiwp.cli.commands.network.SSHManager')
    @patch('praisonaiwp.cli.commands.network.WPClient')
    def test_network_meta_get_not_found(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test network meta get when not found"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.network_meta_get.return_value = None

        # Execute command
        result = self.runner.invoke(network_command, ['meta', 'get', 'nonexistent'])

        # Assertions
        assert result.exit_code == 1
        self.mock_wp_client.network_meta_get.assert_called_once_with('nonexistent')
        assert "Network meta key 'nonexistent' not found" in result.output

    @patch('praisonaiwp.cli.commands.network.Config')
    @patch('praisonaiwp.cli.commands.network.SSHManager')
    @patch('praisonaiwp.cli.commands.network.WPClient')
    def test_network_meta_get_json_output(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test network meta get with JSON output"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.network_meta_get.return_value = "My Network"

        # Execute command with JSON output
        result = self.runner.invoke(network_command, ['meta', 'get', 'site_name', '--json'])

        # Assertions
        assert result.exit_code == 0
        assert '"status": "success"' in result.output
        assert '"network meta get"' in result.output
        assert '"meta_key": "site_name"' in result.output
        assert '"meta_value": "My Network"' in result.output

    @patch('praisonaiwp.cli.commands.network.Config')
    def test_network_meta_get_config_not_found(self, mock_config_class):
        """Test network meta get when config not found"""
        # Setup mock to raise exception
        mock_config_class.side_effect = ConfigNotFoundError("Configuration not found")

        # Execute command
        result = self.runner.invoke(network_command, ['meta', 'get', 'site_name'])

        # Assertions
        assert result.exit_code == 1
        assert "Configuration not found" in result.output

    @patch('praisonaiwp.cli.commands.network.Config')
    @patch('praisonaiwp.cli.commands.network.SSHManager')
    @patch('praisonaiwp.cli.commands.network.WPClient')
    def test_network_meta_set_success(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test network meta set success"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.network_meta_set.return_value = True

        # Execute command
        result = self.runner.invoke(network_command, ['meta', 'set', 'site_name', 'My Network'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.network_meta_set.assert_called_once_with('site_name', 'My Network')
        assert "Network meta 'site_name' set successfully" in result.output

    @patch('praisonaiwp.cli.commands.network.Config')
    @patch('praisonaiwp.cli.commands.network.SSHManager')
    @patch('praisonaiwp.cli.commands.network.WPClient')
    def test_network_meta_set_failure(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test network meta set failure"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.network_meta_set.return_value = False

        # Execute command
        result = self.runner.invoke(network_command, ['meta', 'set', 'site_name', 'My Network'])

        # Assertions
        assert result.exit_code == 1
        assert "Failed to set network meta" in result.output

    @patch('praisonaiwp.cli.commands.network.Config')
    @patch('praisonaiwp.cli.commands.network.SSHManager')
    @patch('praisonaiwp.cli.commands.network.WPClient')
    def test_network_meta_delete_success(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test network meta delete success"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.network_meta_delete.return_value = True

        # Execute command
        result = self.runner.invoke(network_command, ['meta', 'delete', 'site_name'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.network_meta_delete.assert_called_once_with('site_name')
        assert "Network meta 'site_name' deleted successfully" in result.output

    @patch('praisonaiwp.cli.commands.network.Config')
    @patch('praisonaiwp.cli.commands.network.SSHManager')
    @patch('praisonaiwp.cli.commands.network.WPClient')
    def test_network_meta_list_success(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test network meta list success"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.network_meta_list.return_value = {
            "meta": [
                {"meta_id": "1", "meta_key": "site_name", "meta_value": "My Network"},
                {"meta_id": "2", "meta_key": "admin_email", "meta_value": "admin@example.com"}
            ]
        }

        # Execute command
        result = self.runner.invoke(network_command, ['meta', 'list'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.network_meta_list.assert_called_once_with("table")
        assert "Network Meta" in result.output
        assert "site_name" in result.output

    @patch('praisonaiwp.cli.commands.network.Config')
    @patch('praisonaiwp.cli.commands.network.SSHManager')
    @patch('praisonaiwp.cli.commands.network.WPClient')
    def test_network_meta_list_json_format(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test network meta list with JSON format"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.network_meta_list.return_value = {
            "meta": [
                {"meta_id": "1", "meta_key": "site_name", "meta_value": "My Network"}
            ]
        }

        # Execute command
        result = self.runner.invoke(network_command, ['meta', 'list', '--format', 'json'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.network_meta_list.assert_called_once_with("json")
        assert "site_name" in result.output

    @patch('praisonaiwp.cli.commands.network.Config')
    @patch('praisonaiwp.cli.commands.network.SSHManager')
    @patch('praisonaiwp.cli.commands.network.WPClient')
    def test_network_meta_list_empty(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test network meta list with no meta"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.network_meta_list.return_value = {"meta": []}

        # Execute command
        result = self.runner.invoke(network_command, ['meta', 'list'])

        # Assertions
        assert result.exit_code == 0
        assert "No network meta found" in result.output

    @patch('praisonaiwp.cli.commands.network.Config')
    @patch('praisonaiwp.cli.commands.network.SSHManager')
    @patch('praisonaiwp.cli.commands.network.WPClient')
    def test_network_option_get_success(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test network option get success"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.network_option_get.return_value = "My Network"

        # Execute command
        result = self.runner.invoke(network_command, ['option', 'get', 'site_name'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.network_option_get.assert_called_once_with('site_name')
        assert "My Network" in result.output

    @patch('praisonaiwp.cli.commands.network.Config')
    @patch('praisonaiwp.cli.commands.network.SSHManager')
    @patch('praisonaiwp.cli.commands.network.WPClient')
    def test_network_option_get_not_found(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test network option get when not found"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.network_option_get.return_value = None

        # Execute command
        result = self.runner.invoke(network_command, ['option', 'get', 'nonexistent'])

        # Assertions
        assert result.exit_code == 1
        self.mock_wp_client.network_option_get.assert_called_once_with('nonexistent')
        assert "Network option 'nonexistent' not found" in result.output

    @patch('praisonaiwp.cli.commands.network.Config')
    @patch('praisonaiwp.cli.commands.network.SSHManager')
    @patch('praisonaiwp.cli.commands.network.WPClient')
    def test_network_option_set_success(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test network option set success"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.network_option_set.return_value = True

        # Execute command
        result = self.runner.invoke(network_command, ['option', 'set', 'site_name', 'My Network'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.network_option_set.assert_called_once_with('site_name', 'My Network')
        assert "Network option 'site_name' set successfully" in result.output

    @patch('praisonaiwp.cli.commands.network.Config')
    @patch('praisonaiwp.cli.commands.network.SSHManager')
    @patch('praisonaiwp.cli.commands.network.WPClient')
    def test_network_option_delete_success(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test network option delete success"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.network_option_delete.return_value = True

        # Execute command
        result = self.runner.invoke(network_command, ['option', 'delete', 'site_name'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.network_option_delete.assert_called_once_with('site_name')
        assert "Network option 'site_name' deleted successfully" in result.output

    @patch('praisonaiwp.cli.commands.network.Config')
    @patch('praisonaiwp.cli.commands.network.SSHManager')
    @patch('praisonaiwp.cli.commands.network.WPClient')
    def test_network_option_list_success(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test network option list success"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.network_option_list.return_value = {
            "options": [
                {"option_name": "site_name", "option_value": "My Network"},
                {"option_name": "admin_email", "option_value": "admin@example.com"}
            ]
        }

        # Execute command
        result = self.runner.invoke(network_command, ['option', 'list'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.network_option_list.assert_called_once_with("table")
        assert "Network Options" in result.output
        assert "site_name" in result.output

    @patch('praisonaiwp.cli.commands.network.Config')
    @patch('praisonaiwp.cli.commands.network.SSHManager')
    @patch('praisonaiwp.cli.commands.network.WPClient')
    def test_network_option_list_json_output(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test network option list with JSON output"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.network_option_list.return_value = {
            "options": [
                {"option_name": "site_name", "option_value": "My Network"}
            ]
        }

        # Execute command with JSON output
        result = self.runner.invoke(network_command, ['option', 'list', '--json'])

        # Assertions
        assert result.exit_code == 0
        assert '"status": "success"' in result.output
        assert '"network option list"' in result.output
        assert '"option_name": "site_name"' in result.output

    @patch('praisonaiwp.cli.commands.network.Config')
    @patch('praisonaiwp.cli.commands.network.SSHManager')
    @patch('praisonaiwp.cli.commands.network.WPClient')
    def test_network_command_help(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test network command help"""
        # Execute command
        result = self.runner.invoke(network_command, ['--help'])

        # Assertions
        assert result.exit_code == 0
        assert "Manage WordPress multisite network" in result.output
        assert "meta" in result.output
        assert "option" in result.output
