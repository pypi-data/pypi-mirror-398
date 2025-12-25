"""Tests for term CLI commands"""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from praisonaiwp.cli.commands.term import term_command


@pytest.fixture
def mock_term_wp_client():
    """Mock WPClient for term tests"""
    with patch('praisonaiwp.cli.commands.term.WPClient') as mock_client:
        client_instance = Mock()
        mock_client.return_value = client_instance
        yield client_instance


@pytest.fixture
def mock_term_ssh():
    """Mock SSHManager for term tests"""
    with patch('praisonaiwp.cli.commands.term.SSHManager') as mock_ssh:
        ssh_instance = Mock()
        mock_ssh.from_config.return_value = ssh_instance
        yield ssh_instance


@pytest.fixture
def mock_term_config():
    """Mock Config for term tests"""
    with patch('praisonaiwp.cli.commands.term.Config') as mock_config:
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


class TestTermList:
    """Test term list command"""

    def test_term_list_success(self, mock_term_wp_client, mock_term_ssh, mock_term_config):
        """Test successful term list"""
        runner = CliRunner()

        mock_term_wp_client.list_terms.return_value = [
            {'term_id': '1', 'name': 'Uncategorized', 'slug': 'uncategorized'},
            {'term_id': '2', 'name': 'Technology', 'slug': 'technology'}
        ]

        result = runner.invoke(term_command, ['list', 'category'])

        assert result.exit_code == 0
        assert 'Uncategorized' in result.output
        assert 'Technology' in result.output
        mock_term_wp_client.list_terms.assert_called_once_with('category')

    def test_term_list_empty(self, mock_term_wp_client, mock_term_ssh, mock_term_config):
        """Test term list when no terms found"""
        runner = CliRunner()

        mock_term_wp_client.list_terms.return_value = []

        result = runner.invoke(term_command, ['list', 'category'])

        assert result.exit_code == 0
        assert 'no terms' in result.output.lower()

    def test_term_list_with_server(self, mock_term_wp_client, mock_term_ssh, mock_term_config):
        """Test term list with specific server"""
        runner = CliRunner()

        mock_term_wp_client.list_terms.return_value = [{'term_id': '1', 'name': 'Test Term'}]

        result = runner.invoke(term_command, ['list', 'category', '--server', 'staging'])

        assert result.exit_code == 0
        mock_term_config.get_server.assert_called_once_with('staging')

    def test_term_list_error(self, mock_term_wp_client, mock_term_ssh, mock_term_config):
        """Test term list with error"""
        runner = CliRunner()

        mock_term_wp_client.list_terms.side_effect = Exception('Connection error')

        result = runner.invoke(term_command, ['list', 'category'])

        assert result.exit_code == 1
        assert 'error' in result.output.lower()


class TestTermGet:
    """Test term get command"""

    def test_term_get_success(self, mock_term_wp_client, mock_term_ssh, mock_term_config):
        """Test successful term get"""
        runner = CliRunner()

        mock_term_wp_client.get_term.return_value = {
            'term_id': '1',
            'name': 'Uncategorized',
            'slug': 'uncategorized',
            'taxonomy': 'category'
        }

        result = runner.invoke(term_command, ['get', 'category', '1'])

        assert result.exit_code == 0
        assert 'Uncategorized' in result.output
        mock_term_wp_client.get_term.assert_called_once_with('category', '1')

    def test_term_get_not_found(self, mock_term_wp_client, mock_term_ssh, mock_term_config):
        """Test term get when term not found"""
        runner = CliRunner()

        mock_term_wp_client.get_term.return_value = None

        result = runner.invoke(term_command, ['get', 'category', '999'])

        assert result.exit_code == 0
        assert 'not found' in result.output.lower()

    def test_term_get_with_server(self, mock_term_wp_client, mock_term_ssh, mock_term_config):
        """Test term get with specific server"""
        runner = CliRunner()

        mock_term_wp_client.get_term.return_value = {'term_id': '1', 'name': 'Test Term'}

        result = runner.invoke(term_command, ['get', 'category', '1', '--server', 'staging'])

        assert result.exit_code == 0
        mock_term_config.get_server.assert_called_once_with('staging')

    def test_term_get_error(self, mock_term_wp_client, mock_term_ssh, mock_term_config):
        """Test term get with error"""
        runner = CliRunner()

        mock_term_wp_client.get_term.side_effect = Exception('Connection error')

        result = runner.invoke(term_command, ['get', 'category', '1'])

        assert result.exit_code == 1
        assert 'error' in result.output.lower()


class TestTermCreate:
    """Test term create command"""

    def test_term_create_success(self, mock_term_wp_client, mock_term_ssh, mock_term_config):
        """Test successful term create"""
        runner = CliRunner()

        mock_term_wp_client.create_term.return_value = {'term_id': '3', 'name': 'New Category', 'slug': 'new-category'}

        result = runner.invoke(term_command, ['create', 'category', 'New Category'])

        assert result.exit_code == 0
        assert 'success' in result.output.lower()
        assert 'New Category' in result.output
        mock_term_wp_client.create_term.assert_called_once_with('category', 'New Category', None, None, None)

    def test_term_create_with_slug(self, mock_term_wp_client, mock_term_ssh, mock_term_config):
        """Test term create with slug"""
        runner = CliRunner()

        mock_term_wp_client.create_term.return_value = {'term_id': '3', 'name': 'New Category', 'slug': 'custom-slug'}

        result = runner.invoke(term_command, ['create', 'category', 'New Category', '--slug', 'custom-slug'])

        assert result.exit_code == 0
        mock_term_wp_client.create_term.assert_called_once_with('category', 'New Category', 'custom-slug', None, None)

    def test_term_create_with_parent(self, mock_term_wp_client, mock_term_ssh, mock_term_config):
        """Test term create with parent"""
        runner = CliRunner()

        mock_term_wp_client.create_term.return_value = {'term_id': '3', 'name': 'Child Category', 'slug': 'child-category'}

        result = runner.invoke(term_command, ['create', 'category', 'Child Category', '--parent', '1'])

        assert result.exit_code == 0
        mock_term_wp_client.create_term.assert_called_once_with('category', 'Child Category', None, '1', None)

    def test_term_create_failure(self, mock_term_wp_client, mock_term_ssh, mock_term_config):
        """Test term create when operation fails"""
        runner = CliRunner()

        mock_term_wp_client.create_term.return_value = None

        result = runner.invoke(term_command, ['create', 'category', 'New Category'])

        assert result.exit_code == 1
        assert 'failed' in result.output.lower()

    def test_term_create_error(self, mock_term_wp_client, mock_term_ssh, mock_term_config):
        """Test term create with error"""
        runner = CliRunner()

        mock_term_wp_client.create_term.side_effect = Exception('Creation error')

        result = runner.invoke(term_command, ['create', 'category', 'New Category'])

        assert result.exit_code == 1
        assert 'error' in result.output.lower()


class TestTermDelete:
    """Test term delete command"""

    def test_term_delete_success(self, mock_term_wp_client, mock_term_ssh, mock_term_config):
        """Test successful term delete"""
        runner = CliRunner()

        mock_term_wp_client.delete_term.return_value = True

        result = runner.invoke(term_command, ['delete', 'category', '1'])

        assert result.exit_code == 0
        assert 'success' in result.output.lower()
        mock_term_wp_client.delete_term.assert_called_once_with('category', '1')

    def test_term_delete_failure(self, mock_term_wp_client, mock_term_ssh, mock_term_config):
        """Test term delete when operation fails"""
        runner = CliRunner()

        mock_term_wp_client.delete_term.return_value = False

        result = runner.invoke(term_command, ['delete', 'category', '1'])

        assert result.exit_code == 1
        assert 'failed' in result.output.lower()

    def test_term_delete_with_server(self, mock_term_wp_client, mock_term_ssh, mock_term_config):
        """Test term delete with specific server"""
        runner = CliRunner()

        mock_term_wp_client.delete_term.return_value = True

        result = runner.invoke(term_command, ['delete', 'category', '1', '--server', 'staging'])

        assert result.exit_code == 0
        mock_term_config.get_server.assert_called_once_with('staging')

    def test_term_delete_error(self, mock_term_wp_client, mock_term_ssh, mock_term_config):
        """Test term delete with error"""
        runner = CliRunner()

        mock_term_wp_client.delete_term.side_effect = Exception('Deletion error')

        result = runner.invoke(term_command, ['delete', 'category', '1'])

        assert result.exit_code == 1
        assert 'error' in result.output.lower()
