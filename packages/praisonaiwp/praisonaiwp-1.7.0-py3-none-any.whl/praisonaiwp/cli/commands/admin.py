"""WordPress admin management commands"""
import click

from praisonaiwp.cli.main import cli
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.config import Config
from praisonaiwp.core.wp_client import WPClient


@cli.group()
def admin():
    """WordPress admin management."""
    pass


@admin.command()
@click.option('--server', help='Server name from config')
def url(server):
    """Get admin URL."""
    config = Config()
    ssh = SSHManager.from_config(config, server) if server else None
    client = WPClient(ssh, config.get_server(server)['wp_path'] if server else None)
    
    result = client.cli('admin url')
    click.echo(result)


@admin.command()
@click.option('--server', help='Server name from config')
def path(server):
    """Get admin path."""
    config = Config()
    ssh = SSHManager.from_config(config, server) if server else None
    client = WPClient(ssh, config.get_server(server)['wp_path'] if server else None)
    
    result = client.cli('admin path')
    click.echo(result)


@admin.command()
@click.option('--server', help='Server name from config')
def home(server):
    """Get home URL."""
    config = Config()
    ssh = SSHManager.from_config(config, server) if server else None
    client = WPClient(ssh, config.get_server(server)['wp_path'] if server else None)
    
    result = client.cli('admin home')
    click.echo(result)


@admin.command()
@click.option('--server', help='Server name from config')
def siteurl(server):
    """Get site URL."""
    config = Config()
    ssh = SSHManager.from_config(config, server) if server else None
    client = WPClient(ssh, config.get_server(server)['wp_path'] if server else None)
    
    result = client.cli('admin siteurl')
    click.echo(result)


@admin.command()
@click.option('--server', help='Server name from config')
def admin_email(server):
    """Get admin email."""
    config = Config()
    ssh = SSHManager.from_config(config, server) if server else None
    client = WPClient(ssh, config.get_server(server)['wp_path'] if server else None)
    
    result = client.cli('admin admin-email')
    click.echo(result)
