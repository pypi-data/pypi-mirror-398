"""Test site CLI commands"""
from unittest.mock import Mock, patch

from click.testing import CliRunner

from praisonaiwp.cli.commands.site import site_command
from praisonaiwp.utils.exceptions import ConfigNotFoundError


class TestSiteCommands:
    """Test site command group"""

    def setup_method(self):
        """Setup test environment"""
        self.runner = CliRunner()
        self.mock_config = Mock()
        self.mock_ssh_manager = Mock()
        self.mock_wp_client = Mock()

    @patch('praisonaiwp.cli.commands.site.Config')
    @patch('praisonaiwp.cli.commands.site.SSHManager')
    @patch('praisonaiwp.cli.commands.site.WPClient')
    def test_site_list_basic(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test basic site list"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.site_list.return_value = {
            "sites": [
                {"blog_id": "1", "url": "example.com", "last_updated": "2023-01-01", "registered": "2023-01-01"},
                {"blog_id": "2", "url": "test.com", "last_updated": "2023-01-02", "registered": "2023-01-02"}
            ]
        }

        # Execute command
        result = self.runner.invoke(site_command, ['list'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.site_list.assert_called_once_with("table")
        assert "Sites" in result.output
        assert "example.com" in result.output

    @patch('praisonaiwp.cli.commands.site.Config')
    @patch('praisonaiwp.cli.commands.site.SSHManager')
    @patch('praisonaiwp.cli.commands.site.WPClient')
    def test_site_list_json_format(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test site list with JSON format"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.site_list.return_value = {
            "sites": [
                {"blog_id": "1", "url": "example.com", "last_updated": "2023-01-01", "registered": "2023-01-01"}
            ]
        }

        # Execute command
        result = self.runner.invoke(site_command, ['list', '--format', 'json'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.site_list.assert_called_once_with("json")
        assert "example.com" in result.output

    @patch('praisonaiwp.cli.commands.site.Config')
    @patch('praisonaiwp.cli.commands.site.SSHManager')
    @patch('praisonaiwp.cli.commands.site.WPClient')
    def test_site_list_json_output(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test site list with JSON output"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.site_list.return_value = {
            "sites": [
                {"blog_id": "1", "url": "example.com", "last_updated": "2023-01-01", "registered": "2023-01-01"}
            ]
        }

        # Execute command with JSON output
        result = self.runner.invoke(site_command, ['list', '--json'])

        # Assertions
        assert result.exit_code == 0
        assert '"status": "success"' in result.output
        assert '"site list"' in result.output
        assert '"ai_friendly": true' in result.output

    @patch('praisonaiwp.cli.commands.site.Config')
    def test_site_list_config_not_found(self, mock_config_class):
        """Test site list when config not found"""
        # Setup mock to raise exception
        mock_config_class.side_effect = ConfigNotFoundError("Configuration not found")

        # Execute command
        result = self.runner.invoke(site_command, ['list'])

        # Assertions
        assert result.exit_code == 1
        assert "Configuration not found" in result.output

    @patch('praisonaiwp.cli.commands.site.Config')
    @patch('praisonaiwp.cli.commands.site.SSHManager')
    @patch('praisonaiwp.cli.commands.site.WPClient')
    def test_site_list_empty(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test site list with no sites"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.site_list.return_value = {"sites": []}

        # Execute command
        result = self.runner.invoke(site_command, ['list'])

        # Assertions
        assert result.exit_code == 0
        assert "No sites found" in result.output

    @patch('praisonaiwp.cli.commands.site.Config')
    @patch('praisonaiwp.cli.commands.site.SSHManager')
    @patch('praisonaiwp.cli.commands.site.WPClient')
    def test_site_get_success(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test site get success"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.site_get.return_value = {
            "blog_id": "1",
            "url": "example.com",
            "title": "Example Site",
            "registered": "2023-01-01"
        }

        # Execute command
        result = self.runner.invoke(site_command, ['get', '1'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.site_get.assert_called_once_with('1')
        assert "Site: 1" in result.output
        assert "Example Site" in result.output

    @patch('praisonaiwp.cli.commands.site.Config')
    @patch('praisonaiwp.cli.commands.site.SSHManager')
    @patch('praisonaiwp.cli.commands.site.WPClient')
    def test_site_get_not_found(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test site get when site not found"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.site_get.return_value = None

        # Execute command
        result = self.runner.invoke(site_command, ['get', '999'])

        # Assertions
        assert result.exit_code == 1
        self.mock_wp_client.site_get.assert_called_once_with('999')
        assert "Site '999' not found" in result.output

    @patch('praisonaiwp.cli.commands.site.Config')
    @patch('praisonaiwp.cli.commands.site.SSHManager')
    @patch('praisonaiwp.cli.commands.site.WPClient')
    def test_site_create_success(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test site create success"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.site_create.return_value = True

        # Execute command
        result = self.runner.invoke(site_command, ['create', 'example.com', 'Example Site', 'admin@example.com'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.site_create.assert_called_once_with('example.com', 'Example Site', 'admin@example.com', None, None)
        assert "Site 'example.com' created successfully" in result.output
        assert "Title: Example Site" in result.output

    @patch('praisonaiwp.cli.commands.site.Config')
    @patch('praisonaiwp.cli.commands.site.SSHManager')
    @patch('praisonaiwp.cli.commands.site.WPClient')
    def test_site_create_with_options(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test site create with options"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.site_create.return_value = True

        # Execute command
        result = self.runner.invoke(site_command, [
            'create', 'example.com', 'Example Site', 'admin@example.com', '--site-id=2', '--private'
        ])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.site_create.assert_called_once_with('example.com', 'Example Site', 'admin@example.com', '2', True)
        assert "Site ID: 2" in result.output
        assert "Private: True" in result.output

    @patch('praisonaiwp.cli.commands.site.Config')
    @patch('praisonaiwp.cli.commands.site.SSHManager')
    @patch('praisonaiwp.cli.commands.site.WPClient')
    def test_site_delete_success(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test site delete success"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.site_delete.return_value = True

        # Execute command
        result = self.runner.invoke(site_command, ['delete', '1'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.site_delete.assert_called_once_with('1', False)
        assert "Site '1' deleted successfully" in result.output

    @patch('praisonaiwp.cli.commands.site.Config')
    @patch('praisonaiwp.cli.commands.site.SSHManager')
    @patch('praisonaiwp.cli.commands.site.WPClient')
    def test_site_delete_keep_tables(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test site delete with keep tables"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.site_delete.return_value = True

        # Execute command
        result = self.runner.invoke(site_command, ['delete', '1', '--keep-tables'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.site_delete.assert_called_once_with('1', True)
        assert "Site '1' deleted successfully (tables kept)" in result.output

    @patch('praisonaiwp.cli.commands.site.Config')
    @patch('praisonaiwp.cli.commands.site.SSHManager')
    @patch('praisonaiwp.cli.commands.site.WPClient')
    def test_site_activate_success(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test site activate success"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.site_activate.return_value = True

        # Execute command
        result = self.runner.invoke(site_command, ['activate', '1'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.site_activate.assert_called_once_with('1')
        assert "Site '1' activated successfully" in result.output

    @patch('praisonaiwp.cli.commands.site.Config')
    @patch('praisonaiwp.cli.commands.site.SSHManager')
    @patch('praisonaiwp.cli.commands.site.WPClient')
    def test_site_deactivate_success(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test site deactivate success"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.site_deactivate.return_value = True

        # Execute command
        result = self.runner.invoke(site_command, ['deactivate', '1'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.site_deactivate.assert_called_once_with('1')
        assert "Site '1' deactivated successfully" in result.output

    @patch('praisonaiwp.cli.commands.site.Config')
    @patch('praisonaiwp.cli.commands.site.SSHManager')
    @patch('praisonaiwp.cli.commands.site.WPClient')
    def test_site_archive_success(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test site archive success"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.site_archive.return_value = True

        # Execute command
        result = self.runner.invoke(site_command, ['archive', '1'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.site_archive.assert_called_once_with('1')
        assert "Site '1' archived successfully" in result.output

    @patch('praisonaiwp.cli.commands.site.Config')
    @patch('praisonaiwp.cli.commands.site.SSHManager')
    @patch('praisonaiwp.cli.commands.site.WPClient')
    def test_site_spam_success(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test site spam success"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.site_spam.return_value = True

        # Execute command
        result = self.runner.invoke(site_command, ['spam', '1'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.site_spam.assert_called_once_with('1')
        assert "Site '1' marked as spam successfully" in result.output

    @patch('praisonaiwp.cli.commands.site.Config')
    @patch('praisonaiwp.cli.commands.site.SSHManager')
    @patch('praisonaiwp.cli.commands.site.WPClient')
    def test_site_unspam_success(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test site unspam success"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.site_unspam.return_value = True

        # Execute command
        result = self.runner.invoke(site_command, ['unspam', '1'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.site_unspam.assert_called_once_with('1')
        assert "Site '1' unmarked as spam successfully" in result.output

    @patch('praisonaiwp.cli.commands.site.Config')
    @patch('praisonaiwp.cli.commands.site.SSHManager')
    @patch('praisonaiwp.cli.commands.site.WPClient')
    def test_site_create_failure(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test site create failure"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.site_create.return_value = False

        # Execute command
        result = self.runner.invoke(site_command, ['create', 'example.com', 'Example Site', 'admin@example.com'])

        # Assertions
        assert result.exit_code == 1
        assert "Failed to create site" in result.output

    @patch('praisonaiwp.cli.commands.site.Config')
    @patch('praisonaiwp.cli.commands.site.SSHManager')
    @patch('praisonaiwp.cli.commands.site.WPClient')
    def test_site_activate_json_output(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test site activate with JSON output"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.site_activate.return_value = True

        # Execute command with JSON output
        result = self.runner.invoke(site_command, ['activate', '1', '--json'])

        # Assertions
        assert result.exit_code == 0
        assert '"status": "success"' in result.output
        assert '"site activate"' in result.output
        assert '"site_id": "1"' in result.output
        assert '"activated": true' in result.output
