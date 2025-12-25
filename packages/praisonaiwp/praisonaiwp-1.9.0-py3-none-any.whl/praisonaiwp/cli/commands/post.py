"""WordPress post utility commands"""

import click
from rich.console import Console

from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


@click.group()
def post_command():
    """WordPress post utilities"""
    pass


@post_command.command("delete")
@click.argument("post_id", type=int)
@click.option("--server", default=None, help="Server name from config")
@click.confirmation_option(prompt="Are you sure you want to delete this post?")
def delete_post(post_id, server):
    """
    Delete a WordPress post

    Examples:

        # Delete post
        praisonaiwp post delete 123
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

            success = wp.delete_post(post_id)

            if success:
                console.print(f"[green]✓ Deleted post {post_id}[/green]")
            else:
                console.print(f"[red]Failed to delete post {post_id}[/red]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Delete post failed: {e}")
        raise click.Abort() from None


@post_command.command("exists")
@click.argument("post_id", type=int)
@click.option("--server", default=None, help="Server name from config")
def post_exists(post_id, server):
    """
    Check if a WordPress post exists

    Examples:

        # Check if post exists
        praisonaiwp post exists 123
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

            exists = wp.post_exists(post_id)

            if exists:
                console.print(f"[green]✓ Post {post_id} exists[/green]")
            else:
                console.print(f"[red]✗ Post {post_id} does not exist[/red]")
                raise click.ClickException(f"Post {post_id} does not exist")

    except click.ClickException:
        raise
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Check post exists failed: {e}")
        raise click.Abort() from None
