"""WordPress super-admin management commands"""

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
def super_admin_command():
    """Manage WordPress multisite super admins"""
    pass


@super_admin_command.command("list")
@click.option("--format", "format_type", default="table", type=click.Choice(['table', 'json']), help="Output format")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def list_super_admins(ctx, format_type, server, json_output):
    """
    List WordPress multisite super admins

    Examples:
    # List super admins in table format
    praisonaiwp super-admin list

    # List in JSON format
    praisonaiwp super-admin list --format=json

    # JSON output for scripting
    praisonaiwp --json super-admin list
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "super-admin list", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # List super admins
        result = client.super_admin_list(format_type)

        if "error" in result:
            error_msg = result["error"]
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "super-admin list", "SUPER_ADMIN_LIST_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(result, "super-admin list", "super-admin list")
            click.echo(AIFormatter.format_output(response))
        else:
            if format_type == "json":
                console.print(result)
            else:
                if not result.get("super_admins"):
                    console.print("[yellow]No super admins found[/yellow]")
                    return

                table = Table(title="Super Admins")
                table.add_column("User ID", style="cyan")
                table.add_column("Email", style="green")
                table.add_column("Login", style="yellow")

                for admin in result["super_admins"]:
                    table.add_row(admin["user_id"], admin["user_email"], admin["user_login"])

                console.print(table)

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "super-admin list", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Super-admin list failed: {e}")
        raise click.Abort() from None


@super_admin_command.command("add")
@click.argument("user_id")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def add_super_admin(ctx, user_id, server, json_output):
    """
    Add super admin to multisite

    Examples:
    # Add super admin by user ID
    praisonaiwp super-admin add "1"

    # Add super admin by email
    praisonaiwp super-admin add "admin@example.com"
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "super-admin add", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Add super admin
        success = client.super_admin_add(user_id)

        if not success:
            error_msg = "Failed to add super admin"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "super-admin add", "SUPER_ADMIN_ADD_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(
                {"user_id": user_id, "added": True},
                "super-admin add",
                "super-admin add"
            )
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[green]✓[/green] Super admin '{user_id}' added successfully")

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "super-admin add", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Super-admin add failed: {e}")
        raise click.Abort() from None


@super_admin_command.command("remove")
@click.argument("user_id")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def remove_super_admin(ctx, user_id, server, json_output):
    """
    Remove super admin from multisite

    Examples:
    # Remove super admin by user ID
    praisonaiwp super-admin remove "1"

    # Remove super admin by email
    praisonaiwp super-admin remove "admin@example.com"
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "super-admin remove", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Remove super admin
        success = client.super_admin_remove(user_id)

        if not success:
            error_msg = "Failed to remove super admin"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "super-admin remove", "SUPER_ADMIN_REMOVE_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(
                {"user_id": user_id, "removed": True},
                "super-admin remove",
                "super-admin remove"
            )
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[green]✓[/green] Super admin '{user_id}' removed successfully")

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "super-admin remove", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Super-admin remove failed: {e}")
        raise click.Abort() from None
