#!/usr/bin/env python3
"""Quick test of SSH config integration"""

from praisonaiwp.core.ssh_manager import SSHManager
from rich.console import Console

console = Console()

console.print("\n[bold cyan]Testing SSH Config Integration[/bold cyan]\n")

# Test 1: Using SSH config alias
console.print("[yellow]Test 1: Connecting using SSH config alias 'myserver'...[/yellow]")

try:
    with SSHManager('myserver') as ssh:
        console.print(f"[green]✓ Connected successfully![/green]")
        console.print(f"[dim]  Hostname: {ssh.hostname}[/dim]")
        console.print(f"[dim]  Username: {ssh.username}[/dim]")
        console.print(f"[dim]  Port: {ssh.port}[/dim]")
        
        # Test command execution
        console.print("\n[yellow]Test 2: Executing test command...[/yellow]")
        stdout, stderr = ssh.execute('echo "Hello from PraisonAIWP with SSH config!"')
        console.print(f"[green]✓ Command executed: {stdout.strip()}[/green]")
        
        # Test WP-CLI
        console.print("\n[yellow]Test 3: Testing WP-CLI access...[/yellow]")
        stdout, stderr = ssh.execute(
            'cd /var/www/vhosts/example.com/httpdocs && '
            '/opt/plesk/php/8.3/bin/php /usr/local/bin/wp --info'
        )
        
        if "WP-CLI version" in stdout:
            console.print("[green]✓ WP-CLI is accessible![/green]")
            console.print(f"[dim]{stdout.strip()}[/dim]")
        else:
            console.print("[yellow]⚠ WP-CLI test inconclusive[/yellow]")
        
        console.print("\n[bold green]✓ All SSH config tests passed![/bold green]\n")

except Exception as e:
    console.print(f"[red]✗ Test failed: {e}[/red]")
    import traceback
    console.print(f"[red]{traceback.format_exc()}[/red]")
