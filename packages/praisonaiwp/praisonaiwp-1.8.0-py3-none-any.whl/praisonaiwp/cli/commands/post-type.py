"""WordPress post-type management commands"""

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
def post_type_command():
    """Manage WordPress post types"""
    pass


@post_type_command.command("list")
@click.option("--format", "format_type", default="table", type=click.Choice(['table', 'json']), help="Output format")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def list_post_types(ctx, format_type, server, json_output):
    """
    List WordPress post types

    Examples:
    # List post types in table format
    praisonaiwp post-type list

    # List in JSON format
    praisonaiwp post-type list --format=json

    # JSON output for scripting
    praisonaiwp --json post-type list
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "post-type list", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # List post types
        result = client.post_type_list(format_type)

        if "error" in result:
            error_msg = result["error"]
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "post-type list", "POST_TYPE_LIST_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(result, "post-type list", "post-type list")
            click.echo(AIFormatter.format_output(response))
        else:
            if format_type == "json":
                console.print(result)
            else:
                if not result.get("post_types"):
                    console.print("[yellow]No post types found[/yellow]")
                    return

                table = Table(title="Post Types")
                table.add_column("Name", style="cyan")
                table.add_column("Description", style="green")

                for post_type in result["post_types"]:
                    table.add_row(post_type["name"], post_type["description"])

                console.print(table)

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "post-type list", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Post-type list failed: {e}")
        raise click.Abort() from None


@post_type_command.command("get")
@click.argument("post_type")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def get_post_type(ctx, post_type, server, json_output):
    """
    Get post type information by name

    Examples:
    # Get post type information
    praisonaiwp post-type get "post"

    # Get custom post type details
    praisonaiwp post-type get "book"
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "post-type get", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Get post type information
        result = client.post_type_get(post_type)

        if result is None:
            error_msg = f"Post type '{post_type}' not found"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "post-type get", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[yellow]{error_msg}[/yellow]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(result, "post-type get", "post-type get")
            click.echo(AIFormatter.format_output(response))
        else:
            table = Table(title=f"Post Type: {post_type}")
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
            response = AIFormatter.error_response(error_msg, "post-type get", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Post-type get failed: {e}")
        raise click.Abort() from None


@post_type_command.command("create")
@click.argument("post_type")
@click.argument("label")
@click.option("--slug", help="Post type slug")
@click.option("--public", help="Whether public (true/false)")
@click.option("--has-archive", help="Whether has archive (true/false)")
@click.option("--supports", help="Supported features (comma-separated)")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def create_post_type(ctx, post_type, label, slug, public, has_archive, supports, server, json_output):
    """
    Create a new post type

    Examples:
    # Create basic post type
    praisonaiwp post-type create "book" "Books"

    # Create with options
    praisonaiwp post-type create "book" "Books" --public=true --has-archive=true

    # Create with supports
    praisonaiwp post-type create "book" "Books" --supports="title,editor,thumbnail"
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "post-type create", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Create post type
        success = client.post_type_create(post_type, label, slug, public, has_archive, supports)

        if not success:
            error_msg = "Failed to create post type"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "post-type create", "POST_TYPE_CREATE_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(
                {"post_type": post_type, "label": label, "slug": slug, "public": public, "has_archive": has_archive, "supports": supports},
                "post-type create",
                "post-type create"
            )
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[green]✓[/green] Post type '{post_type}' created successfully")
            console.print(f"  Label: {label}")
            if slug:
                console.print(f"  Slug: {slug}")
            if public:
                console.print(f"  Public: {public}")
            if has_archive:
                console.print(f"  Has Archive: {has_archive}")
            if supports:
                console.print(f"  Supports: {supports}")

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "post-type create", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Post-type create failed: {e}")
        raise click.Abort() from None


@post_type_command.command("delete")
@click.argument("post_type")
@click.option("--force", is_flag=True, help="Force deletion")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def delete_post_type(ctx, post_type, force, server, json_output):
    """
    Delete a post type

    Examples:
    # Delete post type
    praisonaiwp post-type delete "book"

    # Force delete
    praisonaiwp post-type delete "book" --force
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "post-type delete", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Delete post type
        success = client.post_type_delete(post_type, force)

        if not success:
            error_msg = "Failed to delete post type"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "post-type delete", "POST_TYPE_DELETE_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(
                {"post_type": post_type, "deleted": True, "force": force},
                "post-type delete",
                "post-type delete"
            )
            click.echo(AIFormatter.format_output(response))
        else:
            force_text = " (forced)" if force else ""
            console.print(f"[green]✓[/green] Post type '{post_type}' deleted successfully{force_text}")

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "post-type delete", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Post-type delete failed: {e}")
        raise click.Abort() from None


@post_type_command.command("update")
@click.argument("post_type")
@click.option("--label", help="New label")
@click.option("--slug", help="New slug")
@click.option("--public", help="Whether public (true/false)")
@click.option("--has-archive", help="Whether has archive (true/false)")
@click.option("--supports", help="Supported features (comma-separated)")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def update_post_type(ctx, post_type, label, slug, public, has_archive, supports, server, json_output):
    """
    Update a post type

    Examples:
    # Update label
    praisonaiwp post-type update "book" --label="New Books"

    # Update multiple properties
    praisonaiwp post-type update "book" --public=false --has-archive=true
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "post-type update", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Build update parameters
        update_params = {}
        if label is not None:
            update_params['label'] = label
        if slug is not None:
            update_params['slug'] = slug
        if public is not None:
            update_params['public'] = public
        if has_archive is not None:
            update_params['has_archive'] = has_archive
        if supports is not None:
            update_params['supports'] = supports

        if not update_params:
            error_msg = "No update parameters provided"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "post-type update", "NO_PARAMS")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[yellow]{error_msg}[/yellow]")
            return

        # Update post type
        success = client.post_type_update(post_type, **update_params)

        if not success:
            error_msg = "Failed to update post type"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "post-type update", "POST_TYPE_UPDATE_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(
                {"post_type": post_type, "updated": True, "changes": update_params},
                "post-type update",
                "post-type update"
            )
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[green]✓[/green] Post type '{post_type}' updated successfully")
            for key, value in update_params.items():
                console.print(f"  {key.title()}: {value}")

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "post-type update", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Post-type update failed: {e}")
        raise click.Abort() from None
