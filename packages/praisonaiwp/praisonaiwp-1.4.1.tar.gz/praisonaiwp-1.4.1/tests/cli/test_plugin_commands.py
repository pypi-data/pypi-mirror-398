"""Tests for plugin CLI commands"""

import pytest
from click.testing import CliRunner
from unittest.mock import Mock, patch, MagicMock
from praisonaiwp.cli.commands.plugin import plugin


@pytest.fixture
def runner():
    """Create CLI runner"""
    return CliRunner()


@pytest.fixture
def mock_config():
    """Mock Config class"""
    with patch('praisonaiwp.cli.commands.plugin.Config') as mock:
        config_instance = Mock()
        config_instance.get_server.return_value = {
            'hostname': 'test.com',
            'username': 'testuser',
            'key_file': '~/.ssh/id_rsa',
            'port': 22,
            'wp_path': '/var/www/html',
            'php_bin': 'php',
            'wp_cli': '/usr/local/bin/wp'
        }
        mock.return_value = config_instance
        yield mock


@pytest.fixture
def mock_ssh():
    """Mock SSHManager"""
    with patch('praisonaiwp.cli.commands.plugin.SSHManager') as mock:
        ssh_instance = MagicMock()
        ssh_instance.__enter__.return_value = ssh_instance
        ssh_instance.__exit__.return_value = None
        mock.return_value = ssh_instance
        yield ssh_instance


@pytest.fixture
def mock_wp_client():
    """Mock WPClient"""
    with patch('praisonaiwp.cli.commands.plugin.WPClient') as mock:
        wp_instance = Mock()
        mock.return_value = wp_instance
        yield wp_instance


class TestPluginListCommand:
    """Test plugin list command"""
    
    def test_list_all_plugins(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test listing all plugins"""
        mock_wp_client.list_plugins.return_value = [
            {'name': 'akismet', 'status': 'active', 'version': '5.0', 'update': 'none'},
            {'name': 'hello', 'status': 'inactive', 'version': '1.7', 'update': 'none'}
        ]
        
        result = runner.invoke(plugin, ['list'])
        
        assert result.exit_code == 0
        assert 'akismet' in result.output
        assert 'hello' in result.output
        mock_wp_client.list_plugins.assert_called_once()
    
    def test_list_active_plugins(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test listing only active plugins"""
        mock_wp_client.list_plugins.return_value = [
            {'name': 'akismet', 'status': 'active', 'version': '5.0', 'update': 'none'}
        ]
        
        result = runner.invoke(plugin, ['list', '--status', 'active'])
        
        assert result.exit_code == 0
        assert 'akismet' in result.output
        mock_wp_client.list_plugins.assert_called_once_with(status='active')
    
    def test_list_no_plugins(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test listing when no plugins found"""
        mock_wp_client.list_plugins.return_value = []
        
        result = runner.invoke(plugin, ['list'])
        
        assert result.exit_code == 0
        assert 'No plugins found' in result.output
    
    def test_list_plugins_with_updates(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test listing plugins with available updates"""
        mock_wp_client.list_plugins.return_value = [
            {'name': 'akismet', 'status': 'active', 'version': '5.0', 'update': '5.1'}
        ]
        
        result = runner.invoke(plugin, ['list'])
        
        assert result.exit_code == 0
        assert 'UPDATE AVAILABLE' in result.output


class TestPluginUpdateCommand:
    """Test plugin update command"""
    
    def test_update_all_plugins(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test updating all plugins"""
        mock_wp_client.update_plugin.return_value = True
        
        result = runner.invoke(plugin, ['update', 'all'])
        
        assert result.exit_code == 0
        assert 'Successfully updated' in result.output
        mock_wp_client.update_plugin.assert_called_once_with('all')
    
    def test_update_single_plugin(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test updating a single plugin"""
        mock_wp_client.update_plugin.return_value = True
        
        result = runner.invoke(plugin, ['update', 'akismet'])
        
        assert result.exit_code == 0
        assert 'Successfully updated' in result.output
        assert 'akismet' in result.output
        mock_wp_client.update_plugin.assert_called_once_with('akismet')
    
    def test_update_plugin_error(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test update plugin with error"""
        mock_wp_client.update_plugin.side_effect = Exception("Update failed")
        
        result = runner.invoke(plugin, ['update', 'akismet'])
        
        assert result.exit_code == 1
        assert 'Error' in result.output


class TestPluginActivateCommand:
    """Test plugin activate command"""
    
    def test_activate_plugin(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test activating a plugin"""
        mock_wp_client.activate_plugin.return_value = True
        
        result = runner.invoke(plugin, ['activate', 'akismet'])
        
        assert result.exit_code == 0
        assert 'Successfully activated' in result.output
        assert 'akismet' in result.output
        mock_wp_client.activate_plugin.assert_called_once_with('akismet')
    
    def test_activate_plugin_error(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test activate plugin with error"""
        mock_wp_client.activate_plugin.side_effect = Exception("Activation failed")
        
        result = runner.invoke(plugin, ['activate', 'akismet'])
        
        assert result.exit_code == 1
        assert 'Error' in result.output


class TestPluginDeactivateCommand:
    """Test plugin deactivate command"""
    
    def test_deactivate_plugin(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test deactivating a plugin"""
        mock_wp_client.deactivate_plugin.return_value = True
        
        result = runner.invoke(plugin, ['deactivate', 'akismet'])
        
        assert result.exit_code == 0
        assert 'Successfully deactivated' in result.output
        assert 'akismet' in result.output
        mock_wp_client.deactivate_plugin.assert_called_once_with('akismet')
    
    def test_deactivate_plugin_error(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test deactivate plugin with error"""
        mock_wp_client.deactivate_plugin.side_effect = Exception("Deactivation failed")
        
        result = runner.invoke(plugin, ['deactivate', 'akismet'])
        
        assert result.exit_code == 1
        assert 'Error' in result.output


class TestPluginCommandIntegration:
    """Integration tests for plugin commands"""
    
    def test_plugin_help(self, runner):
        """Test plugin help command"""
        result = runner.invoke(plugin, ['--help'])
        
        assert result.exit_code == 0
        assert 'Manage WordPress plugins' in result.output
        assert 'list' in result.output
        assert 'update' in result.output
        assert 'activate' in result.output
        assert 'deactivate' in result.output
    
    def test_list_help(self, runner):
        """Test plugin list help"""
        result = runner.invoke(plugin, ['list', '--help'])
        
        assert result.exit_code == 0
        assert 'List installed WordPress plugins' in result.output
    
    def test_update_help(self, runner):
        """Test plugin update help"""
        result = runner.invoke(plugin, ['update', '--help'])
        
        assert result.exit_code == 0
        assert 'Update WordPress plugin' in result.output
