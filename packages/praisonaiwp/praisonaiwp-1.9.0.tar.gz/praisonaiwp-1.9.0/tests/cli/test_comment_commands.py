"""Tests for comment CLI commands"""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from praisonaiwp.cli.commands.comment import comment_command


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_wp_client():
    with patch('praisonaiwp.cli.commands.comment.WPClient') as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


@pytest.fixture
def mock_ssh():
    with patch('praisonaiwp.cli.commands.comment.SSHManager') as mock:
        yield mock


@pytest.fixture
def mock_config():
    with patch('praisonaiwp.cli.commands.comment.Config') as mock:
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


class TestCommentList:
    def test_comment_list_success(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test listing comments"""
        mock_wp_client.list_comments.return_value = [
            {'comment_ID': '1', 'comment_content': 'Test comment 1', 'comment_approved': '1'},
            {'comment_ID': '2', 'comment_content': 'Test comment 2', 'comment_approved': '0'}
        ]

        result = runner.invoke(comment_command, ['list'])

        assert result.exit_code == 0
        mock_wp_client.list_comments.assert_called_once()

    def test_comment_list_with_post_id(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test listing comments for specific post"""
        mock_wp_client.list_comments.return_value = [
            {'comment_ID': '1', 'comment_content': 'Post comment', 'comment_approved': '1'}
        ]

        result = runner.invoke(comment_command, ['list', '--post-id', '123'])

        assert result.exit_code == 0
        mock_wp_client.list_comments.assert_called_once_with(post_id=123, status=None, number=20)


class TestCommentGet:
    def test_comment_get_success(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test getting a specific comment"""
        mock_wp_client.get_comment.return_value = {
            'comment_ID': '1',
            'comment_content': 'Test comment',
            'comment_approved': '1'
        }

        result = runner.invoke(comment_command, ['get', '1'])

        assert result.exit_code == 0
        mock_wp_client.get_comment.assert_called_once_with(1)


class TestCommentCreate:
    def test_comment_create_success(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test creating a comment"""
        mock_wp_client.create_comment.return_value = 123

        result = runner.invoke(comment_command, [
            'create',
            '--post-id', '456',
            '--content', 'Test comment',
            '--author', 'Test User',
            '--email', 'test@example.com'
        ])

        assert result.exit_code == 0
        assert "123" in result.output
        mock_wp_client.create_comment.assert_called_once()


class TestCommentUpdate:
    def test_comment_update_success(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test updating a comment"""
        mock_wp_client.update_comment.return_value = True

        result = runner.invoke(comment_command, [
            'update', '123',
            '--content', 'Updated comment'
        ])

        assert result.exit_code == 0
        assert "Updated" in result.output or "✓" in result.output
        mock_wp_client.update_comment.assert_called_once()


class TestCommentDelete:
    def test_comment_delete_success(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test deleting a comment"""
        mock_wp_client.delete_comment.return_value = True

        result = runner.invoke(comment_command, ['delete', '123'], input='y\n')

        assert result.exit_code == 0
        assert "Deleted" in result.output or "✓" in result.output
        mock_wp_client.delete_comment.assert_called_once_with(123)

    def test_comment_delete_cancelled(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test cancelling comment deletion"""
        result = runner.invoke(comment_command, ['delete', '123'], input='n\n')

        assert result.exit_code == 1
        mock_wp_client.delete_comment.assert_not_called()


class TestCommentApprove:
    def test_comment_approve_success(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test approving a comment"""
        mock_wp_client.approve_comment.return_value = True

        result = runner.invoke(comment_command, ['approve', '123'])

        assert result.exit_code == 0
        assert "Approved" in result.output or "✓" in result.output
        mock_wp_client.approve_comment.assert_called_once_with(123)

    def test_comment_unapprove_success(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test unapproving a comment"""
        mock_wp_client.unapprove_comment.return_value = True

        result = runner.invoke(comment_command, ['approve', '123', '--unapprove'])

        assert result.exit_code == 0
        assert "Unapproved" in result.output or "✓" in result.output
        mock_wp_client.unapprove_comment.assert_called_once_with(123)
