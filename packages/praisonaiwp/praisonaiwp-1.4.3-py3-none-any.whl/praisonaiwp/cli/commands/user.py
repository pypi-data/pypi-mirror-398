"""User management commands"""

import click
import json
from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.utils.logger import get_logger
from rich.console import Console
from rich.table import Table

console = Console()
logger = get_logger(__name__)


@click.group()
def user_command():
    """Manage WordPress users"""
    pass


@user_command.command('list')
@click.option('--role', help='Filter by role (administrator, editor, author, etc.)')
@click.option('--server', default=None, help='Server name from config')
def list_users(role, server):
    """
    List WordPress users
    
    Examples:
    
        # List all users
        praisonaiwp user list
        
        # List administrators only
        praisonaiwp user list --role administrator
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
            
            filters = {}
            if role:
                filters['role'] = role
            
            users = wp.list_users(**filters)
            
            if not users:
                console.print("[yellow]No users found[/yellow]")
                return
            
            table = Table(title="WordPress Users")
            table.add_column("ID", style="cyan")
            table.add_column("Username", style="green")
            table.add_column("Email", style="blue")
            table.add_column("Role", style="yellow")
            
            for user in users:
                table.add_row(
                    str(user.get('ID', '')),
                    user.get('user_login', ''),
                    user.get('user_email', ''),
                    user.get('roles', '')
                )
            
            console.print(table)
            console.print(f"\n[dim]Total: {len(users)} user(s)[/dim]")
                
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"List users failed: {e}")
        raise click.Abort()


@user_command.command('get')
@click.argument('user_id', type=int)
@click.option('--server', default=None, help='Server name from config')
def get_user(user_id, server):
    """
    Get user details
    
    Examples:
    
        # Get user info
        praisonaiwp user get 1
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
            
            user = wp.get_user(user_id)
            console.print_json(json.dumps(user, indent=2))
                
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Get user failed: {e}")
        raise click.Abort()


@user_command.command('create')
@click.argument('username')
@click.argument('email')
@click.option('--role', default='subscriber', help='User role')
@click.option('--password', help='User password')
@click.option('--first-name', help='First name')
@click.option('--last-name', help='Last name')
@click.option('--server', default=None, help='Server name from config')
def create_user(username, email, role, password, first_name, last_name, server):
    """
    Create a new user
    
    Examples:
    
        # Create user
        praisonaiwp user create john john@example.com --role editor
        
        # Create with password
        praisonaiwp user create jane jane@example.com --password secret123
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
            
            kwargs = {'role': role}
            if password:
                kwargs['user_pass'] = password
            if first_name:
                kwargs['first_name'] = first_name
            if last_name:
                kwargs['last_name'] = last_name
            
            user_id = wp.create_user(username, email, **kwargs)
            console.print(f"[green]✓ Created user ID: {user_id}[/green]")
            console.print(f"Username: {username}")
            console.print(f"Email: {email}")
            console.print(f"Role: {role}")
                
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Create user failed: {e}")
        raise click.Abort()


@user_command.command('update')
@click.argument('user_id', type=int)
@click.option('--email', help='New email')
@click.option('--role', help='New role')
@click.option('--password', help='New password')
@click.option('--first-name', help='First name')
@click.option('--last-name', help='Last name')
@click.option('--server', default=None, help='Server name from config')
def update_user(user_id, email, role, password, first_name, last_name, server):
    """
    Update user
    
    Examples:
    
        # Update email
        praisonaiwp user update 5 --email newemail@example.com
        
        # Change role
        praisonaiwp user update 5 --role editor
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
            
            kwargs = {}
            if email:
                kwargs['user_email'] = email
            if role:
                kwargs['role'] = role
            if password:
                kwargs['user_pass'] = password
            if first_name:
                kwargs['first_name'] = first_name
            if last_name:
                kwargs['last_name'] = last_name
            
            if not kwargs:
                console.print("[yellow]No fields to update[/yellow]")
                return
            
            wp.update_user(user_id, **kwargs)
            console.print(f"[green]✓ Updated user ID: {user_id}[/green]")
                
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Update user failed: {e}")
        raise click.Abort()


@user_command.command('delete')
@click.argument('user_id', type=int)
@click.option('--reassign', type=int, help='Reassign posts to this user ID')
@click.option('--server', default=None, help='Server name from config')
@click.confirmation_option(prompt='Are you sure you want to delete this user?')
def delete_user(user_id, reassign, server):
    """
    Delete user
    
    Examples:
    
        # Delete user
        praisonaiwp user delete 5
        
        # Delete and reassign posts
        praisonaiwp user delete 5 --reassign 1
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
            
            wp.delete_user(user_id, reassign=reassign)
            console.print(f"[green]✓ Deleted user ID: {user_id}[/green]")
                
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Delete user failed: {e}")
        raise click.Abort()
