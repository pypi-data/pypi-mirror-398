"""WordPress comment management commands"""

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
def comment_command():
    """Manage WordPress comments"""
    pass


@comment_command.command('list')
@click.option('--post-id', type=int, help='Filter by post ID')
@click.option('--status', help='Filter by status (approved, pending, spam, trash)')
@click.option('--limit', type=int, default=20, help='Number of comments to list')
@click.option('--server', default=None, help='Server name from config')
def list_comments(post_id, status, limit, server):
    """
    List WordPress comments

    Examples:

        # List all comments
        praisonaiwp comment list

        # List comments for specific post
        praisonaiwp comment list --post-id 123

        # List pending comments
        praisonaiwp comment list --status pending
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

            comments = wp.list_comments(
                post_id=post_id,
                status=status,
                number=limit
            )

            if comments:
                table = Table(title="WordPress Comments")
                table.add_column("ID", style="cyan")
                table.add_column("Content", style="white")
                table.add_column("Author", style="green")
                table.add_column("Status", style="yellow")
                table.add_column("Post ID", style="blue")

                for comment in comments:
                    # Truncate content for display
                    content = comment.get('comment_content', '')[:50]
                    if len(comment.get('comment_content', '')) > 50:
                        content += "..."

                    status_text = comment.get('comment_approved', 'unknown')
                    if status_text == '1':
                        status_text = "approved"
                    elif status_text == '0':
                        status_text = "pending"
                    elif status_text == 'spam':
                        status_text = "spam"
                    elif status_text == 'trash':
                        status_text = "trash"

                    table.add_row(
                        str(comment.get('comment_ID', '')),
                        content,
                        comment.get('comment_author', 'Anonymous'),
                        status_text,
                        str(comment.get('comment_post_ID', ''))
                    )

                console.print(table)
            else:
                console.print("[yellow]No comments found[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"List comments failed: {e}")
        raise click.Abort() from None


@comment_command.command('get')
@click.argument('comment_id', type=int)
@click.option('--server', default=None, help='Server name from config')
def get_comment(comment_id, server):
    """
    Get comment details

    Examples:

        # Get comment details
        praisonaiwp comment get 123
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

            comment = wp.get_comment(comment_id)

            if comment:
                table = Table(title=f"Comment {comment_id}")
                table.add_column("Field", style="cyan")
                table.add_column("Value", style="white")

                table.add_row("ID", str(comment.get('comment_ID', '')))
                table.add_row("Content", comment.get('comment_content', ''))
                table.add_row("Author", comment.get('comment_author', 'Anonymous'))
                table.add_row("Email", comment.get('comment_author_email', ''))
                table.add_row("URL", comment.get('comment_author_url', ''))
                table.add_row("IP", comment.get('comment_author_IP', ''))
                table.add_row("Date", comment.get('comment_date', ''))
                table.add_row("Post ID", str(comment.get('comment_post_ID', '')))
                table.add_row("Status", comment.get('comment_approved', ''))

                console.print(table)
            else:
                console.print(f"[red]Comment {comment_id} not found[/red]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Get comment failed: {e}")
        raise click.Abort() from None


@comment_command.command('create')
@click.option('--post-id', required=True, type=int, help='Post ID')
@click.option('--content', required=True, help='Comment content')
@click.option('--author', help='Author name')
@click.option('--email', help='Author email')
@click.option('--url', help='Author URL')
@click.option('--server', default=None, help='Server name from config')
def create_comment(post_id, content, author, email, url, server):
    """
    Create a new comment

    Examples:

        # Create comment
        praisonaiwp comment create --post-id 123 --content "Great post!"

        # Create comment with author info
        praisonaiwp comment create --post-id 123 --content "Nice article" --author "John" --email "john@example.com"
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

            comment_id = wp.create_comment(
                post_id=post_id,
                content=content,
                author_name=author,
                author_email=email,
                author_url=url
            )

            console.print(f"[green]✓ Created comment {comment_id}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Create comment failed: {e}")
        raise click.Abort() from None


@comment_command.command('update')
@click.argument('comment_id', type=int)
@click.option('--content', help='New comment content')
@click.option('--author', help='New author name')
@click.option('--email', help='New author email')
@click.option('--url', help='New author URL')
@click.option('--server', default=None, help='Server name from config')
def update_comment(comment_id, content, author, email, url, server):
    """
    Update a comment

    Examples:

        # Update comment content
        praisonaiwp comment update 123 --content "Updated content"

        # Update author info
        praisonaiwp comment update 123 --author "Jane" --email "jane@example.com"
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

            success = wp.update_comment(
                comment_id=comment_id,
                content=content,
                author_name=author,
                author_email=email,
                author_url=url
            )

            if success:
                console.print(f"[green]✓ Updated comment {comment_id}[/green]")
            else:
                console.print(f"[red]Failed to update comment {comment_id}[/red]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Update comment failed: {e}")
        raise click.Abort() from None


@comment_command.command('delete')
@click.argument('comment_id', type=int)
@click.option('--server', default=None, help='Server name from config')
@click.confirmation_option(prompt='Are you sure you want to delete this comment?')
def delete_comment(comment_id, server):
    """
    Delete a comment

    Examples:

        # Delete comment
        praisonaiwp comment delete 123
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

            success = wp.delete_comment(comment_id)

            if success:
                console.print(f"[green]✓ Deleted comment {comment_id}[/green]")
            else:
                console.print(f"[red]Failed to delete comment {comment_id}[/red]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Delete comment failed: {e}")
        raise click.Abort() from None


@comment_command.command('approve')
@click.argument('comment_id', type=int)
@click.option('--unapprove', is_flag=True, help='Unapprove the comment instead')
@click.option('--server', default=None, help='Server name from config')
def approve_comment(comment_id, unapprove, server):
    """
    Approve or unapprove a comment

    Examples:

        # Approve comment
        praisonaiwp comment approve 123

        # Unapprove comment
        praisonaiwp comment approve 123 --unapprove
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

            if unapprove:
                success = wp.unapprove_comment(comment_id)
                if success:
                    console.print(f"[green]✓ Unapproved comment {comment_id}[/green]")
                else:
                    console.print(f"[red]Failed to unapprove comment {comment_id}[/red]")
            else:
                success = wp.approve_comment(comment_id)
                if success:
                    console.print(f"[green]✓ Approved comment {comment_id}[/green]")
                else:
                    console.print(f"[red]Failed to approve comment {comment_id}[/red]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Approve comment failed: {e}")
        raise click.Abort() from None


@comment_command.command('approve')
@click.argument('comment_id', type=int)
@click.option('--server', default=None, help='Server name from config')
def approve_comment(comment_id, server):
    """
    Approve a WordPress comment

    Examples:

        # Approve comment
        praisonaiwp comment approve 123
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

            success = wp.comment_approve(comment_id)
            if success:
                console.print(f"[green]✓ Approved comment {comment_id}[/green]")
            else:
                console.print(f"[red]✗ Failed to approve comment {comment_id}[/red]")
                raise click.ClickException(f"Comment approval failed for {comment_id}")

    except click.ClickException:
        raise
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Approve comment failed: {e}")
        raise click.Abort() from None


@comment_command.command('unapprove')
@click.argument('comment_id', type=int)
@click.option('--server', default=None, help='Server name from config')
def unapprove_comment(comment_id, server):
    """
    Unapprove a WordPress comment

    Examples:

        # Unapprove comment
        praisonaiwp comment unapprove 123
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

            success = wp.comment_unapprove(comment_id)
            if success:
                console.print(f"[green]✓ Unapproved comment {comment_id}[/green]")
            else:
                console.print(f"[red]✗ Failed to unapprove comment {comment_id}[/red]")
                raise click.ClickException(f"Comment unapproval failed for {comment_id}")

    except click.ClickException:
        raise
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Unapprove comment failed: {e}")
        raise click.Abort() from None


@comment_command.command('spam')
@click.argument('comment_id', type=int)
@click.option('--server', default=None, help='Server name from config')
def spam_comment(comment_id, server):
    """
    Mark a WordPress comment as spam

    Examples:

        # Mark comment as spam
        praisonaiwp comment spam 123
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

            success = wp.comment_spam(comment_id)
            if success:
                console.print(f"[green]✓ Marked comment {comment_id} as spam[/green]")
            else:
                console.print(f"[red]✗ Failed to mark comment {comment_id} as spam[/red]")
                raise click.ClickException(f"Comment spam marking failed for {comment_id}")

    except click.ClickException:
        raise
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Spam comment failed: {e}")
        raise click.Abort() from None


@comment_command.command('trash')
@click.argument('comment_id', type=int)
@click.option('--server', default=None, help='Server name from config')
def trash_comment(comment_id, server):
    """
    Move a WordPress comment to trash

    Examples:

        # Move comment to trash
        praisonaiwp comment trash 123
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

            success = wp.comment_trash(comment_id)
            if success:
                console.print(f"[green]✓ Moved comment {comment_id} to trash[/green]")
            else:
                console.print(f"[red]✗ Failed to move comment {comment_id} to trash[/red]")
                raise click.ClickException(f"Comment trash failed for {comment_id}")

    except click.ClickException:
        raise
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Trash comment failed: {e}")
        raise click.Abort() from None
