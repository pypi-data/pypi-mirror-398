"""Main CLI entry point for PraisonAIWP"""

import click
from pathlib import Path

from praisonaiwp.__version__ import __version__
from praisonaiwp.cli.commands.backup import backup
from praisonaiwp.cli.commands.cache import cache_command
from praisonaiwp.cli.commands.category import category_command
from praisonaiwp.cli.commands.comment import comment_command
from praisonaiwp.cli.commands.config import config_command
from praisonaiwp.cli.commands.core import core_command
from praisonaiwp.cli.commands.create import create_command
from praisonaiwp.cli.commands.cron import cron_command
from praisonaiwp.cli.commands.db import db_command
from praisonaiwp.cli.commands.eval import eval_command
from praisonaiwp.cli.commands.find import find_command
from praisonaiwp.cli.commands.find_wordpress import find_wordpress
from praisonaiwp.cli.commands.help import help_command
from praisonaiwp.cli.commands.import_export import export_command, import_command
from praisonaiwp.cli.commands.init import init_command
from praisonaiwp.cli.commands.install_wp_cli import install_wp_cli
from praisonaiwp.cli.commands.list import list_command
from praisonaiwp.cli.commands.media import media_command
from praisonaiwp.cli.commands.menu import menu_command
from praisonaiwp.cli.commands.meta import meta_command
from praisonaiwp.cli.commands.network import network_command
from praisonaiwp.cli.commands.option import option_command
from praisonaiwp.cli.commands.plugin import plugin
from praisonaiwp.cli.commands.post import post_command
from praisonaiwp.cli.commands.rewrite import rewrite_command
from praisonaiwp.cli.commands.role import role_command
from praisonaiwp.cli.commands.scaffold import scaffold_command
from praisonaiwp.cli.commands.server import server_command
from praisonaiwp.cli.commands.sidebar import sidebar_command
from praisonaiwp.cli.commands.site import site_command
from praisonaiwp.cli.commands.system import system_command
from praisonaiwp.cli.commands.taxonomy import taxonomy_command
from praisonaiwp.cli.commands.term import term_command
from praisonaiwp.cli.commands.theme import theme_command
from praisonaiwp.cli.commands.transient import transient_command
from praisonaiwp.cli.commands.update import update_command
from praisonaiwp.cli.commands.user import user_command
from praisonaiwp.cli.commands.widget import widget_command

# New WP-CLI commands
from praisonaiwp.cli.commands.ability import ability
from praisonaiwp.cli.commands.admin import admin
from praisonaiwp.cli.commands.block import block
from praisonaiwp.cli.commands.cap import cap
from praisonaiwp.cli.commands.cli import wpcli
import importlib.util

# Define commands directory using absolute path
COMMANDS_DIR = Path(__file__).parent / "commands"

# Import modules with hyphens in names
dist_archive_spec = importlib.util.spec_from_file_location("dist_archive", str(COMMANDS_DIR / "dist-archive.py"))
dist_archive_module = importlib.util.module_from_spec(dist_archive_spec)
dist_archive_spec.loader.exec_module(dist_archive_module)
dist_archive = dist_archive_module.dist_archive

eval_file_spec = importlib.util.spec_from_file_location("eval_file", str(COMMANDS_DIR / "eval-file.py"))
eval_file_module = importlib.util.module_from_spec(eval_file_spec)
eval_file_spec.loader.exec_module(eval_file_module)
eval_file = eval_file_module.eval_file

maintenance_mode_spec = importlib.util.spec_from_file_location("maintenance_mode", str(COMMANDS_DIR / "maintenance-mode.py"))
maintenance_mode_module = importlib.util.module_from_spec(maintenance_mode_spec)
maintenance_mode_spec.loader.exec_module(maintenance_mode_module)
maintenance_mode = maintenance_mode_module.maintenance_mode

post_type_spec = importlib.util.spec_from_file_location("post_type", str(COMMANDS_DIR / "post-type.py"))
post_type_module = importlib.util.module_from_spec(post_type_spec)
post_type_spec.loader.exec_module(post_type_module)
post_type = post_type_module.post_type_command

search_replace_spec = importlib.util.spec_from_file_location("search_replace", str(COMMANDS_DIR / "search-replace.py"))
search_replace_module = importlib.util.module_from_spec(search_replace_spec)
search_replace_spec.loader.exec_module(search_replace_module)
search_replace = search_replace_module.search_replace_command

super_admin_spec = importlib.util.spec_from_file_location("super_admin", str(COMMANDS_DIR / "super-admin.py"))
super_admin_module = importlib.util.module_from_spec(super_admin_spec)
super_admin_spec.loader.exec_module(super_admin_module)
super_admin = super_admin_module.super_admin_command

from praisonaiwp.cli.commands.embed import embed
from praisonaiwp.cli.commands.i18n import i18n
from praisonaiwp.cli.commands.language import language
from praisonaiwp.cli.commands.package import package
from praisonaiwp.cli.commands.profile import profile
from praisonaiwp.cli.commands.shell import shell

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


@click.group(context_settings={'help_option_names': ['-h', '--help']})
@click.version_option(__version__, '--version', message='PraisonAIWP v%(version)s')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format for scripting and automation')
@click.pass_context
def cli(ctx, json_output):
    """
    PraisonAIWP - AI-powered WordPress content management

    Simple, powerful WordPress automation via WP-CLI over SSH.

    \b
    CONTENT FORMAT:
    ---------------
    Gutenberg blocks are the DEFAULT and PREFERRED format.
    HTML content is automatically converted to Gutenberg blocks.
    Use --no-block-conversion only if you're providing raw Gutenberg block markup.

    \b
    AUTOMATION & SCRIPTING:
    -----------------------
    For scripting and automation, use --json flag:
    praisonaiwp --json create "Post Title" --content "<!-- wp:paragraph --><p>Content</p><!-- /wp:paragraph -->"

    JSON output includes structured data and error information for programmatic use.

    \b
    GUTENBERG BLOCK FORMAT (default):
    ----------------------------------

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

    # Ensure context object exists and pass JSON output preference
    if ctx.obj is None:
        ctx.obj = {}
    ctx.obj['json_output'] = json_output


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
cli.add_command(option_command, name='option')
cli.add_command(meta_command, name='meta')
cli.add_command(comment_command, name='comment')
cli.add_command(system_command, name='system')
cli.add_command(theme_command, name='theme')
cli.add_command(menu_command, name='menu')
cli.add_command(transient_command, name='transient')
cli.add_command(post_command, name='post')
cli.add_command(db_command, name='db')
cli.add_command(config_command, name='config')
cli.add_command(core_command, name='core')
cli.add_command(cron_command, name='cron')
cli.add_command(taxonomy_command, name='taxonomy')
cli.add_command(term_command, name='term')
cli.add_command(widget_command, name='widget')
cli.add_command(role_command, name='role')
cli.add_command(scaffold_command, name='scaffold')
cli.add_command(cache_command, name='cache')
cli.add_command(rewrite_command, name='rewrite')
cli.add_command(sidebar_command, name='sidebar')
cli.add_command(site_command, name='site')
cli.add_command(network_command, name='network')
cli.add_command(server_command, name='server')
cli.add_command(backup, name='backup')
cli.add_command(help_command, name='help')
cli.add_command(eval_command, name='eval')
cli.add_command(maintenance_mode, name='maintenance-mode')
cli.add_command(export_command, name='export')
cli.add_command(import_command, name='import')
cli.add_command(media_command, name='media')
cli.add_command(post_type, name='post-type')
cli.add_command(search_replace, name='search-replace')
cli.add_command(super_admin, name='super-admin')

# Register new WP-CLI commands
cli.add_command(ability, name='ability')
cli.add_command(admin, name='admin')
cli.add_command(block, name='block')
cli.add_command(cap, name='cap')
cli.add_command(wpcli, name='cli')
cli.add_command(dist_archive, name='dist-archive')
cli.add_command(embed, name='embed')
cli.add_command(eval_file, name='eval-file')
cli.add_command(i18n, name='i18n')
cli.add_command(language, name='language')
cli.add_command(package, name='package')
cli.add_command(profile, name='profile')
cli.add_command(shell, name='shell')

# Register AI commands if available
if AI_COMMANDS_AVAILABLE:
    cli.add_command(ai, name='ai')

# Register MCP commands if available
if MCP_COMMANDS_AVAILABLE:
    cli.add_command(mcp, name='mcp')


if __name__ == '__main__':
    cli()
