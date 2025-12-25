"""Tests for widget CLI commands"""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from praisonaiwp.cli.commands.widget import widget_command


@pytest.fixture
def mock_widget_wp_client():
    """Mock WPClient for widget tests"""
    with patch('praisonaiwp.cli.commands.widget.WPClient') as mock_client:
        client_instance = Mock()
        mock_client.return_value = client_instance
        yield client_instance


@pytest.fixture
def mock_widget_ssh():
    """Mock SSHManager for widget tests"""
    with patch('praisonaiwp.cli.commands.widget.SSHManager') as mock_ssh:
        ssh_instance = Mock()
        mock_ssh.from_config.return_value = ssh_instance
        yield ssh_instance


@pytest.fixture
def mock_widget_config():
    """Mock Config for widget tests"""
    with patch('praisonaiwp.cli.commands.widget.Config') as mock_config:
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


class TestWidgetList:
    """Test widget list command"""

    def test_widget_list_success(self, mock_widget_wp_client, mock_widget_ssh, mock_widget_config):
        """Test successful widget list"""
        runner = CliRunner()

        mock_widget_wp_client.list_widgets.return_value = [
            {'id': '1', 'name': 'Search', 'sidebar': 'sidebar-1'},
            {'id': '2', 'name': 'Recent Posts', 'sidebar': 'sidebar-1'}
        ]

        result = runner.invoke(widget_command, ['list'])

        assert result.exit_code == 0
        assert 'Search' in result.output
        assert 'Recent Posts' in result.output
        mock_widget_wp_client.list_widgets.assert_called_once()

    def test_widget_list_empty(self, mock_widget_wp_client, mock_widget_ssh, mock_widget_config):
        """Test widget list when no widgets found"""
        runner = CliRunner()

        mock_widget_wp_client.list_widgets.return_value = []

        result = runner.invoke(widget_command, ['list'])

        assert result.exit_code == 0
        assert 'no widgets' in result.output.lower()

    def test_widget_list_with_server(self, mock_widget_wp_client, mock_widget_ssh, mock_widget_config):
        """Test widget list with specific server"""
        runner = CliRunner()

        mock_widget_wp_client.list_widgets.return_value = [{'id': '1', 'name': 'Search', 'sidebar': 'sidebar-1'}]

        result = runner.invoke(widget_command, ['list', '--server', 'staging'])

        assert result.exit_code == 0
        mock_widget_config.get_server.assert_called_once_with('staging')

    def test_widget_list_error(self, mock_widget_wp_client, mock_widget_ssh, mock_widget_config):
        """Test widget list with error"""
        runner = CliRunner()

        mock_widget_wp_client.list_widgets.side_effect = Exception('Connection error')

        result = runner.invoke(widget_command, ['list'])

        assert result.exit_code == 1
        assert 'error' in result.output.lower()


class TestWidgetGet:
    """Test widget get command"""

    def test_widget_get_success(self, mock_widget_wp_client, mock_widget_ssh, mock_widget_config):
        """Test successful widget get"""
        runner = CliRunner()

        mock_widget_wp_client.get_widget.return_value = {
            'id': '1',
            'name': 'Search',
            'sidebar': 'sidebar-1',
            'options': {'title': 'Search'}
        }

        result = runner.invoke(widget_command, ['get', '1'])

        assert result.exit_code == 0
        assert 'Search' in result.output
        mock_widget_wp_client.get_widget.assert_called_once_with('1')

    def test_widget_get_not_found(self, mock_widget_wp_client, mock_widget_ssh, mock_widget_config):
        """Test widget get when widget not found"""
        runner = CliRunner()

        mock_widget_wp_client.get_widget.return_value = None

        result = runner.invoke(widget_command, ['get', '999'])

        assert result.exit_code == 0
        assert 'not found' in result.output.lower()

    def test_widget_get_with_server(self, mock_widget_wp_client, mock_widget_ssh, mock_widget_config):
        """Test widget get with specific server"""
        runner = CliRunner()

        mock_widget_wp_client.get_widget.return_value = {'id': '1', 'name': 'Search'}

        result = runner.invoke(widget_command, ['get', '1', '--server', 'staging'])

        assert result.exit_code == 0
        mock_widget_config.get_server.assert_called_once_with('staging')

    def test_widget_get_error(self, mock_widget_wp_client, mock_widget_ssh, mock_widget_config):
        """Test widget get with error"""
        runner = CliRunner()

        mock_widget_wp_client.get_widget.side_effect = Exception('Connection error')

        result = runner.invoke(widget_command, ['get', '1'])

        assert result.exit_code == 1
        assert 'error' in result.output.lower()


class TestWidgetUpdate:
    """Test widget update command"""

    def test_widget_update_success(self, mock_widget_wp_client, mock_widget_ssh, mock_widget_config):
        """Test successful widget update"""
        runner = CliRunner()

        mock_widget_wp_client.update_widget.return_value = True

        result = runner.invoke(widget_command, ['update', '1', '--title', 'New Title'])

        assert result.exit_code == 0
        assert 'success' in result.output.lower()
        mock_widget_wp_client.update_widget.assert_called_once_with('1', {'title': 'New Title'})

    def test_widget_update_with_multiple_options(self, mock_widget_wp_client, mock_widget_ssh, mock_widget_config):
        """Test widget update with multiple options"""
        runner = CliRunner()

        mock_widget_wp_client.update_widget.return_value = True

        result = runner.invoke(widget_command, ['update', '1', '--title', 'New Title', '--text', 'Some text'])

        assert result.exit_code == 0
        mock_widget_wp_client.update_widget.assert_called_once_with('1', {'title': 'New Title', 'text': 'Some text'})

    def test_widget_update_with_server(self, mock_widget_wp_client, mock_widget_ssh, mock_widget_config):
        """Test widget update with specific server"""
        runner = CliRunner()

        mock_widget_wp_client.update_widget.return_value = True

        result = runner.invoke(widget_command, ['update', '1', '--title', 'New Title', '--server', 'staging'])

        assert result.exit_code == 0
        mock_widget_config.get_server.assert_called_once_with('staging')

    def test_widget_update_failure(self, mock_widget_wp_client, mock_widget_ssh, mock_widget_config):
        """Test widget update when operation fails"""
        runner = CliRunner()

        mock_widget_wp_client.update_widget.return_value = False

        result = runner.invoke(widget_command, ['update', '1', '--title', 'New Title'])

        assert result.exit_code == 1
        assert 'failed' in result.output.lower()

    def test_widget_update_error(self, mock_widget_wp_client, mock_widget_ssh, mock_widget_config):
        """Test widget update with error"""
        runner = CliRunner()

        mock_widget_wp_client.update_widget.side_effect = Exception('Update error')

        result = runner.invoke(widget_command, ['update', '1', '--title', 'New Title'])

        assert result.exit_code == 1
        assert 'error' in result.output.lower()
