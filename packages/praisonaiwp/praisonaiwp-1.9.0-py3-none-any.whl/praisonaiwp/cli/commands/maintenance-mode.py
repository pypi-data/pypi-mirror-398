"""WordPress maintenance mode commands"""

import click
from rich.console import Console

from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


@click.group()
def maintenance_mode():
    """
    WordPress maintenance mode management

    Maintenance mode displays a maintenance page to visitors while you're
    updating your site, performing maintenance, or making changes. This
    prevents users from seeing a broken or incomplete site during updates.

    What Maintenance Mode Does:
    - Shows a "Briefly unavailable for scheduled maintenance" page
    - Blocks access to the frontend for non-administrative users
    - Allows administrators to access the site normally
    - Preserves all backend functionality for admins

    When to Use Maintenance Mode:
    - During WordPress core updates
    - When updating major plugins or themes
    - During database migrations or maintenance
    - When making significant site changes
    - During content imports or bulk operations

    Impact:
    - Visitors see maintenance page
    - Search engines can still crawl (if configured)
    - Admin users can access the site normally
    - API endpoints may be affected

    Examples:
        praisonaiwp maintenance-mode status    # Check current status
        praisonaiwp maintenance-mode activate  # Enable maintenance mode
        praisonaiwp maintenance-mode deactivate # Disable maintenance mode
    """
    pass


@maintenance_mode.command('status')
@click.option('--server', default=None, help='Server name from config')
def maintenance_status(server):
    """
    Check if WordPress maintenance mode is currently active

    This command tells you whether your WordPress site is currently in
    maintenance mode, helping you verify the status before or after
    performing maintenance operations.

    What It Checks:
    - Whether maintenance mode is enabled or disabled
    - Current status of the maintenance flag
    - Accessibility state for regular visitors

    Status Results:
    - ACTIVE: Site is in maintenance mode (visitors see maintenance page)
    - INACTIVE: Site is normal (visitors can access normally)
    - ERROR: Unable to determine status

    Examples:
        # Check current maintenance mode status
        praisonaiwp maintenance-mode status

        # Check status for specific server
        praisonaiwp maintenance-mode status --server staging

    Use Cases:
    - Verify maintenance mode is active before starting updates
    - Confirm maintenance mode is disabled after completing work
    - Check status as part of automated deployment scripts
    - Monitor site state during maintenance operations
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

            status = wp.maintenance_mode_status()

            if status is True:
                console.print("[yellow]⚠️  Maintenance mode is ACTIVE[/yellow]")
            elif status is False:
                console.print("[green]✓ Maintenance mode is INACTIVE[/green]")
            else:
                console.print("[red]✗ Failed to check maintenance mode status[/red]")
                raise click.ClickException("Maintenance mode status check failed")

    except click.ClickException:
        raise
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Maintenance mode status failed: {e}")
        raise click.Abort() from None


@maintenance_mode.command('activate')
@click.option('--server', default=None, help='Server name from config')
def maintenance_activate(server):
    """
    Activate WordPress maintenance mode

    This command enables maintenance mode on your WordPress site, displaying
    a maintenance page to visitors while allowing administrators to continue
    accessing the site. Perfect for protecting users during updates or maintenance.

    What Happens When Activated:
    - Visitors see a "Briefly unavailable for scheduled maintenance" page
    - Non-admin users cannot access the frontend
    - Administrators can still access the admin dashboard
    - All WordPress functionality remains available to admins
    - Search engines receive a 503 Service Unavailable response

    Best Practices:
    - Always activate before major updates or maintenance
    - Test admin access after activating
    - Remember to deactivate when maintenance is complete
    - Use during content imports or bulk operations

    Examples:
        # Activate maintenance mode
        praisonaiwp maintenance-mode activate

        # Activate on specific server
        praisonaiwp maintenance-mode activate --server production

    Use Cases:
    - Before WordPress core updates
    - During plugin/theme updates
    - During database maintenance
    - During content migrations
    - When performing bulk operations
    - During site redesign or major changes
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

            console.print("Activating maintenance mode...")
            success = wp.maintenance_mode_activate()

            if success:
                console.print("[green]✓ Maintenance mode activated successfully[/green]")
                console.print("[yellow]⚠️  Your site is now in maintenance mode[/yellow]")
            else:
                console.print("[red]✗ Failed to activate maintenance mode[/red]")
                raise click.ClickException("Maintenance mode activation failed")

    except click.ClickException:
        raise
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Maintenance mode activation failed: {e}")
        raise click.Abort() from None


@maintenance_mode.command('deactivate')
@click.option('--server', default=None, help='Server name from config')
def maintenance_deactivate(server):
    """
    Deactivate WordPress maintenance mode

    This command disables maintenance mode, restoring normal access to your
    WordPress site for all visitors. Use this when maintenance is complete
    and your site is ready to go live again.

    What Happens When Deactivated:
    - Visitors can access the site normally again
    - All users can view the frontend
    - Site returns to normal operation
    - Search engines can crawl normally
    - All functionality is restored for everyone

    When to Deactivate:
    - After completing WordPress updates
    - When plugin/theme updates are finished
    - After database maintenance is complete
    - When content migrations are done
    - After bulk operations finish
    - When site changes are ready for public viewing

    Verification Steps:
    - Test frontend access as a regular user
    - Verify all pages load correctly
    - Check that forms and functionality work
    - Confirm no maintenance page appears

    Examples:
        # Deactivate maintenance mode
        praisonaiwp maintenance-mode deactivate

        # Deactivate on specific server
        praisonaiwp maintenance-mode deactivate --server staging

    Use Cases:
    - After completing WordPress core updates
    - Following plugin/theme installations
    - After database maintenance or migrations
    - When content imports are complete
    - After site redesign or major changes
    - Following any maintenance operations
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

            console.print("Deactivating maintenance mode...")
            success = wp.maintenance_mode_deactivate()

            if success:
                console.print("[green]✓ Maintenance mode deactivated successfully[/green]")
                console.print("[green]✓ Your site is now live[/green]")
            else:
                console.print("[red]✗ Failed to deactivate maintenance mode[/red]")
                raise click.ClickException("Maintenance mode deactivation failed")

    except click.ClickException:
        raise
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Maintenance mode deactivation failed: {e}")
        raise click.Abort() from None
