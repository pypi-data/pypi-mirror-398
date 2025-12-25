"""Package management commands"""
import click

from praisonaiwp.cli.main import cli
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.config import Config
from praisonaiwp.core.wp_client import WPClient


@cli.group()
def package():
    """Package management."""
    pass


@package.command()
@click.argument('path')
@click.option('--server', help='Server name from config')
def install(path, server):
    """Install package."""
    config = Config()
    ssh = SSHManager.from_config(config, server) if server else None
    client = WPClient(ssh, config.get_server(server)['wp_path'] if server else None)
    
    result = client.cli(f'package install {path}')
    click.echo(result)


@package.command()
@click.argument('name')
@click.option('--server', help='Server name from config')
def uninstall(name, server):
    """Uninstall package."""
    config = Config()
    ssh = SSHManager.from_config(config, server) if server else None
    client = WPClient(ssh, config.get_server(server)['wp_path'] if server else None)
    
    result = client.cli(f'package uninstall {name}')
    click.echo(result)


@package.command()
@click.option('--server', help='Server name from config')
def list(server):
    """List installed packages."""
    config = Config()
    ssh = SSHManager.from_config(config, server) if server else None
    client = WPClient(ssh, config.get_server(server)['wp_path'] if server else None)
    
    result = client.cli('package list')
    click.echo(result)


@package.command()
@click.option('--server', help='Server name from config')
def path(server):
    """Get package path."""
    config = Config()
    ssh = SSHManager.from_config(config, server) if server else None
    client = WPClient(ssh, config.get_server(server)['wp_path'] if server else None)
    
    result = client.cli('package path')
    click.echo(result)
