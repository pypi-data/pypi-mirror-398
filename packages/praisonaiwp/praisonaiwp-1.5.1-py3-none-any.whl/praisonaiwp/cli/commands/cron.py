"""WordPress cron management commands"""

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
def cron_command():
    """Manage WordPress cron events"""
    pass


@cron_command.command("list")
@click.option("--server", default=None, help="Server name from config")
def list_cron(server):
    """
    List WordPress cron events

    Examples:
    # List all cron events
    praisonaiwp cron list

    # List from specific server
    praisonaiwp cron list --server staging
    """
    try:
        config = Config()
        server_config = config.get_server(server) if server else config.get_default_server()

        if not server_config:
            console.print(f"[red]Server '{server}' not found in configuration[/red]")
            return

        ssh = SSHManager.from_config(config, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        events = client.list_cron_events()

        if not events:
            console.print("[yellow]No cron events found[/yellow]")
            return

        # Create table
        table = Table(title="WordPress Cron Events")
        table.add_column("Hook", style="cyan", no_wrap=True)
        table.add_column("Next Run", style="green")
        table.add_column("Schedule", style="yellow")

        for event in events:
            table.add_row(
                event.get('hook', 'N/A'),
                event.get('next_run', 'N/A'),
                event.get('schedule', 'N/A')
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"List cron events failed: {e}")
        raise click.Abort() from None


@cron_command.command("run")
@click.option("--server", default=None, help="Server name from config")
def run_cron(server):
    """
    Run WordPress cron events

    Examples:
    # Run all cron events
    praisonaiwp cron run

    # Run on specific server
    praisonaiwp cron run --server staging
    """
    try:
        config = Config()
        server_config = config.get_server(server) if server else config.get_default_server()

        if not server_config:
            console.print(f"[red]Server '{server}' not found in configuration[/red]")
            return

        ssh = SSHManager.from_config(config, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        success = client.run_cron()

        if success:
            console.print("[green]Cron events executed successfully[/green]")
        else:
            console.print("[red]Failed to execute cron events[/red]")
            raise click.Abort()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Run cron failed: {e}")
        raise click.Abort() from None


@cron_command.group()
def event():
    """Manage individual cron events"""
    pass


@event.command("schedule")
@click.argument("hook")
@click.option("--recurrence", required=True, help="Schedule recurrence (hourly, daily, twicedaily)")
@click.option("--time", default=None, help="Time of day for daily/twicedaily (HH:MM)")
@click.option("--args", default=None, help="Arguments to pass to hook (comma-separated)")
@click.option("--server", default=None, help="Server name from config")
def schedule_cron_event(hook, recurrence, time, args, server):
    """
    Schedule a WordPress cron event

    Examples:
    # Schedule hourly event
    praisonaiwp cron event schedule my_hook --recurrence hourly

    # Schedule daily event at specific time
    praisonaiwp cron event schedule my_hook --recurrence daily --time 10:00

    # Schedule event with arguments
    praisonaiwp cron event schedule my_hook --recurrence hourly --args arg1,arg2
    """
    try:
        config = Config()
        server_config = config.get_server(server) if server else config.get_default_server()

        if not server_config:
            console.print(f"[red]Server '{server}' not found in configuration[/red]")
            return

        ssh = SSHManager.from_config(config, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        success = client.schedule_cron_event(hook, recurrence, time, args)

        if success:
            time_info = f" at {time}" if time else ""
            args_info = f" with args {args}" if args else ""
            console.print(f"[green]Successfully scheduled '{hook}' ({recurrence}){time_info}{args_info}[/green]")
        else:
            console.print(f"[red]Failed to schedule cron event '{hook}'[/red]")
            raise click.Abort()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Schedule cron event failed: {e}")
        raise click.Abort() from None


@event.command("delete")
@click.argument("hook")
@click.option("--server", default=None, help="Server name from config")
def delete_cron_event(hook, server):
    """
    Delete a WordPress cron event

    Examples:
    # Delete cron event
    praisonaiwp cron event delete my_hook

    # Delete from specific server
    praisonaiwp cron event delete my_hook --server staging
    """
    try:
        config = Config()
        server_config = config.get_server(server) if server else config.get_default_server()

        if not server_config:
            console.print(f"[red]Server '{server}' not found in configuration[/red]")
            return

        ssh = SSHManager.from_config(config, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        success = client.delete_cron_event(hook)

        if success:
            console.print(f"[green]Successfully deleted cron event '{hook}'[/green]")
        else:
            console.print(f"[red]Failed to delete cron event '{hook}'[/red]")
            raise click.Abort()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Delete cron event failed: {e}")
        raise click.Abort() from None


@cron_command.command("test")
@click.option("--server", default=None, help="Server name from config")
def test_cron(server):
    """
    Test WordPress cron system

    Examples:
    # Test cron system
    praisonaiwp cron test

    # Test on specific server
    praisonaiwp cron test --server staging
    """
    try:
        config = Config()
        server_config = config.get_server(server) if server else config.get_default_server()

        if not server_config:
            console.print(f"[red]Server '{server}' not found in configuration[/red]")
            return

        ssh = SSHManager.from_config(config, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        is_working = client.test_cron()

        if is_working:
            console.print("[green]WordPress cron system is working properly[/green]")
        else:
            console.print("[red]WordPress cron system is not working[/red]")
            console.print("[yellow]Check your wp-config.php for DISABLE_WP_CRON constant[/yellow]")
            raise click.Abort()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Test cron failed: {e}")
        raise click.Abort() from None
