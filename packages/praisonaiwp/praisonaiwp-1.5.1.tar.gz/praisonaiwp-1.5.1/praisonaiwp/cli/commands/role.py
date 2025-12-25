"""WordPress role management commands"""


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
def role_command():
    """Manage WordPress user roles"""
    pass


@role_command.command("list")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def list_roles(ctx, server, json_output):
    """
    List WordPress user roles

    Examples:
    # List all roles
    praisonaiwp role list

    # List from specific server
    praisonaiwp role list --server staging
    """
    try:
        config = Config()
        server_config = config.get_server(server) if server else config.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "role list", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        roles = client.list_roles()

        if not roles:
            message = "No roles found"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.list_response([], 0, "role list")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[yellow]{message}[/yellow]")
            return

        # JSON output for scripting
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.list_response(roles, len(roles), "role list")
            click.echo(AIFormatter.format_output(response))
        else:
            # Human-readable table output
            table = Table(title="WordPress User Roles")
            table.add_column("Name", style="cyan", no_wrap=True)
            table.add_column("Display Name", style="green")

            for role in roles:
                table.add_row(
                    role.get('name', 'N/A'),
                    role.get('display_name', 'N/A')
                )

            console.print(table)

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "role list", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"List roles failed: {e}")
        raise click.Abort() from None


@role_command.command("get")
@click.argument("role")
@click.option("--server", default=None, help="Server name from config")
def get_role(role, server):
    """
    Get WordPress role information

    Examples:
    # Get role info
    praisonaiwp role get editor

    # Get from specific server
    praisonaiwp role get administrator --server staging
    """
    try:
        config = Config()
        server_config = config.get_server(server) if server else config.get_default_server()

        if not server_config:
            console.print(f"[red]Server '{server}' not found in configuration[/red]")
            return

        ssh = SSHManager.from_config(config, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        role_info = client.get_role(role)

        if role_info:
            console.print("[green]Role Information:[/green]")
            console.print(f"[cyan]Name:[/cyan] {role_info.get('name', 'N/A')}")
            console.print(f"[cyan]Display Name:[/cyan] {role_info.get('display_name', 'N/A')}")

            # Display capabilities if available
            capabilities = role_info.get('capabilities', [])
            if capabilities:
                console.print("[cyan]Capabilities:[/cyan]")
                for capability in capabilities:
                    console.print(f"  • {capability}")
        else:
            console.print(f"[yellow]Role '{role}' not found[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Get role failed: {e}")
        raise click.Abort() from None


@role_command.command("create")
@click.argument("role_key")
@click.argument("role_name")
@click.option("--capabilities", default=None, help="Comma-separated list of capabilities")
@click.option("--server", default=None, help="Server name from config")
def create_role(role_key, role_name, capabilities, server):
    """
    Create a WordPress user role

    Examples:
    # Create a basic role
    praisonaiwp role create custom_role "Custom Role"

    # Create role with capabilities
    praisonaiwp role create moderator "Moderator" --capabilities "edit_posts,moderate_comments"

    # Create on specific server
    praisonaiwp role create custom_role "Custom Role" --server staging
    """
    try:
        config = Config()
        server_config = config.get_server(server) if server else config.get_default_server()

        if not server_config:
            console.print(f"[red]Server '{server}' not found in configuration[/red]")
            return

        ssh = SSHManager.from_config(config, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        success = client.create_role(role_key, role_name, capabilities)

        if success:
            console.print(f"[green]Successfully created role '{role_name}' ({role_key})[/green]")
            if capabilities:
                console.print(f"[cyan]Capabilities:[/cyan] {capabilities}")
        else:
            console.print(f"[red]Failed to create role '{role_key}'[/red]")
            raise click.Abort()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Create role failed: {e}")
        raise click.Abort() from None


@role_command.command("delete")
@click.argument("role")
@click.option("--server", default=None, help="Server name from config")
def delete_role(role, server):
    """
    Delete a WordPress user role

    Examples:
    # Delete a role
    praisonaiwp role delete custom_role

    # Delete from specific server
    praisonaiwp role delete custom_role --server staging
    """
    try:
        config = Config()
        server_config = config.get_server(server) if server else config.get_default_server()

        if not server_config:
            console.print(f"[red]Server '{server}' not found in configuration[/red]")
            return

        ssh = SSHManager.from_config(config, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        success = client.delete_role(role)

        if success:
            console.print(f"[green]Successfully deleted role '{role}'[/green]")
        else:
            console.print(f"[red]Failed to delete role '{role}'[/red]")
            raise click.Abort()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Delete role failed: {e}")
        raise click.Abort() from None
