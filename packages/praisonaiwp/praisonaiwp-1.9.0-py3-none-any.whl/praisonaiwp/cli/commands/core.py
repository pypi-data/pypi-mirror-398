"""WordPress core management commands"""

import click
from rich.console import Console

from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


@click.group()
def core_command():
    """Manage WordPress core"""
    pass


@core_command.command("version")
@click.option("--server", default=None, help="Server name from config")
def get_core_version(server):
    """
    Get WordPress core version

    Examples:
    # Get current WordPress version
    praisonaiwp core version

    # Get version from specific server
    praisonaiwp core version --server staging
    """
    try:
        config = Config()
        server_config = config.get_server(server) if server else config.get_default_server()

        if not server_config:
            console.print(f"[red]Server '{server}' not found in configuration[/red]")
            return

        ssh = SSHManager.from_config(config, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        version = client.get_core_version()

        if version:
            console.print(f"[green]WordPress version:[/green] {version}")
        else:
            console.print("[yellow]WordPress installation not found or version unavailable[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Get core version failed: {e}")
        raise click.Abort() from None


@core_command.command("update")
@click.option("--version", default=None, help="Specific version to update to")
@click.option("--force", is_flag=True, help="Force update even if already up to date")
@click.option("--server", default=None, help="Server name from config")
def update_core(version, force, server):
    """
    Update WordPress core

    Examples:
    # Update to latest version
    praisonaiwp core update

    # Update to specific version
    praisonaiwp core update --version 6.4.0

    # Force update
    praisonaiwp core update --force

    # Update on specific server
    praisonaiwp core update --server staging
    """
    try:
        config = Config()
        server_config = config.get_server(server) if server else config.get_default_server()

        if not server_config:
            console.print(f"[red]Server '{server}' not found in configuration[/red]")
            return

        ssh = SSHManager.from_config(config, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        success = client.update_core(version=version, force=force)

        if success:
            if version:
                console.print(f"[green]Successfully updated WordPress to version {version}[/green]")
            else:
                console.print("[green]Successfully updated WordPress to latest version[/green]")
        else:
            console.print("[red]Failed to update WordPress core[/red]")
            raise click.Abort()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Update core failed: {e}")
        raise click.Abort() from None


@core_command.command("download")
@click.option("--version", default=None, help="Specific version to download")
@click.option("--path", default=None, help="Download path")
@click.option("--server", default=None, help="Server name from config")
def download_core(version, path, server):
    """
    Download WordPress core

    Examples:
    # Download latest version
    praisonaiwp core download

    # Download specific version
    praisonaiwp core download --version 6.4.0

    # Download to specific path
    praisonaiwp core download --path /tmp/wordpress

    # Download on specific server
    praisonaiwp core download --server staging
    """
    try:
        config = Config()
        server_config = config.get_server(server) if server else config.get_default_server()

        if not server_config:
            console.print(f"[red]Server '{server}' not found in configuration[/red]")
            return

        ssh = SSHManager.from_config(config, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        download_path = client.download_core(version=version, path=path)

        if download_path:
            version_info = f" version {version}" if version else " latest version"
            console.print(f"[green]Successfully downloaded WordPress{version_info} to {download_path}[/green]")
        else:
            console.print("[red]Failed to download WordPress core[/red]")
            raise click.Abort()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Download core failed: {e}")
        raise click.Abort() from None


@core_command.command("install")
@click.option("--version", default=None, help="Specific version to install")
@click.option("--force", is_flag=True, help="Force installation even if WordPress exists")
@click.option("--server", default=None, help="Server name from config")
def install_core(version, force, server):
    """
    Install WordPress core

    Examples:
    # Install latest version
    praisonaiwp core install

    # Install specific version
    praisonaiwp core install --version 6.4.0

    # Force installation
    praisonaiwp core install --force

    # Install on specific server
    praisonaiwp core install --server staging
    """
    try:
        config = Config()
        server_config = config.get_server(server) if server else config.get_default_server()

        if not server_config:
            console.print(f"[red]Server '{server}' not found in configuration[/red]")
            return

        ssh = SSHManager.from_config(config, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        success = client.install_core(version=version, force=force)

        if success:
            if version:
                console.print(f"[green]Successfully installed WordPress version {version}[/green]")
            else:
                console.print("[green]Successfully installed WordPress latest version[/green]")
            console.print("[yellow]Remember to run wp-config.php setup and database installation[/yellow]")
        else:
            console.print("[red]Failed to install WordPress core[/red]")
            if not force:
                console.print("[yellow]Tip: Use --force to overwrite existing installation[/yellow]")
            raise click.Abort()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Install core failed: {e}")
        raise click.Abort() from None


@core_command.command("verify")
@click.option("--server", default=None, help="Server name from config")
def verify_core(server):
    """
    Verify WordPress core files

    Examples:
    # Verify WordPress installation
    praisonaiwp core verify

    # Verify on specific server
    praisonaiwp core verify --server staging
    """
    try:
        config = Config()
        server_config = config.get_server(server) if server else config.get_default_server()

        if not server_config:
            console.print(f"[red]Server '{server}' not found in configuration[/red]")
            return

        ssh = SSHManager.from_config(config, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        is_valid = client.verify_core()

        if is_valid:
            console.print("[green]WordPress core files are valid[/green]")
        else:
            console.print("[red]WordPress core files are invalid or corrupted[/red]")
            console.print("[yellow]Consider running: praisonaiwp core update --force[/yellow]")
            raise click.Abort()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Verify core failed: {e}")
        raise click.Abort() from None


@core_command.command("check-update")
@click.option("--server", default=None, help="Server name from config")
def check_core_update(server):
    """
    Check for WordPress core updates

    Examples:
    # Check for updates
    praisonaiwp core check-update

    # Check on specific server
    praisonaiwp core check-update --server staging
    """
    try:
        config = Config()
        server_config = config.get_server(server) if server else config.get_default_server()

        if not server_config:
            console.print(f"[red]Server '{server}' not found in configuration[/red]")
            return

        ssh = SSHManager.from_config(config, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        update_info = client.check_core_update()

        if update_info:
            if 'version' in update_info:
                console.print(f"[green]Update available:[/green] {update_info['version']}")
                if 'update_type' in update_info:
                    console.print(f"[cyan]Update type:[/cyan] {update_info['update_type']}")
                if 'download_url' in update_info:
                    console.print(f"[cyan]Download URL:[/cyan] {update_info['download_url']}")
            else:
                console.print("[green]WordPress is up to date[/green]")
        else:
            console.print("[yellow]Unable to check for updates[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Check core update failed: {e}")
        raise click.Abort() from None
