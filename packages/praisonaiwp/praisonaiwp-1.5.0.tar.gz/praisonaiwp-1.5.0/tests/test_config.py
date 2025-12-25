"""Tests for configuration management"""

import sys

import pytest

from praisonaiwp.core.config import Config
from praisonaiwp.utils.exceptions import ConfigNotFoundError


class TestConfig:
    """Test Config functionality"""

    def test_initialize_default_config(self, temp_config_dir):
        """Test initializing default configuration"""
        config = Config(str(temp_config_dir / "config.yaml"))
        config.initialize_default_config()

        assert config.data['version'] == '1.0'
        assert 'servers' in config.data
        assert 'settings' in config.data
        assert config.data['settings']['auto_backup'] is True

    def test_save_and_load_config(self, temp_config_dir):
        """Test saving and loading configuration"""
        config_path = str(temp_config_dir / "config.yaml")

        # Create and save
        config = Config(config_path)
        config.initialize_default_config()
        config.save()

        # Load
        config2 = Config(config_path)
        assert config2.data == config.data

    def test_add_server(self, temp_config_dir):
        """Test adding server configuration"""
        config = Config(str(temp_config_dir / "config.yaml"))
        config.initialize_default_config()

        server_config = {
            'hostname': 'example.com',
            'username': 'user',
            'key_file': '~/.ssh/id_rsa',
            'wp_path': '/var/www/html'
        }

        config.add_server('production', server_config)

        assert 'production' in config.data['servers']
        assert config.data['servers']['production'] == server_config
        # Default server remains 'default' unless explicitly changed
        assert config.data['default_server'] == 'default'

    def test_get_server(self, sample_config):
        """Test getting server configuration"""
        server = sample_config.get_server('test')

        assert server['hostname'] == 'test.example.com'
        assert server['username'] == 'testuser'

    def test_get_server_default(self, sample_config):
        """Test getting default server"""
        # sample_config has default_server='default' but no 'default' server configured
        # So we need to either set default_server to 'test' or expect an error
        sample_config.data['default_server'] = 'test'
        server = sample_config.get_server()

        assert server is not None
        assert 'hostname' in server
        assert server['hostname'] == 'test.example.com'

    def test_get_server_not_found(self, sample_config):
        """Test getting non-existent server"""
        with pytest.raises(ConfigNotFoundError):
            sample_config.get_server('nonexistent')

    def test_list_servers(self, sample_config):
        """Test listing servers"""
        servers = sample_config.list_servers()

        assert 'test' in servers
        assert len(servers) >= 1

    def test_get_setting(self, sample_config):
        """Test getting setting"""
        auto_backup = sample_config.get_setting('auto_backup')
        assert auto_backup is True

        # Test default value
        custom = sample_config.get_setting('custom_setting', 'default')
        assert custom == 'default'

    def test_set_setting(self, sample_config):
        """Test setting value"""
        sample_config.set_setting('test_key', 'test_value')

        assert sample_config.get_setting('test_key') == 'test_value'

    def test_config_not_found(self, temp_config_dir):
        """Test loading non-existent config"""
        config = Config(str(temp_config_dir / "nonexistent.yaml"))

        with pytest.raises(ConfigNotFoundError):
            config._load_config()

    @pytest.mark.skipif(sys.platform == "win32", reason="File permissions work differently on Windows")
    def test_config_file_permissions(self, temp_config_dir):
        """Test config file has correct permissions (Unix only)"""
        config_path = temp_config_dir / "config.yaml"

        config = Config(str(config_path))
        config.initialize_default_config()
        config.save()

        # Check file permissions (should be 600)
        import stat
        mode = config_path.stat().st_mode
        assert stat.S_IMODE(mode) == 0o600

    def test_ssh_host_config(self, temp_config_dir, monkeypatch):
        """Test loading SSH config host"""
        import subprocess

        # Mock ssh -G output
        mock_ssh_output = """hostname christsong.in
user praison
port 22
identityfile ~/.ssh/id_ed25519
"""

        def mock_run(*args, **kwargs):
            class MockResult:
                stdout = mock_ssh_output
                returncode = 0
            return MockResult()

        monkeypatch.setattr(subprocess, 'run', mock_run)

        config = Config(str(temp_config_dir / "config.yaml"))
        config.initialize_default_config()

        # Add server with ssh_host
        config.add_server('test_ssh', {
            'ssh_host': 'ionos',
            'wp_path': '/var/www/html',
            'wp_cli': '/usr/local/bin/wp'
        })

        # Get server config - should merge SSH config
        server = config.get_server('test_ssh')

        assert server['hostname'] == 'christsong.in'
        assert server['username'] == 'praison'
        assert server['port'] == 22
        assert 'id_ed25519' in server['key_file']
        assert server['wp_path'] == '/var/www/html'
