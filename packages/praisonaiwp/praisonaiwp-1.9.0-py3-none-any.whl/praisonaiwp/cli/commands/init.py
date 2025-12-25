"""Init command - Initialize PraisonAIWP configuration"""

import os
from pathlib import Path

import click
from rich.console import Console
from rich.prompt import Confirm, Prompt

from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


@click.command()
def init_command():
    """Initialize PraisonAIWP configuration"""

    console.print("\n[bold cyan]PraisonAIWP Configuration Setup[/bold cyan]\n")

    # Check if config already exists
    config = Config()
    if config.exists():
        if not Confirm.ask("Configuration already exists. Overwrite?", default=False):
            console.print("[yellow]Setup cancelled[/yellow]")
            return

    # Initialize default config
    config.initialize_default_config()

    # Prompt for server details
    console.print("[bold]Server Configuration[/bold]\n")

    hostname = Prompt.ask("Server hostname or IP")
    username = Prompt.ask("SSH username")

    default_key = str(Path.home() / ".ssh" / "id_ed25519")
    key_file = Prompt.ask("SSH private key path", default=default_key)

    # Expand ~ in key path
    key_file = os.path.expanduser(key_file)

    # Verify key file exists
    if not os.path.exists(key_file):
        console.print(f"[red]Error: Key file not found: {key_file}[/red]")
        return

    port = Prompt.ask("SSH port", default="22")

    # Test SSH connection
    console.print("\n[yellow]Testing SSH connection...[/yellow]")

    try:
        with SSHManager(hostname, username, key_file, int(port)) as ssh:
            console.print("[green]✓ SSH connection successful[/green]")

            # Auto-detect WordPress path
            console.print("\n[yellow]Detecting WordPress installation...[/yellow]")

            # Try common paths
            common_paths = [
                "/var/www/html",
                "/var/www/html/wordpress",
                "/var/www/vhosts/*/httpdocs",
                "/home/*/public_html",
            ]

            wp_path = None
            for path in common_paths:
                stdout, _ = ssh.execute(f"find {path} -name wp-config.php -type f 2>/dev/null | head -1")
                if stdout:
                    wp_path = os.path.dirname(stdout.strip())
                    break

            if wp_path:
                console.print(f"[green]✓ Found WordPress at: {wp_path}[/green]")
                use_detected = Confirm.ask("Use this path?", default=True)
                if not use_detected:
                    wp_path = Prompt.ask("WordPress installation path")
            else:
                wp_path = Prompt.ask("WordPress installation path")

            # Auto-detect PHP binary
            console.print("\n[yellow]Detecting PHP binary...[/yellow]")

            # Try to find PHP with mysqli
            stdout, _ = ssh.execute("which php")
            php_bin = stdout.strip() or "php"

            # Check for Plesk PHP
            stdout, _ = ssh.execute("ls -1 /opt/plesk/php/*/bin/php 2>/dev/null | tail -1")
            if stdout:
                plesk_php = stdout.strip()
                console.print(f"[green]✓ Found Plesk PHP: {plesk_php}[/green]")
                use_plesk = Confirm.ask("Use Plesk PHP?", default=True)
                if use_plesk:
                    php_bin = plesk_php

            console.print(f"Using PHP: {php_bin}")

            # Test WP-CLI
            console.print("\n[yellow]Testing WP-CLI...[/yellow]")
            stdout, stderr = ssh.execute(f"cd {wp_path} && {php_bin} /usr/local/bin/wp --info")

            if "WP-CLI version" in stdout:
                console.print("[green]✓ WP-CLI is working[/green]")
            else:
                console.print("[red]✗ WP-CLI test failed[/red]")
                console.print(f"Error: {stderr}")
                return

    except Exception as e:
        console.print(f"[red]✗ Connection failed: {e}[/red]")
        return

    # Save configuration
    server_config = {
        'hostname': hostname,
        'username': username,
        'key_file': key_file,
        'port': int(port),
        'wp_path': wp_path,
        'php_bin': php_bin,
        'wp_cli': '/usr/local/bin/wp'
    }

    config.add_server('default', server_config)
    config.save()

    console.print("\n[bold green]✓ Configuration saved successfully![/bold green]")
    console.print(f"\nConfig file: {config.config_path}")
    console.print("\nYou can now use PraisonAIWP commands:")
    console.print("  praisonaiwp create \"Post Title\" --content \"Content\"")
    console.print("  praisonaiwp update 123 \"old\" \"new\" --line 10")
    console.print("  praisonaiwp find \"search text\"")
    console.print("  praisonaiwp list\n")
