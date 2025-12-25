"""Test cache CLI commands"""

from unittest.mock import Mock, patch

from click.testing import CliRunner

from praisonaiwp.cli.commands.cache import cache_command
from praisonaiwp.utils.exceptions import ConfigNotFoundError


class TestCacheCommands:
    """Test cache command group"""

    def setup_method(self):
        """Setup test environment"""
        self.runner = CliRunner()
        self.mock_config = Mock()
        self.mock_ssh_manager = Mock()
        self.mock_wp_client = Mock()

    @patch('praisonaiwp.cli.commands.cache.Config')
    @patch('praisonaiwp.cli.commands.cache.SSHManager')
    @patch('praisonaiwp.cli.commands.cache.WPClient')
    def test_cache_flush_basic(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test basic cache flush"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.cache_flush.return_value = True

        # Execute command
        result = self.runner.invoke(cache_command, ['flush'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.cache_flush.assert_called_once_with(None)
        assert "Cache flushed successfully" in result.output

    @patch('praisonaiwp.cli.commands.cache.Config')
    @patch('praisonaiwp.cli.commands.cache.SSHManager')
    @patch('praisonaiwp.cli.commands.cache.WPClient')
    def test_cache_flush_with_type(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test cache flush with specific type"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.cache_flush.return_value = True

        # Execute command
        result = self.runner.invoke(cache_command, ['flush', '--type', 'object'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.cache_flush.assert_called_once_with('object')
        assert "Cache flushed successfully (object)" in result.output

    @patch('praisonaiwp.cli.commands.cache.Config')
    @patch('praisonaiwp.cli.commands.cache.SSHManager')
    @patch('praisonaiwp.cli.commands.cache.WPClient')
    def test_cache_flush_json_output(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test cache flush with JSON output"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.cache_flush.return_value = True

        # Execute command with JSON output
        result = self.runner.invoke(cache_command, ['flush', '--json'])

        # Assertions
        assert result.exit_code == 0
        assert '"status": "success"' in result.output
        assert '"cache flush"' in result.output
        assert '"ai_friendly": true' in result.output

    @patch('praisonaiwp.cli.commands.cache.Config')
    def test_cache_flush_config_not_found(self, mock_config_class):
        """Test cache flush when config not found"""
        # Setup mock to raise exception
        mock_config_class.side_effect = ConfigNotFoundError("Configuration not found")

        # Execute command
        result = self.runner.invoke(cache_command, ['flush'])

        # Assertions
        assert result.exit_code == 1
        assert "Configuration not found" in result.output

    @patch('praisonaiwp.cli.commands.cache.Config')
    @patch('praisonaiwp.cli.commands.cache.SSHManager')
    @patch('praisonaiwp.cli.commands.cache.WPClient')
    def test_cache_flush_failure(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test cache flush failure"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.cache_flush.return_value = False

        # Execute command
        result = self.runner.invoke(cache_command, ['flush'])

        # Assertions
        assert result.exit_code == 1
        assert "Failed to flush cache" in result.output

    @patch('praisonaiwp.cli.commands.cache.Config')
    @patch('praisonaiwp.cli.commands.cache.SSHManager')
    @patch('praisonaiwp.cli.commands.cache.WPClient')
    def test_cache_add_success(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test cache add success"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.cache_add.return_value = True

        # Execute command
        result = self.runner.invoke(cache_command, ['add', 'test_key', 'test_value'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.cache_add.assert_called_once_with('test_key', 'test_value', None, None)
        assert "Cache item 'test_key' added successfully" in result.output

    @patch('praisonaiwp.cli.commands.cache.Config')
    @patch('praisonaiwp.cli.commands.cache.SSHManager')
    @patch('praisonaiwp.cli.commands.cache.WPClient')
    def test_cache_add_with_options(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test cache add with group and expiration"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.cache_add.return_value = True

        # Execute command
        result = self.runner.invoke(cache_command, [
            'add', 'test_key', 'test_value', '--group', 'posts', '--expire', '3600'
        ])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.cache_add.assert_called_once_with('test_key', 'test_value', 'posts', 3600)
        assert "Cache item 'test_key' added successfully" in result.output
        assert "Group: posts" in result.output
        assert "Expires in: 3600 seconds" in result.output

    @patch('praisonaiwp.cli.commands.cache.Config')
    @patch('praisonaiwp.cli.commands.cache.SSHManager')
    @patch('praisonaiwp.cli.commands.cache.WPClient')
    def test_cache_get_success(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test cache get success"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.cache_get.return_value = "test_value"

        # Execute command
        result = self.runner.invoke(cache_command, ['get', 'test_key'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.cache_get.assert_called_once_with('test_key', None)
        assert "Cache Item" in result.output
        assert "test_key" in result.output
        assert "test_value" in result.output

    @patch('praisonaiwp.cli.commands.cache.Config')
    @patch('praisonaiwp.cli.commands.cache.SSHManager')
    @patch('praisonaiwp.cli.commands.cache.WPClient')
    def test_cache_get_not_found(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test cache get when item not found"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.cache_get.return_value = None

        # Execute command
        result = self.runner.invoke(cache_command, ['get', 'nonexistent_key'])

        # Assertions
        assert result.exit_code == 1
        self.mock_wp_client.cache_get.assert_called_once_with('nonexistent_key', None)
        assert "Cache item 'nonexistent_key' not found" in result.output

    @patch('praisonaiwp.cli.commands.cache.Config')
    @patch('praisonaiwp.cli.commands.cache.SSHManager')
    @patch('praisonaiwp.cli.commands.cache.WPClient')
    def test_cache_delete_success(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test cache delete success"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.cache_delete.return_value = True

        # Execute command
        result = self.runner.invoke(cache_command, ['delete', 'test_key'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.cache_delete.assert_called_once_with('test_key', None)
        assert "Cache item 'test_key' deleted successfully" in result.output

    @patch('praisonaiwp.cli.commands.cache.Config')
    @patch('praisonaiwp.cli.commands.cache.SSHManager')
    @patch('praisonaiwp.cli.commands.cache.WPClient')
    def test_cache_list_success(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test cache list success"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.cache_list.return_value = {
            'key1': {'value': 'value1', 'group': 'posts'},
            'key2': {'value': 'value2', 'group': 'options'}
        }

        # Execute command
        result = self.runner.invoke(cache_command, ['list'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.cache_list.assert_called_once_with(None)
        assert "Cache Items" in result.output
        assert "key1" in result.output
        assert "key2" in result.output

    @patch('praisonaiwp.cli.commands.cache.Config')
    @patch('praisonaiwp.cli.commands.cache.SSHManager')
    @patch('praisonaiwp.cli.commands.cache.WPClient')
    def test_cache_list_empty(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test cache list with no items"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.cache_list.return_value = {}

        # Execute command
        result = self.runner.invoke(cache_command, ['list'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.cache_list.assert_called_once_with(None)
        assert "No cache items found" in result.output

    @patch('praisonaiwp.cli.commands.cache.Config')
    @patch('praisonaiwp.cli.commands.cache.SSHManager')
    @patch('praisonaiwp.cli.commands.cache.WPClient')
    def test_cache_list_json_output(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test cache list with JSON output"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.cache_list.return_value = {
            'key1': {'value': 'value1', 'group': 'posts'}
        }

        # Execute command with JSON output
        result = self.runner.invoke(cache_command, ['list', '--json'])

        # Assertions
        assert result.exit_code == 0
        assert '"status": "success"' in result.output
        assert '"cache list"' in result.output
        assert '"key1"' in result.output
