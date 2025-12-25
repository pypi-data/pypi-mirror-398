"""Media command - Upload and manage WordPress media"""

import os
import click
from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.utils.logger import get_logger
from rich.console import Console

console = Console()
logger = get_logger(__name__)


@click.command()
@click.argument('file_path')
@click.option('--post-id', type=int, help='Post ID to attach media to')
@click.option('--title', help='Media title')
@click.option('--caption', help='Media caption')
@click.option('--alt', help='Alt text for images')
@click.option('--desc', help='Media description')
@click.option('--server', default=None, help='Server name from config')
def media_command(file_path, post_id, title, caption, alt, desc, server):
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
                console.print(f"[yellow]Uploading local file to server...[/yellow]")
                ssh.upload_file(local_path, remote_file_path)
                console.print(f"[green]✓ File uploaded to {remote_file_path}[/green]")
            elif is_url:
                console.print(f"[yellow]Importing from URL...[/yellow]")
            else:
                # Assume it's a path on the remote server
                console.print(f"[yellow]Importing from remote path...[/yellow]")

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
        logger.error(f"Media command failed: {e}")
        raise click.Abort()
