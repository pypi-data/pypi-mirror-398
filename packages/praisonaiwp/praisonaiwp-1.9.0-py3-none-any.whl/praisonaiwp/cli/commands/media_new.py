"""WordPress media management commands"""

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
def media_command():
    """Manage WordPress media"""
    pass


@media_command.command('upload')
@click.argument('file_path')
@click.option('--title', help='Media title')
@click.option('--caption', help='Media caption')
@click.option('--alt-text', help='Alt text for the media')
@click.option('--server', default=None, help='Server name from config')
def upload_media(file_path, title, caption, alt_text, server):
    """
    Upload a media file to WordPress

    Examples:

        # Upload image
        praisonaiwp media upload /path/to/image.jpg

        # Upload with metadata
        praisonaiwp media upload /path/to/image.jpg --title "My Image" --caption "Image caption" --alt-text "Alt text"
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

            console.print(f"Uploading media: {file_path}...")
            media_info = wp.media_upload(file_path, title, caption, alt_text)

            if media_info:
                console.print(f"[green]✓ Media uploaded successfully[/green]")
                console.print(f"URL: {media_info.get('url', 'N/A')}")
                console.print(f"ID: {media_info.get('id', 'N/A')}")
                console.print(f"Title: {media_info.get('title', 'N/A')}")
            else:
                console.print(f"[red]✗ Failed to upload media[/red]")
                raise click.ClickException("Media upload failed")

    except click.ClickException:
        raise
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Upload media failed: {e}")
        raise click.Abort() from None


@media_command.command('delete')
@click.argument('media_id', type=int)
@click.option('--server', default=None, help='Server name from config')
@click.confirmation_option(prompt='Are you sure you want to delete this media file?')
def delete_media(media_id, server):
    """
    Delete a media file from WordPress

    Examples:

        # Delete media
        praisonaiwp media delete 123
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

            success = wp.media_delete(media_id)
            if success:
                console.print(f"[green]✓ Deleted media ID: {media_id}[/green]")
            else:
                console.print(f"[red]✗ Failed to delete media ID: {media_id}[/red]")
                raise click.ClickException(f"Media deletion failed for {media_id}")

    except click.ClickException:
        raise
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Delete media failed: {e}")
        raise click.Abort() from None


@media_command.command('list')
@click.option('--server', default=None, help='Server name from config')
def list_media(server):
    """
    List WordPress media files

    Examples:

        # List all media
        praisonaiwp media list
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

            media_list = wp.list_media()

            if not media_list:
                console.print("[yellow]No media found[/yellow]")
                return

            table = Table(title="WordPress Media")
            table.add_column("ID", style="cyan")
            table.add_column("Title", style="green")
            table.add_column("URL", style="blue")
            table.add_column("Type", style="yellow")

            for media in media_list:
                table.add_row(
                    str(media.get('ID', '')),
                    media.get('title', ''),
                    media.get('url', ''),
                    media.get('mime_type', '')
                )

            console.print(table)
            console.print(f"\n[dim]Total: {len(media_list)} media file(s)[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"List media failed: {e}")
        raise click.Abort() from None
