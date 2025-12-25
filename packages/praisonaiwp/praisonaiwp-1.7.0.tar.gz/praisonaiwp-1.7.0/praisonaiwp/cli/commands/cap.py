"""Capability management commands"""
import click

from praisonaiwp.cli.main import cli
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.config import Config
from praisonaiwp.core.wp_client import WPClient


@cli.group()
def cap():
    """Manage role capabilities."""
    pass


@cap.command()
@click.argument('role')
@click.option('--server', help='Server name from config')
def list(role, server):
    """List role capabilities."""
    config = Config()
    ssh = SSHManager.from_config(config, server) if server else None
    client = WPClient(ssh, config.get_server(server)['wp_path'] if server else None)
    
    result = client.cli(f'cap list {role}')
    click.echo(result)


@cap.command()
@click.argument('role')
@click.argument('capability')
@click.option('--grant', is_flag=True, help='Grant capability')
@click.option('--server', help='Server name from config')
def add(role, capability, grant, server):
    """Add capability to role."""
    config = Config()
    ssh = SSHManager.from_config(config, server) if server else None
    client = WPClient(ssh, config.get_server(server)['wp_path'] if server else None)
    
    if grant:
        result = client.cli(f'cap add {role} {capability} --grant')
    else:
        result = client.cli(f'cap add {role} {capability}')
    
    click.echo(result)


@cap.command()
@click.argument('role')
@click.argument('capability')
@click.option('--server', help='Server name from config')
def remove(role, capability, server):
    """Remove capability from role."""
    config = Config()
    ssh = SSHManager.from_config(config, server) if server else None
    client = WPClient(ssh, config.get_server(server)['wp_path'] if server else None)
    
    result = client.cli(f'cap remove {role} {capability}')
    click.echo(result)
