"""WordPress options management commands"""

import click
from rich.console import Console

from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


@click.group()
def option_command():
    """Manage WordPress options"""
    pass


@option_command.command('get')
@click.argument('option_name')
@click.option('--server', default=None, help='Server name from config')
def get_option(option_name, server):
    """
    Get WordPress option value

    Examples:

        # Get site name
        praisonaiwp option get blogname

        # Get from specific server
        praisonaiwp option get siteurl --server production
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

            value = wp.get_option(option_name)
            console.print(value)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Get option failed: {e}")
        raise click.Abort() from None


@option_command.command('set')
@click.argument('option_name')
@click.argument('value')
@click.option('--server', default=None, help='Server name from config')
def set_option(option_name, value, server):
    """
    Set WordPress option value

    Examples:

        # Set site name
        praisonaiwp option set blogname "My New Site"

        # Set option on specific server
        praisonaiwp option set posts_per_page 20 --server production
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

            wp.set_option(option_name, value)
            console.print(f"[green]✓ Set option '{option_name}' = '{value}'[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Set option failed: {e}")
        raise click.Abort() from None


@option_command.command('delete')
@click.argument('option_name')
@click.option('--server', default=None, help='Server name from config')
@click.confirmation_option(prompt='Are you sure you want to delete this option?')
def delete_option(option_name, server):
    """
    Delete WordPress option

    Examples:

        # Delete option
        praisonaiwp option delete custom_option

        # Delete from specific server
        praisonaiwp option delete temp_setting --server production
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

            wp.delete_option(option_name)
            console.print(f"[green]✓ Deleted option '{option_name}'[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Delete option failed: {e}")
        raise click.Abort() from None
