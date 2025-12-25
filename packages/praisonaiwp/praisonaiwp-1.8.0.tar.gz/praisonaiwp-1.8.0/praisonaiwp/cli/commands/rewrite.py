"""WordPress rewrite management commands"""

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
def rewrite_command():
    """Manage WordPress rewrite rules and permalinks"""
    pass


@rewrite_command.command("list")
@click.option("--format", "format_type", default="table", type=click.Choice(['table', 'json']), help="Output format")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def list_rewrite(ctx, format_type, server, json_output):
    """
    List WordPress rewrite rules

    Examples:
    # List rewrite rules in table format
    praisonaiwp rewrite list

    # List in JSON format
    praisonaiwp rewrite list --format=json

    # JSON output for scripting
    praisonaiwp --json rewrite list
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "rewrite list", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # List rewrite rules
        result = client.rewrite_list(format_type)

        if "error" in result:
            error_msg = result["error"]
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "rewrite list", "REWRITE_LIST_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(result, "rewrite list", "rewrite list")
            click.echo(AIFormatter.format_output(response))
        else:
            if format_type == "json":
                console.print(result)
            else:
                if not result.get("rules"):
                    console.print("[yellow]No rewrite rules found[/yellow]")
                    return

                table = Table(title="Rewrite Rules")
                table.add_column("Match", style="cyan")
                table.add_column("Source", style="green")
                table.add_column("Query", style="yellow")

                for rule in result["rules"]:
                    table.add_row(rule["match"], rule["source"], rule["query"])

                console.print(table)

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "rewrite list", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Rewrite list failed: {e}")
        raise click.Abort() from None


@rewrite_command.command("flush")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def flush_rewrite(ctx, server, json_output):
    """
    Flush WordPress rewrite rules

    Examples:
    # Flush rewrite rules
    praisonaiwp rewrite flush

    # JSON output for scripting
    praisonaiwp --json rewrite flush
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "rewrite flush", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Flush rewrite rules
        success = client.rewrite_flush()

        if not success:
            error_msg = "Failed to flush rewrite rules"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "rewrite flush", "REWRITE_FLUSH_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(
                {"flushed": True},
                "rewrite flush",
                "rewrite flush"
            )
            click.echo(AIFormatter.format_output(response))
        else:
            console.print("[green]✓[/green] Rewrite rules flushed successfully")

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "rewrite flush", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Rewrite flush failed: {e}")
        raise click.Abort() from None


@rewrite_command.command("structure")
@click.argument("structure")
@click.option("--category-base", help="Category base")
@click.option("--tag-base", help="Tag base")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def set_structure(ctx, structure, category_base, tag_base, server, json_output):
    """
    Update permalink structure

    Examples:
    # Set permalink structure
    praisonaiwp rewrite structure "/%postname%/"

    # Set with category and tag bases
    praisonaiwp rewrite structure "/%category%/%postname%/" --category-base="category" --tag-base="tag"
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "rewrite structure", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Set permalink structure
        success = client.rewrite_structure(structure, category_base, tag_base)

        if not success:
            error_msg = "Failed to update permalink structure"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "rewrite structure", "REWRITE_STRUCTURE_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(
                {"structure": structure, "category_base": category_base, "tag_base": tag_base},
                "permalink structure update",
                "rewrite structure"
            )
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[green]✓[/green] Permalink structure updated to: {structure}")
            if category_base:
                console.print(f"  Category base: {category_base}")
            if tag_base:
                console.print(f"  Tag base: {tag_base}")

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "rewrite structure", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Rewrite structure failed: {e}")
        raise click.Abort() from None


@rewrite_command.command("get")
@click.argument("type")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def get_rewrite(ctx, type, server, json_output):
    """
    Get rewrite rule by type

    Examples:
    # Get rewrite rule
    praisonaiwp rewrite get "category"

    # Get author rewrite rule
    praisonaiwp rewrite get "author"
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "rewrite get", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Get rewrite rule
        rule = client.rewrite_get(type)

        if rule is None:
            error_msg = f"Rewrite rule '{type}' not found"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "rewrite get", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[yellow]{error_msg}[/yellow]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(
                {"type": type, "rule": rule},
                "rewrite get",
                "rewrite get"
            )
            click.echo(AIFormatter.format_output(response))
        else:
            table = Table(title="Rewrite Rule")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Type", type)
            table.add_row("Rule", rule)

            console.print(table)

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "rewrite get", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Rewrite get failed: {e}")
        raise click.Abort() from None


@rewrite_command.command("set")
@click.argument("type")
@click.argument("rule")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def set_rewrite(ctx, type, rule, server, json_output):
    """
    Set rewrite rule

    Examples:
    # Set rewrite rule
    praisonaiwp rewrite set "category" "category/(.+)/?$"

    # Set custom rewrite rule
    praisonaiwp rewrite set "custom" "custom/(.+)/?$"
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "rewrite set", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Set rewrite rule
        success = client.rewrite_set(type, rule)

        if not success:
            error_msg = "Failed to set rewrite rule"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "rewrite set", "REWRITE_SET_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(
                {"type": type, "rule": rule, "set": True},
                "rewrite set",
                "rewrite set"
            )
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[green]✓[/green] Rewrite rule '{type}' set successfully")
            console.print(f"  Rule: {rule}")

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "rewrite set", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Rewrite set failed: {e}")
        raise click.Abort() from None
