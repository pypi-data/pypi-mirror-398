"""Test search-replace CLI commands"""

from unittest.mock import Mock, patch

from click.testing import CliRunner

from praisonaiwp.cli.commands.search_replace import search_replace_command
from praisonaiwp.utils.exceptions import ConfigNotFoundError


class TestSearchReplaceCommands:
    """Test search-replace command group"""

    def setup_method(self):
        """Setup test environment"""
        self.runner = CliRunner()
        self.mock_config = Mock()
        self.mock_ssh_manager = Mock()
        self.mock_wp_client = Mock()

    @patch('praisonaiwp.cli.commands.search_replace.Config')
    @patch('praisonaiwp.cli.commands.search_replace.SSHManager')
    @patch('praisonaiwp.cli.commands.search_replace.WPClient')
    def test_search_replace_run_basic(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test basic search-replace"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.search_replace.return_value = {
            "success": True,
            "tables": {
                "wp_posts": {"rows": 10, "changes": 5}
            }
        }

        # Execute command
        result = self.runner.invoke(search_replace_command, [
            'run', 'old-text', 'new-text'
        ])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.search_replace.assert_called_once_with(
            'old-text', 'new-text', None, False, False
        )
        assert "Search-Replace Results" in result.output
        assert "old-text" in result.output
        assert "new-text" in result.output

    @patch('praisonaiwp.cli.commands.search_replace.Config')
    @patch('praisonaiwp.cli.commands.search_replace.SSHManager')
    @patch('praisonaiwp.cli.commands.search_replace.WPClient')
    def test_search_replace_run_dry_run(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test search-replace with dry run"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.search_replace.return_value = {
            "success": True,
            "tables": {
                "wp_posts": {"rows": 10, "changes": 5}
            }
        }

        # Execute command
        result = self.runner.invoke(search_replace_command, [
            'run', 'old-domain.com', 'new-domain.com', '--dry-run'
        ])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.search_replace.assert_called_once_with(
            'old-domain.com', 'new-domain.com', None, True, False
        )
        assert "Search-Replace Results" in result.output
        assert "Yes" in result.output  # Dry Run column
        assert "This was a dry run" in result.output

    @patch('praisonaiwp.cli.commands.search_replace.Config')
    @patch('praisonaiwp.cli.commands.search_replace.SSHManager')
    @patch('praisonaiwp.cli.commands.search_replace.WPClient')
    def test_search_replace_run_with_table(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test search-replace with specific table"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.search_replace.return_value = {
            "success": True,
            "tables": {
                "wp_options": {"rows": 5, "changes": 2}
            }
        }

        # Execute command
        result = self.runner.invoke(search_replace_command, [
            'run', 'http://old.com', 'https://new.com', '--table', 'wp_options'
        ])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.search_replace.assert_called_once_with(
            'http://old.com', 'https://new.com', 'wp_options', False, False
        )
        assert "wp_options" in result.output

    @patch('praisonaiwp.cli.commands.search_replace.Config')
    @patch('praisonaiwp.cli.commands.search_replace.SSHManager')
    @patch('praisonaiwp.cli.commands.search_replace.WPClient')
    def test_search_replace_run_regex(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test search-replace with regex"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.search_replace.return_value = {
            "success": True,
            "tables": {
                "wp_posts": {"rows": 8, "changes": 3}
            }
        }

        # Execute command
        result = self.runner.invoke(search_replace_command, [
            'run', 'old-(\\d+)', 'new-\\1', '--regex'
        ])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.search_replace.assert_called_once_with(
            'old-(\\d+)', 'new-\\1', None, False, True
        )
        assert "Yes" in result.output  # Regex column

    @patch('praisonaiwp.cli.commands.search_replace.Config')
    @patch('praisonaiwp.cli.commands.search_replace.SSHManager')
    @patch('praisonaiwp.cli.commands.search_replace.WPClient')
    def test_search_replace_run_json_output(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test search-replace with JSON output"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.search_replace.return_value = {
            "success": True,
            "tables": {
                "wp_posts": {"rows": 10, "changes": 5}
            }
        }

        # Execute command with JSON output
        result = self.runner.invoke(search_replace_command, [
            'run', 'old', 'new', '--json'
        ])

        # Assertions
        assert result.exit_code == 0
        assert '"status": "success"' in result.output
        assert '"search-replace operation"' in result.output
        assert '"ai_friendly": true' in result.output

    @patch('praisonaiwp.cli.commands.search_replace.Config')
    def test_search_replace_run_config_not_found(self, mock_config_class):
        """Test search-replace when config not found"""
        # Setup mock to raise exception
        mock_config_class.side_effect = ConfigNotFoundError("Configuration not found")

        # Execute command
        result = self.runner.invoke(search_replace_command, [
            'run', 'old', 'new'
        ])

        # Assertions
        assert result.exit_code == 1
        assert "Configuration not found" in result.output

    @patch('praisonaiwp.cli.commands.search_replace.Config')
    @patch('praisonaiwp.cli.commands.search_replace.SSHManager')
    @patch('praisonaiwp.cli.commands.search_replace.WPClient')
    def test_search_replace_run_wpcli_error(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test search-replace with WP-CLI error"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.search_replace.return_value = {"error": "Search failed"}

        # Execute command
        result = self.runner.invoke(search_replace_command, [
            'run', 'old', 'new'
        ])

        # Assertions
        assert result.exit_code == 1
        assert "Search failed" in result.output

    @patch('praisonaiwp.cli.commands.search_replace.Config')
    @patch('praisonaiwp.cli.commands.search_replace.SSHManager')
    @patch('praisonaiwp.cli.commands.search_replace.WPClient')
    def test_db_optimize_success(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test database optimization success"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.db_optimize.return_value = True

        # Execute command
        result = self.runner.invoke(search_replace_command, ['db-optimize'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.db_optimize.assert_called_once()
        assert "Database optimized successfully!" in result.output

    @patch('praisonaiwp.cli.commands.search_replace.Config')
    @patch('praisonaiwp.cli.commands.search_replace.SSHManager')
    @patch('praisonaiwp.cli.commands.search_replace.WPClient')
    def test_db_optimize_failure(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test database optimization failure"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.db_optimize.return_value = False

        # Execute command
        result = self.runner.invoke(search_replace_command, ['db-optimize'])

        # Assertions
        assert result.exit_code == 1
        assert "Failed to optimize database" in result.output

    @patch('praisonaiwp.cli.commands.search_replace.Config')
    @patch('praisonaiwp.cli.commands.search_replace.SSHManager')
    @patch('praisonaiwp.cli.commands.search_replace.WPClient')
    def test_db_repair_success(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test database repair success"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.db_repair.return_value = True

        # Execute command
        result = self.runner.invoke(search_replace_command, ['db-repair'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.db_repair.assert_called_once()
        assert "Database repaired successfully!" in result.output

    @patch('praisonaiwp.cli.commands.search_replace.Config')
    @patch('praisonaiwp.cli.commands.search_replace.SSHManager')
    @patch('praisonaiwp.cli.commands.search_replace.WPClient')
    def test_db_check_success(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test database check success"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.db_check.return_value = {
            "wp_posts": "OK",
            "wp_options": "OK",
            "wp_users": "OK"
        }

        # Execute command
        result = self.runner.invoke(search_replace_command, ['db-check'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.db_check.assert_called_once()
        assert "Database Check Results" in result.output
        assert "wp_posts" in result.output

    @patch('praisonaiwp.cli.commands.search_replace.Config')
    @patch('praisonaiwp.cli.commands.search_replace.SSHManager')
    @patch('praisonaiwp.cli.commands.search_replace.WPClient')
    def test_db_check_json_output(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test database check with JSON output"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.db_check.return_value = {
            "wp_posts": "OK",
            "wp_options": "OK"
        }

        # Execute command with JSON output
        result = self.runner.invoke(search_replace_command, [
            'db-check', '--json'
        ])

        # Assertions
        assert result.exit_code == 0
        assert '"status": "success"' in result.output
        assert '"database check"' in result.output
        assert '"wp_posts": "OK"' in result.output
