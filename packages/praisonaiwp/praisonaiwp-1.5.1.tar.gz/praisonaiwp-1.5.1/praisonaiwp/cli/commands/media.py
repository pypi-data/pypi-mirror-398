"""Media command - Upload and manage WordPress media"""

import json
import os

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
    """Upload and manage WordPress media"""
    pass


@media_command.command('upload')
@click.argument('file_path')
@click.option('--post-id', type=int, help='Post ID to attach media to')
@click.option('--title', help='Media title')
@click.option('--caption', help='Media caption')
@click.option('--alt', help='Alt text for images')
@click.option('--desc', help='Media description')
@click.option('--server', default=None, help='Server name from config')
def upload_media(file_path, post_id, title, caption, alt, desc, server):
    """
    Upload media to WordPress

    Examples:

        # Upload a local file (auto-uploads via SFTP)
        praisonaiwp media /path/to/image.jpg

        # Upload and attach to post
        praisonaiwp media /path/to/image.jpg --post-id 123

        # Upload with metadata
        praisonaiwp media /path/to/image.jpg --title "My Image" --alt "Description"

        # Import from URL (file must be accessible from server)
        praisonaiwp media https://example.com/image.jpg
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

            # Determine if file_path is local or URL
            is_url = file_path.startswith('http://') or file_path.startswith('https://')
            local_path = os.path.expanduser(file_path)
            is_local_file = not is_url and os.path.exists(local_path)

            remote_file_path = file_path

            if is_local_file:
                # Upload local file to remote server first
                filename = os.path.basename(local_path)
                remote_file_path = f"/tmp/{filename}"
                console.print("[yellow]Uploading local file to server...[/yellow]")
                ssh.upload_file(local_path, remote_file_path)
                console.print(f"[green]✓ File uploaded to {remote_file_path}[/green]")
            elif is_url:
                console.print("[yellow]Importing from URL...[/yellow]")
            else:
                # Assume it's a path on the remote server
                console.print("[yellow]Importing from remote path...[/yellow]")

            # Build kwargs for import_media
            kwargs = {}
            if title:
                kwargs['title'] = title
            if caption:
                kwargs['caption'] = caption
            if alt:
                kwargs['alt'] = alt
            if desc:
                kwargs['desc'] = desc

            console.print("[yellow]Importing to WordPress media library...[/yellow]")
            attachment_id = wp.import_media(remote_file_path, post_id=post_id, **kwargs)

            # Clean up temp file if we uploaded it
            if is_local_file:
                ssh.execute(f"rm -f {remote_file_path}")
                console.print("[dim]Cleaned up temporary file[/dim]")

            console.print(f"\n[green]✓ Imported media with ID: {attachment_id}[/green]")
            console.print(f"Source: {file_path}")
            if post_id:
                console.print(f"Attached to post: {post_id}")
            console.print()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Media upload failed: {e}")
        raise click.Abort() from None


@media_command.command('get')
@click.argument('attachment_id', type=int)
@click.option('--field', help='Specific field to retrieve (guid, post_title, post_mime_type, etc.)')
@click.option('--server', default=None, help='Server name from config')
def get_media(attachment_id, field, server):
    """
    Get media/attachment information

    Examples:

        # Get all attachment info
        praisonaiwp media get 240814

        # Get specific field (URL)
        praisonaiwp media get 240814 --field guid

        # Get title
        praisonaiwp media get 240814 --field post_title
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

            result = wp.get_media_info(attachment_id, field=field)

            if field:
                console.print(result)
            else:
                console.print_json(json.dumps(result, indent=2))

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Get media failed: {e}")
        raise click.Abort() from None


@media_command.command('url')
@click.argument('attachment_id', type=int)
@click.option('--server', default=None, help='Server name from config')
def get_url(attachment_id, server):
    """
    Get media URL

    Examples:

        # Get media URL
        praisonaiwp media url 240814
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

            url = wp.get_media_url(attachment_id)
            console.print(url)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Get media URL failed: {e}")
        raise click.Abort() from None


@media_command.command('list')
@click.option('--post-id', type=int, help='Filter by parent post ID')
@click.option('--mime-type', help='Filter by MIME type (e.g., image/jpeg, application/pdf)')
@click.option('--server', default=None, help='Server name from config')
def list_media(post_id, mime_type, server):
    """
    List media/attachments

    Examples:

        # List all attachments
        praisonaiwp media list

        # List attachments for a specific post
        praisonaiwp media list --post-id 240812

        # List PDFs only
        praisonaiwp media list --mime-type application/pdf
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

            filters = {}
            if mime_type:
                filters['post_mime_type'] = mime_type

            attachments = wp.list_media(post_id=post_id, **filters)

            if not attachments:
                console.print("[yellow]No attachments found[/yellow]")
                return

            # Create table
            table = Table(title="Media Attachments")
            table.add_column("ID", style="cyan")
            table.add_column("Title", style="green")
            table.add_column("Type", style="yellow")
            table.add_column("URL", style="blue")

            for att in attachments:
                table.add_row(
                    str(att.get('ID', '')),
                    att.get('post_title', ''),
                    att.get('post_mime_type', ''),
                    att.get('guid', '')
                )

            console.print(table)
            console.print(f"\n[dim]Total: {len(attachments)} attachment(s)[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"List media failed: {e}")
        raise click.Abort() from None
