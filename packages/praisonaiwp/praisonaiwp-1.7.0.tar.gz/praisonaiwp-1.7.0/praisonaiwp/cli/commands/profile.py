"""WordPress profiling commands"""
import click

from praisonaiwp.cli.main import cli
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.config import Config
from praisonaiwp.core.wp_client import WPClient


@cli.group()
def profile():
    """WordPress performance profiling."""
    pass


@profile.command()
@click.argument('url')
@click.option('--server', help='Server name from config')
def stage(url, server):
    """Profile WordPress stage."""
    config = Config()
    ssh = SSHManager.from_config(config, server) if server else None
    client = WPClient(ssh, config.get_server(server)['wp_path'] if server else None)
    
    result = client.cli(f'profile stage {url}')
    click.echo(result)


@profile.command()
@click.argument('url')
@click.option('--server', help='Server name from config')
def bootstrap(url, server):
    """Profile WordPress bootstrap."""
    config = Config()
    ssh = SSHManager.from_config(config, server) if server else None
    client = WPClient(ssh, config.get_server(server)['wp_path'] if server else None)
    
    result = client.cli(f'profile bootstrap {url}')
    click.echo(result)


@profile.command()
@click.argument('url')
@click.option('--server', help='Server name from config')
def main(url, server):
    """Profile WordPress main."""
    config = Config()
    ssh = SSHManager.from_config(config, server) if server else None
    client = WPClient(ssh, config.get_server(server)['wp_path'] if server else None)
    
    result = client.cli(f'profile main {url}')
    click.echo(result)


@profile.command()
@click.argument('url')
@click.option('--server', help='Server name from config')
def hook(url, server):
    """Profile WordPress hooks."""
    config = Config()
    ssh = SSHManager.from_config(config, server) if server else None
    client = WPClient(ssh, config.get_server(server)['wp_path'] if server else None)
    
    result = client.cli(f'profile hook {url}')
    click.echo(result)


@profile.command()
@click.argument('url')
@click.option('--server', help='Server name from config')
def query(url, server):
    """Profile WordPress queries."""
    config = Config()
    ssh = SSHManager.from_config(config, server) if server else None
    client = WPClient(ssh, config.get_server(server)['wp_path'] if server else None)
    
    result = client.cli(f'profile query {url}')
    click.echo(result)
