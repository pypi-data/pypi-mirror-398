"""Tests for core CLI commands"""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from praisonaiwp.cli.commands.core import core_command


@pytest.fixture
def mock_core_wp_client():
    """Mock WPClient for core tests"""
    with patch('praisonaiwp.cli.commands.core.WPClient') as mock_client:
        client_instance = Mock()
        mock_client.return_value = client_instance
        yield client_instance


@pytest.fixture
def mock_core_ssh():
    """Mock SSHManager for core tests"""
    with patch('praisonaiwp.cli.commands.core.SSHManager') as mock_ssh:
        ssh_instance = Mock()
        mock_ssh.from_config.return_value = ssh_instance
        yield ssh_instance


@pytest.fixture
def mock_core_config():
    """Mock Config for core tests"""
    with patch('praisonaiwp.cli.commands.core.Config') as mock_config:
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


class TestCoreVersion:
    """Test core version command"""

    def test_core_version_success(self, mock_core_wp_client, mock_core_ssh, mock_core_config):
        """Test successful core version check"""
        runner = CliRunner()

        # Mock the core version response
        mock_core_wp_client.get_core_version.return_value = '6.4.2'

        result = runner.invoke(core_command, ['version'])

        assert result.exit_code == 0
        assert '6.4.2' in result.output
        mock_core_wp_client.get_core_version.assert_called_once()

    def test_core_version_with_server(self, mock_core_wp_client, mock_core_ssh, mock_core_config):
        """Test core version with specific server"""
        runner = CliRunner()

        mock_core_wp_client.get_core_version.return_value = '6.4.1'

        result = runner.invoke(core_command, ['version', '--server', 'staging'])

        assert result.exit_code == 0
        assert '6.4.1' in result.output
        mock_core_config.get_server.assert_called_once_with('staging')

    def test_core_version_not_found(self, mock_core_wp_client, mock_core_ssh, mock_core_config):
        """Test core version when WordPress not found"""
        runner = CliRunner()

        mock_core_wp_client.get_core_version.return_value = None

        result = runner.invoke(core_command, ['version'])

        assert result.exit_code == 0
        assert 'not found' in result.output.lower()

    def test_core_version_error(self, mock_core_wp_client, mock_core_ssh, mock_core_config):
        """Test core version with error"""
        runner = CliRunner()

        mock_core_wp_client.get_core_version.side_effect = Exception('Connection error')

        result = runner.invoke(core_command, ['version'])

        assert result.exit_code == 1
        assert 'error' in result.output.lower()


class TestCoreUpdate:
    """Test core update command"""

    def test_core_update_success(self, mock_core_wp_client, mock_core_ssh, mock_core_config):
        """Test successful core update"""
        runner = CliRunner()

        mock_core_wp_client.update_core.return_value = True

        result = runner.invoke(core_command, ['update'])

        assert result.exit_code == 0
        assert 'success' in result.output.lower()
        mock_core_wp_client.update_core.assert_called_once_with(version=None, force=False)

    def test_core_update_with_version(self, mock_core_wp_client, mock_core_ssh, mock_core_config):
        """Test core update with specific version"""
        runner = CliRunner()

        mock_core_wp_client.update_core.return_value = True

        result = runner.invoke(core_command, ['update', '--version', '6.4.0'])

        assert result.exit_code == 0
        mock_core_wp_client.update_core.assert_called_once_with(version='6.4.0', force=False)

    def test_core_update_force(self, mock_core_wp_client, mock_core_ssh, mock_core_config):
        """Test core update with force flag"""
        runner = CliRunner()

        mock_core_wp_client.update_core.return_value = True

        result = runner.invoke(core_command, ['update', '--force'])

        assert result.exit_code == 0
        mock_core_wp_client.update_core.assert_called_once_with(version=None, force=True)

    def test_core_update_with_server(self, mock_core_wp_client, mock_core_ssh, mock_core_config):
        """Test core update with specific server"""
        runner = CliRunner()

        mock_core_wp_client.update_core.return_value = True

        result = runner.invoke(core_command, ['update', '--server', 'staging'])

        assert result.exit_code == 0
        mock_core_config.get_server.assert_called_once_with('staging')

    def test_core_update_failure(self, mock_core_wp_client, mock_core_ssh, mock_core_config):
        """Test core update when operation fails"""
        runner = CliRunner()

        mock_core_wp_client.update_core.return_value = False

        result = runner.invoke(core_command, ['update'])

        assert result.exit_code == 1
        assert 'failed' in result.output.lower()

    def test_core_update_error(self, mock_core_wp_client, mock_core_ssh, mock_core_config):
        """Test core update with error"""
        runner = CliRunner()

        mock_core_wp_client.update_core.side_effect = Exception('Permission denied')

        result = runner.invoke(core_command, ['update'])

        assert result.exit_code == 1
        assert 'error' in result.output.lower()


class TestCoreDownload:
    """Test core download command"""

    def test_core_download_success(self, mock_core_wp_client, mock_core_ssh, mock_core_config):
        """Test successful core download"""
        runner = CliRunner()

        mock_core_wp_client.download_core.return_value = '/path/to/wordpress.zip'

        result = runner.invoke(core_command, ['download'])

        assert result.exit_code == 0
        assert 'success' in result.output.lower()
        assert '/path/to/wordpress.zip' in result.output
        mock_core_wp_client.download_core.assert_called_once_with(version=None, path=None)

    def test_core_download_with_version(self, mock_core_wp_client, mock_core_ssh, mock_core_config):
        """Test core download with specific version"""
        runner = CliRunner()

        mock_core_wp_client.download_core.return_value = '/path/to/wordpress-6.4.0.zip'

        result = runner.invoke(core_command, ['download', '--version', '6.4.0'])

        assert result.exit_code == 0
        mock_core_wp_client.download_core.assert_called_once_with(version='6.4.0', path=None)

    def test_core_download_with_path(self, mock_core_wp_client, mock_core_ssh, mock_core_config):
        """Test core download with custom path"""
        runner = CliRunner()

        mock_core_wp_client.download_core.return_value = '/custom/path/wordpress.zip'

        result = runner.invoke(core_command, ['download', '--path', '/custom/path'])

        assert result.exit_code == 0
        mock_core_wp_client.download_core.assert_called_once_with(version=None, path='/custom/path')

    def test_core_download_with_server(self, mock_core_wp_client, mock_core_ssh, mock_core_config):
        """Test core download with specific server"""
        runner = CliRunner()

        mock_core_wp_client.download_core.return_value = '/remote/path/wordpress.zip'

        result = runner.invoke(core_command, ['download', '--server', 'staging'])

        assert result.exit_code == 0
        mock_core_config.get_server.assert_called_once_with('staging')

    def test_core_download_failure(self, mock_core_wp_client, mock_core_ssh, mock_core_config):
        """Test core download when operation fails"""
        runner = CliRunner()

        mock_core_wp_client.download_core.return_value = None

        result = runner.invoke(core_command, ['download'])

        assert result.exit_code == 1
        assert 'failed' in result.output.lower()

    def test_core_download_error(self, mock_core_wp_client, mock_core_ssh, mock_core_config):
        """Test core download with error"""
        runner = CliRunner()

        mock_core_wp_client.download_core.side_effect = Exception('Network error')

        result = runner.invoke(core_command, ['download'])

        assert result.exit_code == 1
        assert 'error' in result.output.lower()


class TestCoreInstall:
    """Test core install command"""

    def test_core_install_success(self, mock_core_wp_client, mock_core_ssh, mock_core_config):
        """Test successful core install"""
        runner = CliRunner()

        mock_core_wp_client.install_core.return_value = True

        result = runner.invoke(core_command, ['install'])

        assert result.exit_code == 0
        assert 'success' in result.output.lower()
        mock_core_wp_client.install_core.assert_called_once_with(version=None, force=False)

    def test_core_install_with_version(self, mock_core_wp_client, mock_core_ssh, mock_core_config):
        """Test core install with specific version"""
        runner = CliRunner()

        mock_core_wp_client.install_core.return_value = True

        result = runner.invoke(core_command, ['install', '--version', '6.4.0'])

        assert result.exit_code == 0
        mock_core_wp_client.install_core.assert_called_once_with(version='6.4.0', force=False)

    def test_core_install_force(self, mock_core_wp_client, mock_core_ssh, mock_core_config):
        """Test core install with force flag"""
        runner = CliRunner()

        mock_core_wp_client.install_core.return_value = True

        result = runner.invoke(core_command, ['install', '--force'])

        assert result.exit_code == 0
        mock_core_wp_client.install_core.assert_called_once_with(version=None, force=True)

    def test_core_install_with_server(self, mock_core_wp_client, mock_core_ssh, mock_core_config):
        """Test core install with specific server"""
        runner = CliRunner()

        mock_core_wp_client.install_core.return_value = True

        result = runner.invoke(core_command, ['install', '--server', 'staging'])

        assert result.exit_code == 0
        mock_core_config.get_server.assert_called_once_with('staging')

    def test_core_install_failure(self, mock_core_wp_client, mock_core_ssh, mock_core_config):
        """Test core install when operation fails"""
        runner = CliRunner()

        mock_core_wp_client.install_core.return_value = False

        result = runner.invoke(core_command, ['install'])

        assert result.exit_code == 1
        assert 'failed' in result.output.lower()

    def test_core_install_error(self, mock_core_wp_client, mock_core_ssh, mock_core_config):
        """Test core install with error"""
        runner = CliRunner()

        mock_core_wp_client.install_core.side_effect = Exception('Installation error')

        result = runner.invoke(core_command, ['install'])

        assert result.exit_code == 1
        assert 'error' in result.output.lower()


class TestCoreVerify:
    """Test core verify command"""

    def test_core_verify_success(self, mock_core_wp_client, mock_core_ssh, mock_core_config):
        """Test successful core verify"""
        runner = CliRunner()

        mock_core_wp_client.verify_core.return_value = True

        result = runner.invoke(core_command, ['verify'])

        assert result.exit_code == 0
        assert 'valid' in result.output.lower()
        mock_core_wp_client.verify_core.assert_called_once()

    def test_core_verify_invalid(self, mock_core_wp_client, mock_core_ssh, mock_core_config):
        """Test core verify when invalid"""
        runner = CliRunner()

        mock_core_wp_client.verify_core.return_value = False

        result = runner.invoke(core_command, ['verify'])

        assert result.exit_code == 1
        assert 'invalid' in result.output.lower()

    def test_core_verify_with_server(self, mock_core_wp_client, mock_core_ssh, mock_core_config):
        """Test core verify with specific server"""
        runner = CliRunner()

        mock_core_wp_client.verify_core.return_value = True

        result = runner.invoke(core_command, ['verify', '--server', 'staging'])

        assert result.exit_code == 0
        mock_core_config.get_server.assert_called_once_with('staging')

    def test_core_verify_error(self, mock_core_wp_client, mock_core_ssh, mock_core_config):
        """Test core verify with error"""
        runner = CliRunner()

        mock_core_wp_client.verify_core.side_effect = Exception('Verification error')

        result = runner.invoke(core_command, ['verify'])

        assert result.exit_code == 1
        assert 'error' in result.output.lower()
