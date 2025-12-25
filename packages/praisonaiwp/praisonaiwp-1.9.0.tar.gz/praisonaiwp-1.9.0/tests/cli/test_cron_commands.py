"""Tests for cron CLI commands"""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from praisonaiwp.cli.commands.cron import cron_command


@pytest.fixture
def mock_cron_wp_client():
    """Mock WPClient for cron tests"""
    with patch('praisonaiwp.cli.commands.cron.WPClient') as mock_client:
        client_instance = Mock()
        mock_client.return_value = client_instance
        yield client_instance


@pytest.fixture
def mock_cron_ssh():
    """Mock SSHManager for cron tests"""
    with patch('praisonaiwp.cli.commands.cron.SSHManager') as mock_ssh:
        ssh_instance = Mock()
        mock_ssh.from_config.return_value = ssh_instance
        yield ssh_instance


@pytest.fixture
def mock_cron_config():
    """Mock Config for cron tests"""
    with patch('praisonaiwp.cli.commands.cron.Config') as mock_config:
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


class TestCronList:
    """Test cron list command"""

    def test_cron_list_success(self, mock_cron_wp_client, mock_cron_ssh, mock_cron_config):
        """Test successful cron list"""
        runner = CliRunner()

        # Mock the cron list response
        mock_cron_wp_client.list_cron_events.return_value = [
            {'hook': 'wp_scheduled_delete', 'next_run': '2024-01-01 10:00:00', 'schedule': 'daily'},
            {'hook': 'wp_version_check', 'next_run': '2024-01-01 12:00:00', 'schedule': 'twicedaily'}
        ]

        result = runner.invoke(cron_command, ['list'])

        assert result.exit_code == 0
        assert 'wp_scheduled_delete' in result.output
        assert 'wp_version_check' in result.output
        mock_cron_wp_client.list_cron_events.assert_called_once()

    def test_cron_list_empty(self, mock_cron_wp_client, mock_cron_ssh, mock_cron_config):
        """Test cron list when no events found"""
        runner = CliRunner()

        mock_cron_wp_client.list_cron_events.return_value = []

        result = runner.invoke(cron_command, ['list'])

        assert result.exit_code == 0
        assert 'no cron events' in result.output.lower()

    def test_cron_list_with_server(self, mock_cron_wp_client, mock_cron_ssh, mock_cron_config):
        """Test cron list with specific server"""
        runner = CliRunner()

        mock_cron_wp_client.list_cron_events.return_value = [{'hook': 'test_event', 'next_run': '2024-01-01 10:00:00'}]

        result = runner.invoke(cron_command, ['list', '--server', 'staging'])

        assert result.exit_code == 0
        mock_cron_config.get_server.assert_called_once_with('staging')

    def test_cron_list_error(self, mock_cron_wp_client, mock_cron_ssh, mock_cron_config):
        """Test cron list with error"""
        runner = CliRunner()

        mock_cron_wp_client.list_cron_events.side_effect = Exception('Connection error')

        result = runner.invoke(cron_command, ['list'])

        assert result.exit_code == 1
        assert 'error' in result.output.lower()


class TestCronRun:
    """Test cron run command"""

    def test_cron_run_success(self, mock_cron_wp_client, mock_cron_ssh, mock_cron_config):
        """Test successful cron run"""
        runner = CliRunner()

        mock_cron_wp_client.run_cron.return_value = True

        result = runner.invoke(cron_command, ['run'])

        assert result.exit_code == 0
        assert 'success' in result.output.lower()
        mock_cron_wp_client.run_cron.assert_called_once()

    def test_cron_run_with_server(self, mock_cron_wp_client, mock_cron_ssh, mock_cron_config):
        """Test cron run with specific server"""
        runner = CliRunner()

        mock_cron_wp_client.run_cron.return_value = True

        result = runner.invoke(cron_command, ['run', '--server', 'staging'])

        assert result.exit_code == 0
        mock_cron_config.get_server.assert_called_once_with('staging')

    def test_cron_run_failure(self, mock_cron_wp_client, mock_cron_ssh, mock_cron_config):
        """Test cron run when operation fails"""
        runner = CliRunner()

        mock_cron_wp_client.run_cron.return_value = False

        result = runner.invoke(cron_command, ['run'])

        assert result.exit_code == 1
        assert 'failed' in result.output.lower()

    def test_cron_run_error(self, mock_cron_wp_client, mock_cron_ssh, mock_cron_config):
        """Test cron run with error"""
        runner = CliRunner()

        mock_cron_wp_client.run_cron.side_effect = Exception('Execution error')

        result = runner.invoke(cron_command, ['run'])

        assert result.exit_code == 1
        assert 'error' in result.output.lower()


class TestCronEvent:
    """Test cron event command"""

    def test_cron_event_schedule_success(self, mock_cron_wp_client, mock_cron_ssh, mock_cron_config):
        """Test successful cron event schedule"""
        runner = CliRunner()

        mock_cron_wp_client.schedule_cron_event.return_value = True

        result = runner.invoke(cron_command, ['event', 'schedule', 'my_hook', '--recurrence', 'hourly'])

        assert result.exit_code == 0
        assert 'success' in result.output.lower()
        mock_cron_wp_client.schedule_cron_event.assert_called_once_with('my_hook', 'hourly', None, None)

    def test_cron_event_schedule_with_time(self, mock_cron_wp_client, mock_cron_ssh, mock_cron_config):
        """Test cron event schedule with specific time"""
        runner = CliRunner()

        mock_cron_wp_client.schedule_cron_event.return_value = True

        result = runner.invoke(cron_command, ['event', 'schedule', 'my_hook', '--recurrence', 'daily', '--time', '10:00'])

        assert result.exit_code == 0
        mock_cron_wp_client.schedule_cron_event.assert_called_once_with('my_hook', 'daily', '10:00', None)

    def test_cron_event_schedule_with_args(self, mock_cron_wp_client, mock_cron_ssh, mock_cron_config):
        """Test cron event schedule with arguments"""
        runner = CliRunner()

        mock_cron_wp_client.schedule_cron_event.return_value = True

        result = runner.invoke(cron_command, ['event', 'schedule', 'my_hook', '--recurrence', 'hourly', '--args', 'arg1,arg2'])

        assert result.exit_code == 0
        mock_cron_wp_client.schedule_cron_event.assert_called_once_with('my_hook', 'hourly', None, 'arg1,arg2')

    def test_cron_event_delete_success(self, mock_cron_wp_client, mock_cron_ssh, mock_cron_config):
        """Test successful cron event delete"""
        runner = CliRunner()

        mock_cron_wp_client.delete_cron_event.return_value = True

        result = runner.invoke(cron_command, ['event', 'delete', 'my_hook'])

        assert result.exit_code == 0
        assert 'success' in result.output.lower()
        mock_cron_wp_client.delete_cron_event.assert_called_once_with('my_hook')

    def test_cron_event_delete_with_server(self, mock_cron_wp_client, mock_cron_ssh, mock_cron_config):
        """Test cron event delete with specific server"""
        runner = CliRunner()

        mock_cron_wp_client.delete_cron_event.return_value = True

        result = runner.invoke(cron_command, ['event', 'delete', 'my_hook', '--server', 'staging'])

        assert result.exit_code == 0
        mock_cron_config.get_server.assert_called_once_with('staging')

    def test_cron_event_failure(self, mock_cron_wp_client, mock_cron_ssh, mock_cron_config):
        """Test cron event when operation fails"""
        runner = CliRunner()

        mock_cron_wp_client.schedule_cron_event.return_value = False

        result = runner.invoke(cron_command, ['event', 'schedule', 'my_hook', '--recurrence', 'hourly'])

        assert result.exit_code == 1
        assert 'failed' in result.output.lower()

    def test_cron_event_error(self, mock_cron_wp_client, mock_cron_ssh, mock_cron_config):
        """Test cron event with error"""
        runner = CliRunner()

        mock_cron_wp_client.schedule_cron_event.side_effect = Exception('Scheduling error')

        result = runner.invoke(cron_command, ['event', 'schedule', 'my_hook', '--recurrence', 'hourly'])

        assert result.exit_code == 1
        assert 'error' in result.output.lower()


class TestCronTest:
    """Test cron test command"""

    def test_cron_test_success(self, mock_cron_wp_client, mock_cron_ssh, mock_cron_config):
        """Test successful cron test"""
        runner = CliRunner()

        mock_cron_wp_client.test_cron.return_value = True

        result = runner.invoke(cron_command, ['test'])

        assert result.exit_code == 0
        assert 'working' in result.output.lower()
        mock_cron_wp_client.test_cron.assert_called_once()

    def test_cron_test_failure(self, mock_cron_wp_client, mock_cron_ssh, mock_cron_config):
        """Test cron test when not working"""
        runner = CliRunner()

        mock_cron_wp_client.test_cron.return_value = False

        result = runner.invoke(cron_command, ['test'])

        assert result.exit_code == 1
        assert 'not working' in result.output.lower()

    def test_cron_test_with_server(self, mock_cron_wp_client, mock_cron_ssh, mock_cron_config):
        """Test cron test with specific server"""
        runner = CliRunner()

        mock_cron_wp_client.test_cron.return_value = True

        result = runner.invoke(cron_command, ['test', '--server', 'staging'])

        assert result.exit_code == 0
        mock_cron_config.get_server.assert_called_once_with('staging')

    def test_cron_test_error(self, mock_cron_wp_client, mock_cron_ssh, mock_cron_config):
        """Test cron test with error"""
        runner = CliRunner()

        mock_cron_wp_client.test_cron.side_effect = Exception('Test error')

        result = runner.invoke(cron_command, ['test'])

        assert result.exit_code == 1
        assert 'error' in result.output.lower()
