"""Eval file commands"""
import click

from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.config import Config
from praisonaiwp.core.wp_client import WPClient


@click.command()
@click.argument('file_path')
@click.option('--server', help='Server name from config')
def eval_file(file_path, server):
    """Execute PHP file."""
    config = Config()
    ssh = SSHManager.from_config(config, server) if server else None
    client = WPClient(ssh, config.get_server(server)['wp_path'] if server else None)
    
    result = client.cli(f'eval-file {file_path}')
    click.echo(result)
