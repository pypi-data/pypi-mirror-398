"""WordPress database backup and restore commands"""

import click
from rich.console import Console

from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


@click.group()
def backup():
    """WordPress database backup and restore"""
    pass


@backup.command('export')
@click.argument('file_path')
@click.option('--tables', help='Specific tables to export (comma-separated)')
@click.option('--server', default=None, help='Server name from config')
def export_database(file_path, tables, server):
    """
    Export WordPress database

    Examples:

        # Export entire database
        praisonaiwp backup export /path/to/backup.sql

        # Export specific tables
        praisonaiwp backup export /path/to/backup.sql --tables wp_posts,wp_users
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

            console.print(f"Exporting database to: {file_path}...")
            success = wp.db_export(file_path, tables)

            if success:
                console.print(f"[green]✓ Database exported successfully to: {file_path}[/green]")
                if tables:
                    console.print(f"Tables: {tables}")
                else:
                    console.print("All tables exported")
            else:
                console.print(f"[red]✗ Failed to export database[/red]")
                raise click.ClickException("Database export failed")

    except click.ClickException:
        raise
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Export database failed: {e}")
        raise click.Abort() from None


@backup.command('import')
@click.argument('file_path')
@click.option('--server', default=None, help='Server name from config')
@click.confirmation_option(prompt='Are you sure you want to import this database? This will overwrite existing data!')
def import_database(file_path, server):
    """
    Import WordPress database

    Examples:

        # Import database
        praisonaiwp backup import /path/to/backup.sql
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

            console.print(f"Importing database from: {file_path}...")
            success = wp.db_import(file_path)

            if success:
                console.print(f"[green]✓ Database imported successfully from: {file_path}[/green]")
                console.print("[yellow]⚠️  You may need to clear caches and update permalinks[/yellow]")
            else:
                console.print(f"[red]✗ Failed to import database[/red]")
                raise click.ClickException("Database import failed")

    except click.ClickException:
        raise
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Import database failed: {e}")
        raise click.Abort() from None


@backup.command('create')
@click.option('--filename', help='Backup filename (auto-generated if not provided)')
@click.option('--tables', help='Specific tables to backup (comma-separated)')
@click.option('--server', default=None, help='Server name from config')
def create_backup(filename, tables, server):
    """
    Create a timestamped database backup

    Examples:

        # Create backup with auto-generated filename
        praisonaiwp backup create

        # Create backup with custom filename
        praisonaiwp backup create --filename my-backup.sql

        # Backup specific tables
        praisonaiwp backup create --tables wp_posts,wp_users
    """
    try:
        import datetime

        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backup_{timestamp}.sql"

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

            console.print(f"Creating backup: {filename}...")
            success = wp.db_export(filename, tables)

            if success:
                console.print(f"[green]✓ Backup created successfully: {filename}[/green]")
                console.print(f"Size: Calculating...")
                console.print(f"Location: {server_config['wp_path']}/{filename}")
            else:
                console.print(f"[red]✗ Failed to create backup[/red]")
                raise click.ClickException("Backup creation failed")

    except click.ClickException:
        raise
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Create backup failed: {e}")
        raise click.Abort() from None
