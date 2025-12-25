"""Tests for meta CLI commands (post and user meta)"""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from praisonaiwp.cli.commands.meta import meta_command


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_wp_client():
    with patch('praisonaiwp.cli.commands.meta.WPClient') as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


@pytest.fixture
def mock_ssh():
    with patch('praisonaiwp.cli.commands.meta.SSHManager') as mock:
        yield mock


@pytest.fixture
def mock_config():
    with patch('praisonaiwp.cli.commands.meta.Config') as mock:
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


class TestPostMetaGet:
    def test_post_meta_get_success(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test getting post meta value"""
        mock_wp_client.get_post_meta.return_value = "test_value"

        result = runner.invoke(meta_command, ['post-get', '123', 'custom_field'])

        assert result.exit_code == 0
        assert "test_value" in result.output
        mock_wp_client.get_post_meta.assert_called_once_with(123, 'custom_field')

    def test_post_meta_get_all(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test getting all post meta"""
        mock_wp_client.get_post_meta.return_value = [
            {'meta_key': 'field1', 'meta_value': 'value1'},
            {'meta_key': 'field2', 'meta_value': 'value2'}
        ]

        result = runner.invoke(meta_command, ['post-get', '123'])

        assert result.exit_code == 0
        mock_wp_client.get_post_meta.assert_called_once_with(123, None)


class TestPostMetaSet:
    def test_post_meta_set_success(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test setting post meta value"""
        mock_wp_client.set_post_meta.return_value = True

        result = runner.invoke(meta_command, ['post-set', '123', 'custom_field', 'test_value'])

        assert result.exit_code == 0
        assert "Set meta" in result.output or "✓" in result.output
        mock_wp_client.set_post_meta.assert_called_once_with(123, 'custom_field', 'test_value')


class TestPostMetaUpdate:
    def test_post_meta_update_success(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test updating post meta value"""
        mock_wp_client.update_post_meta.return_value = True

        result = runner.invoke(meta_command, ['post-update', '123', 'custom_field', 'new_value'])

        assert result.exit_code == 0
        assert "Updated meta" in result.output or "✓" in result.output
        mock_wp_client.update_post_meta.assert_called_once_with(123, 'custom_field', 'new_value')


class TestPostMetaDelete:
    def test_post_meta_delete_success(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test deleting post meta"""
        mock_wp_client.delete_post_meta.return_value = True

        result = runner.invoke(meta_command, ['post-delete', '123', 'custom_field'])

        assert result.exit_code == 0
        assert "Deleted meta" in result.output or "✓" in result.output
        mock_wp_client.delete_post_meta.assert_called_once_with(123, 'custom_field')


class TestUserMetaGet:
    def test_user_meta_get_success(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test getting user meta value"""
        mock_wp_client.get_user_meta.return_value = "test_value"

        result = runner.invoke(meta_command, ['user-get', '456', 'user_field'])

        assert result.exit_code == 0
        assert "test_value" in result.output
        mock_wp_client.get_user_meta.assert_called_once_with(456, 'user_field')

    def test_user_meta_get_all(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test getting all user meta"""
        mock_wp_client.get_user_meta.return_value = [
            {'meta_key': 'field1', 'meta_value': 'value1'},
            {'meta_key': 'field2', 'meta_value': 'value2'}
        ]

        result = runner.invoke(meta_command, ['user-get', '456'])

        assert result.exit_code == 0
        mock_wp_client.get_user_meta.assert_called_once_with(456, None)


class TestUserMetaSet:
    def test_user_meta_set_success(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test setting user meta value"""
        mock_wp_client.set_user_meta.return_value = True

        result = runner.invoke(meta_command, ['user-set', '456', 'user_field', 'test_value'])

        assert result.exit_code == 0
        assert "Set meta" in result.output or "✓" in result.output
        mock_wp_client.set_user_meta.assert_called_once_with(456, 'user_field', 'test_value')


class TestUserMetaUpdate:
    def test_user_meta_update_success(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test updating user meta value"""
        mock_wp_client.update_user_meta.return_value = True

        result = runner.invoke(meta_command, ['user-update', '456', 'user_field', 'new_value'])

        assert result.exit_code == 0
        assert "Updated meta" in result.output or "✓" in result.output
        mock_wp_client.update_user_meta.assert_called_once_with(456, 'user_field', 'new_value')


class TestUserMetaDelete:
    def test_user_meta_delete_success(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test deleting user meta"""
        mock_wp_client.delete_user_meta.return_value = True

        result = runner.invoke(meta_command, ['user-delete', '456', 'user_field'])

        assert result.exit_code == 0
        assert "Deleted meta" in result.output or "✓" in result.output
        mock_wp_client.delete_user_meta.assert_called_once_with(456, 'user_field')
