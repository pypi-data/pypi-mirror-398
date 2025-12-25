"""List command - List WordPress posts"""

import click
from rich.console import Console
from rich.table import Table

from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


@click.command()
@click.option('--type', 'post_type', default='post', help='Post type (post, page, all)')
@click.option('--status', default='publish', help='Post status (publish, draft, all)')
@click.option('--limit', type=int, help='Limit number of results')
@click.option('--search', '-s', help='Search posts by title/content')
@click.option('--server', default=None, help='Server name from config')
def list_command(post_type, status, limit, search, server):
    """
    List WordPress posts

    Examples:

        # List all posts
        praisonaiwp list

        # List pages
        praisonaiwp list --type page

        # List drafts
        praisonaiwp list --status draft

        # List with limit
        praisonaiwp list --limit 10
    """

    try:
        # Load configuration
        config = Config()
        server_config = config.get_server(server)

        console.print(f"\n[yellow]Fetching {post_type}s...[/yellow]\n")

        with SSHManager(
            server_config['hostname'],
            server_config['username'],
            server_config['key_file'],
            server_config.get('port', 22)
        ) as ssh:

            wp = WPClient(
                ssh,
                server_config['wp_path'],
                server_config.get('php_bin', 'php'),
                server_config.get('wp_cli', '/usr/local/bin/wp')
            )

            # Build filters
            filters = {}
            if status != 'all':
                filters['post_status'] = status
            if limit:
                filters['posts_per_page'] = limit
            if search:
                filters['s'] = search
                console.print(f"[cyan]Searching for: {search}[/cyan]\n")

            # Get posts
            posts = wp.list_posts(post_type=post_type, **filters)

            if not posts:
                console.print(f"[yellow]No {post_type}s found[/yellow]")
                return

            # Display results in table
            table = Table(title=f"{post_type.capitalize()}s ({len(posts)})")

            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Title", style="white")
            table.add_column("Status", style="green")
            table.add_column("Modified", style="dim")

            for post in posts:
                table.add_row(
                    str(post['ID']),
                    post['post_title'][:50] + ('...' if len(post['post_title']) > 50 else ''),
                    post['post_status'],
                    post.get('post_modified', 'N/A')
                )

            console.print(table)
            console.print()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"List command failed: {e}")
        raise click.Abort() from None
