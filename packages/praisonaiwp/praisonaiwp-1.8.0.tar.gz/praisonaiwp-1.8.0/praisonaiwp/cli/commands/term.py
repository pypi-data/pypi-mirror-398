"""WordPress term management commands"""

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
def term_command():
    """Manage WordPress taxonomy terms"""
    pass


@term_command.command("list")
@click.argument("taxonomy")
@click.option("--server", default=None, help="Server name from config")
def list_terms(taxonomy, server):
    """
    List WordPress taxonomy terms

    Examples:
    # List all categories
    praisonaiwp term list category

    # List all tags
    praisonaiwp term list post_tag

    # List from specific server
    praisonaiwp term list category --server staging
    """
    try:
        config = Config()
        server_config = config.get_server(server) if server else config.get_default_server()

        if not server_config:
            console.print(f"[red]Server '{server}' not found in configuration[/red]")
            return

        ssh = SSHManager.from_config(config, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        terms = client.list_terms(taxonomy)

        if not terms:
            console.print(f"[yellow]No terms found for taxonomy '{taxonomy}'[/yellow]")
            return

        # Create table
        table = Table(title=f"Terms for '{taxonomy}'")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="green")
        table.add_column("Slug", style="yellow")

        for term in terms:
            table.add_row(
                term.get('term_id', 'N/A'),
                term.get('name', 'N/A'),
                term.get('slug', 'N/A')
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"List terms failed: {e}")
        raise click.Abort() from None


@term_command.command("get")
@click.argument("taxonomy")
@click.argument("term_id")
@click.option("--server", default=None, help="Server name from config")
def get_term(taxonomy, term_id, server):
    """
    Get WordPress taxonomy term information

    Examples:
    # Get term info
    praisonaiwp term get category 1

    # Get from specific server
    praisonaiwp term get post_tag 5 --server staging
    """
    try:
        config = Config()
        server_config = config.get_server(server) if server else config.get_default_server()

        if not server_config:
            console.print(f"[red]Server '{server}' not found in configuration[/red]")
            return

        ssh = SSHManager.from_config(config, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        term_info = client.get_term(taxonomy, term_id)

        if term_info:
            console.print("[green]Term Information:[/green]")
            console.print(f"[cyan]ID:[/cyan] {term_info.get('term_id', 'N/A')}")
            console.print(f"[cyan]Name:[/cyan] {term_info.get('name', 'N/A')}")
            console.print(f"[cyan]Slug:[/cyan] {term_info.get('slug', 'N/A')}")
            console.print(f"[cyan]Taxonomy:[/cyan] {term_info.get('taxonomy', 'N/A')}")
            console.print(f"[cyan]Description:[/cyan] {term_info.get('description', 'N/A')}")
        else:
            console.print(f"[yellow]Term '{term_id}' not found in taxonomy '{taxonomy}'[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Get term failed: {e}")
        raise click.Abort() from None


@term_command.command("create")
@click.argument("taxonomy")
@click.argument("name")
@click.option("--slug", default=None, help="Term slug")
@click.option("--parent", default=None, help="Parent term ID")
@click.option("--description", default=None, help="Term description")
@click.option("--server", default=None, help="Server name from config")
def create_term(taxonomy, name, slug, parent, description, server):
    """
    Create a WordPress taxonomy term

    Examples:
    # Create a category
    praisonaiwp term create category "Technology"

    # Create a tag with slug
    praisonaiwp term create post_tag "WordPress" --slug wordpress

    # Create a child category
    praisonaiwp term create category "Child Category" --parent 1

    # Create from specific server
    praisonaiwp term create category "News" --server staging
    """
    try:
        config = Config()
        server_config = config.get_server(server) if server else config.get_default_server()

        if not server_config:
            console.print(f"[red]Server '{server}' not found in configuration[/red]")
            return

        ssh = SSHManager.from_config(config, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        term_info = client.create_term(taxonomy, name, slug, parent, description)

        if term_info:
            console.print(f"[green]Successfully created term '{name}'[/green]")
            console.print(f"[cyan]ID:[/cyan] {term_info.get('term_id', 'N/A')}")
            console.print(f"[cyan]Slug:[/cyan] {term_info.get('slug', 'N/A')}")
        else:
            console.print(f"[red]Failed to create term '{name}'[/red]")
            raise click.Abort()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Create term failed: {e}")
        raise click.Abort() from None


@term_command.command("delete")
@click.argument("taxonomy")
@click.argument("term_id")
@click.option("--server", default=None, help="Server name from config")
def delete_term(taxonomy, term_id, server):
    """
    Delete a WordPress taxonomy term

    Examples:
    # Delete a term
    praisonaiwp term delete category 1

    # Delete from specific server
    praisonaiwp term delete post_tag 5 --server staging
    """
    try:
        config = Config()
        server_config = config.get_server(server) if server else config.get_default_server()

        if not server_config:
            console.print(f"[red]Server '{server}' not found in configuration[/red]")
            return

        ssh = SSHManager.from_config(config, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        success = client.delete_term(taxonomy, term_id)

        if success:
            console.print(f"[green]Successfully deleted term '{term_id}' from '{taxonomy}'[/green]")
        else:
            console.print(f"[red]Failed to delete term '{term_id}'[/red]")
            raise click.Abort()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Delete term failed: {e}")
        raise click.Abort() from None
