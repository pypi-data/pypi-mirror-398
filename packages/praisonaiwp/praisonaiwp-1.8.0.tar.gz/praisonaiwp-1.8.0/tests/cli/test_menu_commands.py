"""Tests for menu CLI commands"""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from praisonaiwp.cli.commands.menu import menu_command


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_wp_client():
    with patch("praisonaiwp.cli.commands.menu.WPClient") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


@pytest.fixture
def mock_ssh():
    with patch("praisonaiwp.cli.commands.menu.SSHManager") as mock:
        yield mock


@pytest.fixture
def mock_config():
    with patch("praisonaiwp.cli.commands.menu.Config") as mock:
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


class TestMenuList:
    def test_menu_list_success(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test listing menus"""
        mock_wp_client.list_menus.return_value = [
            {"term_id": "2", "name": "Primary Menu", "slug": "primary-menu", "count": "5"},
            {"term_id": "3", "name": "Footer Menu", "slug": "footer-menu", "count": "3"},
        ]

        result = runner.invoke(menu_command, ["list"])

        assert result.exit_code == 0
        mock_wp_client.list_menus.assert_called_once()

    def test_menu_list_empty(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test listing when no menus found"""
        mock_wp_client.list_menus.return_value = []

        result = runner.invoke(menu_command, ["list"])

        assert result.exit_code == 0
        assert "No menus found" in result.output


class TestMenuCreate:
    def test_menu_create_success(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test creating a menu"""
        mock_wp_client.create_menu.return_value = 123

        result = runner.invoke(menu_command, ["create", "Main Menu"])

        assert result.exit_code == 0
        assert "123" in result.output
        assert "Created" in result.output
        mock_wp_client.create_menu.assert_called_once_with("Main Menu")

    def test_menu_create_with_server(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test creating menu with specific server"""
        mock_wp_client.create_menu.return_value = 456

        result = runner.invoke(menu_command, ["create", "Secondary Menu", "--server", "production"])

        assert result.exit_code == 0
        mock_config.get_server.assert_called_with("production")


class TestMenuDelete:
    def test_menu_delete_success(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test deleting a menu"""
        mock_wp_client.delete_menu.return_value = True

        result = runner.invoke(menu_command, ["delete", "123"], input="y\n")

        assert result.exit_code == 0
        assert "Deleted" in result.output or "✓" in result.output
        mock_wp_client.delete_menu.assert_called_once_with(123)

    def test_menu_delete_cancelled(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test cancelling menu deletion"""
        result = runner.invoke(menu_command, ["delete", "123"], input="n\n")

        assert result.exit_code == 1
        mock_wp_client.delete_menu.assert_not_called()


class TestMenuAddItem:
    def test_menu_add_item_success(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test adding item to menu"""
        mock_wp_client.add_menu_item.return_value = 789

        result = runner.invoke(
            menu_command, ["add-item", "123", "--title", "Home", "--url", "https://example.com"]
        )

        assert result.exit_code == 0
        assert "789" in result.output
        assert "Added" in result.output
        mock_wp_client.add_menu_item.assert_called_once()

    def test_menu_add_item_with_options(self, runner, mock_config, mock_ssh, mock_wp_client):
        """Test adding menu item with all options"""
        mock_wp_client.add_menu_item.return_value = 999

        result = runner.invoke(
            menu_command,
            [
                "add-item",
                "123",
                "--title",
                "About",
                "--url",
                "https://example.com/about",
                "--parent",
                "456",
                "--order",
                "2",
            ],
        )

        assert result.exit_code == 0
        mock_wp_client.add_menu_item.assert_called_once()
