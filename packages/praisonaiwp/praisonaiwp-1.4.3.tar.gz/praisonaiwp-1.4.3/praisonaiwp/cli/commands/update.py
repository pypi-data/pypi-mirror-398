"""Update command - Update WordPress posts"""

import click
from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.editors.content_editor import ContentEditor
from praisonaiwp.utils.logger import get_logger
from praisonaiwp.utils.block_converter import convert_to_blocks as html_to_blocks, has_blocks
from rich.console import Console
from rich.prompt import Confirm

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
@click.argument('post_id', type=int)
@click.argument('find_text', required=False)
@click.argument('replace_text', required=False)
@click.option('--line', type=int, help='Update specific line number')
@click.option('--nth', type=int, help='Update nth occurrence')
@click.option('--preview', is_flag=True, help='Preview changes without applying')
@click.option('--category', help='Comma-separated category names/slugs')
@click.option('--category-id', help='Comma-separated category IDs')
@click.option('--post-content', help='Replace entire post content')
@click.option('--post-title', help='Update post title')
@click.option('--post-status', help='Update post status (publish, draft, private)')
@click.option('--post-excerpt', help='Update post excerpt')
@click.option('--post-author', help='Update post author (user ID or login)')
@click.option('--post-date', help='Update post date (YYYY-MM-DD HH:MM:SS)')
@click.option('--tags', help='Update tags (comma-separated)')
@click.option('--meta', help='Update post meta in JSON format')
@click.option('--comment-status', help='Update comment status (open, closed)')
@click.option('--no-block-conversion', is_flag=True, help='Disable automatic HTML to Gutenberg blocks conversion')
@click.option('--server', default=None, help='Server name from config')
def update_command(post_id, find_text, replace_text, line, nth, preview, category, category_id, 
                   post_content, post_title, post_status, post_excerpt, post_author, post_date,
                   tags, meta, comment_status, no_block_conversion, server):
    """
    Update WordPress post content
    
    \b
    CONTENT FORMAT:
    Content should be HTML. By default, it auto-converts to Gutenberg blocks.
    Use --no-block-conversion to send raw Gutenberg block markup directly.
    
    \b
    EXAMPLES:
    
        # Update all occurrences
        praisonaiwp update 123 "old text" "new text"
        
        # Update specific line
        praisonaiwp update 123 "old text" "new text" --line 10
        
        # Replace entire content with HTML
        praisonaiwp update 123 --post-content "<h2>New</h2><p>Content</p>"
        
        # Replace with raw Gutenberg blocks
        praisonaiwp update 123 --no-block-conversion --post-content "<!-- wp:paragraph --><p>Hello</p><!-- /wp:paragraph -->"
        
        # Update categories only
        praisonaiwp update 123 --category "RAG,AI"
    
    \b
    GUTENBERG BLOCKS (use with --no-block-conversion):
    
    \b
        <!-- wp:paragraph --><p>Text</p><!-- /wp:paragraph -->
        <!-- wp:heading --><h2 class="wp-block-heading">Title</h2><!-- /wp:heading -->
        <!-- wp:code --><pre class="wp-block-code"><code>code</code></pre><!-- /wp:code -->
        <!-- wp:table --><figure class="wp-block-table"><table>...</table></figure><!-- /wp:table -->
        <!-- wp:separator --><hr class="wp-block-separator has-alpha-channel-opacity"/><!-- /wp:separator -->
    """
    
    try:
        # Load configuration
        config = Config()
        server_config = config.get_server(server)
        
        # Validate inputs - need at least one update operation
        if not (find_text and replace_text) and not (category or category_id) and not any([
            post_content, post_title, post_status, post_excerpt, post_author, 
            post_date, tags, meta, comment_status
        ]):
            console.print("[red]Error: At least one update operation is required[/red]")
            console.print("Options: find/replace text, --post-content, --post-title, --post-status, --post-excerpt,")
            console.print("         --post-author, --post-date, --tags, --meta, --comment-status, --category")
            raise click.Abort()
        
        console.print(f"\n[yellow]Fetching post {post_id}...[/yellow]")
        
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
            
            # Get current content
            try:
                post_data = wp.get_post(post_id)
            except Exception:
                console.print(f"[red]Error: Post {post_id} not found[/red]")
                raise click.Abort()
            
            # Handle direct field updates first
            update_fields = {}
            if post_content:
                # Auto-convert HTML to blocks (unless disabled)
                if not no_block_conversion and not has_blocks(post_content):
                    console.print("[cyan]Auto-converting HTML to Gutenberg blocks...[/cyan]")
                    post_content = html_to_blocks(post_content)
                    console.print("[green]✓ Content converted to blocks[/green]")
                elif no_block_conversion:
                    console.print("[yellow]Block conversion disabled - using raw HTML[/yellow]")
                update_fields['post_content'] = post_content
                console.print("[cyan]Updating post content...[/cyan]")
            if post_title:
                update_fields['post_title'] = post_title
                console.print(f"[cyan]Updating post title to: {post_title}[/cyan]")
            if post_status:
                update_fields['post_status'] = post_status
                console.print(f"[cyan]Updating post status to: {post_status}[/cyan]")
            if post_excerpt:
                update_fields['post_excerpt'] = post_excerpt
                console.print("[cyan]Updating post excerpt...[/cyan]")
            if post_author:
                # Handle author lookup
                if post_author.isdigit():
                    update_fields['post_author'] = int(post_author)
                else:
                    user = wp.get_user(post_author)
                    if user:
                        update_fields['post_author'] = int(user['ID'])
                    else:
                        console.print(f"[yellow]Warning: User '{post_author}' not found[/yellow]")
                console.print(f"[cyan]Updating post author...[/cyan]")
            if post_date:
                update_fields['post_date'] = post_date
                console.print(f"[cyan]Updating post date to: {post_date}[/cyan]")
            if tags:
                update_fields['tags_input'] = tags
                console.print(f"[cyan]Updating tags...[/cyan]")
            if meta:
                update_fields['meta_input'] = meta
                console.print("[cyan]Updating post meta...[/cyan]")
            if comment_status:
                update_fields['comment_status'] = comment_status
                console.print(f"[cyan]Updating comment status to: {comment_status}[/cyan]")
            
            if update_fields:
                wp.update_post(post_id, **update_fields)
                console.print("[green]✓ Post fields updated successfully[/green]")
            
            # Handle content update if find/replace provided
            if find_text and replace_text:
                current_content = wp.get_post(post_id, field='post_content')
                
                # Apply replacement based on options
                editor = ContentEditor()
                
                if line:
                    console.print(f"[cyan]Replacing at line {line}...[/cyan]")
                    new_content = editor.replace_at_line(current_content, line, find_text, replace_text)
                elif nth:
                    console.print(f"[cyan]Replacing occurrence #{nth}...[/cyan]")
                    new_content = editor.replace_nth_occurrence(current_content, find_text, replace_text, nth)
                else:
                    console.print("[cyan]Replacing all occurrences...[/cyan]")
                    new_content = current_content.replace(find_text, replace_text)
                
                # Show preview
                changes = _show_preview(current_content, new_content)
                
                if not changes:
                    console.print("[yellow]No changes to apply[/yellow]")
                    return
                
                if preview:
                    console.print("\n[yellow]Preview mode - no changes applied[/yellow]")
                    return
                
                # Confirm changes
                if not Confirm.ask("\n[bold]Apply these changes?[/bold]", default=True):
                    console.print("[yellow]Update cancelled[/yellow]")
                    return
                
                # Apply content changes
                console.print("\n[yellow]Updating post content...[/yellow]")
                wp.update_post(post_id, post_content=new_content)
            
            # Update categories if provided
            if category or category_id:
                console.print("\n[yellow]Updating categories...[/yellow]")
                category_ids = _parse_category_input(category, category_id, wp)
                if category_ids:
                    wp.set_post_categories(post_id, category_ids)
                    
                    # Get category names for display
                    category_names = []
                    for cid in category_ids:
                        cat = wp.get_category_by_id(cid)
                        if cat:
                            category_names.append(cat['name'])
                    
                    console.print(f"[green]✓ Post {post_id} updated successfully[/green]")
                    console.print(f"Title: {post_data.get('post_title', 'N/A')}")
                    console.print(f"Categories: {', '.join(category_names)}\n")
                else:
                    console.print(f"[green]✓ Post {post_id} updated successfully[/green]")
                    console.print(f"Title: {post_data.get('post_title', 'N/A')}\n")
            elif find_text and replace_text:
                console.print(f"[green]✓ Post {post_id} updated successfully[/green]")
                console.print(f"Title: {post_data.get('post_title', 'N/A')}\n")
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Update command failed: {e}")
        raise click.Abort()


def _show_preview(old_content, new_content):
    """Show preview of changes"""
    
    old_lines = old_content.split('\n')
    new_lines = new_content.split('\n')
    
    changes = []
    for i, (old_line, new_line) in enumerate(zip(old_lines, new_lines), 1):
        if old_line != new_line:
            changes.append((i, old_line, new_line))
    
    if changes:
        console.print(f"\n[bold cyan]Changes to be made: {len(changes)}[/bold cyan]\n")
        
        for line_num, old_line, new_line in changes[:5]:  # Show first 5 changes
            console.print(f"[bold]Line {line_num}:[/bold]")
            console.print(f"  [red]- {old_line.strip()}[/red]")
            console.print(f"  [green]+ {new_line.strip()}[/green]\n")
        
        if len(changes) > 5:
            console.print(f"[dim]... and {len(changes) - 5} more changes[/dim]\n")
    
    return changes
