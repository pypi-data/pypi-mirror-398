"""WordPress search-replace commands"""


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
def search_replace_command():
    """Manage WordPress search-replace operations"""
    pass


@search_replace_command.command("run")
@click.argument("search")
@click.argument("replace")
@click.option("--table", help="Specific table to search")
@click.option("--dry-run", is_flag=True, help="Show what would be replaced without doing it")
@click.option("--regex", is_flag=True, help="Use regular expressions")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def run_search_replace(ctx, search, replace, table, dry_run, regex, server, json_output):
    """
    Search and replace in database

    Examples:
    # Basic search and replace
    praisonaiwp search-replace run "old-domain.com" "new-domain.com"

    # Dry run to preview changes
    praisonaiwp search-replace run "old" "new" --dry-run

    # Search in specific table
    praisonaiwp search-replace run "http://old.com" "https://new.com" --table=wp_posts

    # Use regular expressions
    praisonaiwp search-replace run "old-(\\d+)" "new-\\1" --regex

    # JSON output for scripting
    praisonaiwp --json search-replace run "old" "new"
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "search-replace run", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Perform search-replace
        result = client.search_replace(search, replace, table, dry_run, regex)

        if "error" in result:
            error_msg = result["error"]
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "search-replace run", "SEARCH_REPLACE_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(result, "search-replace operation", "search-replace run")
            click.echo(AIFormatter.format_output(response))
        else:
            # Human-friendly output
            table = Table(title="Search-Replace Results")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Search", search)
            table.add_row("Replace", replace)

            if table:
                table.add_row("Table", table)

            table.add_row("Dry Run", "Yes" if dry_run else "No")
            table.add_row("Regex", "Yes" if regex else "No")

            # Add results from WP-CLI
            if "success" in result:
                table.add_row("Status", "[green]Success[/green]")
            if "tables" in result:
                for table_name, table_data in result["tables"].items():
                    if isinstance(table_data, dict):
                        if "rows" in table_data:
                            table.add_row(f"Rows in {table_name}", str(table_data["rows"]))
                        if "changes" in table_data:
                            table.add_row(f"Changes in {table_name}", str(table_data["changes"]))

            console.print(table)

            if dry_run:
                console.print("\n[yellow]This was a dry run. No changes were made.[/yellow]")
                console.print("Run without --dry-run to apply changes.")

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "search-replace run", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Search-replace failed: {e}")
        raise click.Abort() from None


@search_replace_command.command("db-optimize")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def optimize_database(ctx, server, json_output):
    """
    Optimize database

    Examples:
    # Optimize database
    praisonaiwp search-replace db-optimize

    # Optimize specific server
    praisonaiwp search-replace db-optimize --server staging
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "search-replace db-optimize", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Optimize database
        success = client.db_optimize()

        if not success:
            error_msg = "Failed to optimize database"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "search-replace db-optimize", "DB_OPTIMIZE_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(
                {"optimized": True},
                "database optimization",
                "search-replace db-optimize"
            )
            click.echo(AIFormatter.format_output(response))
        else:
            console.print("[green]✓[/green] Database optimized successfully!")

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "search-replace db-optimize", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Database optimize failed: {e}")
        raise click.Abort() from None


@search_replace_command.command("db-repair")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def repair_database(ctx, server, json_output):
    """
    Repair database

    Examples:
    # Repair database
    praisonaiwp search-replace db-repair

    # Repair specific server
    praisonaiwp search-replace db-repair --server staging
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "search-replace db-repair", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Repair database
        success = client.db_repair()

        if not success:
            error_msg = "Failed to repair database"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "search-replace db-repair", "DB_REPAIR_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(
                {"repaired": True},
                "database repair",
                "search-replace db-repair"
            )
            click.echo(AIFormatter.format_output(response))
        else:
            console.print("[green]✓[/green] Database repaired successfully!")

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "search-replace db-repair", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Database repair failed: {e}")
        raise click.Abort() from None


@search_replace_command.command("db-check")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def check_database(ctx, server, json_output):
    """
    Check database status

    Examples:
    # Check database
    praisonaiwp search-replace db-check

    # Check specific server
    praisonaiwp search-replace db-check --server staging
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "search-replace db-check", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Check database
        result = client.db_check()

        if "error" in result:
            error_msg = result["error"]
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "search-replace db-check", "DB_CHECK_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(result, "database check", "search-replace db-check")
            click.echo(AIFormatter.format_output(response))
        else:
            # Human-friendly output
            table = Table(title="Database Check Results")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")

            for key, value in result.items():
                if key != "error":
                    table.add_row(key.replace("_", " ").title(), str(value))

            console.print(table)

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "search-replace db-check", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Database check failed: {e}")
        raise click.Abort() from None
