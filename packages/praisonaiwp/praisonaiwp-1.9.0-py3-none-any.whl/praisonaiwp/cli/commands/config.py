"""WordPress config management commands"""

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
def config_command():
    """Manage WordPress configuration"""
    pass


@config_command.command("get")
@click.argument("param")
@click.option("--server", default=None, help="Server name from config")
def get_config(param, server):
    """
    Get WordPress configuration parameter

    Examples:
    # Get site title
    praisonaiwp config get blogname

    # Get database charset
    praisonaiwp config get db_charset

    # Get from specific server
    praisonaiwp config get blogname --server staging
    """
    try:
        config = Config()
        server_config = config.get_server(server) if server else config.get_default_server()

        if not server_config:
            console.print(f"[red]Server '{server}' not found in configuration[/red]")
            return

        ssh = SSHManager.from_config(config, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        value = client.get_config_param(param)

        if value is not None:
            console.print(f"[green]{param}:[/green] {value}")
        else:
            console.print(f"[yellow]Configuration parameter '{param}' not found[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Get config failed: {e}")
        raise click.Abort() from None


@config_command.command("set")
@click.argument("param")
@click.argument("value")
@click.option("--server", default=None, help="Server name from config")
def set_config(param, value, server):
    """
    Set WordPress configuration parameter

    Examples:
    # Set site title
    praisonaiwp config set blogname "My New Blog"

    # Set admin email
    praisonaiwp config set admin_email "admin@example.com"

    # Set on specific server
    praisonaiwp config set blogname "Staging Blog" --server staging
    """
    try:
        config = Config()
        server_config = config.get_server(server) if server else config.get_default_server()

        if not server_config:
            console.print(f"[red]Server '{server}' not found in configuration[/red]")
            return

        ssh = SSHManager.from_config(config, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        success = client.set_config_param(param, value)

        if success:
            console.print(f"[green]Successfully set {param} = {value}[/green]")
        else:
            console.print(f"[red]Failed to set {param}[/red]")
            raise click.Abort()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Set config failed: {e}")
        raise click.Abort() from None


@config_command.command("list")
@click.option("--search", default=None, help="Search filter for parameter names")
@click.option("--server", default=None, help="Server name from config")
def list_config(search, server):
    """
    List all WordPress configuration parameters

    Examples:
    # List all configuration
    praisonaiwp config list

    # Search for blog-related parameters
    praisonaiwp config list --search blog

    # List from specific server
    praisonaiwp config list --server staging
    """
    try:
        config = Config()
        server_config = config.get_server(server) if server else config.get_default_server()

        if not server_config:
            console.print(f"[red]Server '{server}' not found in configuration[/red]")
            return

        ssh = SSHManager.from_config(config, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        config_data = client.get_all_config()

        if not config_data:
            console.print("[yellow]No configuration found[/yellow]")
            return

        # Filter results if search is provided
        if search:
            config_data = {k: v for k, v in config_data.items() if search.lower() in k.lower()}

        if not config_data:
            console.print(f"[yellow]No configuration parameters matching '{search}' found[/yellow]")
            return

        # Create table
        table = Table(title="WordPress Configuration")
        table.add_column("Parameter", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")

        for param, value in config_data.items():
            # Truncate long values for display
            display_value = str(value)
            if len(display_value) > 100:
                display_value = display_value[:97] + "..."
            table.add_row(param, display_value)

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"List config failed: {e}")
        raise click.Abort() from None


@config_command.command("create")
@click.option("--dbhost", default="localhost", help="Database host")
@click.option("--dbname", required=True, help="Database name")
@click.option("--dbuser", required=True, help="Database user")
@click.option("--dbpass", required=True, help="Database password")
@click.option("--dbprefix", default="wp_", help="Database table prefix")
@click.option("--dbcharset", default="utf8", help="Database charset")
@click.option("--dbscollate", default="utf8_general_ci", help="Database collation")
@click.option("--server", default=None, help="Server name from config")
@click.option("--force", is_flag=True, help="Overwrite existing config")
def create_config(dbhost, dbname, dbuser, dbpass, dbprefix, dbcharset, dbscollate, server, force):
    """
    Create WordPress wp-config.php file

    Examples:
    # Create basic config
    praisonaiwp config create --dbname wordpress --dbuser wpuser --dbpass wppass

    # Create config with custom settings
    praisonaiwp config create --dbhost localhost --dbname wordpress --dbuser wpuser --dbpass wppass --dbprefix custom_

    # Create on specific server
    praisonaiwp config create --dbname wordpress --dbuser wpuser --dbpass wppass --server staging
    """
    try:
        config = Config()
        server_config = config.get_server(server) if server else config.get_default_server()

        if not server_config:
            console.print(f"[red]Server '{server}' not found in configuration[/red]")
            return

        ssh = SSHManager.from_config(config, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        # Prepare config parameters
        config_params = {
            'DB_HOST': dbhost,
            'DB_NAME': dbname,
            'DB_USER': dbuser,
            'DB_PASSWORD': dbpass,
            'DB_CHARSET': dbcharset,
            'DB_COLLATE': dbscollate,
            '$table_prefix': dbprefix
        }

        success = client.create_config(config_params, force=force)

        if success:
            console.print("[green]wp-config.php created successfully[/green]")
            console.print(f"[cyan]Database:[/cyan] {dbuser}@{dbhost}/{dbname}")
            console.print(f"[cyan]Table Prefix:[/cyan] {dbprefix}")
        else:
            console.print("[red]Failed to create wp-config.php[/red]")
            if not force:
                console.print("[yellow]Tip: Use --force to overwrite existing config[/yellow]")
            raise click.Abort()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Create config failed: {e}")
        raise click.Abort() from None


@config_command.command("path")
@click.option("--server", default=None, help="Server name from config")
def config_path(server):
    """
    Show WordPress configuration file path

    Examples:
    # Show config path
    praisonaiwp config path

    # Show config path for specific server
    praisonaiwp config path --server staging
    """
    try:
        config = Config()
        server_config = config.get_server(server) if server else config.get_default_server()

        if not server_config:
            console.print(f"[red]Server '{server}' not found in configuration[/red]")
            return

        ssh = SSHManager.from_config(config, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        config_path = client.get_config_path()

        if config_path:
            console.print(f"[green]wp-config.php path:[/green] {config_path}")
        else:
            console.print("[red]wp-config.php not found[/red]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Get config path failed: {e}")
        raise click.Abort() from None
