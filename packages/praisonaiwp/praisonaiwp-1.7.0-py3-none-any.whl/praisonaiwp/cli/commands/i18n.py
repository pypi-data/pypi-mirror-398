"""Internationalization commands"""
import click

from praisonaiwp.cli.main import cli
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.config import Config
from praisonaiwp.core.wp_client import WPClient


@cli.group()
def i18n():
    """Internationalization management."""
    pass


@i18n.command()
@click.argument('domain')
@click.argument('pot_file')
@click.option('--server', help='Server name from config')
def make_pot(domain, pot_file, server):
    """Generate POT file."""
    config = Config()
    ssh = SSHManager.from_config(config, server) if server else None
    client = WPClient(ssh, config.get_server(server)['wp_path'] if server else None)
    
    result = client.cli(f'i18n make-pot {domain} {pot_file}')
    click.echo(result)


@i18n.command()
@click.argument('pot_file')
@click.argument('po_file')
@click.option('--server', help='Server name from config')
def make_mo(pot_file, po_file, server):
    """Generate MO file from PO file."""
    config = Config()
    ssh = SSHManager.from_config(config, server) if server else None
    client = WPClient(ssh, config.get_server(server)['wp_path'] if server else None)
    
    result = client.cli(f'i18n make-mo {pot_file} {po_file}')
    click.echo(result)


@i18n.command()
@click.argument('pot_file')
@click.argument('po_file')
@click.option('--server', help='Server name from config')
def update_po(pot_file, po_file, server):
    """Update PO file from POT file."""
    config = Config()
    ssh = SSHManager.from_config(config, server) if server else None
    client = WPClient(ssh, config.get_server(server)['wp_path'] if server else None)
    
    result = client.cli(f'i18n update-po {pot_file} {po_file}')
    click.echo(result)
