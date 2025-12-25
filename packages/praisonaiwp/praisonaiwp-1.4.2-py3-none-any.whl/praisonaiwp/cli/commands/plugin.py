"""Plugin management commands"""

import click
from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.utils.logger import get_logger

logger = get_logger(__name__)


@click.group()
def plugin():
    """Manage WordPress plugins"""
    pass


@plugin.command('list')
@click.option('--status', type=click.Choice(['all', 'active', 'inactive']), default='all',
              help='Filter plugins by status')
@click.option('--server', help='Server name from config (default: first server)')
def list_plugins(status, server):
    """
    List installed WordPress plugins
    
    Examples:
        # List all plugins
        praisonaiwp plugin list
        
        # List only active plugins
        praisonaiwp plugin list --status active
    """
    try:
        config = Config()
        server_config = config.get_server(server)
        
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
            
            kwargs = {}
            if status != 'all':
                kwargs['status'] = status
            
            plugins = wp.list_plugins(**kwargs)
            
            if not plugins:
                click.echo("No plugins found")
                return
            
            click.echo(f"\nFound {len(plugins)} plugin(s):\n")
            for plugin in plugins:
                name = plugin.get('name', 'Unknown')
                status_str = plugin.get('status', 'unknown')
                version = plugin.get('version', 'N/A')
                update = plugin.get('update', 'none')
                
                status_icon = "✓" if status_str == "active" else "○"
                update_icon = " [UPDATE AVAILABLE]" if update != "none" else ""
                
                click.echo(f"  {status_icon} {name} (v{version}){update_icon}")
                click.echo(f"    Status: {status_str}")
                if update != "none":
                    click.echo(f"    Update: {update}")
                click.echo()
    
    except Exception as e:
        logger.error(f"Failed to list plugins: {e}")
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@plugin.command('update')
@click.argument('plugin', default='all')
@click.option('--server', help='Server name from config (default: first server)')
def update_plugin(plugin, server):
    """
    Update WordPress plugin(s)
    
    PLUGIN: Plugin slug/path or "all" to update all plugins (default: all)
    
    Examples:
        # Update all plugins
        praisonaiwp plugin update
        praisonaiwp plugin update all
        
        # Update specific plugin
        praisonaiwp plugin update akismet
    """
    try:
        config = Config()
        server_config = config.get_server(server)
        
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
            
            click.echo(f"Updating plugin(s): {plugin}...")
            wp.update_plugin(plugin)
            click.echo(f"✓ Successfully updated plugin(s): {plugin}")
    
    except Exception as e:
        logger.error(f"Failed to update plugin: {e}")
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@plugin.command('activate')
@click.argument('plugin')
@click.option('--server', help='Server name from config (default: first server)')
def activate_plugin(plugin, server):
    """
    Activate a WordPress plugin
    
    Examples:
        praisonaiwp plugin activate akismet
    """
    try:
        config = Config()
        server_config = config.get_server(server)
        
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
            
            click.echo(f"Activating plugin: {plugin}...")
            wp.activate_plugin(plugin)
            click.echo(f"✓ Successfully activated plugin: {plugin}")
    
    except Exception as e:
        logger.error(f"Failed to activate plugin: {e}")
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@plugin.command('deactivate')
@click.argument('plugin')
@click.option('--server', help='Server name from config (default: first server)')
def deactivate_plugin(plugin, server):
    """
    Deactivate a WordPress plugin
    
    Examples:
        praisonaiwp plugin deactivate akismet
    """
    try:
        config = Config()
        server_config = config.get_server(server)
        
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
            
            click.echo(f"Deactivating plugin: {plugin}...")
            wp.deactivate_plugin(plugin)
            click.echo(f"✓ Successfully deactivated plugin: {plugin}")
    
    except Exception as e:
        logger.error(f"Failed to deactivate plugin: {e}")
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
