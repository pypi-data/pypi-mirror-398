"""Tests for category CLI commands"""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from praisonaiwp.cli.commands.category import category_command


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_wp_client():
    with patch('praisonaiwp.cli.commands.category.WPClient') as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


@pytest.fixture
def mock_ssh():
    with patch('praisonaiwp.cli.commands.category.SSHManager') as mock:
        yield mock


@pytest.fixture
def mock_config():
    with patch('praisonaiwp.cli.commands.category.Config') as mock:
        config = MagicMock()
        config.get_server.return_value = {
            'hostname': 'test.com',
            'username': 'testuser',
            'wp_path': '/var/www/html',
            'php_bin': 'php',
            'wp_cli': '/usr/local/bin/wp'
        }
        mock.return_value = config
        yield config


class TestCategoryCreate:
    def test_category_create_success(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test creating a category"""
        mock_wp_client.create_category.return_value = 123

        result = runner.invoke(category_command, ['create', 'Technology'])

        assert result.exit_code == 0
        assert "123" in result.output
        assert "Created" in result.output
        mock_wp_client.create_category.assert_called_once_with(
            name='Technology',
            slug=None,
            description=None,
            parent=None
        )

    def test_category_create_with_options(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test creating a category with all options"""
        mock_wp_client.create_category.return_value = 456

        result = runner.invoke(category_command, [
            'create', 'AI',
            '--slug', 'artificial-intelligence',
            '--description', 'AI related posts',
            '--parent', '123'
        ])

        assert result.exit_code == 0
        mock_wp_client.create_category.assert_called_once_with(
            name='AI',
            slug='artificial-intelligence',
            description='AI related posts',
            parent=123
        )


class TestCategoryUpdate:
    def test_category_update_success(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test updating a category"""
        mock_wp_client.update_category.return_value = True

        result = runner.invoke(category_command, [
            'update', '123',
            '--name', 'New Name'
        ])

        assert result.exit_code == 0
        assert "Updated" in result.output
        mock_wp_client.update_category.assert_called_once_with(
            category_id=123,
            name='New Name',
            slug=None,
            description=None,
            parent=None
        )

    def test_category_update_multiple_fields(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test updating multiple category fields"""
        mock_wp_client.update_category.return_value = True

        result = runner.invoke(category_command, [
            'update', '123',
            '--name', 'AI',
            '--slug', 'artificial-intelligence',
            '--description', 'Updated description'
        ])

        assert result.exit_code == 0
        mock_wp_client.update_category.assert_called_once_with(
            category_id=123,
            name='AI',
            slug='artificial-intelligence',
            description='Updated description',
            parent=None
        )


class TestCategoryDelete:
    def test_category_delete_success(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test deleting a category"""
        mock_wp_client.delete_category.return_value = True

        result = runner.invoke(category_command, ['delete', '123'], input='y\n')

        assert result.exit_code == 0
        assert "Deleted" in result.output
        mock_wp_client.delete_category.assert_called_once_with(123)

    def test_category_delete_cancelled(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test cancelling category deletion"""
        result = runner.invoke(category_command, ['delete', '123'], input='n\n')

        assert result.exit_code == 1
        mock_wp_client.delete_category.assert_not_called()


class TestCategoryExistingCommands:
    """Test existing category commands still work"""

    def test_category_set_success(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test setting categories (existing command)"""
        mock_wp_client.get_category_by_name.return_value = {'term_id': '123', 'name': 'Technology'}
        mock_wp_client.get_category_by_id.return_value = {'term_id': '123', 'name': 'Technology'}
        mock_wp_client.set_post_categories.return_value = True

        result = runner.invoke(category_command, [
            'set', '456',
            '--category', 'Technology'
        ])

        assert result.exit_code == 0

    def test_category_add_success(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test adding categories (existing command)"""
        mock_wp_client.get_category_by_name.return_value = {'term_id': '123', 'name': 'Technology'}
        mock_wp_client.get_category_by_id.return_value = {'term_id': '123', 'name': 'Technology'}
        mock_wp_client.add_post_categories.return_value = True

        result = runner.invoke(category_command, [
            'add', '456',
            '--category', 'Technology'
        ])

        assert result.exit_code == 0

    def test_category_list_success(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test listing categories (existing command)"""
        mock_wp_client.list_categories.return_value = [
            {'term_id': '123', 'name': 'Technology', 'slug': 'tech', 'parent': '0', 'count': '5'}
        ]

        result = runner.invoke(category_command, ['list'])

        assert result.exit_code == 0
