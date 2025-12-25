"""WordPress network management commands"""

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
def network_command():
    """Manage WordPress multisite network"""
    pass


@network_command.group("meta")
def network_meta():
    """Manage network meta"""
    pass


@network_meta.command("get")
@click.argument("meta_key")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def network_meta_get(ctx, meta_key, server, json_output):
    """
    Get network meta value

    Examples:
    # Get network meta value
    praisonaiwp network meta get "site_name"
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "network meta get", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Get network meta value
        result = client.network_meta_get(meta_key)

        if result is None:
            error_msg = f"Network meta key '{meta_key}' not found"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "network meta get", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[yellow]{error_msg}[/yellow]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(
                {"meta_key": meta_key, "meta_value": result},
                "network meta get",
                "network meta get"
            )
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[green]{result}[/green]")

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "network meta get", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Network meta get failed: {e}")
        raise click.Abort() from None


@network_meta.command("set")
@click.argument("meta_key")
@click.argument("meta_value")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def network_meta_set(ctx, meta_key, meta_value, server, json_output):
    """
    Set network meta value

    Examples:
    # Set network meta value
    praisonaiwp network meta set "site_name" "My Network"
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "network meta set", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Set network meta value
        success = client.network_meta_set(meta_key, meta_value)

        if not success:
            error_msg = "Failed to set network meta"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "network meta set", "NETWORK_META_SET_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(
                {"meta_key": meta_key, "meta_value": meta_value, "set": True},
                "network meta set",
                "network meta set"
            )
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[green]✓[/green] Network meta '{meta_key}' set successfully")

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "network meta set", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Network meta set failed: {e}")
        raise click.Abort() from None


@network_meta.command("delete")
@click.argument("meta_key")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def network_meta_delete(ctx, meta_key, server, json_output):
    """
    Delete network meta

    Examples:
    # Delete network meta
    praisonaiwp network meta delete "site_name"
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "network meta delete", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Delete network meta
        success = client.network_meta_delete(meta_key)

        if not success:
            error_msg = "Failed to delete network meta"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "network meta delete", "NETWORK_META_DELETE_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(
                {"meta_key": meta_key, "deleted": True},
                "network meta delete",
                "network meta delete"
            )
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[green]✓[/green] Network meta '{meta_key}' deleted successfully")

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "network meta delete", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Network meta delete failed: {e}")
        raise click.Abort() from None


@network_meta.command("list")
@click.option("--format", "format_type", default="table", type=click.Choice(['table', 'json']), help="Output format")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def network_meta_list(ctx, format_type, server, json_output):
    """
    List network meta

    Examples:
    # List network meta in table format
    praisonaiwp network meta list

    # List in JSON format
    praisonaiwp network meta list --format=json
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "network meta list", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # List network meta
        result = client.network_meta_list(format_type)

        if "error" in result:
            error_msg = result["error"]
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "network meta list", "NETWORK_META_LIST_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(result, "network meta list", "network meta list")
            click.echo(AIFormatter.format_output(response))
        else:
            if format_type == "json":
                console.print(result)
            else:
                if not result.get("meta"):
                    console.print("[yellow]No network meta found[/yellow]")
                    return

                table = Table(title="Network Meta")
                table.add_column("Meta ID", style="cyan")
                table.add_column("Meta Key", style="green")
                table.add_column("Meta Value", style="yellow")

                for meta in result["meta"]:
                    table.add_row(meta["meta_id"], meta["meta_key"], meta["meta_value"])

                console.print(table)

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "network meta list", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Network meta list failed: {e}")
        raise click.Abort() from None


@network_command.group("option")
def network_option():
    """Manage network options"""
    pass


@network_option.command("get")
@click.argument("option_name")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def network_option_get(ctx, option_name, server, json_output):
    """
    Get network option value

    Examples:
    # Get network option value
    praisonaiwp network option get "site_name"
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "network option get", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Get network option value
        result = client.network_option_get(option_name)

        if result is None:
            error_msg = f"Network option '{option_name}' not found"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "network option get", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[yellow]{error_msg}[/yellow]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(
                {"option_name": option_name, "option_value": result},
                "network option get",
                "network option get"
            )
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[green]{result}[/green]")

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "network option get", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Network option get failed: {e}")
        raise click.Abort() from None


@network_option.command("set")
@click.argument("option_name")
@click.argument("option_value")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def network_option_set(ctx, option_name, option_value, server, json_output):
    """
    Set network option value

    Examples:
    # Set network option value
    praisonaiwp network option set "site_name" "My Network"
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "network option set", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Set network option value
        success = client.network_option_set(option_name, option_value)

        if not success:
            error_msg = "Failed to set network option"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "network option set", "NETWORK_OPTION_SET_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(
                {"option_name": option_name, "option_value": option_value, "set": True},
                "network option set",
                "network option set"
            )
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[green]✓[/green] Network option '{option_name}' set successfully")

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "network option set", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Network option set failed: {e}")
        raise click.Abort() from None


@network_option.command("delete")
@click.argument("option_name")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def network_option_delete(ctx, option_name, server, json_output):
    """
    Delete network option

    Examples:
    # Delete network option
    praisonaiwp network option delete "site_name"
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "network option delete", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Delete network option
        success = client.network_option_delete(option_name)

        if not success:
            error_msg = "Failed to delete network option"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "network option delete", "NETWORK_OPTION_DELETE_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(
                {"option_name": option_name, "deleted": True},
                "network option delete",
                "network option delete"
            )
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[green]✓[/green] Network option '{option_name}' deleted successfully")

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "network option delete", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Network option delete failed: {e}")
        raise click.Abort() from None


@network_option.command("list")
@click.option("--format", "format_type", default="table", type=click.Choice(['table', 'json']), help="Output format")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def network_option_list(ctx, format_type, server, json_output):
    """
    List network options

    Examples:
    # List network options in table format
    praisonaiwp network option list

    # List in JSON format
    praisonaiwp network option list --format=json
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "network option list", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # List network options
        result = client.network_option_list(format_type)

        if "error" in result:
            error_msg = result["error"]
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "network option list", "NETWORK_OPTION_LIST_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(result, "network option list", "network option list")
            click.echo(AIFormatter.format_output(response))
        else:
            if format_type == "json":
                console.print(result)
            else:
                if not result.get("options"):
                    console.print("[yellow]No network options found[/yellow]")
                    return

                table = Table(title="Network Options")
                table.add_column("Option Name", style="cyan")
                table.add_column("Option Value", style="green")

                for option in result["options"]:
                    table.add_row(option["option_name"], option["option_value"])

                console.print(table)

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "network option list", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Network option list failed: {e}")
        raise click.Abort() from None
