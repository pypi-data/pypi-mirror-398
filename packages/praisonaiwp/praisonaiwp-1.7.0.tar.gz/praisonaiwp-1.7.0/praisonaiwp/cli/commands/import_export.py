"""WordPress import/export commands"""

import click
from rich.console import Console

from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


@click.group()
def export_command():
    """
    Export WordPress content to various formats

    This command exports your WordPress content (posts, pages, media, etc.)
    to XML format, perfect for backups, migrations, or content transfers.
    The export includes all post types, taxonomies, media attachments,
    and maintains the structure of your WordPress site.

    What Gets Exported:
    - All posts and pages (including custom post types)
    - Categories, tags, and custom taxonomies
    - Media attachments and metadata
    - Comments and comment metadata
    - Users and user metadata
    - Custom fields and post meta
    - Menu structures and navigation

    Export Formats:
    - WordPress Extended RSS (WXR) XML format
    - Compatible with WordPress import functionality
    - Preserves all content relationships
    - Includes media attachment references

    Common Use Cases:
    - Create complete site backups
    - Migrate content between WordPress sites
    - Transfer content to development environments
    - Archive content for long-term storage
    - Prepare content for platform migration

    Examples:
        praisonaiwp export content                    # Export all content
        praisonaiwp export content --dir /backups     # Export to specific directory
        praisonaiwp export content --format xml       # Export in XML format
    """
    pass


@export_command.command('content')
@click.option('--dir', help='Directory to save export files')
@click.option('--format', default='wordpress', help='Export format')
@click.option('--server', default=None, help='Server name from config')
def export_content(dir, format, server):
    """
    Export all WordPress content to XML file

    This command exports your complete WordPress site content including posts,
    pages, media, comments, users, and all metadata to a WordPress Extended
    RSS (WXR) XML file. Perfect for backups, migrations, or content transfers.

    Export Contents:
    - Posts and pages (all post types)
    - Categories, tags, and taxonomies
    - Media library items and attachments
    - Comments with threading and metadata
    - Users with roles and capabilities
    - Custom fields and post meta data
    - Menu structures and navigation items

    Export Options:
    - --dir: Specify output directory for export files
    - --format: Choose export format (wordpress, xml)
    - --server: Target specific WordPress installation

    File Output:
    - Creates XML file with timestamp
    - Includes all content relationships
    - Preserves media attachment references
    - Compatible with WordPress import tool

    Examples:
        # Export all content to default location
        praisonaiwp export content

        # Export to specific directory
        praisonaiwp export content --dir /backups/exports

        # Export with custom format
        praisonaiwp export content --format xml --dir /tmp

        # Export from specific server
        praisonaiwp export content --server staging --dir /backups

    Use Cases:
    - Create regular content backups
    - Migrate between WordPress sites
    - Transfer to development environment
    - Archive content before major changes
    - Prepare for platform migration
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

            console.print("Exporting WordPress content...")

            # Build export arguments
            args = []
            if dir:
                args.append(f"--dir={dir}")
            if format:
                args.append(f"--format={format}")

            args_str = " ".join(args) if args else None
            result = wp.export_content(args_str)

            if result is not None:
                console.print("[green]✓ Content exported successfully[/green]")
                console.print(f"Export result: {result}")
            else:
                console.print("[red]✗ Failed to export content[/red]")
                raise click.ClickException("Content export failed")

    except click.ClickException:
        raise
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Export content failed: {e}")
        raise click.Abort() from None


@click.group()
def import_command():
    """
    Import WordPress content from exported files

    This command imports WordPress content from XML export files, allowing you
    to restore backups, migrate content between sites, or transfer content
    from other WordPress installations. Supports all WordPress content types
    and maintains relationships between posts, media, and taxonomies.

    What Can Be Imported:
    - Posts and pages (all post types)
    - Categories, tags, and custom taxonomies
    - Media library items and attachments
    - Comments with threading and metadata
    - Users with roles and capabilities
    - Custom fields and post meta data
    - Menu structures and navigation items

    Supported Formats:
    - WordPress Extended RSS (WXR) XML files
    - Standard WordPress export files
    - Files from WordPress export tool
    - Compatible with WP-CLI export format

    Import Options:
    - Handle existing content (skip, update, or create)
    - Manage user mapping and creation
    - Process media attachments
    - Preserve post IDs and relationships

    Common Use Cases:
    - Restore content from backup
    - Migrate between WordPress sites
    - Merge content from multiple sites
    - Set up development environments
    - Recover from content loss

    Examples:
        praisonaiwp import content backup.xml              # Import from file
        praisonaiwp import content backup.xml --authors create  # Create new users
        praisonaiwp import content backup.xml --server staging  # Import to staging
    """
    pass


@import_command.command('content')
@click.argument('file_path')
@click.option('--authors', help='How to handle authors')
@click.option('--server', default=None, help='Server name from config')
def import_content(file_path, authors, server):
    """
    Import WordPress content from XML export file

    This command imports WordPress content from an XML export file, restoring
    posts, pages, media, comments, users, and all metadata. Perfect for
    content migration, backup restoration, or site transfers.

    Import Process:
    - Parses XML export file for content structure
    - Creates or updates posts and pages
    - Imports categories, tags, and taxonomies
    - Processes media attachments and references
    - Imports comments with threading preserved
    - Handles user creation and mapping
    - Restores custom fields and metadata

    Author Handling Options:
    - create: Create new users for unknown authors
    - mapping: Map to existing users by email/username
    - skip: Skip content from unknown authors

    File Requirements:
    - Must be valid WordPress export XML (WXR format)
    - Can be generated by WordPress export tool
    - Compatible with standard WP-CLI exports
    - Should contain complete content structure

    Examples:
        # Import content from XML file
        praisonaiwp import content backup.xml

        # Import with automatic user creation
        praisonaiwp import content backup.xml --authors create

        # Import to specific server
        praisonaiwp import content backup.xml --server staging

        # Import with custom author handling
        praisonaiwp import content backup.xml --authors mapping

    Use Cases:
    - Restore content from backup files
    - Migrate content between WordPress sites
    - Set up development environments
    - Merge content from multiple sources
    - Recover from content loss or corruption
    - Transfer content to new hosting

    Important Notes:
    - Large imports may take considerable time
    - Media files may need separate handling
    - Existing content may be updated or skipped
    - User permissions affect import success
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

            console.print(f"Importing content from: {file_path}...")

            # Build import arguments
            args = []
            if authors:
                args.append(f"--authors={authors}")

            args_str = " ".join(args) if args else None
            success = wp.import_content(file_path, args_str)

            if success:
                console.print("[green]✓ Content imported successfully[/green]")
                console.print(f"Imported from: {file_path}")
            else:
                console.print("[red]✗ Failed to import content[/red]")
                raise click.ClickException(f"Content import failed: {file_path}")

    except click.ClickException:
        raise
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Import content failed: {e}")
        raise click.Abort() from None
