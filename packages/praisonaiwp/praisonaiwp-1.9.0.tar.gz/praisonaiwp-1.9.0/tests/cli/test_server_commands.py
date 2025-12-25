"""Test server CLI commands"""

from unittest.mock import Mock, patch

from click.testing import CliRunner

from praisonaiwp.cli.commands.server import server_command
from praisonaiwp.utils.exceptions import ConfigNotFoundError, SSHConnectionError


class TestServerCommands:
    """Test server command group"""

    def setup_method(self):
        """Setup test environment"""
        self.runner = CliRunner()
        self.mock_config = Mock()
        self.mock_ssh_manager = Mock()
        self.mock_wp_client = Mock()

    @patch('praisonaiwp.cli.commands.server.Config')
    @patch('praisonaiwp.cli.commands.server.SSHManager')
    @patch('praisonaiwp.cli.commands.server.WPClient')
    def test_server_start_default(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test starting server with default settings"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.start_server.return_value = "http://localhost:8080"

        # Execute command
        result = self.runner.invoke(server_command, ['start'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.start_server.assert_called_once_with('localhost', 8080, None, None)
        assert "Development server started successfully!" in result.output
        assert "http://localhost:8080" in result.output

    @patch('praisonaiwp.cli.commands.server.Config')
    @patch('praisonaiwp.cli.commands.server.SSHManager')
    @patch('praisonaiwp.cli.commands.server.WPClient')
    def test_server_start_custom_settings(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test starting server with custom settings"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.start_server.return_value = "http://0.0.0.0:9000"

        # Execute command
        result = self.runner.invoke(server_command, [
            'start',
            '--host', '0.0.0.0',
            '--port', '9000',
            '--config', 'development.ini',
            '--docroot', '/custom/path'
        ])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.start_server.assert_called_once_with(
            '0.0.0.0', 9000, 'development.ini', '/custom/path'
        )
        assert "http://0.0.0.0:9000" in result.output

    @patch('praisonaiwp.cli.commands.server.Config')
    @patch('praisonaiwp.cli.commands.server.SSHManager')
    @patch('praisonaiwp.cli.commands.server.WPClient')
    def test_server_start_json_output(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test starting server with JSON output"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.start_server.return_value = "http://localhost:8080"

        # Execute command with JSON output
        result = self.runner.invoke(server_command, ['start', '--json'])

        # Assertions
        assert result.exit_code == 0
        assert '"status": "success"' in result.output
        assert '"url": "http://localhost:8080"' in result.output
        assert '"ai_friendly": true' in result.output

    @patch('praisonaiwp.cli.commands.server.Config')
    def test_server_start_config_not_found(self, mock_config_class):
        """Test server start when config not found"""
        # Setup mock to raise exception
        mock_config_class.side_effect = ConfigNotFoundError("Configuration not found")

        # Execute command
        result = self.runner.invoke(server_command, ['start'])

        # Assertions
        assert result.exit_code == 1
        assert "Configuration not found" in result.output

    @patch('praisonaiwp.cli.commands.server.Config')
    @patch('praisonaiwp.cli.commands.server.SSHManager')
    @patch('praisonaiwp.cli.commands.server.WPClient')
    def test_server_start_server_not_found(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test server start when server not found"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_server.side_effect = Exception("Server 'nonexistent' not found")

        # Execute command
        result = self.runner.invoke(server_command, ['start', '--server', 'nonexistent'])

        # Assertions
        assert result.exit_code == 1
        assert "Server 'nonexistent' not found" in result.output

    @patch('praisonaiwp.cli.commands.server.Config')
    @patch('praisonaiwp.cli.commands.server.SSHManager')
    @patch('praisonaiwp.cli.commands.server.WPClient')
    def test_server_start_ssh_error(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test server start with SSH connection error"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.side_effect = SSHConnectionError("Connection failed")

        # Execute command
        result = self.runner.invoke(server_command, ['start'])

        # Assertions
        assert result.exit_code == 1
        assert "Connection failed" in result.output

    @patch('praisonaiwp.cli.commands.server.Config')
    @patch('praisonaiwp.cli.commands.server.SSHManager')
    @patch('praisonaiwp.cli.commands.server.WPClient')
    def test_server_start_wpcli_error(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test server start with WP-CLI error"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.start_server.return_value = None

        # Execute command
        result = self.runner.invoke(server_command, ['start'])

        # Assertions
        assert result.exit_code == 1
        assert "Failed to start development server" in result.output

    @patch('praisonaiwp.cli.commands.server.Config')
    @patch('praisonaiwp.cli.commands.server.SSHManager')
    @patch('praisonaiwp.cli.commands.server.WPClient')
    def test_server_shell_default(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test opening shell with default settings"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.open_shell.return_value = "wp>"

        # Execute command
        result = self.runner.invoke(server_command, ['shell'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.open_shell.assert_called_once()
        assert "PHP shell opened successfully!" in result.output
        assert "wp>" in result.output

    @patch('praisonaiwp.cli.commands.server.Config')
    @patch('praisonaiwp.cli.commands.server.SSHManager')
    @patch('praisonaiwp.cli.commands.server.WPClient')
    def test_server_shell_json_output(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test opening shell with JSON output"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.open_shell.return_value = "wp>"

        # Execute command with JSON output
        result = self.runner.invoke(server_command, ['shell', '--json'])

        # Assertions
        assert result.exit_code == 0
        assert '"status": "success"' in result.output
        assert '"prompt": "wp>"' in result.output
        assert '"type": "interactive"' in result.output

    @patch('praisonaiwp.cli.commands.server.Config')
    @patch('praisonaiwp.cli.commands.server.SSHManager')
    @patch('praisonaiwp.cli.commands.server.WPClient')
    def test_server_shell_error(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test shell opening error"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.open_shell.return_value = None

        # Execute command
        result = self.runner.invoke(server_command, ['shell'])

        # Assertions
        assert result.exit_code == 1
        assert "Failed to open PHP shell" in result.output

    @patch('praisonaiwp.cli.commands.server.Config')
    @patch('praisonaiwp.cli.commands.server.SSHManager')
    @patch('praisonaiwp.cli.commands.server.WPClient')
    def test_server_shell_with_server(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test opening shell for specific server"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_server.return_value = {
            'hostname': 'staging-server',
            'wp_path': '/var/www/staging'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.open_shell.return_value = "wp>"

        # Execute command
        result = self.runner.invoke(server_command, ['shell', '--server', 'staging'])

        # Assertions
        assert result.exit_code == 0
        self.mock_config.get_server.assert_called_once_with('staging')
        self.mock_wp_client.open_shell.assert_called_once()
        assert "PHP shell opened successfully!" in result.output
