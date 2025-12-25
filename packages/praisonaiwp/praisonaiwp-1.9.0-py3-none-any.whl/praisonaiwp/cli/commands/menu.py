"""WordPress menu management commands"""

import click
from rich.console import Console
from rich.table import Table

from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


@click.group()
def menu_command():
    """Manage WordPress menus"""
    pass


@menu_command.command("list")
@click.option("--server", default=None, help="Server name from config")
def list_menus(server):
    """
    List WordPress menus

    Examples:

        # List all menus
        praisonaiwp menu list

        # List menus from specific server
        praisonaiwp menu list --server production
    """
    try:
        config = Config()
        server_config = config.get_server(server)

        with SSHManager(
            server_config["hostname"],
            server_config["username"],
            server_config.get("key_filename"),
            server_config.get("port", 22),
        ) as ssh:

            wp = WPClient(
                ssh,
                server_config["wp_path"],
                server_config.get("php_bin", "php"),
                server_config.get("wp_cli", "/usr/local/bin/wp"),
            )

            menus = wp.list_menus()

            if menus:
                table = Table(title="WordPress Menus")
                table.add_column("ID", style="cyan")
                table.add_column("Name", style="white")
                table.add_column("Slug", style="dim")
                table.add_column("Items", style="green")

                for menu in menus:
                    table.add_row(
                        str(menu.get("term_id", "")),
                        menu.get("name", ""),
                        menu.get("slug", ""),
                        str(menu.get("count", "0")),
                    )

                console.print(table)
            else:
                console.print("[yellow]No menus found[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"List menus failed: {e}")
        raise click.Abort() from None


@menu_command.command("create")
@click.argument("menu_name")
@click.option("--server", default=None, help="Server name from config")
def create_menu(menu_name, server):
    """
    Create a new WordPress menu

    Examples:

        # Create menu
        praisonaiwp menu create "Main Menu"

        # Create menu on specific server
        praisonaiwp menu create "Footer Menu" --server production
    """
    try:
        config = Config()
        server_config = config.get_server(server)

        with SSHManager(
            server_config["hostname"],
            server_config["username"],
            server_config.get("key_filename"),
            server_config.get("port", 22),
        ) as ssh:

            wp = WPClient(
                ssh,
                server_config["wp_path"],
                server_config.get("php_bin", "php"),
                server_config.get("wp_cli", "/usr/local/bin/wp"),
            )

            menu_id = wp.create_menu(menu_name)

            console.print(f"[green]✓ Created menu '{menu_name}' with ID {menu_id}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Create menu failed: {e}")
        raise click.Abort() from None


@menu_command.command("delete")
@click.argument("menu_id", type=int)
@click.option("--server", default=None, help="Server name from config")
@click.confirmation_option(prompt="Are you sure you want to delete this menu?")
def delete_menu(menu_id, server):
    """
    Delete a WordPress menu

    Examples:

        # Delete menu
        praisonaiwp menu delete 123
    """
    try:
        config = Config()
        server_config = config.get_server(server)

        with SSHManager(
            server_config["hostname"],
            server_config["username"],
            server_config.get("key_filename"),
            server_config.get("port", 22),
        ) as ssh:

            wp = WPClient(
                ssh,
                server_config["wp_path"],
                server_config.get("php_bin", "php"),
                server_config.get("wp_cli", "/usr/local/bin/wp"),
            )

            success = wp.delete_menu(menu_id)

            if success:
                console.print(f"[green]✓ Deleted menu {menu_id}[/green]")
            else:
                console.print(f"[red]Failed to delete menu {menu_id}[/red]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Delete menu failed: {e}")
        raise click.Abort() from None


@menu_command.command("add-item")
@click.argument("menu_id", type=int)
@click.option("--title", required=True, help="Menu item title")
@click.option("--url", required=True, help="Menu item URL")
@click.option("--parent", type=int, help="Parent menu item ID")
@click.option("--order", type=int, help="Menu item order")
@click.option("--server", default=None, help="Server name from config")
def add_menu_item(menu_id, title, url, parent, order, server):
    """
    Add item to WordPress menu

    Examples:

        # Add simple menu item
        praisonaiwp menu add-item 123 --title "Home" --url "https://example.com"

        # Add child menu item
        praisonaiwp menu add-item 123 --title "About" --url "https://example.com/about" --parent 456 --order 2
    """
    try:
        config = Config()
        server_config = config.get_server(server)

        with SSHManager(
            server_config["hostname"],
            server_config["username"],
            server_config.get("key_filename"),
            server_config.get("port", 22),
        ) as ssh:

            wp = WPClient(
                ssh,
                server_config["wp_path"],
                server_config.get("php_bin", "php"),
                server_config.get("wp_cli", "/usr/local/bin/wp"),
            )

            item_id = wp.add_menu_item(
                menu_id=menu_id, title=title, url=url, parent=parent, order=order
            )

            console.print(f"[green]✓ Added menu item '{title}' with ID {item_id}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Add menu item failed: {e}")
        raise click.Abort() from None
