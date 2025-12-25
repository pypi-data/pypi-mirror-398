"""WordPress taxonomy management commands"""

import click
from rich.console import Console
from rich.table import Table

from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


@click.group()
def taxonomy_command():
    """Manage WordPress taxonomies"""
    pass


@taxonomy_command.command("list")
@click.option("--server", default=None, help="Server name from config")
def list_taxonomies(server):
    """
    List WordPress taxonomies

    Examples:
    # List all taxonomies
    praisonaiwp taxonomy list

    # List from specific server
    praisonaiwp taxonomy list --server staging
    """
    try:
        config = Config()
        server_config = config.get_server(server) if server else config.get_default_server()

        if not server_config:
            console.print(f"[red]Server '{server}' not found in configuration[/red]")
            return

        ssh = SSHManager.from_config(config, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        taxonomies = client.list_taxonomies()

        if not taxonomies:
            console.print("[yellow]No taxonomies found[/yellow]")
            return

        # Create table
        table = Table(title="WordPress Taxonomies")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Label", style="green")
        table.add_column("Hierarchical", style="yellow")
        table.add_column("Public", style="blue")

        for taxonomy in taxonomies:
            table.add_row(
                taxonomy.get('name', 'N/A'),
                taxonomy.get('label', 'N/A'),
                str(taxonomy.get('hierarchical', False)),
                str(taxonomy.get('public', True))
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"List taxonomies failed: {e}")
        raise click.Abort() from None


@taxonomy_command.command("get")
@click.argument("taxonomy")
@click.option("--server", default=None, help="Server name from config")
def get_taxonomy(taxonomy, server):
    """
    Get WordPress taxonomy information

    Examples:
    # Get taxonomy info
    praisonaiwp taxonomy get category

    # Get from specific server
    praisonaiwp taxonomy get post_tag --server staging
    """
    try:
        config = Config()
        server_config = config.get_server(server) if server else config.get_default_server()

        if not server_config:
            console.print(f"[red]Server '{server}' not found in configuration[/red]")
            return

        ssh = SSHManager.from_config(config, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        taxonomy_info = client.get_taxonomy(taxonomy)

        if taxonomy_info:
            console.print("[green]Taxonomy Information:[/green]")
            console.print(f"[cyan]Name:[/cyan] {taxonomy_info.get('name', 'N/A')}")
            console.print(f"[cyan]Label:[/cyan] {taxonomy_info.get('label', 'N/A')}")
            console.print(f"[cyan]Hierarchical:[/cyan] {taxonomy_info.get('hierarchical', False)}")
            console.print(f"[cyan]Public:[/cyan] {taxonomy_info.get('public', True)}")
            console.print(f"[cyan]Show UI:[/cyan] {taxonomy_info.get('show_ui', True)}")
        else:
            console.print(f"[yellow]Taxonomy '{taxonomy}' not found[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Get taxonomy failed: {e}")
        raise click.Abort() from None
