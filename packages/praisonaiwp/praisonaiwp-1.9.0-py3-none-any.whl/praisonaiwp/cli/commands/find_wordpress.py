"""Find WordPress installations command"""

import click
from rich.console import Console
from rich.table import Table

from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_finder import WordPressFinder
from praisonaiwp.utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


@click.command()
@click.option('--server', default='default', help='Server name from config')
@click.option('--interactive', '-i', is_flag=True, help='Interactively select installation')
@click.option('--update-config', is_flag=True, help='Update config with found path')
def find_wordpress(server, interactive, update_config):
    """
    Find WordPress installations on remote server

    Automatically searches common locations and verifies installations.
    """
    try:
        # Load config
        config = Config()
        if not config.exists():
            console.print("[red]Configuration not found. Run 'praisonaiwp init' first.[/red]")
            return

        server_config = config.get_server(server)

        console.print(f"\n[bold cyan]Finding WordPress installations on {server}[/bold cyan]\n")

        # Connect to server
        with SSHManager(
            server_config['hostname'],
            server_config.get('username'),
            server_config.get('key_file'),
            server_config.get('port', 22)
        ) as ssh:

            finder = WordPressFinder(ssh)

            # Find all installations
            console.print("[yellow]Searching for WordPress installations...[/yellow]")
            console.print("[dim]This may take a moment...[/dim]\n")

            installations = finder.find_all(verify=True)

            if not installations:
                console.print("[red]✗ No WordPress installations found[/red]\n")
                console.print("[yellow]Searched locations:[/yellow]")
                console.print("  • /var/www/html")
                console.print("  • /var/www/vhosts/*/httpdocs")
                console.print("  • /home/*/public_html")
                console.print("  • And other common paths\n")
                console.print("[dim]Specify path manually with --wp-path option[/dim]")
                return

            # Display results
            console.print(f"[green]✓ Found {len(installations)} WordPress installation(s)[/green]\n")

            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("#", style="dim", width=3)
            table.add_column("Path", style="cyan")
            table.add_column("Version", style="green")
            table.add_column("Components", style="yellow")

            for idx, install in enumerate(installations, 1):
                version = install.get('version', 'unknown')

                components = []
                if install.get('has_wp_config'):
                    components.append("config")
                if install.get('has_wp_content'):
                    components.append("content")
                if install.get('has_wp_includes'):
                    components.append("includes")

                components_str = ", ".join(components) if components else "incomplete"

                table.add_row(str(idx), install['path'], version, components_str)

            console.print(table)
            console.print()

            # Interactive selection
            if interactive and len(installations) > 1:
                selected_path = finder.interactive_select(installations)

                if selected_path:
                    console.print(f"\n[green]Selected: {selected_path}[/green]")

                    if update_config:
                        console.print("\n[yellow]Updating config...[/yellow]")
                        server_config['wp_path'] = selected_path
                        config.save()
                        console.print("[green]✓ Config updated[/green]")
                else:
                    console.print("\n[yellow]No selection made[/yellow]")

            elif update_config and len(installations) == 1:
                path = installations[0]['path']
                console.print(f"\n[yellow]Updating config with: {path}[/yellow]")
                server_config['wp_path'] = path
                config.save()
                console.print("[green]✓ Config updated[/green]")

            elif len(installations) > 1:
                console.print("[dim]Use --interactive to select installation[/dim]")
                console.print("[dim]Use --update-config to save to configuration[/dim]")

    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        logger.error(f"Find WordPress failed: {e}", exc_info=True)
