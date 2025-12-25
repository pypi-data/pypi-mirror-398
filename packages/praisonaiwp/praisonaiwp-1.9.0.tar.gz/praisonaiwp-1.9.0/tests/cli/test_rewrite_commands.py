"""Test rewrite CLI commands"""

from unittest.mock import Mock, patch

from click.testing import CliRunner

from praisonaiwp.cli.commands.rewrite import rewrite_command
from praisonaiwp.utils.exceptions import ConfigNotFoundError


class TestRewriteCommands:
    """Test rewrite command group"""

    def setup_method(self):
        """Setup test environment"""
        self.runner = CliRunner()
        self.mock_config = Mock()
        self.mock_ssh_manager = Mock()
        self.mock_wp_client = Mock()

    @patch('praisonaiwp.cli.commands.rewrite.Config')
    @patch('praisonaiwp.cli.commands.rewrite.SSHManager')
    @patch('praisonaiwp.cli.commands.rewrite.WPClient')
    def test_rewrite_list_basic(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test basic rewrite list"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.rewrite_list.return_value = {
            "rules": [
                {"match": "^category/(.+)$", "source": "category", "query": "category_name=$matches[1]"},
                {"match": "^tag/(.+)$", "source": "tag", "query": "tag=$matches[1]"}
            ]
        }

        # Execute command
        result = self.runner.invoke(rewrite_command, ['list'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.rewrite_list.assert_called_once_with("table")
        assert "Rewrite Rules" in result.output
        assert "category" in result.output

    @patch('praisonaiwp.cli.commands.rewrite.Config')
    @patch('praisonaiwp.cli.commands.rewrite.SSHManager')
    @patch('praisonaiwp.cli.commands.rewrite.WPClient')
    def test_rewrite_list_json_format(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test rewrite list with JSON format"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.rewrite_list.return_value = {
            "rules": [
                {"match": "^category/(.+)$", "source": "category", "query": "category_name=$matches[1]"}
            ]
        }

        # Execute command
        result = self.runner.invoke(rewrite_command, ['list', '--format', 'json'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.rewrite_list.assert_called_once_with("json")
        assert "category" in result.output

    @patch('praisonaiwp.cli.commands.rewrite.Config')
    @patch('praisonaiwp.cli.commands.rewrite.SSHManager')
    @patch('praisonaiwp.cli.commands.rewrite.WPClient')
    def test_rewrite_list_json_output(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test rewrite list with JSON output"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.rewrite_list.return_value = {
            "rules": [
                {"match": "^category/(.+)$", "source": "category", "query": "category_name=$matches[1]"}
            ]
        }

        # Execute command with JSON output
        result = self.runner.invoke(rewrite_command, ['list', '--json'])

        # Assertions
        assert result.exit_code == 0
        assert '"status": "success"' in result.output
        assert '"rewrite list"' in result.output
        assert '"ai_friendly": true' in result.output

    @patch('praisonaiwp.cli.commands.rewrite.Config')
    def test_rewrite_list_config_not_found(self, mock_config_class):
        """Test rewrite list when config not found"""
        # Setup mock to raise exception
        mock_config_class.side_effect = ConfigNotFoundError("Configuration not found")

        # Execute command
        result = self.runner.invoke(rewrite_command, ['list'])

        # Assertions
        assert result.exit_code == 1
        assert "Configuration not found" in result.output

    @patch('praisonaiwp.cli.commands.rewrite.Config')
    @patch('praisonaiwp.cli.commands.rewrite.SSHManager')
    @patch('praisonaiwp.cli.commands.rewrite.WPClient')
    def test_rewrite_list_empty(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test rewrite list with no rules"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.rewrite_list.return_value = {"rules": []}

        # Execute command
        result = self.runner.invoke(rewrite_command, ['list'])

        # Assertions
        assert result.exit_code == 0
        assert "No rewrite rules found" in result.output

    @patch('praisonaiwp.cli.commands.rewrite.Config')
    @patch('praisonaiwp.cli.commands.rewrite.SSHManager')
    @patch('praisonaiwp.cli.commands.rewrite.WPClient')
    def test_rewrite_flush_success(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test rewrite flush success"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.rewrite_flush.return_value = True

        # Execute command
        result = self.runner.invoke(rewrite_command, ['flush'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.rewrite_flush.assert_called_once()
        assert "Rewrite rules flushed successfully" in result.output

    @patch('praisonaiwp.cli.commands.rewrite.Config')
    @patch('praisonaiwp.cli.commands.rewrite.SSHManager')
    @patch('praisonaiwp.cli.commands.rewrite.WPClient')
    def test_rewrite_flush_json_output(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test rewrite flush with JSON output"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.rewrite_flush.return_value = True

        # Execute command with JSON output
        result = self.runner.invoke(rewrite_command, ['flush', '--json'])

        # Assertions
        assert result.exit_code == 0
        assert '"status": "success"' in result.output
        assert '"rewrite flush"' in result.output
        assert '"flushed": true' in result.output

    @patch('praisonaiwp.cli.commands.rewrite.Config')
    @patch('praisonaiwp.cli.commands.rewrite.SSHManager')
    @patch('praisonaiwp.cli.commands.rewrite.WPClient')
    def test_rewrite_flush_failure(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test rewrite flush failure"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.rewrite_flush.return_value = False

        # Execute command
        result = self.runner.invoke(rewrite_command, ['flush'])

        # Assertions
        assert result.exit_code == 1
        assert "Failed to flush rewrite rules" in result.output

    @patch('praisonaiwp.cli.commands.rewrite.Config')
    @patch('praisonaiwp.cli.commands.rewrite.SSHManager')
    @patch('praisonaiwp.cli.commands.rewrite.WPClient')
    def test_rewrite_structure_success(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test rewrite structure success"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.rewrite_structure.return_value = True

        # Execute command
        result = self.runner.invoke(rewrite_command, ['structure', '/%postname%/'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.rewrite_structure.assert_called_once_with('/%postname%/', None, None)
        assert "Permalink structure updated to: /%postname%/" in result.output

    @patch('praisonaiwp.cli.commands.rewrite.Config')
    @patch('praisonaiwp.cli.commands.rewrite.SSHManager')
    @patch('praisonaiwp.cli.commands.rewrite.WPClient')
    def test_rewrite_structure_with_bases(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test rewrite structure with category and tag bases"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.rewrite_structure.return_value = True

        # Execute command
        result = self.runner.invoke(rewrite_command, [
            'structure', '/%category%/%postname%/', '--category-base', 'category', '--tag-base', 'tag'
        ])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.rewrite_structure.assert_called_once_with('/%category%/%postname%/', 'category', 'tag')
        assert "Category base: category" in result.output
        assert "Tag base: tag" in result.output

    @patch('praisonaiwp.cli.commands.rewrite.Config')
    @patch('praisonaiwp.cli.commands.rewrite.SSHManager')
    @patch('praisonaiwp.cli.commands.rewrite.WPClient')
    def test_rewrite_get_success(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test rewrite get success"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.rewrite_get.return_value = "category/(.+)/?$"

        # Execute command
        result = self.runner.invoke(rewrite_command, ['get', 'category'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.rewrite_get.assert_called_once_with('category')
        assert "Rewrite Rule" in result.output
        assert "category" in result.output
        assert "category/(.+)/?$" in result.output

    @patch('praisonaiwp.cli.commands.rewrite.Config')
    @patch('praisonaiwp.cli.commands.rewrite.SSHManager')
    @patch('praisonaiwp.cli.commands.rewrite.WPClient')
    def test_rewrite_get_not_found(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test rewrite get when rule not found"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.rewrite_get.return_value = None

        # Execute command
        result = self.runner.invoke(rewrite_command, ['get', 'nonexistent'])

        # Assertions
        assert result.exit_code == 1
        self.mock_wp_client.rewrite_get.assert_called_once_with('nonexistent')
        assert "Rewrite rule 'nonexistent' not found" in result.output

    @patch('praisonaiwp.cli.commands.rewrite.Config')
    @patch('praisonaiwp.cli.commands.rewrite.SSHManager')
    @patch('praisonaiwp.cli.commands.rewrite.WPClient')
    def test_rewrite_set_success(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test rewrite set success"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.rewrite_set.return_value = True

        # Execute command
        result = self.runner.invoke(rewrite_command, ['set', 'category', 'category/(.+)/?$'])

        # Assertions
        assert result.exit_code == 0
        self.mock_wp_client.rewrite_set.assert_called_once_with('category', 'category/(.+)/?$')
        assert "Rewrite rule 'category' set successfully" in result.output
        assert "Rule: category/(.+)/?$" in result.output

    @patch('praisonaiwp.cli.commands.rewrite.Config')
    @patch('praisonaiwp.cli.commands.rewrite.SSHManager')
    @patch('praisonaiwp.cli.commands.rewrite.WPClient')
    def test_rewrite_set_json_output(self, mock_wp_client_class, mock_ssh_manager_class, mock_config_class):
        """Test rewrite set with JSON output"""
        # Setup mocks
        mock_config_class.return_value = self.mock_config
        self.mock_config.get_default_server.return_value = {
            'hostname': 'test-server',
            'wp_path': '/var/www/html'
        }
        mock_ssh_manager_class.from_config.return_value = self.mock_ssh_manager
        mock_wp_client_class.return_value = self.mock_wp_client
        self.mock_wp_client.rewrite_set.return_value = True

        # Execute command with JSON output
        result = self.runner.invoke(rewrite_command, ['set', 'category', 'category/(.+)/?$', '--json'])

        # Assertions
        assert result.exit_code == 0
        assert '"status": "success"' in result.output
        assert '"rewrite set"' in result.output
        assert '"type": "category"' in result.output
        assert '"rule": "category/(.+)/?$"' in result.output
