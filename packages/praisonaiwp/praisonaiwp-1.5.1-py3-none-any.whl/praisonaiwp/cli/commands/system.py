"""WordPress system management commands"""

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
def system_command():
    """Manage WordPress system operations"""
    pass


@system_command.command('cache-flush')
@click.option('--server', default=None, help='Server name from config')
def cache_flush(server):
    """
    Flush WordPress cache

    Examples:

        # Flush cache
        praisonaiwp system cache-flush

        # Flush cache on specific server
        praisonaiwp system cache-flush --server production
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

            success = wp.cache_flush()

            if success:
                console.print("[green]✓ Cache flushed successfully[/green]")
            else:
                console.print("[red]✗ Failed to flush cache[/red]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Cache flush failed: {e}")
        raise click.Abort() from None


@system_command.command('cache-type')
@click.option('--server', default=None, help='Server name from config')
def cache_type(server):
    """
    Get cache type information

    Examples:

        # Get cache type
        praisonaiwp system cache-type
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

            cache_type = wp.get_cache_type()

            if cache_type:
                console.print(f"[cyan]Cache type:[/cyan] {cache_type}")
            else:
                console.print("[yellow]No caching system detected[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Get cache type failed: {e}")
        raise click.Abort() from None


@system_command.command('version')
@click.option('--detailed', is_flag=True, help='Show detailed version information')
@click.option('--server', default=None, help='Server name from config')
def version(detailed, server):
    """
    Get WordPress version information

    Examples:

        # Get version
        praisonaiwp system version

        # Get detailed version info
        praisonaiwp system version --detailed
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

            wp_version = wp.get_version()

            if detailed:
                # Get additional system info
                table = Table(title="WordPress System Information")
                table.add_column("Property", style="cyan")
                table.add_column("Value", style="white")

                table.add_row("WordPress Version", wp_version)
                table.add_row("WP-CLI Path", server_config.get('wp_cli', '/usr/local/bin/wp'))
                table.add_row("PHP Binary", server_config.get('php_bin', 'php'))
                table.add_row("WordPress Path", server_config['wp_path'])
                table.add_row("Server", server_config['hostname'])

                console.print(table)
            else:
                console.print(f"[cyan]WordPress version:[/cyan] {wp_version}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Get version failed: {e}")
        raise click.Abort() from None


@system_command.command('check-install')
@click.option('--server', default=None, help='Server name from config')
def check_install(server):
    """
    Check WordPress installation

    Examples:

        # Check installation
        praisonaiwp system check-install
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

            is_valid = wp.check_install()

            if is_valid:
                console.print("[green]✓ WordPress installation is valid[/green]")
            else:
                console.print("[red]✗ WordPress installation is invalid or corrupted[/red]")
                raise click.ClickException("WordPress installation check failed")

    except click.ClickException:
        raise
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Check install failed: {e}")
        raise click.Abort() from None
