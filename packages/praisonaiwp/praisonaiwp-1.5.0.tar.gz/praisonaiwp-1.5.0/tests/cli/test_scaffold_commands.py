"""Tests for scaffold CLI commands"""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from praisonaiwp.cli.commands.scaffold import scaffold_command


@pytest.fixture
def mock_scaffold_wp_client():
    """Mock WPClient for scaffold tests"""
    with patch('praisonaiwp.cli.commands.scaffold.WPClient') as mock_client:
        client_instance = Mock()
        mock_client.return_value = client_instance
        yield client_instance


@pytest.fixture
def mock_scaffold_ssh():
    """Mock SSHManager for scaffold tests"""
    with patch('praisonaiwp.cli.commands.scaffold.SSHManager') as mock_ssh:
        ssh_instance = Mock()
        mock_ssh.from_config.return_value = ssh_instance
        yield ssh_instance


@pytest.fixture
def mock_scaffold_config():
    """Mock Config for scaffold tests"""
    with patch('praisonaiwp.cli.commands.scaffold.Config') as mock_config:
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


class TestScaffoldPostType:
    """Test scaffold post-type command"""

    def test_scaffold_post_type_success(self, mock_scaffold_wp_client, mock_scaffold_ssh, mock_scaffold_config):
        """Test successful post type scaffold"""
        runner = CliRunner()

        mock_scaffold_wp_client.scaffold_post_type.return_value = True

        result = runner.invoke(scaffold_command, ['post-type', 'book'])

        assert result.exit_code == 0
        assert 'success' in result.output.lower()
        assert 'book' in result.output
        mock_scaffold_wp_client.scaffold_post_type.assert_called_once_with('book', None, None, None, None)

    def test_scaffold_post_type_with_options(self, mock_scaffold_wp_client, mock_scaffold_ssh, mock_scaffold_config):
        """Test post type scaffold with options"""
        runner = CliRunner()

        mock_scaffold_wp_client.scaffold_post_type.return_value = True

        result = runner.invoke(scaffold_command, [
            'post-type', 'book',
            '--label', 'Books',
            '--public', 'true',
            '--has_archive', 'true',
            '--supports', 'title,editor'
        ])

        assert result.exit_code == 0
        mock_scaffold_wp_client.scaffold_post_type.assert_called_once_with(
            'book', 'Books', 'true', 'true', 'title,editor'
        )

    def test_scaffold_post_type_with_server(self, mock_scaffold_wp_client, mock_scaffold_ssh, mock_scaffold_config):
        """Test post type scaffold with specific server"""
        runner = CliRunner()

        mock_scaffold_wp_client.scaffold_post_type.return_value = True

        result = runner.invoke(scaffold_command, ['post-type', 'book', '--server', 'staging'])

        assert result.exit_code == 0
        mock_scaffold_config.get_server.assert_called_once_with('staging')

    def test_scaffold_post_type_failure(self, mock_scaffold_wp_client, mock_scaffold_ssh, mock_scaffold_config):
        """Test post type scaffold when operation fails"""
        runner = CliRunner()

        mock_scaffold_wp_client.scaffold_post_type.return_value = False

        result = runner.invoke(scaffold_command, ['post-type', 'book'])

        assert result.exit_code == 1
        assert 'failed' in result.output.lower()

    def test_scaffold_post_type_error(self, mock_scaffold_wp_client, mock_scaffold_ssh, mock_scaffold_config):
        """Test post type scaffold with error"""
        runner = CliRunner()

        mock_scaffold_wp_client.scaffold_post_type.side_effect = Exception('Scaffold error')

        result = runner.invoke(scaffold_command, ['post-type', 'book'])

        assert result.exit_code == 1
        assert 'error' in result.output.lower()


class TestScaffoldTaxonomy:
    """Test scaffold taxonomy command"""

    def test_scaffold_taxonomy_success(self, mock_scaffold_wp_client, mock_scaffold_ssh, mock_scaffold_config):
        """Test successful taxonomy scaffold"""
        runner = CliRunner()

        mock_scaffold_wp_client.scaffold_taxonomy.return_value = True

        result = runner.invoke(scaffold_command, ['taxonomy', 'genre'])

        assert result.exit_code == 0
        assert 'success' in result.output.lower()
        assert 'genre' in result.output
        mock_scaffold_wp_client.scaffold_taxonomy.assert_called_once_with('genre', None, None, None, None)

    def test_scaffold_taxonomy_with_options(self, mock_scaffold_wp_client, mock_scaffold_ssh, mock_scaffold_config):
        """Test taxonomy scaffold with options"""
        runner = CliRunner()

        mock_scaffold_wp_client.scaffold_taxonomy.return_value = True

        result = runner.invoke(scaffold_command, [
            'taxonomy', 'genre',
            '--label', 'Genres',
            '--public', 'true',
            '--hierarchical', 'true',
            '--post_types', 'book'
        ])

        assert result.exit_code == 0
        mock_scaffold_wp_client.scaffold_taxonomy.assert_called_once_with(
            'genre', 'Genres', 'true', 'true', 'book'
        )

    def test_scaffold_taxonomy_with_server(self, mock_scaffold_wp_client, mock_scaffold_ssh, mock_scaffold_config):
        """Test taxonomy scaffold with specific server"""
        runner = CliRunner()

        mock_scaffold_wp_client.scaffold_taxonomy.return_value = True

        result = runner.invoke(scaffold_command, ['taxonomy', 'genre', '--server', 'staging'])

        assert result.exit_code == 0
        mock_scaffold_config.get_server.assert_called_once_with('staging')

    def test_scaffold_taxonomy_failure(self, mock_scaffold_wp_client, mock_scaffold_ssh, mock_scaffold_config):
        """Test taxonomy scaffold when operation fails"""
        runner = CliRunner()

        mock_scaffold_wp_client.scaffold_taxonomy.return_value = False

        result = runner.invoke(scaffold_command, ['taxonomy', 'genre'])

        assert result.exit_code == 1
        assert 'failed' in result.output.lower()

    def test_scaffold_taxonomy_error(self, mock_scaffold_wp_client, mock_scaffold_ssh, mock_scaffold_config):
        """Test taxonomy scaffold with error"""
        runner = CliRunner()

        mock_scaffold_wp_client.scaffold_taxonomy.side_effect = Exception('Scaffold error')

        result = runner.invoke(scaffold_command, ['taxonomy', 'genre'])

        assert result.exit_code == 1
        assert 'error' in result.output.lower()


class TestScaffoldPlugin:
    """Test scaffold plugin command"""

    def test_scaffold_plugin_success(self, mock_scaffold_wp_client, mock_scaffold_ssh, mock_scaffold_config):
        """Test successful plugin scaffold"""
        runner = CliRunner()

        mock_scaffold_wp_client.scaffold_plugin.return_value = True

        result = runner.invoke(scaffold_command, ['plugin', 'my-plugin'])

        assert result.exit_code == 0
        assert 'success' in result.output.lower()
        assert 'my-plugin' in result.output
        mock_scaffold_wp_client.scaffold_plugin.assert_called_once_with('my-plugin', None, None, None)

    def test_scaffold_plugin_with_options(self, mock_scaffold_wp_client, mock_scaffold_ssh, mock_scaffold_config):
        """Test plugin scaffold with options"""
        runner = CliRunner()

        mock_scaffold_wp_client.scaffold_plugin.return_value = True

        result = runner.invoke(scaffold_command, [
            'plugin', 'my-plugin',
            '--plugin_name', 'My Plugin',
            '--plugin_uri', 'https://example.com',
            '--author', 'Test Author'
        ])

        assert result.exit_code == 0
        mock_scaffold_wp_client.scaffold_plugin.assert_called_once_with(
            'my-plugin', 'My Plugin', 'https://example.com', 'Test Author'
        )

    def test_scaffold_plugin_with_server(self, mock_scaffold_wp_client, mock_scaffold_ssh, mock_scaffold_config):
        """Test plugin scaffold with specific server"""
        runner = CliRunner()

        mock_scaffold_wp_client.scaffold_plugin.return_value = True

        result = runner.invoke(scaffold_command, ['plugin', 'my-plugin', '--server', 'staging'])

        assert result.exit_code == 0
        mock_scaffold_config.get_server.assert_called_once_with('staging')

    def test_scaffold_plugin_failure(self, mock_scaffold_wp_client, mock_scaffold_ssh, mock_scaffold_config):
        """Test plugin scaffold when operation fails"""
        runner = CliRunner()

        mock_scaffold_wp_client.scaffold_plugin.return_value = False

        result = runner.invoke(scaffold_command, ['plugin', 'my-plugin'])

        assert result.exit_code == 1
        assert 'failed' in result.output.lower()

    def test_scaffold_plugin_error(self, mock_scaffold_wp_client, mock_scaffold_ssh, mock_scaffold_config):
        """Test plugin scaffold with error"""
        runner = CliRunner()

        mock_scaffold_wp_client.scaffold_plugin.side_effect = Exception('Scaffold error')

        result = runner.invoke(scaffold_command, ['plugin', 'my-plugin'])

        assert result.exit_code == 1
        assert 'error' in result.output.lower()


class TestScaffoldTheme:
    """Test scaffold theme command"""

    def test_scaffold_theme_success(self, mock_scaffold_wp_client, mock_scaffold_ssh, mock_scaffold_config):
        """Test successful theme scaffold"""
        runner = CliRunner()

        mock_scaffold_wp_client.scaffold_theme.return_value = True

        result = runner.invoke(scaffold_command, ['theme', 'my-theme'])

        assert result.exit_code == 0
        assert 'success' in result.output.lower()
        assert 'my-theme' in result.output
        mock_scaffold_wp_client.scaffold_theme.assert_called_once_with('my-theme', None, None, None, None)

    def test_scaffold_theme_with_options(self, mock_scaffold_wp_client, mock_scaffold_ssh, mock_scaffold_config):
        """Test theme scaffold with options"""
        runner = CliRunner()

        mock_scaffold_wp_client.scaffold_theme.return_value = True

        result = runner.invoke(scaffold_command, [
            'theme', 'my-theme',
            '--theme_name', 'My Theme',
            '--theme_uri', 'https://example.com',
            '--author', 'Test Author',
            '--author_uri', 'https://author.com'
        ])

        assert result.exit_code == 0
        mock_scaffold_wp_client.scaffold_theme.assert_called_once_with(
            'my-theme', 'My Theme', 'https://example.com', 'Test Author', 'https://author.com'
        )

    def test_scaffold_theme_with_server(self, mock_scaffold_wp_client, mock_scaffold_ssh, mock_scaffold_config):
        """Test theme scaffold with specific server"""
        runner = CliRunner()

        mock_scaffold_wp_client.scaffold_theme.return_value = True

        result = runner.invoke(scaffold_command, ['theme', 'my-theme', '--server', 'staging'])

        assert result.exit_code == 0
        mock_scaffold_config.get_server.assert_called_once_with('staging')

    def test_scaffold_theme_failure(self, mock_scaffold_wp_client, mock_scaffold_ssh, mock_scaffold_config):
        """Test theme scaffold when operation fails"""
        runner = CliRunner()

        mock_scaffold_wp_client.scaffold_theme.return_value = False

        result = runner.invoke(scaffold_command, ['theme', 'my-theme'])

        assert result.exit_code == 1
        assert 'failed' in result.output.lower()

    def test_scaffold_theme_error(self, mock_scaffold_wp_client, mock_scaffold_ssh, mock_scaffold_config):
        """Test theme scaffold with error"""
        runner = CliRunner()

        mock_scaffold_wp_client.scaffold_theme.side_effect = Exception('Scaffold error')

        result = runner.invoke(scaffold_command, ['theme', 'my-theme'])

        assert result.exit_code == 1
        assert 'error' in result.output.lower()
