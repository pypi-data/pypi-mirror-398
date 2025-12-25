"""Tests for post utility CLI commands"""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from praisonaiwp.cli.commands.db import db_command
from praisonaiwp.cli.commands.post import post_command


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_wp_client():
    with patch("praisonaiwp.cli.commands.post.WPClient") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


@pytest.fixture
def mock_db_wp_client():
    with patch("praisonaiwp.cli.commands.db.WPClient") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


@pytest.fixture
def mock_ssh():
    with patch("praisonaiwp.cli.commands.post.SSHManager") as mock:
        yield mock


@pytest.fixture
def mock_db_ssh():
    with patch("praisonaiwp.cli.commands.db.SSHManager") as mock:
        yield mock


@pytest.fixture
def mock_config():
    with patch("praisonaiwp.cli.commands.post.Config") as mock:
        config = MagicMock()
        config.get_server.return_value = {
            "hostname": "test.com",
            "username": "testuser",
            "wp_path": "/var/www/html",
            "php_bin": "php",
            "wp_cli": "/usr/local/bin/wp",
        }
        mock.return_value = config
        yield config


@pytest.fixture
def mock_db_config():
    with patch("praisonaiwp.cli.commands.db.Config") as mock:
        config = MagicMock()
        config.get_server.return_value = {
            "hostname": "test.com",
            "username": "testuser",
            "wp_path": "/var/www/html",
            "php_bin": "php",
            "wp_cli": "/usr/local/bin/wp",
        }
        mock.return_value = config
        yield config


class TestPostDelete:
    def test_post_delete_success(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test deleting a post"""
        mock_wp_client.delete_post.return_value = True

        result = runner.invoke(post_command, ["delete", "123"], input="y\n")

        assert result.exit_code == 0
        assert "Deleted" in result.output or "✓" in result.output
        mock_wp_client.delete_post.assert_called_once_with(123)

    def test_post_delete_cancelled(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test cancelling post deletion"""
        result = runner.invoke(post_command, ["delete", "123"], input="n\n")

        assert result.exit_code == 1
        mock_wp_client.delete_post.assert_not_called()


class TestPostExists:
    def test_post_exists_true(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test checking if post exists (true)"""
        mock_wp_client.post_exists.return_value = True

        result = runner.invoke(post_command, ["exists", "123"])

        assert result.exit_code == 0
        assert "exists" in result.output or "✓" in result.output
        mock_wp_client.post_exists.assert_called_once_with(123)

    def test_post_exists_false(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test checking if post exists (false)"""
        mock_wp_client.post_exists.return_value = False

        result = runner.invoke(post_command, ["exists", "999"])

        assert result.exit_code == 1
        assert "does not exist" in result.output or "✗" in result.output


class TestDbQuery:
    def test_db_query_success(self, runner, mock_db_config, mock_db_ssh, mock_db_wp_client):
        """Test database query"""
        mock_db_wp_client.db_query.return_value = [
            {"ID": "123", "post_title": "Test Post", "post_status": "publish"},
            {"ID": "456", "post_title": "Another Post", "post_status": "draft"},
        ]

        result = runner.invoke(
            db_command, ["query", "SELECT * FROM wp_posts WHERE post_status = 'publish'"]
        )

        assert result.exit_code == 0
        mock_db_wp_client.db_query.assert_called_once_with(
            "SELECT * FROM wp_posts WHERE post_status = 'publish'"
        )

    def test_db_query_empty(self, runner, mock_db_config, mock_db_ssh, mock_db_wp_client):
        """Test database query with no results"""
        mock_db_wp_client.db_query.return_value = []

        result = runner.invoke(
            db_command, ["query", "SELECT * FROM wp_posts WHERE post_title = 'nonexistent'"]
        )

        assert result.exit_code == 0
        assert "No results" in result.output

    def test_db_query_with_server(self, runner, mock_db_config, mock_db_ssh, mock_db_wp_client):
        """Test database query with specific server"""
        mock_db_wp_client.db_query.return_value = [{"ID": "123"}]

        result = runner.invoke(
            db_command, ["query", "SELECT COUNT(*) FROM wp_posts", "--server", "production"]
        )

        assert result.exit_code == 0
        mock_db_config.get_server.assert_called_with("production")
