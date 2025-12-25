"""WordPress eval commands"""

import click
from rich.console import Console

from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


@click.group()
def eval_command():
    """
    Execute PHP code in WordPress context

    This command allows you to run PHP code directly within your WordPress
    environment, perfect for debugging, testing, and administrative tasks.
    The code executes with full WordPress context including all functions,
    classes, and database access.

    Common Use Cases:
    - Debug WordPress functions and variables
    - Test custom code before implementing
    - Retrieve site information programmatically
    - Perform administrative tasks via code
    - Validate WordPress configuration

    Examples:
        praisonaiwp eval code "echo get_bloginfo('name');"
        praisonaiwp eval code "echo count_users();"
        praisonaiwp eval file /path/to/debug-script.php
    """
    pass


@eval_command.command('code')
@click.argument('php_code')
@click.option('--server', default=None, help='Server name from config')
def eval_code(php_code, server):
    """
    Execute PHP code directly in WordPress context

    This command executes PHP code with full WordPress environment access,
    including all WordPress functions, classes, database connections, and
    loaded plugins/themes. Perfect for debugging, testing, and quick tasks.

    What You Can Do:
    - Access any WordPress function (get_option, get_posts, etc.)
    - Query the WordPress database directly
    - Test plugin/theme functionality
    - Debug variables and configuration
    - Perform administrative operations

    Available WordPress Functions:
    - get_bloginfo(): Get site information
    - get_option(): Retrieve WordPress options
    - get_posts(): Query posts and pages
    - wp_get_current_user(): Get current user info
    - And all other WordPress core functions

    Examples:
        # Get site name and version
        praisonaiwp eval code "echo get_bloginfo('name');"
        praisonaiwp eval code "echo get_bloginfo('version');"

        # Count total posts
        praisonaiwp eval code "echo count_posts();"

        # Get site URL
        praisonaiwp eval code "echo get_site_url();"

        # Check if plugin is active
        praisonaiwp eval code "echo is_plugin_active('akismet/akismet.php') ? 'Active' : 'Inactive';"
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

            console.print("Executing PHP code...")
            result = wp.eval_code(php_code)

            if result is not None:
                console.print("[green]✓ PHP code executed successfully[/green]")
                console.print(f"Output: {result}")
            else:
                console.print("[red]✗ Failed to execute PHP code[/red]")
                raise click.ClickException("PHP code execution failed")

    except click.ClickException:
        raise
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Eval code failed: {e}")
        raise click.Abort() from None


@eval_command.command('file')
@click.argument('file_path')
@click.option('--server', default=None, help='Server name from config')
def eval_file(file_path, server):
    """
    Execute PHP file in WordPress context

    This command executes a PHP file within the WordPress environment,
    giving you access to all WordPress functions, classes, and database
    connections. Perfect for running complex scripts, migrations, or
    administrative tasks.

    Use Cases:
    - Run database migration scripts
    - Execute bulk operations on posts/users
    - Test complex WordPress functionality
    - Run administrative scripts
    - Perform site maintenance tasks

    File Requirements:
    - Must be a valid PHP file (.php extension)
    - Can use any WordPress functions
    - Has access to $wpdb for database operations
    - Can include other WordPress files

    Examples:
        # Execute a migration script
        praisonaiwp eval file /path/to/migration.php

        # Run a bulk update script
        praisonaiwp eval file /path/to/bulk-update.php

        # Execute a custom admin script
        praisonaiwp eval file /path/to/admin-task.php

    Sample Script Content:
        <?php
        // Access WordPress database
        global $wpdb;
        $users = $wpdb->get_results("SELECT * FROM {$wpdb->users}");
        echo "Total users: " . count($users);

        // Use WordPress functions
        $posts = get_posts(['post_type' => 'post', 'numberposts' => 5]);
        foreach ($posts as $post) {
            echo "Post: " . $post->post_title . "\\n";
        }
        ?>
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

            console.print(f"Executing PHP file: {file_path}...")
            result = wp.eval_file(file_path)

            if result is not None:
                console.print("[green]✓ PHP file executed successfully[/green]")
                console.print(f"Output: {result}")
            else:
                console.print("[red]✗ Failed to execute PHP file[/red]")
                raise click.ClickException(f"PHP file execution failed: {file_path}")

    except click.ClickException:
        raise
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Eval file failed: {e}")
        raise click.Abort() from None
