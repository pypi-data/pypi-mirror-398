"""Distribution archive commands"""
import click

from praisonaiwp.cli.main import cli
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.config import Config
from praisonaiwp.core.wp_client import WPClient


@cli.command()
@click.argument('path')
@click.option('--format', default='zip', help='Archive format (zip, tar)')
@click.option('--server', help='Server name from config')
def dist_archive(path, format, server):
    """Create distribution archive."""
    config = Config()
    ssh = SSHManager.from_config(config, server) if server else None
    client = WPClient(ssh, config.get_server(server)['wp_path'] if server else None)
    
    result = client.cli(f'dist-archive {path} --format={format}')
    click.echo(result)
