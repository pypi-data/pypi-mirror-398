"""Test sidebar CLI commands"""

from unittest.mock import Mock, patch

from click.testing import CliRunner

from praisonaiwp.cli.commands.sidebar import sidebar_command
from praisonaiwp.utils.exceptions import ConfigNotFoundError


class TestSidebarCommands:
    """Test sidebar command group"""

    def setup_method(self):
        """Setup test environment"""
        self.runner = CliRunner()
        self.mock_config = Mock()
        self.mock_ssh_manager = Mock()
        self.mock_wp_client = Mock()

    @patch('praisonaiwp.cli.commands.sidebar.Config')
    @patch('praisonaiwp.cli.commands.sidebar.SSHManager')
    @patch('praisonaiwp.cli.commands.sidebar.WPClient')
    def test_sidebar_list_basic(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test basic sidebar list"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.sidebar_list.return_value = {
            "sidebar-1": {"name": "Primary Sidebar", "description": "Main sidebar"},
            "sidebar-2": {"name": "Secondary Sidebar", "description": "Secondary sidebar"}
        }

        # Execute command
        result = self.runner.invoke(sidebar_command, ['list'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.sidebar_list.assert_called_once()
        assert "Sidebars" in result.output
        assert "Primary Sidebar" in result.output

    @patch('praisonaiwp.cli.commands.sidebar.Config')
    @patch('praisonaiwp.cli.commands.sidebar.SSHManager')
    @patch('praisonaiwp.cli.commands.sidebar.WPClient')
    def test_sidebar_list_json_output(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test sidebar list with JSON output"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.sidebar_list.return_value = {
            "sidebar-1": {"name": "Primary Sidebar"}
        }

        # Execute command with JSON output
        result = self.runner.invoke(sidebar_command, ['list', '--json'])

        # Assertions
        assert result.exit_code == 0
        assert '"status": "success"' in result.output
        assert '"sidebar list"' in result.output
        assert '"ai_friendly": true' in result.output

    @patch('praisonaiwp.cli.commands.sidebar.Config')
    def test_sidebar_list_config_not_found(self, mock_config_class):
        """Test sidebar list when config not found"""
        # Setup mock to raise exception
        mock_config_class.side_effect = ConfigNotFoundError("Configuration not found")

        # Execute command
        result = self.runner.invoke(sidebar_command, ['list'])

        # Assertions
        assert result.exit_code == 1
        assert "Configuration not found" in result.output

    @patch('praisonaiwp.cli.commands.sidebar.Config')
    @patch('praisonaiwp.cli.commands.sidebar.SSHManager')
    @patch('praisonaiwp.cli.commands.sidebar.WPClient')
    def test_sidebar_list_empty(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test sidebar list with no sidebars"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.sidebar_list.return_value = {}

        # Execute command
        result = self.runner.invoke(sidebar_command, ['list'])

        # Assertions
        assert result.exit_code == 0
        assert "No sidebars found" in result.output

    @patch('praisonaiwp.cli.commands.sidebar.Config')
    @patch('praisonaiwp.cli.commands.sidebar.SSHManager')
    @patch('praisonaiwp.cli.commands.sidebar.WPClient')
    def test_sidebar_get_success(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test sidebar get success"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.sidebar_get.return_value = {
            "id": "sidebar-1",
            "name": "Primary Sidebar",
            "description": "Main sidebar",
            "widgets": ["search-2", "recent-posts-2"]
        }

        # Execute command
        result = self.runner.invoke(sidebar_command, ['get', 'sidebar-1'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.sidebar_get.assert_called_once_with('sidebar-1')
        assert "Sidebar: sidebar-1" in result.output
        assert "Primary Sidebar" in result.output

    @patch('praisonaiwp.cli.commands.sidebar.Config')
    @patch('praisonaiwp.cli.commands.sidebar.SSHManager')
    @patch('praisonaiwp.cli.commands.sidebar.WPClient')
    def test_sidebar_get_not_found(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test sidebar get when sidebar not found"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.sidebar_get.return_value = None

        # Execute command
        result = self.runner.invoke(sidebar_command, ['get', 'nonexistent'])

        # Assertions
        assert result.exit_code == 1
        self.mock_wp_client.sidebar_get.assert_called_once_with('nonexistent')
        assert "Sidebar 'nonexistent' not found" in result.output

    @patch('praisonaiwp.cli.commands.sidebar.Config')
    @patch('praisonaiwp.cli.commands.sidebar.SSHManager')
    @patch('praisonaiwp.cli.commands.sidebar.WPClient')
    def test_sidebar_update_success(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test sidebar update success"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.sidebar_update.return_value = True

        # Execute command
        result = self.runner.invoke(sidebar_command, ['update', 'sidebar-1', 'search-2', 'recent-posts-2'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.sidebar_update.assert_called_once_with('sidebar-1', ['search-2', 'recent-posts-2'])
        assert "Sidebar 'sidebar-1' updated with 2 widgets" in result.output
        assert "search-2, recent-posts-2" in result.output

    @patch('praisonaiwp.cli.commands.sidebar.Config')
    @patch('praisonaiwp.cli.commands.sidebar.SSHManager')
    @patch('praisonaiwp.cli.commands.sidebar.WPClient')
    def test_sidebar_update_empty(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test sidebar update with no widgets (empty)"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.sidebar_update.return_value = True

        # Execute command
        result = self.runner.invoke(sidebar_command, ['update', 'sidebar-1'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.sidebar_update.assert_called_once_with('sidebar-1', [])
        assert "Sidebar 'sidebar-1' emptied" in result.output

    @patch('praisonaiwp.cli.commands.sidebar.Config')
    @patch('praisonaiwp.cli.commands.sidebar.SSHManager')
    @patch('praisonaiwp.cli.commands.sidebar.WPClient')
    def test_sidebar_add_widget_success(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test sidebar add widget success"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.sidebar_add_widget.return_value = True

        # Execute command
        result = self.runner.invoke(sidebar_command, ['add-widget', 'sidebar-1', 'search-2'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.sidebar_add_widget.assert_called_once_with('sidebar-1', 'search-2', None)
        assert "Widget 'search-2' added to sidebar 'sidebar-1' successfully" in result.output

    @patch('praisonaiwp.cli.commands.sidebar.Config')
    @patch('praisonaiwp.cli.commands.sidebar.SSHManager')
    @patch('praisonaiwp.cli.commands.sidebar.WPClient')
    def test_sidebar_add_widget_with_position(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test sidebar add widget with position"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.sidebar_add_widget.return_value = True

        # Execute command
        result = self.runner.invoke(sidebar_command, ['add-widget', 'sidebar-1', 'search-2', '--position', '1'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.sidebar_add_widget.assert_called_once_with('sidebar-1', 'search-2', 1)
        assert "Position: 1" in result.output

    @patch('praisonaiwp.cli.commands.sidebar.Config')
    @patch('praisonaiwp.cli.commands.sidebar.SSHManager')
    @patch('praisonaiwp.cli.commands.sidebar.WPClient')
    def test_sidebar_remove_widget_success(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test sidebar remove widget success"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.sidebar_remove_widget.return_value = True

        # Execute command
        result = self.runner.invoke(sidebar_command, ['remove-widget', 'sidebar-1', 'search-2'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.sidebar_remove_widget.assert_called_once_with('sidebar-1', 'search-2')
        assert "Widget 'search-2' removed from sidebar 'sidebar-1' successfully" in result.output

    @patch('praisonaiwp.cli.commands.sidebar.Config')
    @patch('praisonaiwp.cli.commands.sidebar.SSHManager')
    @patch('praisonaiwp.cli.commands.sidebar.WPClient')
    def test_sidebar_empty_success(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test sidebar empty success"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.sidebar_empty.return_value = True

        # Execute command
        result = self.runner.invoke(sidebar_command, ['empty', 'sidebar-1'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.sidebar_empty.assert_called_once_with('sidebar-1')
        assert "Sidebar 'sidebar-1' emptied successfully" in result.output

    @patch('praisonaiwp.cli.commands.sidebar.Config')
    @patch('praisonaiwp.cli.commands.sidebar.SSHManager')
    @patch('praisonaiwp.cli.commands.sidebar.WPClient')
    def test_sidebar_empty_json_output(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test sidebar empty with JSON output"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.sidebar_empty.return_value = True

        # Execute command with JSON output
        result = self.runner.invoke(sidebar_command, ['empty', 'sidebar-1', '--json'])

        # Assertions
        assert result.exit_code == 0
        assert '"status": "success"' in result.output
        assert '"sidebar empty"' in result.output
        assert '"sidebar_id": "sidebar-1"' in result.output
        assert '"emptied": true' in result.output

    @patch('praisonaiwp.cli.commands.sidebar.Config')
    @patch('praisonaiwp.cli.commands.sidebar.SSHManager')
    @patch('praisonaiwp.cli.commands.sidebar.WPClient')
    def test_sidebar_update_failure(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test sidebar update failure"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.sidebar_update.return_value = False

        # Execute command
        result = self.runner.invoke(sidebar_command, ['update', 'sidebar-1', 'search-2'])

        # Assertions
        assert result.exit_code == 1
        assert "Failed to update sidebar" in result.output
