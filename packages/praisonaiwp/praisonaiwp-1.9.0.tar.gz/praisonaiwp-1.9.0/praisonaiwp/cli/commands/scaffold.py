"""WordPress scaffold commands"""

import click
from rich.console import Console

from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


@click.group()
def scaffold_command():
    """Generate WordPress code (post types, taxonomies, plugins, themes)"""
    pass


@scaffold_command.command("post-type")
@click.argument("slug")
@click.option("--label", default=None, help="Post type label")
@click.option("--public", default=None, help="Whether post type is public (true/false)")
@click.option("--has_archive", default=None, help="Whether post type has archive (true/false)")
@click.option("--supports", default=None, help="Comma-separated list of supported features")
@click.option("--server", default=None, help="Server name from config")
def scaffold_post_type(slug, label, public, has_archive, supports, server):
    """
    Generate a custom post type

    Examples:
    # Generate basic post type
    praisonaiwp scaffold post-type book

    # Generate with options
    praisonaiwp scaffold post-type book --label "Books" --public true --has_archive true --supports "title,editor,thumbnail"

    # Generate on specific server
    praisonaiwp scaffold post-type book --server staging
    """
    try:
        config = Config()
        server_config = config.get_server(server) if server else config.get_default_server()

        if not server_config:
            console.print(f"[red]Server '{server}' not found in configuration[/red]")
            return

        ssh = SSHManager.from_config(config, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        success = client.scaffold_post_type(slug, label, public, has_archive, supports)

        if success:
            console.print(f"[green]Successfully generated post type '{slug}'[/green]")
            if label:
                console.print(f"[cyan]Label:[/cyan] {label}")
            if public:
                console.print(f"[cyan]Public:[/cyan] {public}")
            if has_archive:
                console.print(f"[cyan]Has Archive:[/cyan] {has_archive}")
            if supports:
                console.print(f"[cyan]Supports:[/cyan] {supports}")
        else:
            console.print(f"[red]Failed to generate post type '{slug}'[/red]")
            raise click.Abort()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Scaffold post type failed: {e}")
        raise click.Abort() from None


@scaffold_command.command("taxonomy")
@click.argument("slug")
@click.option("--label", default=None, help="Taxonomy label")
@click.option("--public", default=None, help="Whether taxonomy is public (true/false)")
@click.option("--hierarchical", default=None, help="Whether taxonomy is hierarchical (true/false)")
@click.option("--post_types", default=None, help="Comma-separated list of post types")
@click.option("--server", default=None, help="Server name from config")
def scaffold_taxonomy(slug, label, public, hierarchical, post_types, server):
    """
    Generate a custom taxonomy

    Examples:
    # Generate basic taxonomy
    praisonaiwp scaffold taxonomy genre

    # Generate with options
    praisonaiwp scaffold taxonomy genre --label "Genres" --public true --hierarchical true --post_types "book"

    # Generate on specific server
    praisonaiwp scaffold taxonomy genre --server staging
    """
    try:
        config = Config()
        server_config = config.get_server(server) if server else config.get_default_server()

        if not server_config:
            console.print(f"[red]Server '{server}' not found in configuration[/red]")
            return

        ssh = SSHManager.from_config(config, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        success = client.scaffold_taxonomy(slug, label, public, hierarchical, post_types)

        if success:
            console.print(f"[green]Successfully generated taxonomy '{slug}'[/green]")
            if label:
                console.print(f"[cyan]Label:[/cyan] {label}")
            if public:
                console.print(f"[cyan]Public:[/cyan] {public}")
            if hierarchical:
                console.print(f"[cyan]Hierarchical:[/cyan] {hierarchical}")
            if post_types:
                console.print(f"[cyan]Post Types:[/cyan] {post_types}")
        else:
            console.print(f"[red]Failed to generate taxonomy '{slug}'[/red]")
            raise click.Abort()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Scaffold taxonomy failed: {e}")
        raise click.Abort() from None


@scaffold_command.command("plugin")
@click.argument("slug")
@click.option("--plugin_name", default=None, help="Plugin name")
@click.option("--plugin_uri", default=None, help="Plugin URI")
@click.option("--author", default=None, help="Plugin author")
@click.option("--server", default=None, help="Server name from config")
def scaffold_plugin(slug, plugin_name, plugin_uri, author, server):
    """
    Generate a WordPress plugin

    Examples:
    # Generate basic plugin
    praisonaiwp scaffold plugin my-plugin

    # Generate with options
    praisonaiwp scaffold plugin my-plugin --plugin_name "My Plugin" --plugin_uri "https://example.com" --author "Test Author"

    # Generate on specific server
    praisonaiwp scaffold plugin my-plugin --server staging
    """
    try:
        config = Config()
        server_config = config.get_server(server) if server else config.get_default_server()

        if not server_config:
            console.print(f"[red]Server '{server}' not found in configuration[/red]")
            return

        ssh = SSHManager.from_config(config, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        success = client.scaffold_plugin(slug, plugin_name, plugin_uri, author)

        if success:
            console.print(f"[green]Successfully generated plugin '{slug}'[/green]")
            if plugin_name:
                console.print(f"[cyan]Plugin Name:[/cyan] {plugin_name}")
            if plugin_uri:
                console.print(f"[cyan]Plugin URI:[/cyan] {plugin_uri}")
            if author:
                console.print(f"[cyan]Author:[/cyan] {author}")
        else:
            console.print(f"[red]Failed to generate plugin '{slug}'[/red]")
            raise click.Abort()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Scaffold plugin failed: {e}")
        raise click.Abort() from None


@scaffold_command.command("theme")
@click.argument("slug")
@click.option("--theme_name", default=None, help="Theme name")
@click.option("--theme_uri", default=None, help="Theme URI")
@click.option("--author", default=None, help="Theme author")
@click.option("--author_uri", default=None, help="Author URI")
@click.option("--server", default=None, help="Server name from config")
def scaffold_theme(slug, theme_name, theme_uri, author, author_uri, server):
    """
    Generate a WordPress theme

    Examples:
    # Generate basic theme
    praisonaiwp scaffold theme my-theme

    # Generate with options
    praisonaiwp scaffold theme my-theme --theme_name "My Theme" --theme_uri "https://example.com" --author "Test Author" --author_uri "https://author.com"

    # Generate on specific server
    praisonaiwp scaffold theme my-theme --server staging
    """
    try:
        config = Config()
        server_config = config.get_server(server) if server else config.get_default_server()

        if not server_config:
            console.print(f"[red]Server '{server}' not found in configuration[/red]")
            return

        ssh = SSHManager.from_config(config, server_config.get('hostname', server))
        client = WPClient(ssh, server_config['wp_path'])

        success = client.scaffold_theme(slug, theme_name, theme_uri, author, author_uri)

        if success:
            console.print(f"[green]Successfully generated theme '{slug}'[/green]")
            if theme_name:
                console.print(f"[cyan]Theme Name:[/cyan] {theme_name}")
            if theme_uri:
                console.print(f"[cyan]Theme URI:[/cyan] {theme_uri}")
            if author:
                console.print(f"[cyan]Author:[/cyan] {author}")
            if author_uri:
                console.print(f"[cyan]Author URI:[/cyan] {author_uri}")
        else:
            console.print(f"[red]Failed to generate theme '{slug}'[/red]")
            raise click.Abort()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Scaffold theme failed: {e}")
        raise click.Abort() from None
