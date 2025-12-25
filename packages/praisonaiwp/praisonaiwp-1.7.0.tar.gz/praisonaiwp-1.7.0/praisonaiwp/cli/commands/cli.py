"""WP-CLI management commands"""
import click

from praisonaiwp.cli.main import cli
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.config import Config
from praisonaiwp.core.wp_client import WPClient


@cli.group()
def wpcli():
    """WP-CLI management."""
    pass


@wpcli.command()
@click.option('--server', help='Server name from config')
def version(server):
    """Get WP-CLI version."""
    config = Config()
    ssh = SSHManager.from_config(config, server) if server else None
    client = WPClient(ssh, config.get_server(server)['wp_path'] if server else None)
    
    result = client.cli('cli version')
    click.echo(result)


@wpcli.command()
@click.option('--server', help='Server name from config')
def info(server):
    """Get WP-CLI info."""
    config = Config()
    ssh = SSHManager.from_config(config, server) if server else None
    client = WPClient(ssh, config.get_server(server)['wp_path'] if server else None)
    
    result = client.cli('cli info')
    click.echo(result)


@wpcli.command()
@click.option('--server', help='Server name from config')
def cache_clear(server):
    """Clear WP-CLI cache."""
    config = Config()
    ssh = SSHManager.from_config(config, server) if server else None
    client = WPClient(ssh, config.get_server(server)['wp_path'] if server else None)
    
    result = client.cli('cli cache clear')
    click.echo(result)


@wpcli.command()
@click.option('--server', help='Server name from config')
def cmd_dump(server):
    """Dump available commands."""
    config = Config()
    ssh = SSHManager.from_config(config, server) if server else None
    client = WPClient(ssh, config.get_server(server)['wp_path'] if server else None)
    
    result = client.cli('cli cmd-dump')
    click.echo(result)


@wpcli.command()
@click.option('--server', help='Server name from config')
def update(server):
    """Update WP-CLI."""
    config = Config()
    ssh = SSHManager.from_config(config, server) if server else None
    client = WPClient(ssh, config.get_server(server)['wp_path'] if server else None)
    
    result = client.cli('cli update')
    click.echo(result)
