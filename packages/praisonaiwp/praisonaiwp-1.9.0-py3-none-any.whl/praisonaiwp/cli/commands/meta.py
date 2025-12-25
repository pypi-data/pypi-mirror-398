"""WordPress post and user meta management commands"""


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
def meta_command():
    """Manage WordPress post and user meta"""
    pass


# Post Meta Commands
@meta_command.command('post-get')
@click.argument('post_id', type=int)
@click.argument('key', required=False)
@click.option('--server', default=None, help='Server name from config')
def get_post_meta(post_id, key, server):
    """
    Get post meta value(s)

    Examples:

        # Get specific meta field
        praisonaiwp meta post-get 123 custom_field

        # Get all meta fields
        praisonaiwp meta post-get 123
    """
    try:
        config = Config()
        server_config = config.get_server(server)

        with SSHManager(
            server_config['hostname'],
            server_config['username'],
            server_config.get('key_filename'),
            server_config.get('port', 22)
        ) as ssh:

            wp = WPClient(
                ssh,
                server_config['wp_path'],
                server_config.get('php_bin', 'php'),
                server_config.get('wp_cli', '/usr/local/bin/wp')
            )

            result = wp.get_post_meta(post_id, key)

            if isinstance(result, list):
                # Display as table
                table = Table(title=f"Post {post_id} Meta Fields")
                table.add_column("Key", style="cyan")
                table.add_column("Value", style="green")

                for meta in result:
                    table.add_row(
                        meta.get('meta_key', ''),
                        str(meta.get('meta_value', ''))
                    )

                console.print(table)
            else:
                # Single value
                console.print(result)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Get post meta failed: {e}")
        raise click.Abort() from None


@meta_command.command('post-set')
@click.argument('post_id', type=int)
@click.argument('key')
@click.argument('value')
@click.option('--server', default=None, help='Server name from config')
def set_post_meta(post_id, key, value, server):
    """
    Set post meta value

    Examples:

        # Set meta field
        praisonaiwp meta post-set 123 custom_field "test value"
    """
    try:
        config = Config()
        server_config = config.get_server(server)

        with SSHManager(
            server_config['hostname'],
            server_config['username'],
            server_config.get('key_filename'),
            server_config.get('port', 22)
        ) as ssh:

            wp = WPClient(
                ssh,
                server_config['wp_path'],
                server_config.get('php_bin', 'php'),
                server_config.get('wp_cli', '/usr/local/bin/wp')
            )

            wp.set_post_meta(post_id, key, value)
            console.print(f"[green]✓ Set meta '{key}' = '{value}' for post {post_id}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Set post meta failed: {e}")
        raise click.Abort() from None


@meta_command.command('post-update')
@click.argument('post_id', type=int)
@click.argument('key')
@click.argument('value')
@click.option('--server', default=None, help='Server name from config')
def update_post_meta(post_id, key, value, server):
    """
    Update post meta value

    Examples:

        # Update meta field
        praisonaiwp meta post-update 123 custom_field "new value"
    """
    try:
        config = Config()
        server_config = config.get_server(server)

        with SSHManager(
            server_config['hostname'],
            server_config['username'],
            server_config.get('key_filename'),
            server_config.get('port', 22)
        ) as ssh:

            wp = WPClient(
                ssh,
                server_config['wp_path'],
                server_config.get('php_bin', 'php'),
                server_config.get('wp_cli', '/usr/local/bin/wp')
            )

            wp.update_post_meta(post_id, key, value)
            console.print(f"[green]✓ Updated meta '{key}' = '{value}' for post {post_id}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Update post meta failed: {e}")
        raise click.Abort() from None


@meta_command.command('post-delete')
@click.argument('post_id', type=int)
@click.argument('key')
@click.option('--server', default=None, help='Server name from config')
def delete_post_meta(post_id, key, server):
    """
    Delete post meta field

    Examples:

        # Delete meta field
        praisonaiwp meta post-delete 123 custom_field
    """
    try:
        config = Config()
        server_config = config.get_server(server)

        with SSHManager(
            server_config['hostname'],
            server_config['username'],
            server_config.get('key_filename'),
            server_config.get('port', 22)
        ) as ssh:

            wp = WPClient(
                ssh,
                server_config['wp_path'],
                server_config.get('php_bin', 'php'),
                server_config.get('wp_cli', '/usr/local/bin/wp')
            )

            wp.delete_post_meta(post_id, key)
            console.print(f"[green]✓ Deleted meta '{key}' from post {post_id}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Delete post meta failed: {e}")
        raise click.Abort() from None


# User Meta Commands
@meta_command.command('user-get')
@click.argument('user_id', type=int)
@click.argument('key', required=False)
@click.option('--server', default=None, help='Server name from config')
def get_user_meta(user_id, key, server):
    """
    Get user meta value(s)

    Examples:

        # Get specific meta field
        praisonaiwp meta user-get 456 user_field

        # Get all meta fields
        praisonaiwp meta user-get 456
    """
    try:
        config = Config()
        server_config = config.get_server(server)

        with SSHManager(
            server_config['hostname'],
            server_config['username'],
            server_config.get('key_filename'),
            server_config.get('port', 22)
        ) as ssh:

            wp = WPClient(
                ssh,
                server_config['wp_path'],
                server_config.get('php_bin', 'php'),
                server_config.get('wp_cli', '/usr/local/bin/wp')
            )

            result = wp.get_user_meta(user_id, key)

            if isinstance(result, list):
                # Display as table
                table = Table(title=f"User {user_id} Meta Fields")
                table.add_column("Key", style="cyan")
                table.add_column("Value", style="green")

                for meta in result:
                    table.add_row(
                        meta.get('meta_key', ''),
                        str(meta.get('meta_value', ''))
                    )

                console.print(table)
            else:
                # Single value
                console.print(result)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Get user meta failed: {e}")
        raise click.Abort() from None


@meta_command.command('user-set')
@click.argument('user_id', type=int)
@click.argument('key')
@click.argument('value')
@click.option('--server', default=None, help='Server name from config')
def set_user_meta(user_id, key, value, server):
    """
    Set user meta value

    Examples:

        # Set meta field
        praisonaiwp meta user-set 456 user_field "test value"
    """
    try:
        config = Config()
        server_config = config.get_server(server)

        with SSHManager(
            server_config['hostname'],
            server_config['username'],
            server_config.get('key_filename'),
            server_config.get('port', 22)
        ) as ssh:

            wp = WPClient(
                ssh,
                server_config['wp_path'],
                server_config.get('php_bin', 'php'),
                server_config.get('wp_cli', '/usr/local/bin/wp')
            )

            wp.set_user_meta(user_id, key, value)
            console.print(f"[green]✓ Set meta '{key}' = '{value}' for user {user_id}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Set user meta failed: {e}")
        raise click.Abort() from None


@meta_command.command('user-update')
@click.argument('user_id', type=int)
@click.argument('key')
@click.argument('value')
@click.option('--server', default=None, help='Server name from config')
def update_user_meta(user_id, key, value, server):
    """
    Update user meta value

    Examples:

        # Update meta field
        praisonaiwp meta user-update 456 user_field "new value"
    """
    try:
        config = Config()
        server_config = config.get_server(server)

        with SSHManager(
            server_config['hostname'],
            server_config['username'],
            server_config.get('key_filename'),
            server_config.get('port', 22)
        ) as ssh:

            wp = WPClient(
                ssh,
                server_config['wp_path'],
                server_config.get('php_bin', 'php'),
                server_config.get('wp_cli', '/usr/local/bin/wp')
            )

            wp.update_user_meta(user_id, key, value)
            console.print(f"[green]✓ Updated meta '{key}' = '{value}' for user {user_id}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Update user meta failed: {e}")
        raise click.Abort() from None


@meta_command.command('user-delete')
@click.argument('user_id', type=int)
@click.argument('key')
@click.option('--server', default=None, help='Server name from config')
def delete_user_meta(user_id, key, server):
    """
    Delete user meta field

    Examples:

        # Delete meta field
        praisonaiwp meta user-delete 456 user_field
    """
    try:
        config = Config()
        server_config = config.get_server(server)

        with SSHManager(
            server_config['hostname'],
            server_config['username'],
            server_config.get('key_filename'),
            server_config.get('port', 22)
        ) as ssh:

            wp = WPClient(
                ssh,
                server_config['wp_path'],
                server_config.get('php_bin', 'php'),
                server_config.get('wp_cli', '/usr/local/bin/wp')
            )

            wp.delete_user_meta(user_id, key)
            console.print(f"[green]✓ Deleted meta '{key}' from user {user_id}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Delete user meta failed: {e}")
        raise click.Abort() from None
