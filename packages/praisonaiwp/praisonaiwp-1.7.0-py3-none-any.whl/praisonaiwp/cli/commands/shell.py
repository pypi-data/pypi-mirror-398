"""WordPress shell commands"""
import click

from praisonaiwp.cli.main import cli
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.config import Config
from praisonaiwp.core.wp_client import WPClient


@cli.command()
@click.option('--server', help='Server name from config')
def shell(server):
    """Interactive WordPress shell."""
    config = Config()
    ssh = SSHManager.from_config(config, server) if server else None
    client = WPClient(ssh, config.get_server(server)['wp_path'] if server else None)
    
    click.echo("Starting WordPress shell. Type 'exit' to quit.")
    
    while True:
        try:
            command = input("wp> ")
            if command.lower() in ['exit', 'quit']:
                break
            
            if command.strip():
                result = client.cli(command)
                click.echo(result)
        except KeyboardInterrupt:
            break
    
    click.echo("WordPress shell closed.")
