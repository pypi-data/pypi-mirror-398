"""WordPress site management commands"""

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
def site_command():
    """Manage WordPress multisite sites"""
    pass


@site_command.command("list")
@click.option("--format", "format_type", default="table", type=click.Choice(['table', 'json']), help="Output format")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def list_sites(ctx, format_type, server, json_output):
    """
    List WordPress multisite sites

    Examples:
    # List sites in table format
    praisonaiwp site list

    # List in JSON format
    praisonaiwp site list --format=json

    # JSON output for scripting
    praisonaiwp --json site list
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "site list", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # List sites
        result = client.site_list(format_type)

        if "error" in result:
            error_msg = result["error"]
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "site list", "SITE_LIST_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(result, "site list", "site list")
            click.echo(AIFormatter.format_output(response))
        else:
            if format_type == "json":
                console.print(result)
            else:
                if not result.get("sites"):
                    console.print("[yellow]No sites found[/yellow]")
                    return

                table = Table(title="Sites")
                table.add_column("Blog ID", style="cyan")
                table.add_column("URL", style="green")
                table.add_column("Last Updated", style="yellow")
                table.add_column("Registered", style="magenta")

                for site in result["sites"]:
                    table.add_row(site["blog_id"], site["url"], site["last_updated"], site["registered"])

                console.print(table)

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "site list", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Site list failed: {e}")
        raise click.Abort() from None


@site_command.command("get")
@click.argument("site_id")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def get_site(ctx, site_id, server, json_output):
    """
    Get site information by ID

    Examples:
    # Get site information
    praisonaiwp site get "1"

    # Get site by URL
    praisonaiwp site get "example.com"
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "site get", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Get site information
        result = client.site_get(site_id)

        if result is None:
            error_msg = f"Site '{site_id}' not found"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "site get", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[yellow]{error_msg}[/yellow]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(result, "site get", "site get")
            click.echo(AIFormatter.format_output(response))
        else:
            table = Table(title=f"Site: {site_id}")
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
            response = AIFormatter.error_response(error_msg, "site get", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Site get failed: {e}")
        raise click.Abort() from None


@site_command.command("create")
@click.argument("url")
@click.argument("title")
@click.argument("email")
@click.option("--site-id", help="Site ID")
@click.option("--private/--public", default=None, help="Whether site is private")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def create_site(ctx, url, title, email, site_id, private, server, json_output):
    """
    Create a new site in multisite

    Examples:
    # Create basic site
    praisonaiwp site create "example.com" "Example Site" "admin@example.com"

    # Create with site ID
    praisonaiwp site create "example.com" "Example Site" "admin@example.com" --site-id=2

    # Create private site
    praisonaiwp site create "example.com" "Example Site" "admin@example.com" --private
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "site create", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Create site
        success = client.site_create(url, title, email, site_id, private)

        if not success:
            error_msg = "Failed to create site"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "site create", "SITE_CREATE_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(
                {"url": url, "title": title, "email": email, "site_id": site_id, "private": private},
                "site create",
                "site create"
            )
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[green]✓[/green] Site '{url}' created successfully")
            console.print(f"  Title: {title}")
            console.print(f"  Email: {email}")
            if site_id:
                console.print(f"  Site ID: {site_id}")
            if private is not None:
                console.print(f"  Private: {private}")

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "site create", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Site create failed: {e}")
        raise click.Abort() from None


@site_command.command("delete")
@click.argument("site_id")
@click.option("--keep-tables", is_flag=True, help="Keep database tables")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def delete_site(ctx, site_id, keep_tables, server, json_output):
    """
    Delete a site from multisite

    Examples:
    # Delete site
    praisonaiwp site delete "1"

    # Delete but keep tables
    praisonaiwp site delete "1" --keep-tables
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "site delete", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Delete site
        success = client.site_delete(site_id, keep_tables)

        if not success:
            error_msg = "Failed to delete site"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "site delete", "SITE_DELETE_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(
                {"site_id": site_id, "deleted": True, "keep_tables": keep_tables},
                "site delete",
                "site delete"
            )
            click.echo(AIFormatter.format_output(response))
        else:
            tables_text = " (tables kept)" if keep_tables else ""
            console.print(f"[green]✓[/green] Site '{site_id}' deleted successfully{tables_text}")

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "site delete", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Site delete failed: {e}")
        raise click.Abort() from None


@site_command.command("activate")
@click.argument("site_id")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def activate_site(ctx, site_id, server, json_output):
    """
    Activate a site theme/plugins

    Examples:
    # Activate site
    praisonaiwp site activate "1"
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "site activate", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Activate site
        success = client.site_activate(site_id)

        if not success:
            error_msg = "Failed to activate site"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "site activate", "SITE_ACTIVATE_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(
                {"site_id": site_id, "activated": True},
                "site activate",
                "site activate"
            )
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[green]✓[/green] Site '{site_id}' activated successfully")

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "site activate", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Site activate failed: {e}")
        raise click.Abort() from None


@site_command.command("deactivate")
@click.argument("site_id")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def deactivate_site(ctx, site_id, server, json_output):
    """
    Deactivate a site theme/plugins

    Examples:
    # Deactivate site
    praisonaiwp site deactivate "1"
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "site deactivate", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Deactivate site
        success = client.site_deactivate(site_id)

        if not success:
            error_msg = "Failed to deactivate site"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "site deactivate", "SITE_DEACTIVATE_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(
                {"site_id": site_id, "deactivated": True},
                "site deactivate",
                "site deactivate"
            )
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[green]✓[/green] Site '{site_id}' deactivated successfully")

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "site deactivate", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Site deactivate failed: {e}")
        raise click.Abort() from None


@site_command.command("archive")
@click.argument("site_id")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def archive_site(ctx, site_id, server, json_output):
    """
    Archive a site

    Examples:
    # Archive site
    praisonaiwp site archive "1"
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "site archive", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Archive site
        success = client.site_archive(site_id)

        if not success:
            error_msg = "Failed to archive site"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "site archive", "SITE_ARCHIVE_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(
                {"site_id": site_id, "archived": True},
                "site archive",
                "site archive"
            )
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[green]✓[/green] Site '{site_id}' archived successfully")

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "site archive", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Site archive failed: {e}")
        raise click.Abort() from None


@site_command.command("unarchive")
@click.argument("site_id")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def unarchive_site(ctx, site_id, server, json_output):
    """
    Unarchive a site

    Examples:
    # Unarchive site
    praisonaiwp site unarchive "1"
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "site unarchive", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Unarchive site
        success = client.site_unarchive(site_id)

        if not success:
            error_msg = "Failed to unarchive site"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "site unarchive", "SITE_UNARCHIVE_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(
                {"site_id": site_id, "unarchived": True},
                "site unarchive",
                "site unarchive"
            )
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[green]✓[/green] Site '{site_id}' unarchived successfully")

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "site unarchive", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Site unarchive failed: {e}")
        raise click.Abort() from None


@site_command.command("spam")
@click.argument("site_id")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def spam_site(ctx, site_id, server, json_output):
    """
    Mark a site as spam

    Examples:
    # Mark site as spam
    praisonaiwp site spam "1"
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "site spam", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Mark site as spam
        success = client.site_spam(site_id)

        if not success:
            error_msg = "Failed to mark site as spam"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "site spam", "SITE_SPAM_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(
                {"site_id": site_id, "spammed": True},
                "site spam",
                "site spam"
            )
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[green]✓[/green] Site '{site_id}' marked as spam successfully")

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "site spam", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Site spam failed: {e}")
        raise click.Abort() from None


@site_command.command("unspam")
@click.argument("site_id")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def unspam_site(ctx, site_id, server, json_output):
    """
    Unmark a site as spam

    Examples:
    # Unmark site as spam
    praisonaiwp site unspam "1"
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "site unspam", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Unmark site as spam
        success = client.site_unspam(site_id)

        if not success:
            error_msg = "Failed to unmark site as spam"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "site unspam", "SITE_UNSPAM_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(
                {"site_id": site_id, "unspammed": True},
                "site unspam",
                "site unspam"
            )
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[green]✓[/green] Site '{site_id}' unmarked as spam successfully")

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "site unspam", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Site unspam failed: {e}")
        raise click.Abort() from None
