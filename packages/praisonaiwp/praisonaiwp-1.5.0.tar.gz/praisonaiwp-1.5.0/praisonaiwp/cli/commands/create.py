"""Create command - Create WordPress posts"""

import csv
import json
from pathlib import Path

import click
import yaml
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.utils.block_converter import convert_to_blocks as html_to_blocks
from praisonaiwp.utils.block_converter import has_blocks
from praisonaiwp.utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


def _parse_category_input(category_str, category_id_str, wp):
    """
    Parse category input and return list of category IDs

    Args:
        category_str: Comma-separated category names/slugs
        category_id_str: Comma-separated category IDs
        wp: WPClient instance

    Returns:
        List of category IDs
    """
    category_ids = []

    if category_id_str:
        # Parse category IDs
        try:
            category_ids = [int(cid.strip()) for cid in category_id_str.split(',')]
        except ValueError:
            raise click.ClickException("Invalid category ID format. Must be comma-separated integers.")

    elif category_str:
        # Parse category names/slugs
        category_names = [name.strip() for name in category_str.split(',')]

        for name in category_names:
            cat = wp.get_category_by_name(name)
            if not cat:
                raise click.ClickException(f"Category '{name}' not found")
            category_ids.append(int(cat['term_id']))

    return category_ids


@click.command()
@click.argument('title_or_file', required=False)
@click.option('--content', help='Post content (HTML format, auto-converts to Gutenberg blocks)')
@click.option('--status', default='publish', help='Post status (publish, draft, private)')
@click.option('--type', 'post_type', default='post', help='Post type (post, page)')
@click.option('--category', help='Comma-separated category names/slugs')
@click.option('--category-id', help='Comma-separated category IDs')
@click.option('--author', help='Post author (user ID or login)')
@click.option('--excerpt', help='Post excerpt')
@click.option('--date', help='Post date (YYYY-MM-DD HH:MM:SS)')
@click.option('--tags', help='Comma-separated tag names or IDs')
@click.option('--meta', help='Post meta in JSON format: {"key":"value"}')
@click.option('--comment-status', help='Comment status (open, closed)')
@click.option('--no-block-conversion', is_flag=True, help='Disable automatic HTML to Gutenberg blocks conversion')
@click.option('--server', default=None, help='Server name from config')
def create_command(title_or_file, content, status, post_type, category, category_id, author,
                   excerpt, date, tags, meta, comment_status, no_block_conversion, server):
    """
    Create WordPress posts

    \b
    CONTENT FORMAT:
    Content should be HTML. By default, it auto-converts to Gutenberg blocks.
    Use --no-block-conversion to send raw Gutenberg block markup directly.

    \b
    EXAMPLES:

        # Single post with HTML (auto-converts to blocks)
        praisonaiwp create "My Post" --content "<h2>Title</h2><p>Content</p>"

        # With categories
        praisonaiwp create "My Post" --content "<p>Hello</p>" --category "RAG,AI"

        # From file (auto-detects JSON/YAML/CSV)
        praisonaiwp create posts.json

        # Create page
        praisonaiwp create "About Us" --content "<p>About</p>" --type page

    \b
    GUTENBERG BLOCKS (use with --no-block-conversion):

    \b
        Paragraph:
            <!-- wp:paragraph -->
            <p>Text</p>
            <!-- /wp:paragraph -->

    \b
        Heading:
            <!-- wp:heading -->
            <h2 class="wp-block-heading">Title</h2>
            <!-- /wp:heading -->

    \b
        Code:
            <!-- wp:code -->
            <pre class="wp-block-code"><code>code</code></pre>
            <!-- /wp:code -->

    \b
        Table:
            <!-- wp:table -->
            <figure class="wp-block-table"><table>...</table></figure>
            <!-- /wp:table -->

    \b
        Separator:
            <!-- wp:separator -->
            <hr class="wp-block-separator has-alpha-channel-opacity"/>
            <!-- /wp:separator -->
    """

    try:
        # Load configuration
        config = Config()
        server_config = config.get_server(server)

        # Determine operation mode
        if not title_or_file:
            # Interactive mode
            title_or_file = click.prompt("Post title")
            if not content:
                content = click.prompt("Post content")

        # Check if it's a file
        if title_or_file and Path(title_or_file).exists():
            # Bulk create from file
            _create_from_file(title_or_file, server_config, config)
        else:
            # Single post create
            _create_single_post(
                title_or_file,
                content,
                status,
                post_type,
                category,
                category_id,
                author,
                excerpt,
                date,
                tags,
                meta,
                comment_status,
                no_block_conversion,
                server_config
            )

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Create command failed: {e}")
        raise click.Abort() from None


def _create_single_post(title, content, status, post_type, category, category_id, author,
                        excerpt, date, tags, meta, comment_status, no_block_conversion, server_config):
    """Create a single post"""

    if not content:
        console.print("[red]Error: --content is required[/red]")
        raise click.Abort() from None

    console.print(f"\n[yellow]Creating {post_type}...[/yellow]")

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

        # Auto-convert HTML to blocks (unless disabled)
        if not no_block_conversion and content and not has_blocks(content):
            console.print("[cyan]Auto-converting HTML to Gutenberg blocks...[/cyan]")
            content = html_to_blocks(content)
            console.print("[green]✓ Content converted to blocks[/green]")
        elif no_block_conversion and content:
            console.print("[yellow]Block conversion disabled - using raw HTML[/yellow]")

        # Prepare post arguments
        post_args = {
            'post_title': title,
            'post_content': content,
            'post_status': status,
            'post_type': post_type,
        }

        # Add author if specified
        if author:
            # Check if author is numeric (user ID) or string (login)
            if author.isdigit():
                post_args['post_author'] = int(author)
            else:
                # Look up user by login
                user = wp.get_user(author)
                if user:
                    post_args['post_author'] = int(user['ID'])
                else:
                    console.print(f"[yellow]Warning: User '{author}' not found, using default author[/yellow]")

        # Add optional fields
        if excerpt:
            post_args['post_excerpt'] = excerpt
        if date:
            post_args['post_date'] = date
        if comment_status:
            post_args['comment_status'] = comment_status
        if tags:
            post_args['tags_input'] = tags
        if meta:
            # meta should be JSON string like '{"key":"value"}'
            post_args['meta_input'] = meta

        post_id = wp.create_post(**post_args)

        # Set categories if provided
        if category or category_id:
            category_ids = _parse_category_input(category, category_id, wp)
            if category_ids:
                wp.set_post_categories(post_id, category_ids)

                # Get category names for display
                category_names = []
                for cid in category_ids:
                    cat = wp.get_category_by_id(cid)
                    if cat:
                        category_names.append(cat['name'])

                console.print(f"[green]✓ Created {post_type} ID: {post_id}[/green]")
                console.print(f"Title: {title}")
                console.print(f"Status: {status}")
                console.print(f"Categories: {', '.join(category_names)}\n")
            else:
                console.print(f"[green]✓ Created {post_type} ID: {post_id}[/green]")
                console.print(f"Title: {title}")
                console.print(f"Status: {status}\n")
        else:
            console.print(f"[green]✓ Created {post_type} ID: {post_id}[/green]")
            console.print(f"Title: {title}")
            console.print(f"Status: {status}\n")


def _create_from_file(file_path, server_config, config):
    """Create posts from file"""

    # Detect file format and parse
    posts = _parse_file(file_path)

    if not posts:
        console.print("[red]Error: No posts found in file[/red]")
        return

    console.print(f"\n[cyan]Found {len(posts)} posts in file[/cyan]")

    # Check if should use parallel mode
    parallel_threshold = config.get_setting('parallel_threshold', 10)
    use_parallel = len(posts) > parallel_threshold

    if use_parallel:
        console.print("[yellow]Using parallel mode for faster creation...[/yellow]")
        # TODO: Implement parallel execution via Node.js
        console.print("[yellow]Note: Parallel mode not yet implemented, using sequential[/yellow]")

    # Create posts sequentially
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

        created_ids = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:

            task = progress.add_task(f"Creating {len(posts)} posts...", total=len(posts))

            for i, post in enumerate(posts, 1):
                try:
                    post_id = wp.create_post(
                        post_title=post.get('title', f'Untitled Post {i}'),
                        post_content=post.get('content', ''),
                        post_status=post.get('status', 'publish'),
                        post_type=post.get('type', 'post')
                    )
                    created_ids.append(post_id)
                    progress.update(task, advance=1)

                except Exception as e:
                    console.print(f"[red]✗ Failed to create post {i}: {e}[/red]")
                    logger.error(f"Failed to create post: {e}")

        console.print(f"\n[green]✓ Created {len(created_ids)} posts successfully[/green]")
        console.print(f"Post IDs: {', '.join(map(str, created_ids))}\n")


def _parse_file(file_path):
    """Parse posts from file (JSON, YAML, or CSV)"""

    file_path = Path(file_path)
    suffix = file_path.suffix.lower()

    try:
        if suffix == '.json':
            with open(file_path) as f:
                return json.load(f)

        elif suffix in ['.yaml', '.yml']:
            with open(file_path) as f:
                return yaml.safe_load(f)

        elif suffix == '.csv':
            posts = []
            with open(file_path) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    posts.append(row)
            return posts

        else:
            console.print(f"[red]Unsupported file format: {suffix}[/red]")
            return []

    except Exception as e:
        console.print(f"[red]Error parsing file: {e}[/red]")
        logger.error(f"File parsing failed: {e}")
        return []
