"""WordPress widget management commands"""

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
def widget_command():
    """Manage WordPress widgets"""
    pass


@widget_command.command("list")
@click.option("--server", default=None, help="Server name from config")
def list_widgets(server):
    """
    List WordPress widgets

    Examples:
    # List all widgets
    praisonaiwp widget list

    # List from specific server
    praisonaiwp widget list --server staging
    """
    try:
        config = Config()
        server_config = config.get_server(server) if server else config.get_default_server()

        if not server_config:
            console.print(f"[red]Server '{server}' not found in configuration[/red]")
            return

        ssh = SSHManager.from_config(config, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        widgets = client.list_widgets()

        if not widgets:
            console.print("[yellow]No widgets found[/yellow]")
            return

        # Create table
        table = Table(title="WordPress Widgets")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="green")
        table.add_column("Sidebar", style="yellow")

        for widget in widgets:
            table.add_row(
                widget.get('id', 'N/A'),
                widget.get('name', 'N/A'),
                widget.get('sidebar', 'N/A')
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"List widgets failed: {e}")
        raise click.Abort() from None


@widget_command.command("get")
@click.argument("widget_id")
@click.option("--server", default=None, help="Server name from config")
def get_widget(widget_id, server):
    """
    Get WordPress widget information

    Examples:
    # Get widget info
    praisonaiwp widget get 1

    # Get from specific server
    praisonaiwp widget get 2 --server staging
    """
    try:
        config = Config()
        server_config = config.get_server(server) if server else config.get_default_server()

        if not server_config:
            console.print(f"[red]Server '{server}' not found in configuration[/red]")
            return

        ssh = SSHManager.from_config(config, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        widget_info = client.get_widget(widget_id)

        if widget_info:
            console.print("[green]Widget Information:[/green]")
            console.print(f"[cyan]ID:[/cyan] {widget_info.get('id', 'N/A')}")
            console.print(f"[cyan]Name:[/cyan] {widget_info.get('name', 'N/A')}")
            console.print(f"[cyan]Sidebar:[/cyan] {widget_info.get('sidebar', 'N/A')}")

            # Display options if available
            options = widget_info.get('options', {})
            if options:
                console.print("[cyan]Options:[/cyan]")
                for key, value in options.items():
                    console.print(f"  {key}: {value}")
        else:
            console.print(f"[yellow]Widget '{widget_id}' not found[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Get widget failed: {e}")
        raise click.Abort() from None


@widget_command.command("update")
@click.argument("widget_id")
@click.option("--title", default=None, help="Widget title")
@click.option("--text", default=None, help="Widget text content")
@click.option("--server", default=None, help="Server name from config")
def update_widget(widget_id, title, text, server):
    """
    Update a WordPress widget

    Examples:
    # Update widget title
    praisonaiwp widget update 1 --title "New Title"

    # Update widget text
    praisonaiwp widget update 1 --text "New content"

    # Update both title and text
    praisonaiwp widget update 1 --title "New Title" --text "New content"

    # Update on specific server
    praisonaiwp widget update 1 --title "New Title" --server staging
    """
    try:
        config = Config()
        server_config = config.get_server(server) if server else config.get_default_server()

        if not server_config:
            console.print(f"[red]Server '{server}' not found in configuration[/red]")
            return

        ssh = SSHManager.from_config(config, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Build options dictionary
        options = {}
        if title is not None:
            options['title'] = title
        if text is not None:
            options['text'] = text

        if not options:
            console.print("[yellow]No options specified for update[/yellow]")
            return

        success = client.update_widget(widget_id, options)

        if success:
            console.print(f"[green]Successfully updated widget '{widget_id}'[/green]")
            for key, value in options.items():
                console.print(f"[cyan]{key}:[/cyan] {value}")
        else:
            console.print(f"[red]Failed to update widget '{widget_id}'[/red]")
            raise click.Abort()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Update widget failed: {e}")
        raise click.Abort() from None
