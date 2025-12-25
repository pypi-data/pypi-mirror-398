"""Ability management commands"""
import click

from praisonaiwp.cli.main import cli
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.config import Config
from praisonaiwp.core.wp_client import WPClient


@cli.group()
def ability():
    """Manage user capabilities."""
    pass


@ability.command()
@click.argument('user_id', type=int)
@click.option('--server', help='Server name from config')
def list(user_id, server):
    """List user capabilities."""
    config = Config()
    ssh = SSHManager.from_config(config, server) if server else None
    client = WPClient(ssh, config.get_server(server)['wp_path'] if server else None)
    
    result = client.cli(f'ability list {user_id}')
    click.echo(result)


@ability.command()
@click.argument('user_id', type=int)
@click.argument('capability')
@click.option('--grant', is_flag=True, help='Grant capability')
@click.option('--deny', is_flag=True, help='Deny capability')
@click.option('--server', help='Server name from config')
def add(user_id, capability, grant, deny, server):
    """Add or remove user capability."""
    config = Config()
    ssh = SSHManager.from_config(config, server) if server else None
    client = WPClient(ssh, config.get_server(server)['wp_path'] if server else None)
    
    if grant:
        result = client.cli(f'capability add {user_id} {capability} --grant')
    elif deny:
        result = client.cli(f'capability add {user_id} {capability} --deny')
    else:
        result = client.cli(f'capability add {user_id} {capability}')
    
    click.echo(result)


@ability.command()
@click.argument('user_id', type=int)
@click.argument('capability')
@click.option('--server', help='Server name from config')
def remove(user_id, capability, server):
    """Remove user capability."""
    config = Config()
    ssh = SSHManager.from_config(config, server) if server else None
    client = WPClient(ssh, config.get_server(server)['wp_path'] if server else None)
    
    result = client.cli(f'capability remove {user_id} {capability}')
    click.echo(result)


@ability.command()
@click.argument('capability')
@click.option('--server', help='Server name from config')
def check(capability, server):
    """Check if current user has capability."""
    config = Config()
    ssh = SSHManager.from_config(config, server) if server else None
    client = WPClient(ssh, config.get_server(server)['wp_path'] if server else None)
    
    result = client.cli(f'capability check {capability}')
    click.echo(result)
