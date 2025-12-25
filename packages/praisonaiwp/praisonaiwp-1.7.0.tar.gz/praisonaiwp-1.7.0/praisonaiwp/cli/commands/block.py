"""WordPress block management commands"""
import click

from praisonaiwp.cli.main import cli
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.config import Config
from praisonaiwp.core.wp_client import WPClient


@cli.group()
def block():
    """Manage WordPress blocks."""
    pass


@block.command()
@click.option('--server', help='Server name from config')
def list(server):
    """List available blocks."""
    config = Config()
    ssh = SSHManager.from_config(config, server) if server else None
    client = WPClient(ssh, config.get_server(server)['wp_path'] if server else None)
    
    result = client.cli('block list')
    click.echo(result)


@block.command()
@click.argument('block_name')
@click.option('--server', help='Server name from config')
def get(block_name, server):
    """Get block information."""
    config = Config()
    ssh = SSHManager.from_config(config, server) if server else None
    client = WPClient(ssh, config.get_server(server)['wp_path'] if server else None)
    
    result = client.cli(f'block get {block_name}')
    click.echo(result)


@block.command()
@click.argument('block_name')
@click.option('--server', help='Server name from config')
def register(block_name, server):
    """Register a block."""
    config = Config()
    ssh = SSHManager.from_config(config, server) if server else None
    client = WPClient(ssh, config.get_server(server)['wp_path'] if server else None)
    
    result = client.cli(f'block register {block_name}')
    click.echo(result)


@block.command()
@click.argument('block_name')
@click.option('--server', help='Server name from config')
def unregister(block_name, server):
    """Unregister a block."""
    config = Config()
    ssh = SSHManager.from_config(config, server) if server else None
    client = WPClient(ssh, config.get_server(server)['wp_path'] if server else None)
    
    result = client.cli(f'block unregister {block_name}')
    click.echo(result)
