"""Install WP-CLI command"""

import click
from rich.console import Console
from rich.prompt import Confirm

from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_installer import WPCLIInstaller
from praisonaiwp.utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


@click.command()
@click.option('--server', default='default', help='Server name from config')
@click.option('--install-path', default='/usr/local/bin/wp', help='Installation path')
@click.option('--no-sudo', is_flag=True, help='Do not use sudo')
@click.option('--install-deps', is_flag=True, help='Install dependencies (curl, php)')
@click.option('--php-bin', help='PHP binary to test with')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompts')
def install_wp_cli(server, install_path, no_sudo, install_deps, php_bin, yes):
    """
    Automatically install WP-CLI on remote server

    Detects OS and installs WP-CLI with appropriate method.
    """
    try:
        # Load config
        config = Config()
        if not config.exists():
            console.print("[red]Configuration not found. Run 'praisonaiwp init' first.[/red]")
            return

        server_config = config.get_server(server)

        console.print(f"\n[bold cyan]Installing WP-CLI on {server}[/bold cyan]\n")

        # Connect to server
        with SSHManager(
            server_config['hostname'],
            server_config.get('username'),
            server_config.get('key_file'),
            server_config.get('port', 22)
        ) as ssh:

            installer = WPCLIInstaller(ssh)

            # Detect OS
            console.print("[yellow]Detecting remote OS...[/yellow]")
            os_type, os_version = installer.detect_os()
            console.print(f"[green]✓ Detected: {os_type} {os_version}[/green]\n")

            # Check if already installed
            console.print("[yellow]Checking if WP-CLI is already installed...[/yellow]")
            if installer.check_wp_cli_installed(install_path):
                console.print(f"[green]✓ WP-CLI is already installed at {install_path}[/green]")
                return

            console.print(f"[yellow]WP-CLI not found at {install_path}[/yellow]\n")

            # Confirm installation
            if not yes:
                console.print("[bold]Installation plan:[/bold]")
                console.print(f"  OS: {os_type} {os_version}")
                console.print(f"  Install path: {install_path}")
                console.print(f"  Use sudo: {not no_sudo}")
                console.print(f"  Install dependencies: {install_deps}")
                if php_bin:
                    console.print(f"  PHP binary: {php_bin}")
                console.print()

                if not Confirm.ask("Proceed with installation?"):
                    console.print("[yellow]Installation cancelled[/yellow]")
                    return

            # Install
            console.print("\n[bold cyan]Installing WP-CLI...[/bold cyan]\n")

            success = installer.auto_install(
                install_path=install_path,
                use_sudo=not no_sudo,
                install_deps=install_deps,
                php_bin=php_bin
            )

            if success:
                console.print("\n[bold green]✓ WP-CLI installed successfully![/bold green]\n")

                # Update config with WP-CLI path
                if install_path != '/usr/local/bin/wp':
                    console.print("[yellow]Updating config with WP-CLI path...[/yellow]")
                    server_config['wp_cli'] = install_path
                    config.save()
                    console.print("[green]✓ Config updated[/green]\n")

                console.print("[dim]You can now use PraisonAIWP commands![/dim]")
            else:
                console.print("\n[red]✗ Installation failed[/red]")
                console.print("[yellow]Please check the logs for details[/yellow]")

    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        logger.error(f"Installation failed: {e}", exc_info=True)
