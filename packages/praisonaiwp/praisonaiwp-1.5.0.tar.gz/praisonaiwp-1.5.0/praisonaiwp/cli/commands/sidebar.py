"""WordPress sidebar management commands"""

import click
from rich.console import Console
from rich.table import Table

from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.utils.ai_formatter import AIFormatter
from praisonaiwp.utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


@click.group()
def sidebar_command():
    """Manage WordPress sidebars and widgets"""
    pass


@sidebar_command.command("list")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def list_sidebars(ctx, server, json_output):
    """
    List WordPress sidebars

    Examples:
    # List all sidebars
    praisonaiwp sidebar list

    # JSON output for scripting
    praisonaiwp --json sidebar list
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "sidebar list", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # List sidebars
        result = client.sidebar_list()

        if "error" in result:
            error_msg = result["error"]
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "sidebar list", "SIDEBAR_LIST_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(result, "sidebar list", "sidebar list")
            click.echo(AIFormatter.format_output(response))
        else:
            if not result:
                console.print("[yellow]No sidebars found[/yellow]")
                return

            table = Table(title="Sidebars")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Description", style="yellow")

            for sidebar_id, sidebar_info in result.items():
                if isinstance(sidebar_info, dict):
                    name = sidebar_info.get('name', sidebar_id)
                    description = sidebar_info.get('description', '')
                else:
                    name = sidebar_info
                    description = ''

                table.add_row(sidebar_id, name, description)

            console.print(table)

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "sidebar list", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Sidebar list failed: {e}")
        raise click.Abort() from None


@sidebar_command.command("get")
@click.argument("sidebar_id")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def get_sidebar(ctx, sidebar_id, server, json_output):
    """
    Get sidebar information by ID

    Examples:
    # Get sidebar information
    praisonaiwp sidebar get "sidebar-1"

    # Get specific sidebar details
    praisonaiwp sidebar get "footer-widgets"
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "sidebar get", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Get sidebar information
        result = client.sidebar_get(sidebar_id)

        if result is None:
            error_msg = f"Sidebar '{sidebar_id}' not found"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "sidebar get", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[yellow]{error_msg}[/yellow]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(result, "sidebar get", "sidebar get")
            click.echo(AIFormatter.format_output(response))
        else:
            table = Table(title=f"Sidebar: {sidebar_id}")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")

            for key, value in result.items():
                if isinstance(value, list):
                    value = ", ".join(str(v) for v in value)
                table.add_row(key, str(value))

            console.print(table)

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "sidebar get", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Sidebar get failed: {e}")
        raise click.Abort() from None


@sidebar_command.command("update")
@click.argument("sidebar_id")
@click.argument("widgets", nargs=-1, required=False)
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def update_sidebar(ctx, sidebar_id, widgets, server, json_output):
    """
    Update sidebar with widgets

    Examples:
    # Update sidebar with widgets
    praisonaiwp sidebar update "sidebar-1" "widget-1" "widget-2"

    # Empty sidebar (no widgets)
    praisonaiwp sidebar update "sidebar-1"
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "sidebar update", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Update sidebar
        success = client.sidebar_update(sidebar_id, list(widgets))

        if not success:
            error_msg = "Failed to update sidebar"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "sidebar update", "SIDEBAR_UPDATE_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(
                {"sidebar_id": sidebar_id, "widgets": list(widgets)},
                "sidebar update",
                "sidebar update"
            )
            click.echo(AIFormatter.format_output(response))
        else:
            if widgets:
                console.print(f"[green]✓[/green] Sidebar '{sidebar_id}' updated with {len(widgets)} widgets")
                console.print(f"  Widgets: {', '.join(widgets)}")
            else:
                console.print(f"[green]✓[/green] Sidebar '{sidebar_id}' emptied")

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "sidebar update", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Sidebar update failed: {e}")
        raise click.Abort() from None


@sidebar_command.command("add-widget")
@click.argument("sidebar_id")
@click.argument("widget_id")
@click.option("--position", type=int, help="Position in sidebar")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def add_widget(ctx, sidebar_id, widget_id, position, server, json_output):
    """
    Add widget to sidebar

    Examples:
    # Add widget to sidebar
    praisonaiwp sidebar add-widget "sidebar-1" "search-2"

    # Add widget at specific position
    praisonaiwp sidebar add-widget "sidebar-1" "search-2" --position=1
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "sidebar add-widget", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Add widget to sidebar
        success = client.sidebar_add_widget(sidebar_id, widget_id, position)

        if not success:
            error_msg = "Failed to add widget to sidebar"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "sidebar add-widget", "SIDEBAR_ADD_WIDGET_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(
                {"sidebar_id": sidebar_id, "widget_id": widget_id, "position": position},
                "sidebar add-widget",
                "sidebar add-widget"
            )
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[green]✓[/green] Widget '{widget_id}' added to sidebar '{sidebar_id}' successfully")
            if position is not None:
                console.print(f"  Position: {position}")

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "sidebar add-widget", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Sidebar add-widget failed: {e}")
        raise click.Abort() from None


@sidebar_command.command("remove-widget")
@click.argument("sidebar_id")
@click.argument("widget_id")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def remove_widget(ctx, sidebar_id, widget_id, server, json_output):
    """
    Remove widget from sidebar

    Examples:
    # Remove widget from sidebar
    praisonaiwp sidebar remove-widget "sidebar-1" "search-2"
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "sidebar remove-widget", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Remove widget from sidebar
        success = client.sidebar_remove_widget(sidebar_id, widget_id)

        if not success:
            error_msg = "Failed to remove widget from sidebar"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "sidebar remove-widget", "SIDEBAR_REMOVE_WIDGET_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(
                {"sidebar_id": sidebar_id, "widget_id": widget_id, "removed": True},
                "sidebar remove-widget",
                "sidebar remove-widget"
            )
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[green]✓[/green] Widget '{widget_id}' removed from sidebar '{sidebar_id}' successfully")

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "sidebar remove-widget", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Sidebar remove-widget failed: {e}")
        raise click.Abort() from None


@sidebar_command.command("empty")
@click.argument("sidebar_id")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def empty_sidebar(ctx, sidebar_id, server, json_output):
    """
    Empty all widgets from sidebar

    Examples:
    # Empty sidebar
    praisonaiwp sidebar empty "sidebar-1"
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "sidebar empty", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Empty sidebar
        success = client.sidebar_empty(sidebar_id)

        if not success:
            error_msg = "Failed to empty sidebar"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "sidebar empty", "SIDEBAR_EMPTY_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(
                {"sidebar_id": sidebar_id, "emptied": True},
                "sidebar empty",
                "sidebar empty"
            )
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[green]✓[/green] Sidebar '{sidebar_id}' emptied successfully")

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "sidebar empty", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Sidebar empty failed: {e}")
        raise click.Abort() from None
