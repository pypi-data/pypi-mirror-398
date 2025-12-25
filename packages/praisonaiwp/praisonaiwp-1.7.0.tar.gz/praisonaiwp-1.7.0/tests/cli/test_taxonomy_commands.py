"""Tests for taxonomy CLI commands"""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from praisonaiwp.cli.commands.taxonomy import taxonomy_command


@pytest.fixture
def mock_taxonomy_wp_client():
    """Mock WPClient for taxonomy tests"""
    with patch('praisonaiwp.cli.commands.taxonomy.WPClient') as mock_client:
        client_instance = Mock()
        mock_client.return_value = client_instance
        yield client_instance


@pytest.fixture
def mock_taxonomy_ssh():
    """Mock SSHManager for taxonomy tests"""
    with patch('praisonaiwp.cli.commands.taxonomy.SSHManager') as mock_ssh:
        ssh_instance = Mock()
        mock_ssh.from_config.return_value = ssh_instance
        yield ssh_instance


@pytest.fixture
def mock_taxonomy_config():
    """Mock Config for taxonomy tests"""
    with patch('praisonaiwp.cli.commands.taxonomy.Config') as mock_config:
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


class TestTaxonomyList:
    """Test taxonomy list command"""

    def test_taxonomy_list_success(self, mock_taxonomy_wp_client, mock_taxonomy_ssh, mock_taxonomy_config):
        """Test successful taxonomy list"""
        runner = CliRunner()

        mock_taxonomy_wp_client.list_taxonomies.return_value = [
            {'name': 'category', 'label': 'Categories', 'hierarchical': True},
            {'name': 'post_tag', 'label': 'Tags', 'hierarchical': False}
        ]

        result = runner.invoke(taxonomy_command, ['list'])

        assert result.exit_code == 0
        assert 'category' in result.output
        assert 'post_tag' in result.output
        mock_taxonomy_wp_client.list_taxonomies.assert_called_once()

    def test_taxonomy_list_empty(self, mock_taxonomy_wp_client, mock_taxonomy_ssh, mock_taxonomy_config):
        """Test taxonomy list when no taxonomies found"""
        runner = CliRunner()

        mock_taxonomy_wp_client.list_taxonomies.return_value = []

        result = runner.invoke(taxonomy_command, ['list'])

        assert result.exit_code == 0
        assert 'no taxonomies' in result.output.lower()

    def test_taxonomy_list_with_server(self, mock_taxonomy_wp_client, mock_taxonomy_ssh, mock_taxonomy_config):
        """Test taxonomy list with specific server"""
        runner = CliRunner()

        mock_taxonomy_wp_client.list_taxonomies.return_value = [{'name': 'category', 'label': 'Categories'}]

        result = runner.invoke(taxonomy_command, ['list', '--server', 'staging'])

        assert result.exit_code == 0
        mock_taxonomy_config.get_server.assert_called_once_with('staging')

    def test_taxonomy_list_error(self, mock_taxonomy_wp_client, mock_taxonomy_ssh, mock_taxonomy_config):
        """Test taxonomy list with error"""
        runner = CliRunner()

        mock_taxonomy_wp_client.list_taxonomies.side_effect = Exception('Connection error')

        result = runner.invoke(taxonomy_command, ['list'])

        assert result.exit_code == 1
        assert 'error' in result.output.lower()


class TestTaxonomyGet:
    """Test taxonomy get command"""

    def test_taxonomy_get_success(self, mock_taxonomy_wp_client, mock_taxonomy_ssh, mock_taxonomy_config):
        """Test successful taxonomy get"""
        runner = CliRunner()

        mock_taxonomy_wp_client.get_taxonomy.return_value = {
            'name': 'category',
            'label': 'Categories',
            'hierarchical': True,
            'public': True
        }

        result = runner.invoke(taxonomy_command, ['get', 'category'])

        assert result.exit_code == 0
        assert 'Categories' in result.output
        assert 'True' in result.output
        mock_taxonomy_wp_client.get_taxonomy.assert_called_once_with('category')

    def test_taxonomy_get_not_found(self, mock_taxonomy_wp_client, mock_taxonomy_ssh, mock_taxonomy_config):
        """Test taxonomy get when taxonomy not found"""
        runner = CliRunner()

        mock_taxonomy_wp_client.get_taxonomy.return_value = None

        result = runner.invoke(taxonomy_command, ['get', 'nonexistent'])

        assert result.exit_code == 0
        assert 'not found' in result.output.lower()

    def test_taxonomy_get_with_server(self, mock_taxonomy_wp_client, mock_taxonomy_ssh, mock_taxonomy_config):
        """Test taxonomy get with specific server"""
        runner = CliRunner()

        mock_taxonomy_wp_client.get_taxonomy.return_value = {'name': 'category', 'label': 'Categories'}

        result = runner.invoke(taxonomy_command, ['get', 'category', '--server', 'staging'])

        assert result.exit_code == 0
        mock_taxonomy_config.get_server.assert_called_once_with('staging')

    def test_taxonomy_get_error(self, mock_taxonomy_wp_client, mock_taxonomy_ssh, mock_taxonomy_config):
        """Test taxonomy get with error"""
        runner = CliRunner()

        mock_taxonomy_wp_client.get_taxonomy.side_effect = Exception('Connection error')

        result = runner.invoke(taxonomy_command, ['get', 'category'])

        assert result.exit_code == 1
        assert 'error' in result.output.lower()
