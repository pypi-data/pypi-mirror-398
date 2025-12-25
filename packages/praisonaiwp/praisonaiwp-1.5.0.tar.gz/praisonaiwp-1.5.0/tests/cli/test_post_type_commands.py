"""Test post-type CLI commands"""
from unittest.mock import Mock, patch

from click.testing import CliRunner

from praisonaiwp.cli.commands.post_type import post_type_command
from praisonaiwp.utils.exceptions import ConfigNotFoundError


class TestPostTypeCommands:
    """Test post-type command group"""

    def setup_method(self):
        """Setup test environment"""
        self.runner = CliRunner()
        self.mock_config = Mock()
        self.mock_ssh_manager = Mock()
        self.mock_wp_client = Mock()

    @patch('praisonaiwp.cli.commands.post_type.Config')
    @patch('praisonaiwp.cli.commands.post_type.SSHManager')
    @patch('praisonaiwp.cli.commands.post_type.WPClient')
    def test_post_type_list_basic(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test basic post-type list"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.post_type_list.return_value = {
            "post_types": [
                {"name": "post", "description": "Posts"},
                {"name": "page", "description": "Pages"}
            ]
        }

        # Execute command
        result = self.runner.invoke(post_type_command, ['list'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.post_type_list.assert_called_once_with("table")
        assert "Post Types" in result.output
        assert "post" in result.output

    @patch('praisonaiwp.cli.commands.post_type.Config')
    @patch('praisonaiwp.cli.commands.post_type.SSHManager')
    @patch('praisonaiwp.cli.commands.post_type.WPClient')
    def test_post_type_list_json_format(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test post-type list with JSON format"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.post_type_list.return_value = {
            "post_types": [
                {"name": "post", "description": "Posts"}
            ]
        }

        # Execute command
        result = self.runner.invoke(post_type_command, ['list', '--format', 'json'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.post_type_list.assert_called_once_with("json")
        assert "post" in result.output

    @patch('praisonaiwp.cli.commands.post_type.Config')
    @patch('praisonaiwp.cli.commands.post_type.SSHManager')
    @patch('praisonaiwp.cli.commands.post_type.WPClient')
    def test_post_type_list_json_output(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test post-type list with JSON output"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.post_type_list.return_value = {
            "post_types": [
                {"name": "post", "description": "Posts"}
            ]
        }

        # Execute command with JSON output
        result = self.runner.invoke(post_type_command, ['list', '--json'])

        # Assertions
        assert result.exit_code == 0
        assert '"status": "success"' in result.output
        assert '"post-type list"' in result.output
        assert '"ai_friendly": true' in result.output

    @patch('praisonaiwp.cli.commands.post_type.Config')
    def test_post_type_list_config_not_found(self, mock_config_class):
        """Test post-type list when config not found"""
        # Setup mock to raise exception
        mock_config_class.side_effect = ConfigNotFoundError("Configuration not found")

        # Execute command
        result = self.runner.invoke(post_type_command, ['list'])

        # Assertions
        assert result.exit_code == 1
        assert "Configuration not found" in result.output

    @patch('praisonaiwp.cli.commands.post_type.Config')
    @patch('praisonaiwp.cli.commands.post_type.SSHManager')
    @patch('praisonaiwp.cli.commands.post_type.WPClient')
    def test_post_type_list_empty(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test post-type list with no post types"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.post_type_list.return_value = {"post_types": []}

        # Execute command
        result = self.runner.invoke(post_type_command, ['list'])

        # Assertions
        assert result.exit_code == 0
        assert "No post types found" in result.output

    @patch('praisonaiwp.cli.commands.post_type.Config')
    @patch('praisonaiwp.cli.commands.post_type.SSHManager')
    @patch('praisonaiwp.cli.commands.post_type.WPClient')
    def test_post_type_get_success(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test post-type get success"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.post_type_get.return_value = {
            "name": "post",
            "label": "Posts",
            "public": True,
            "has_archive": False
        }

        # Execute command
        result = self.runner.invoke(post_type_command, ['get', 'post'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.post_type_get.assert_called_once_with('post')
        assert "Post Type: post" in result.output
        assert "Posts" in result.output

    @patch('praisonaiwp.cli.commands.post_type.Config')
    @patch('praisonaiwp.cli.commands.post_type.SSHManager')
    @patch('praisonaiwp.cli.commands.post_type.WPClient')
    def test_post_type_get_not_found(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test post-type get when post type not found"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.post_type_get.return_value = None

        # Execute command
        result = self.runner.invoke(post_type_command, ['get', 'nonexistent'])

        # Assertions
        assert result.exit_code == 1
        self.mock_wp_client.post_type_get.assert_called_once_with('nonexistent')
        assert "Post type 'nonexistent' not found" in result.output

    @patch('praisonaiwp.cli.commands.post_type.Config')
    @patch('praisonaiwp.cli.commands.post_type.SSHManager')
    @patch('praisonaiwp.cli.commands.post_type.WPClient')
    def test_post_type_create_success(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test post-type create success"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.post_type_create.return_value = True

        # Execute command
        result = self.runner.invoke(post_type_command, ['create', 'book', 'Books'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.post_type_create.assert_called_once_with('book', 'Books', None, None, None, None)
        assert "Post type 'book' created successfully" in result.output
        assert "Label: Books" in result.output

    @patch('praisonaiwp.cli.commands.post_type.Config')
    @patch('praisonaiwp.cli.commands.post_type.SSHManager')
    @patch('praisonaiwp.cli.commands.post_type.WPClient')
    def test_post_type_create_with_options(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test post-type create with options"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.post_type_create.return_value = True

        # Execute command
        result = self.runner.invoke(post_type_command, [
            'create', 'book', 'Books', '--public=true', '--has-archive=true', '--supports=title,editor'
        ])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.post_type_create.assert_called_once_with('book', 'Books', None, 'true', 'true', 'title,editor')
        assert "Public: true" in result.output
        assert "Has Archive: true" in result.output
        assert "Supports: title,editor" in result.output

    @patch('praisonaiwp.cli.commands.post_type.Config')
    @patch('praisonaiwp.cli.commands.post_type.SSHManager')
    @patch('praisonaiwp.cli.commands.post_type.WPClient')
    def test_post_type_delete_success(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test post-type delete success"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.post_type_delete.return_value = True

        # Execute command
        result = self.runner.invoke(post_type_command, ['delete', 'book'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.post_type_delete.assert_called_once_with('book', False)
        assert "Post type 'book' deleted successfully" in result.output

    @patch('praisonaiwp.cli.commands.post_type.Config')
    @patch('praisonaiwp.cli.commands.post_type.SSHManager')
    @patch('praisonaiwp.cli.commands.post_type.WPClient')
    def test_post_type_delete_force(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test post-type delete with force"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.post_type_delete.return_value = True

        # Execute command
        result = self.runner.invoke(post_type_command, ['delete', 'book', '--force'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.post_type_delete.assert_called_once_with('book', True)
        assert "Post type 'book' deleted successfully (forced)" in result.output

    @patch('praisonaiwp.cli.commands.post_type.Config')
    @patch('praisonaiwp.cli.commands.post_type.SSHManager')
    @patch('praisonaiwp.cli.commands.post_type.WPClient')
    def test_post_type_update_success(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test post-type update success"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.post_type_update.return_value = True

        # Execute command
        result = self.runner.invoke(post_type_command, ['update', 'book', '--label', 'New Books'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.post_type_update.assert_called_once_with('book', label='New Books')
        assert "Post type 'book' updated successfully" in result.output
        assert "Label: New Books" in result.output

    @patch('praisonaiwp.cli.commands.post_type.Config')
    @patch('praisonaiwp.cli.commands.post_type.SSHManager')
    @patch('praisonaiwp.cli.commands.post_type.WPClient')
    def test_post_type_update_no_params(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test post-type update with no parameters"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client

        # Execute command
        result = self.runner.invoke(post_type_command, ['update', 'book'])

        # Assertions
        assert result.exit_code == 1
        assert "No update parameters provided" in result.output

    @patch('praisonaiwp.cli.commands.post_type.Config')
    @patch('praisonaiwp.cli.commands.post_type.SSHManager')
    @patch('praisonaiwp.cli.commands.post_type.WPClient')
    def test_post_type_update_json_output(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test post-type update with JSON output"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.post_type_update.return_value = True

        # Execute command with JSON output
        result = self.runner.invoke(post_type_command, ['update', 'book', '--label', 'New Books', '--json'])

        # Assertions
        assert result.exit_code == 0
        assert '"status": "success"' in result.output
        assert '"post-type update"' in result.output
        assert '"post_type": "book"' in result.output
        assert '"updated": true' in result.output

    @patch('praisonaiwp.cli.commands.post_type.Config')
    @patch('praisonaiwp.cli.commands.post_type.SSHManager')
    @patch('praisonaiwp.cli.commands.post_type.WPClient')
    def test_post_type_create_failure(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test post-type create failure"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.post_type_create.return_value = False

        # Execute command
        result = self.runner.invoke(post_type_command, ['create', 'book', 'Books'])

        # Assertions
        assert result.exit_code == 1
        assert "Failed to create post type" in result.output
