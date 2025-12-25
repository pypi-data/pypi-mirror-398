"""Main CLI entry point for PraisonAIWP"""

import click
from praisonaiwp.__version__ import __version__
from praisonaiwp.cli.commands.init import init_command
from praisonaiwp.cli.commands.create import create_command
from praisonaiwp.cli.commands.update import update_command
from praisonaiwp.cli.commands.find import find_command
from praisonaiwp.cli.commands.list import list_command
from praisonaiwp.cli.commands.category import category_command
from praisonaiwp.cli.commands.media import media_command
from praisonaiwp.cli.commands.plugin import plugin
from praisonaiwp.cli.commands.install_wp_cli import install_wp_cli
from praisonaiwp.cli.commands.find_wordpress import find_wordpress
from praisonaiwp.cli.commands.user import user_command

# Try to import AI commands (optional)
try:
    from praisonaiwp.cli.commands.ai_commands import ai
    AI_COMMANDS_AVAILABLE = True
except ImportError:
    AI_COMMANDS_AVAILABLE = False

# Try to import MCP commands (optional)
try:
    from praisonaiwp.cli.commands.mcp_commands import mcp
    MCP_COMMANDS_AVAILABLE = True
except ImportError:
    MCP_COMMANDS_AVAILABLE = False


@click.group()
@click.version_option(version=__version__)
def cli():
    """
    PraisonAIWP - AI-powered WordPress content management
    
    Simple, powerful WordPress automation via WP-CLI over SSH.
    
    \b
    PREFERRED CONTENT STRUCTURE:
    ----------------------------
    WordPress-based HTML structure is preferred for best compatibility.
    
    \b
    CONTENT FORMAT:
    ---------------
    Content should be HTML. By default, it auto-converts to Gutenberg blocks.
    Use --no-block-conversion to send raw Gutenberg block markup directly.
    
    \b
    GUTENBERG BLOCK FORMAT (use with --no-block-conversion):
    --------------------------------------------------------
    
    \b
    Paragraph:
        <!-- wp:paragraph -->
        <p>Your text here</p>
        <!-- /wp:paragraph -->
    
    \b
    Heading (h2, h3, h4):
        <!-- wp:heading -->
        <h2 class="wp-block-heading">Title</h2>
        <!-- /wp:heading -->
        
        <!-- wp:heading {"level":3} -->
        <h3 class="wp-block-heading">Subtitle</h3>
        <!-- /wp:heading -->
    
    \b
    Code block:
        <!-- wp:code -->
        <pre class="wp-block-code"><code>your code here</code></pre>
        <!-- /wp:code -->
    
    \b
    Table:
        <!-- wp:table -->
        <figure class="wp-block-table"><table><thead><tr><th>Header</th></tr></thead>
        <tbody><tr><td>Cell</td></tr></tbody></table></figure>
        <!-- /wp:table -->
    
    \b
    Separator:
        <!-- wp:separator -->
        <hr class="wp-block-separator has-alpha-channel-opacity"/>
        <!-- /wp:separator -->
    
    \b
    List (unordered):
        <!-- wp:list -->
        <ul class="wp-block-list"><li>Item 1</li><li>Item 2</li></ul>
        <!-- /wp:list -->
    
    \b
    List (ordered):
        <!-- wp:list {"ordered":true} -->
        <ol class="wp-block-list"><li>First</li><li>Second</li></ol>
        <!-- /wp:list -->
    
    \b
    Image:
        <!-- wp:image {"id":123} -->
        <figure class="wp-block-image"><img src="URL" alt="Alt text"/></figure>
        <!-- /wp:image -->
    
    \b
    Quote:
        <!-- wp:quote -->
        <blockquote class="wp-block-quote"><p>Quote text</p><cite>Author</cite></blockquote>
        <!-- /wp:quote -->
    
    \b
    Columns (2 columns):
        <!-- wp:columns -->
        <div class="wp-block-columns">
        <!-- wp:column -->
        <div class="wp-block-column"><!-- wp:paragraph --><p>Col 1</p><!-- /wp:paragraph --></div>
        <!-- /wp:column -->
        <!-- wp:column -->
        <div class="wp-block-column"><!-- wp:paragraph --><p>Col 2</p><!-- /wp:paragraph --></div>
        <!-- /wp:column -->
        </div>
        <!-- /wp:columns -->
    
    \b
    Button:
        <!-- wp:buttons -->
        <div class="wp-block-buttons">
        <!-- wp:button -->
        <div class="wp-block-button"><a class="wp-block-button__link">Click Me</a></div>
        <!-- /wp:button -->
        </div>
        <!-- /wp:buttons -->
    
    \b
    OTHER BLOCKS (same pattern <!-- wp:NAME -->...<!-- /wp:NAME -->):
    preformatted, pullquote, verse, audio, video, file, gallery, cover,
    media-text, group, spacer, embed, html, shortcode, details
    
    \b
    EXAMPLES:
    ---------
    
        # Create post with HTML (auto-converts to blocks)
        praisonaiwp create "My Post" --content "<h2>Title</h2><p>Content</p>"
        
        # Create post with raw Gutenberg blocks
        praisonaiwp create "My Post" --no-block-conversion --content "<!-- wp:paragraph --><p>Hello</p><!-- /wp:paragraph -->"
        
        # Update post content
        praisonaiwp update 123 --post-content "<p>New content</p>"
        
        # List posts
        praisonaiwp list --type page
    """
    pass


# Register commands
cli.add_command(init_command, name='init')
cli.add_command(install_wp_cli, name='install-wp-cli')
cli.add_command(find_wordpress, name='find-wordpress')
cli.add_command(create_command, name='create')
cli.add_command(update_command, name='update')
cli.add_command(find_command, name='find')
cli.add_command(list_command, name='list')
cli.add_command(category_command, name='category')
cli.add_command(media_command, name='media')
cli.add_command(plugin, name='plugin')
cli.add_command(user_command, name='user')

# Register AI commands if available
if AI_COMMANDS_AVAILABLE:
    cli.add_command(ai, name='ai')

# Register MCP commands if available
if MCP_COMMANDS_AVAILABLE:
    cli.add_command(mcp, name='mcp')


if __name__ == '__main__':
    cli()
