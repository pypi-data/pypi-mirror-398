"""WordPress cache management commands"""

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
def cache_command():
    """Manage WordPress cache"""
    pass


@cache_command.command("flush")
@click.option("--type", "cache_type", help="Specific cache type to flush")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def flush_cache(ctx, cache_type, server, json_output):
    """
    Flush WordPress cache

    Examples:
    # Flush all cache
    praisonaiwp cache flush

    # Flush specific cache type
    praisonaiwp cache flush --type=object

    # JSON output for scripting
    praisonaiwp --json cache flush
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "cache flush", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Flush cache
        success = client.cache_flush(cache_type)

        if not success:
            error_msg = "Failed to flush cache"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "cache flush", "CACHE_FLUSH_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(
                {"flushed": True, "type": cache_type or "all"},
                "cache flush",
                "cache flush"
            )
            click.echo(AIFormatter.format_output(response))
        else:
            cache_desc = f" ({cache_type})" if cache_type else ""
            console.print(f"[green]✓[/green] Cache flushed successfully{cache_desc}")

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "cache flush", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Cache flush failed: {e}")
        raise click.Abort() from None


@cache_command.command("add")
@click.argument("key")
@click.argument("value")
@click.option("--group", help="Cache group")
@click.option("--expire", type=int, help="Expiration time in seconds")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def add_cache(ctx, key, value, group, expire, server, json_output):
    """
    Add item to cache

    Examples:
    # Add cache item
    praisonaiwp cache add "my_key" "my_value"

    # Add with group and expiration
    praisonaiwp cache add "my_key" "my_value" --group=posts --expire=3600
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "cache add", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Add cache item
        success = client.cache_add(key, value, group, expire)

        if not success:
            error_msg = "Failed to add cache item"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "cache add", "CACHE_ADD_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(
                {"key": key, "group": group, "expire": expire},
                "cache add",
                "cache add"
            )
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[green]✓[/green] Cache item '{key}' added successfully")
            if group:
                console.print(f"  Group: {group}")
            if expire:
                console.print(f"  Expires in: {expire} seconds")

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "cache add", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Cache add failed: {e}")
        raise click.Abort() from None


@cache_command.command("get")
@click.argument("key")
@click.option("--group", help="Cache group")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def get_cache(ctx, key, group, server, json_output):
    """
    Get item from cache

    Examples:
    # Get cache item
    praisonaiwp cache get "my_key"

    # Get from specific group
    praisonaiwp cache get "my_key" --group=posts
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "cache get", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Get cache item
        value = client.cache_get(key, group)

        if value is None:
            error_msg = f"Cache item '{key}' not found"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "cache get", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[yellow]{error_msg}[/yellow]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(
                {"key": key, "value": value, "group": group},
                "cache get",
                "cache get"
            )
            click.echo(AIFormatter.format_output(response))
        else:
            table = Table(title="Cache Item")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Key", key)
            table.add_row("Value", value)
            if group:
                table.add_row("Group", group)

            console.print(table)

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "cache get", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Cache get failed: {e}")
        raise click.Abort() from None


@cache_command.command("delete")
@click.argument("key")
@click.option("--group", help="Cache group")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def delete_cache(ctx, key, group, server, json_output):
    """
    Delete item from cache

    Examples:
    # Delete cache item
    praisonaiwp cache delete "my_key"

    # Delete from specific group
    praisonaiwp cache delete "my_key" --group=posts
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "cache delete", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Delete cache item
        success = client.cache_delete(key, group)

        if not success:
            error_msg = "Failed to delete cache item"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "cache delete", "CACHE_DELETE_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(
                {"key": key, "group": group, "deleted": True},
                "cache delete",
                "cache delete"
            )
            click.echo(AIFormatter.format_output(response))
        else:
            group_desc = f" from group '{group}'" if group else ""
            console.print(f"[green]✓[/green] Cache item '{key}' deleted successfully{group_desc}")

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "cache delete", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Cache delete failed: {e}")
        raise click.Abort() from None


@cache_command.command("list")
@click.option("--group", help="Cache group")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def list_cache(ctx, group, server, json_output):
    """
    List cache items

    Examples:
    # List all cache items
    praisonaiwp cache list

    # List specific group
    praisonaiwp cache list --group=posts
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "cache list", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # List cache items
        result = client.cache_list(group)

        if "error" in result:
            error_msg = result["error"]
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "cache list", "CACHE_LIST_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(result, "cache list", "cache list")
            click.echo(AIFormatter.format_output(response))
        else:
            if not result:
                console.print("[yellow]No cache items found[/yellow]")
                return

            table = Table(title="Cache Items")
            table.add_column("Key", style="cyan")
            table.add_column("Value", style="green")
            table.add_column("Group", style="yellow")

            for key, item in result.items():
                if isinstance(item, dict):
                    value = item.get('value', 'N/A')
                    item_group = item.get('group', 'N/A')
                else:
                    value = str(item)
                    item_group = group or 'N/A'

                table.add_row(key, value, item_group)

            console.print(table)

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "cache list", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Cache list failed: {e}")
        raise click.Abort() from None
