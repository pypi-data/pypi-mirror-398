"""WordPress help command"""

import click
from rich.console import Console

from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


@click.command()
@click.argument('command', required=False)
@click.option('--server', default=None, help='Server name from config')
def help_command(command, server):
    """
    Get help for WordPress commands

    Examples:

        # Get general help
        praisonaiwp help

        # Get help for specific command
        praisonaiwp help post
    """
    try:
        config = Config()
        server_config = config.get_server(server)

        with SSHManager(
            server_config['hostname'],
            server_config['username'],
            server_config.get('key_filename'),
            server_config.get('port', 22)
        ) as ssh:

            wp = WPClient(
                ssh,
                server_config['wp_path'],
                server_config.get('php_bin', 'php'),
                server_config.get('wp_cli', '/usr/local/bin/wp')
            )

            if command:
                # Get help for specific command
                help_text = wp.get_help(command)
                if help_text:
                    console.print(f"[green]Help for '{command}':[/green]")
                    console.print(help_text)
                else:
                    console.print(f"[red]No help available for '{command}'[/red]")
            else:
                # Get general help
                help_text = wp.get_help()
                if help_text:
                    console.print("[green]PraisonAIWP Help:[/green]")
                    console.print(help_text)
                    console.print("\n[dim]Use 'praisonaiwp help <command>' for specific command help.[/dim]")
                else:
                    console.print("[red]No help available[/red]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Help command failed: {e}")
        raise click.Abort() from None
