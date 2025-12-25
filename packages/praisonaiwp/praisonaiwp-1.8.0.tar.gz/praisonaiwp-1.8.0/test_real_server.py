#!/usr/bin/env python3
"""
Test PraisonAIWP with real WordPress server
Creates a test post to verify functionality
"""

import os
from pathlib import Path

from rich.console import Console

from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.editors.content_editor import ContentEditor

console = Console()


def get_server_config():
    """Get server configuration from config file or environment variables"""

    # Try to load from config file first
    try:
        config = Config()
        if config.exists():
            server_name = os.getenv('PRAISONAIWP_SERVER', 'default')
            server_config = config.get_server(server_name)
            console.print(f"[green]✓ Loaded config from {config.config_path}[/green]")
            console.print(f"[dim]Using server: {server_name}[/dim]")
            return server_config
    except Exception as e:
        console.print(f"[yellow]⚠ Could not load config: {e}[/yellow]")

    # Fall back to environment variables
    console.print("[yellow]Using environment variables for configuration[/yellow]")
    console.print("[dim]Set WP_HOSTNAME, WP_SSH_USER, WP_PATH, etc.[/dim]")

    server_config = {
        'hostname': os.getenv('WP_HOSTNAME'),
        'username': os.getenv('WP_SSH_USER'),
        'key_file': os.getenv('WP_SSH_KEY', str(Path.home() / '.ssh' / 'id_ed25519')),
        'port': int(os.getenv('WP_SSH_PORT', '22')),
        'wp_path': os.getenv('WP_PATH'),
        'php_bin': os.getenv('WP_PHP_BIN', 'php'),
        'wp_cli': os.getenv('WP_CLI_BIN', '/usr/local/bin/wp')
    }

    # Validate required fields
    if not server_config['hostname']:
        raise ValueError(
            "WP_HOSTNAME environment variable is required.\n"
            "Run 'praisonaiwp init' to create config or set environment variables."
        )
    if not server_config['username']:
        raise ValueError(
            "WP_SSH_USER environment variable is required.\n"
            "Run 'praisonaiwp init' to create config or set environment variables."
        )
    if not server_config['wp_path']:
        raise ValueError(
            "WP_PATH environment variable is required.\n"
            "Run 'praisonaiwp init' to create config or set environment variables."
        )

    return server_config


# Get server configuration
SERVER_CONFIG = get_server_config()


def test_connection():
    """Test SSH connection"""
    console.print("\n[bold cyan]Step 1: Testing SSH Connection[/bold cyan]")

    try:
        with SSHManager(
            SERVER_CONFIG['hostname'],
            SERVER_CONFIG['username'],
            SERVER_CONFIG['key_file'],
            SERVER_CONFIG['port']
        ) as ssh:
            console.print(f"[green]✓ Connected to {SERVER_CONFIG['hostname']}[/green]")

            # Test basic command
            stdout, stderr = ssh.execute('echo "Hello from PraisonAIWP"')
            console.print(f"[green]✓ Command execution working: {stdout.strip()}[/green]")

            return ssh
    except Exception as e:
        console.print(f"[red]✗ Connection failed: {e}[/red]")
        return None


def test_wp_cli():
    """Test WP-CLI access"""
    console.print("\n[bold cyan]Step 2: Testing WP-CLI Access[/bold cyan]")

    try:
        with SSHManager(
            SERVER_CONFIG['hostname'],
            SERVER_CONFIG['username'],
            SERVER_CONFIG['key_file'],
            SERVER_CONFIG['port']
        ) as ssh:

            wp = WPClient(
                ssh,
                SERVER_CONFIG['wp_path'],
                SERVER_CONFIG['php_bin'],
                SERVER_CONFIG['wp_cli']
            )

            # Test WP-CLI
            stdout, stderr = ssh.execute(
                f"cd {SERVER_CONFIG['wp_path']} && "
                f"{SERVER_CONFIG['php_bin']} {SERVER_CONFIG['wp_cli']} --info"
            )

            if "WP-CLI version" in stdout:
                console.print("[green]✓ WP-CLI is working[/green]")
                console.print(f"[dim]{stdout.strip()}[/dim]")
            else:
                console.print("[red]✗ WP-CLI test failed[/red]")
                return None

            return wp
    except Exception as e:
        console.print(f"[red]✗ WP-CLI test failed: {e}[/red]")
        return None


def create_test_post():
    """Create a test post"""
    console.print("\n[bold cyan]Step 3: Creating Test Post[/bold cyan]")

    try:
        with SSHManager(
            SERVER_CONFIG['hostname'],
            SERVER_CONFIG['username'],
            SERVER_CONFIG['key_file'],
            SERVER_CONFIG['port']
        ) as ssh:

            wp = WPClient(
                ssh,
                SERVER_CONFIG['wp_path'],
                SERVER_CONFIG['php_bin'],
                SERVER_CONFIG['wp_cli']
            )

            # Create test post
            console.print("[yellow]Creating test post...[/yellow]")

            post_id = wp.create_post(
                post_title="PraisonAIWP Test Post",
                post_content="""
<!-- wp:heading -->
<h2>Test Post from PraisonAIWP</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>This is a test post created by PraisonAIWP framework.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Testing line-specific content editing capabilities.</p>
<!-- /wp:paragraph -->

<!-- wp:heading -->
<h2>Test Post from PraisonAIWP</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>This heading appears twice to test line-specific replacement.</p>
<!-- /wp:paragraph -->
                """.strip(),
                post_status="draft",  # Create as draft for safety
                post_type="post"
            )

            console.print("[green]✓ Test post created successfully![/green]")
            console.print(f"[bold]Post ID:[/bold] {post_id}")

            # Get the post to verify
            post_data = wp.get_post(post_id)
            console.print(f"[bold]Title:[/bold] {post_data['post_title']}")
            console.print(f"[bold]Status:[/bold] {post_data['post_status']}")
            console.print(f"[bold]Type:[/bold] {post_data['post_type']}")

            return post_id

    except Exception as e:
        console.print(f"[red]✗ Failed to create post: {e}[/red]")
        import traceback
        console.print(f"[red]{traceback.format_exc()}[/red]")
        return None


def test_line_specific_update(post_id):
    """Test line-specific content update"""
    console.print("\n[bold cyan]Step 4: Testing Line-Specific Update[/bold cyan]")

    try:
        with SSHManager(
            SERVER_CONFIG['hostname'],
            SERVER_CONFIG['username'],
            SERVER_CONFIG['key_file'],
            SERVER_CONFIG['port']
        ) as ssh:

            wp = WPClient(
                ssh,
                SERVER_CONFIG['wp_path'],
                SERVER_CONFIG['php_bin'],
                SERVER_CONFIG['wp_cli']
            )

            # Get current content
            console.print("[yellow]Fetching post content...[/yellow]")
            content = wp.get_post(post_id, field='post_content')

            # Find occurrences
            editor = ContentEditor()
            occurrences = editor.find_occurrences(content, "Test Post from PraisonAIWP")

            console.print(f"[cyan]Found {len(occurrences)} occurrence(s) of 'Test Post from PraisonAIWP':[/cyan]")
            for line_num, line_content in occurrences:
                console.print(f"  Line {line_num}: {line_content[:60]}...")

            # Replace ONLY at line 2 (first occurrence)
            console.print("\n[yellow]Replacing text at line 2 only...[/yellow]")
            new_content = editor.replace_at_line(
                content,
                2,
                "Test Post from PraisonAIWP",
                "✅ UPDATED at Line 2 - PraisonAIWP Works!"
            )

            # Update post
            wp.update_post(post_id, post_content=new_content)

            console.print("[green]✓ Post updated successfully![/green]")

            # Verify the update
            console.print("\n[yellow]Verifying update...[/yellow]")
            updated_content = wp.get_post(post_id, field='post_content')
            updated_occurrences = editor.find_occurrences(updated_content, "Test Post from PraisonAIWP")

            console.print(f"[cyan]After update, found {len(updated_occurrences)} occurrence(s) of original text:[/cyan]")
            for line_num, line_content in updated_occurrences:
                console.print(f"  Line {line_num}: {line_content[:60]}...")

            # Check for updated text
            updated_check = editor.find_occurrences(updated_content, "✅ UPDATED at Line 2")
            console.print(f"[green]✓ Found {len(updated_check)} occurrence(s) of updated text[/green]")

            console.print("\n[bold green]✓ Line-specific update test PASSED![/bold green]")
            console.print("[dim]Line 2 was updated, other occurrences remain unchanged[/dim]")

            return True

    except Exception as e:
        console.print(f"[red]✗ Update test failed: {e}[/red]")
        import traceback
        console.print(f"[red]{traceback.format_exc()}[/red]")
        return False


def cleanup_test_post(post_id):
    """Delete test post"""
    console.print("\n[bold cyan]Step 5: Cleanup[/bold cyan]")

    try:
        with SSHManager(
            SERVER_CONFIG['hostname'],
            SERVER_CONFIG['username'],
            SERVER_CONFIG['key_file'],
            SERVER_CONFIG['port']
        ) as ssh:

            WPClient(
                ssh,
                SERVER_CONFIG['wp_path'],
                SERVER_CONFIG['php_bin'],
                SERVER_CONFIG['wp_cli']
            )

            # Delete post
            console.print(f"[yellow]Deleting test post {post_id}...[/yellow]")
            stdout, stderr = ssh.execute(
                f"cd {SERVER_CONFIG['wp_path']} && "
                f"{SERVER_CONFIG['php_bin']} {SERVER_CONFIG['wp_cli']} post delete {post_id} --force"
            )

            console.print("[green]✓ Test post deleted[/green]")
            return True

    except Exception as e:
        console.print(f"[yellow]⚠ Cleanup failed (post may still exist): {e}[/yellow]")
        return False


def main():
    """Run all tests"""
    console.print("\n[bold magenta]═══════════════════════════════════════════════════[/bold magenta]")
    console.print("[bold magenta]  PraisonAIWP Real-World Server Test[/bold magenta]")
    console.print("[bold magenta]═══════════════════════════════════════════════════[/bold magenta]")

    # Test connection
    if not test_connection():
        console.print("\n[red]✗ Connection test failed. Exiting.[/red]")
        return

    # Test WP-CLI
    if not test_wp_cli():
        console.print("\n[red]✗ WP-CLI test failed. Exiting.[/red]")
        return

    # Create test post
    post_id = create_test_post()
    if not post_id:
        console.print("\n[red]✗ Post creation failed. Exiting.[/red]")
        return

    # Test line-specific update
    if not test_line_specific_update(post_id):
        console.print("\n[red]✗ Update test failed.[/red]")

    # Cleanup
    console.print("\n[yellow]Do you want to delete the test post?[/yellow]")
    cleanup = input("Delete test post? (y/n): ")
    if cleanup.lower() == 'y':
        cleanup_test_post(post_id)
    else:
        console.print(f"[cyan]Test post {post_id} kept for manual inspection[/cyan]")

    console.print("\n[bold green]═══════════════════════════════════════════════════[/bold green]")
    console.print("[bold green]  Test Complete![/bold green]")
    console.print("[bold green]═══════════════════════════════════════════════════[/bold green]\n")


if __name__ == "__main__":
    main()
