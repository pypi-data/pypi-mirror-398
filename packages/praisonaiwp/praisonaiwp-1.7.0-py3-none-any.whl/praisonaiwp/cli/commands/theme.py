"""WordPress theme management commands"""

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
def theme_command():
    """Manage WordPress themes"""
    pass


@theme_command.command("list")
@click.option("--server", default=None, help="Server name from config")
def list_themes(server):
    """
    List WordPress themes

    Examples:

        # List all themes
        praisonaiwp theme list

        # List themes from specific server
        praisonaiwp theme list --server production
    """
    try:
        config = Config()
        server_config = config.get_server(server)

        with SSHManager(
            server_config["hostname"],
            server_config["username"],
            server_config.get("key_filename"),
            server_config.get("port", 22),
        ) as ssh:

            wp = WPClient(
                ssh,
                server_config["wp_path"],
                server_config.get("php_bin", "php"),
                server_config.get("wp_cli", "/usr/local/bin/wp"),
            )

            themes = wp.list_themes()

            if themes:
                table = Table(title="WordPress Themes")
                table.add_column("Name", style="cyan")
                table.add_column("Slug", style="white")
                table.add_column("Status", style="green")
                table.add_column("Version", style="yellow")
                table.add_column("Author", style="blue")

                for theme in themes:
                    status = theme.get("status", "unknown")
                    if status == "active":
                        status = "[green]active[/green]"
                    elif status == "inactive":
                        status = "[dim]inactive[/dim]"

                    table.add_row(
                        theme.get("name", ""),
                        theme.get("slug", ""),
                        status,
                        theme.get("version", ""),
                        theme.get("author", ""),
                    )

                console.print(table)
            else:
                console.print("[yellow]No themes found[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"List themes failed: {e}")
        raise click.Abort() from None


@theme_command.command("activate")
@click.argument("theme_slug")
@click.option("--server", default=None, help="Server name from config")
def activate_theme(theme_slug, server):
    """
    Activate a WordPress theme

    Examples:

        # Activate theme
        praisonaiwp theme activate twentytwentythree

        # Activate theme on specific server
        praisonaiwp theme activate twentytwentythree --server production
    """
    try:
        config = Config()
        server_config = config.get_server(server)

        with SSHManager(
            server_config["hostname"],
            server_config["username"],
            server_config.get("key_filename"),
            server_config.get("port", 22),
        ) as ssh:

            wp = WPClient(
                ssh,
                server_config["wp_path"],
                server_config.get("php_bin", "php"),
                server_config.get("wp_cli", "/usr/local/bin/wp"),
            )

            success = wp.activate_theme(theme_slug)

            if success:
                console.print(f"[green]✓ Activated theme '{theme_slug}'[/green]")
            else:
                console.print(f"[red]✗ Failed to activate theme '{theme_slug}'[/red]")
                raise click.ClickException(f"Theme activation failed for '{theme_slug}'")

    except click.ClickException:
        raise
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Activate theme failed: {e}")
        raise click.Abort() from None


@theme_command.command("install")
@click.argument("theme_slug")
@click.option("--version", help="Specific version to install")
@click.option("--force", is_flag=True, help="Force installation even if already installed")
@click.option("--server", default=None, help="Server name from config")
def install_theme(theme_slug, version, force, server):
    """
    Install a WordPress theme

    Examples:

        # Install latest version
        praisonaiwp theme install twentytwentythree

        # Install specific version
        praisonaiwp theme install twentytwentythree --version 1.0

        # Force installation
        praisonaiwp theme install twentytwentythree --force
    """
    try:
        config = Config()
        server_config = config.get_server(server)

        with SSHManager(
            server_config["hostname"],
            server_config["username"],
            server_config.get("key_filename"),
            server_config.get("port", 22),
        ) as ssh:

            wp = WPClient(
                ssh,
                server_config["wp_path"],
                server_config.get("php_bin", "php"),
                server_config.get("wp_cli", "/usr/local/bin/wp"),
            )

            console.print(f"Installing theme: {theme_slug}...")
            success = wp.theme_install(theme_slug, version, force)

            if success:
                console.print(f"[green]✓ Successfully installed theme '{theme_slug}'[/green]")
            else:
                console.print(f"[red]✗ Failed to install theme '{theme_slug}'[/red]")
                raise click.ClickException(f"Theme installation failed for '{theme_slug}'")

    except click.ClickException:
        raise
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Install theme failed: {e}")
        raise click.Abort() from None


@theme_command.command("delete")
@click.argument("theme_slug")
@click.option("--force", is_flag=True, help="Force deletion even if active")
@click.option("--server", default=None, help="Server name from config")
def delete_theme(theme_slug, force, server):
    """
    Delete a WordPress theme

    Examples:

        # Delete theme
        praisonaiwp theme delete twentytwentythree

        # Force delete even if active
        praisonaiwp theme delete twentytwentythree --force
    """
    try:
        config = Config()
        server_config = config.get_server(server)

        with SSHManager(
            server_config["hostname"],
            server_config["username"],
            server_config.get("key_filename"),
            server_config.get("port", 22),
        ) as ssh:

            wp = WPClient(
                ssh,
                server_config["wp_path"],
                server_config.get("php_bin", "php"),
                server_config.get("wp_cli", "/usr/local/bin/wp"),
            )

            console.print(f"Deleting theme: {theme_slug}...")
            success = wp.theme_delete(theme_slug, force)

            if success:
                console.print(f"[green]✓ Successfully deleted theme '{theme_slug}'[/green]")
            else:
                console.print(f"[red]✗ Failed to delete theme '{theme_slug}'[/red]")
                raise click.ClickException(f"Theme deletion failed for '{theme_slug}'")

    except click.ClickException:
        raise
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Delete theme failed: {e}")
        raise click.Abort() from None
