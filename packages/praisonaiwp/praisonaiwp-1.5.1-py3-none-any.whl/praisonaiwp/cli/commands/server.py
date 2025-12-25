"""WordPress development server commands"""


import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.utils.ai_formatter import AIFormatter
from praisonaiwp.utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


@click.group()
def server_command():
    """Manage WordPress development server"""
    pass


@server_command.command("start")
@click.option("--host", default="localhost", help="Host to bind to (default: localhost)")
@click.option("--port", default=8080, type=int, help="Port to bind to (default: 8080)")
@click.option("--config", help="Path to PHP configuration file")
@click.option("--docroot", help="Document root path")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def start_server(ctx, host, port, config, docroot, server, json_output):
    """
    Start PHP development server

    Examples:
    # Start server with default settings
    praisonaiwp server start

    # Start server on specific host and port
    praisonaiwp server start --host=0.0.0.0 --port=9000

    # Start server with custom PHP config
    praisonaiwp server start --config=development.ini

    # Start server for multisite
    praisonaiwp server start --host=localhost.localdomain --port=80
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "server start", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Start the server
        server_url = client.start_server(host, port, config, docroot)

        if not server_url:
            error_msg = "Failed to start development server"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "server start", "SERVER_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(
                {"url": server_url, "host": host, "port": port},
                "development server",
                "server start"
            )
            click.echo(AIFormatter.format_output(response))
        else:
            # Human-friendly output
            panel_content = Text()
            panel_content.append("Development server started successfully!\n\n", style="bold green")
            panel_content.append("URL: ", style="bold")
            panel_content.append(f"{server_url}\n", style="blue")
            panel_content.append("Host: ", style="bold")
            panel_content.append(f"{host}\n", style="cyan")
            panel_content.append("Port: ", style="bold")
            panel_content.append(f"{port}\n", style="cyan")

            if config:
                panel_content.append("Config: ", style="bold")
                panel_content.append(f"{config}\n", style="yellow")

            if docroot:
                panel_content.append("Docroot: ", style="bold")
                panel_content.append(f"{docroot}\n", style="yellow")

            panel_content.append("\n", style="")
            panel_content.append("Press Ctrl+C to stop the server", style="dim")

            panel = Panel(
                panel_content,
                title="[bold green]Development Server[/bold green]",
                border_style="green"
            )
            console.print(panel)

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "server start", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Start server failed: {e}")
        raise click.Abort() from None


@server_command.command("shell")
@click.option("--server", default=None, help="Server name from config")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.pass_context
def open_shell(ctx, server, json_output):
    """
    Open interactive PHP console

    Examples:
    # Open PHP shell
    praisonaiwp server shell

    # Open shell for specific server
    praisonaiwp server shell --server staging
    """
    try:
        config_manager = Config()
        server_config = config_manager.get_server(server) if server else config_manager.get_default_server()

        if not server_config:
            error_msg = f"Server '{server}' not found in configuration"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "server shell", "NOT_FOUND")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        ssh = SSHManager.from_config(config_manager, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Open the shell
        shell_prompt = client.open_shell()

        if not shell_prompt:
            error_msg = "Failed to open PHP shell"
            if json_output or ctx.obj.get('json_output'):
                response = AIFormatter.error_response(error_msg, "server shell", "SHELL_ERROR")
                click.echo(AIFormatter.format_output(response))
            else:
                console.print(f"[red]{error_msg}[/red]")
            return

        # Output results
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.create_response(
                {"prompt": shell_prompt, "type": "interactive"},
                "PHP shell",
                "server shell"
            )
            click.echo(AIFormatter.format_output(response))
        else:
            # Human-friendly output
            console.print("[green]✓[/green] PHP shell opened successfully!")
            console.print(f"[dim]Interactive prompt: {shell_prompt}[/dim]")
            console.print("[dim]Type 'exit' or press Ctrl+D to close the shell[/dim]")

    except Exception as e:
        error_msg = str(e)
        if json_output or ctx.obj.get('json_output'):
            response = AIFormatter.error_response(error_msg, "server shell", "CONNECTION_ERROR")
            click.echo(AIFormatter.format_output(response))
        else:
            console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Open shell failed: {e}")
        raise click.Abort() from None
