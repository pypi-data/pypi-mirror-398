"""WordPress transient management commands"""

import click
from rich.console import Console

from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


@click.group()
def transient_command():
    """Manage WordPress transients"""
    pass


@transient_command.command("get")
@click.argument("key")
@click.option("--server", default=None, help="Server name from config")
def get_transient(key, server):
    """
    Get transient value

    Examples:

        # Get transient value
        praisonaiwp transient get cache_key

        # Get from specific server
        praisonaiwp transient get cache_key --server production
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

            value = wp.get_transient(key)

            if value is not None:
                console.print(f"[cyan]Transient '{key}':[/cyan] {value}")
            else:
                console.print(f"[yellow]Transient '{key}' not found[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Get transient failed: {e}")
        raise click.Abort() from None


@transient_command.command("set")
@click.argument("key")
@click.argument("value")
@click.option("--expire", type=int, default=3600, help="Expiration time in seconds (default: 3600)")
@click.option("--server", default=None, help="Server name from config")
def set_transient(key, value, expire, server):
    """
    Set transient value

    Examples:

        # Set transient with default expiration (1 hour)
        praisonaiwp transient set cache_key "test_value"

        # Set transient with custom expiration
        praisonaiwp transient set cache_key "test_value" --expire 7200

        # Set on specific server
        praisonaiwp transient set cache_key "test_value" --server production
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

            success = wp.set_transient(key, value, expire)

            if success:
                expire_text = f" ({expire}s)" if expire != 0 else " (no expiration)"
                console.print(f"[green]✓ Set transient '{key}' = '{value}'{expire_text}[/green]")
            else:
                console.print(f"[red]✗ Failed to set transient '{key}'[/red]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Set transient failed: {e}")
        raise click.Abort() from None


@transient_command.command("delete")
@click.argument("key")
@click.option("--server", default=None, help="Server name from config")
def delete_transient(key, server):
    """
    Delete transient

    Examples:

        # Delete transient
        praisonaiwp transient delete cache_key

        # Delete from specific server
        praisonaiwp transient delete cache_key --server production
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

            success = wp.delete_transient(key)

            if success:
                console.print(f"[green]✓ Deleted transient '{key}'[/green]")
            else:
                console.print(f"[red]✗ Transient '{key}' not found or failed to delete[/red]")
                raise click.ClickException(f"Transient deletion failed for '{key}'")

    except click.ClickException:
        raise
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Delete transient failed: {e}")
        raise click.Abort() from None
