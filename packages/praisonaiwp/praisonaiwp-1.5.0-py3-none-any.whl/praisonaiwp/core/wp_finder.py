"""WordPress installation finder for PraisonAIWP"""

from typing import List, Optional, Tuple

from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.utils.logger import get_logger

logger = get_logger(__name__)


class WordPressFinder:
    """Automatic WordPress installation finder"""

    # Common WordPress installation paths
    COMMON_PATHS = [
        '/var/www/html',
        '/var/www/html/wordpress',
        '/usr/share/nginx/html',
        '/usr/share/nginx/html/wordpress',
        '/var/www/wordpress',
        '/opt/wordpress',
        '/srv/www/wordpress',
        '/home/*/public_html',
        '/home/*/www',
        '/home/*/htdocs',
        '/var/www/vhosts/*/httpdocs',
        '/var/www/vhosts/*/public_html',
    ]

    def __init__(self, ssh: SSHManager):
        """
        Initialize WordPress Finder

        Args:
            ssh: SSH Manager instance
        """
        self.ssh = ssh

    def find_wp_config(self, search_paths: Optional[List[str]] = None) -> List[str]:
        """
        Find wp-config.php files on the server

        Args:
            search_paths: Custom paths to search (optional)

        Returns:
            List of paths containing wp-config.php
        """
        logger.info("Searching for WordPress installations...")

        found_paths = []

        try:
            # Use find command to locate wp-config.php
            # Limit search depth and exclude common non-WordPress directories
            find_cmd = (
                "find /var/www /home /usr/share/nginx /opt /srv "
                "-maxdepth 5 "
                "-type f "
                "-name 'wp-config.php' "
                "-not -path '*/wp-content/*' "
                "-not -path '*/node_modules/*' "
                "-not -path '*/vendor/*' "
                "2>/dev/null"
            )

            stdout, stderr = self.ssh.execute(find_cmd, timeout=30)

            if stdout:
                # Extract directory paths
                for line in stdout.strip().split('\n'):
                    if line and 'wp-config.php' in line:
                        # Get directory path (remove /wp-config.php)
                        wp_path = line.rsplit('/wp-config.php', 1)[0]
                        if wp_path:
                            found_paths.append(wp_path)

            logger.info(f"Found {len(found_paths)} WordPress installation(s)")
            return found_paths

        except Exception as e:
            logger.warning(f"Search failed: {e}")
            return []

    def check_common_paths(self) -> List[str]:
        """
        Check common WordPress installation paths

        Returns:
            List of valid WordPress paths
        """
        logger.info("Checking common WordPress paths...")

        found_paths = []

        for path_pattern in self.COMMON_PATHS:
            try:
                # Handle wildcard patterns
                if '*' in path_pattern:
                    # Use shell expansion
                    cmd = f"ls -d {path_pattern}/wp-config.php 2>/dev/null || true"
                    stdout, stderr = self.ssh.execute(cmd)

                    if stdout:
                        for line in stdout.strip().split('\n'):
                            if line and 'wp-config.php' in line:
                                wp_path = line.rsplit('/wp-config.php', 1)[0]
                                if wp_path not in found_paths:
                                    found_paths.append(wp_path)
                else:
                    # Direct path check
                    cmd = f"test -f {path_pattern}/wp-config.php && echo 'found' || echo 'not found'"
                    stdout, stderr = self.ssh.execute(cmd)

                    if 'found' in stdout:
                        found_paths.append(path_pattern)

            except Exception as e:
                logger.debug(f"Error checking {path_pattern}: {e}")
                continue

        logger.info(f"Found {len(found_paths)} WordPress installation(s) in common paths")
        return found_paths

    def verify_wordpress(self, path: str) -> Tuple[bool, dict]:
        """
        Verify if path contains a valid WordPress installation

        Args:
            path: Path to check

        Returns:
            Tuple of (is_valid, info_dict)
        """
        logger.debug(f"Verifying WordPress at {path}")

        info = {
            'path': path,
            'has_wp_config': False,
            'has_wp_content': False,
            'has_wp_includes': False,
            'version': None,
            'valid': False
        }

        try:
            # Check wp-config.php
            stdout, stderr = self.ssh.execute(f"test -f {path}/wp-config.php && echo 'yes' || echo 'no'")
            info['has_wp_config'] = 'yes' in stdout

            # Check wp-content directory
            stdout, stderr = self.ssh.execute(f"test -d {path}/wp-content && echo 'yes' || echo 'no'")
            info['has_wp_content'] = 'yes' in stdout

            # Check wp-includes directory
            stdout, stderr = self.ssh.execute(f"test -d {path}/wp-includes && echo 'yes' || echo 'no'")
            info['has_wp_includes'] = 'yes' in stdout

            # Try to get WordPress version
            version_file = f"{path}/wp-includes/version.php"
            stdout, stderr = self.ssh.execute(
                f"test -f {version_file} && grep \"\\$wp_version\" {version_file} | head -1 || echo 'not found'"
            )

            if 'not found' not in stdout and '$wp_version' in stdout:
                # Extract version number
                # Format: $wp_version = '6.4.2';
                try:
                    version = stdout.split("'")[1]
                    info['version'] = version
                except:
                    pass

            # Valid if has all three core components
            info['valid'] = (
                info['has_wp_config'] and
                info['has_wp_content'] and
                info['has_wp_includes']
            )

            return info['valid'], info

        except Exception as e:
            logger.warning(f"Verification failed for {path}: {e}")
            return False, info

    def find_all(self, verify: bool = True) -> List[dict]:
        """
        Find all WordPress installations on the server

        Args:
            verify: Whether to verify each installation (default: True)

        Returns:
            List of WordPress installation info dicts
        """
        logger.info("Finding all WordPress installations...")

        all_paths = set()

        # Method 1: Search for wp-config.php
        found_paths = self.find_wp_config()
        all_paths.update(found_paths)

        # Method 2: Check common paths
        common_paths = self.check_common_paths()
        all_paths.update(common_paths)

        # Verify each path
        installations = []

        for path in all_paths:
            if verify:
                is_valid, info = self.verify_wordpress(path)
                if is_valid:
                    installations.append(info)
                    logger.info(f"✓ Valid WordPress found: {path} (v{info.get('version', 'unknown')})")
                else:
                    logger.debug(f"✗ Invalid WordPress at {path}")
            else:
                installations.append({'path': path, 'valid': None})

        logger.info(f"Found {len(installations)} valid WordPress installation(s)")
        return installations

    def find_best(self) -> Optional[str]:
        """
        Find the best WordPress installation (most likely to be the main one)

        Returns:
            Path to WordPress installation or None
        """
        installations = self.find_all(verify=True)

        if not installations:
            logger.warning("No WordPress installations found")
            return None

        if len(installations) == 1:
            path = installations[0]['path']
            logger.info(f"Found single WordPress installation: {path}")
            return path

        # Multiple installations found - prioritize by path
        priority_patterns = [
            '/var/www/html/wordpress',
            '/var/www/html',
            '/var/www/wordpress',
            '/usr/share/nginx/html/wordpress',
            '/usr/share/nginx/html',
        ]

        # Check priority patterns first
        for pattern in priority_patterns:
            for install in installations:
                if install['path'] == pattern:
                    logger.info(f"Selected WordPress installation: {pattern}")
                    return pattern

        # Return first valid installation
        path = installations[0]['path']
        logger.info(f"Selected first WordPress installation: {path}")
        logger.info(f"Note: {len(installations)} installations found. Use --wp-path to specify.")

        return path

    def interactive_select(self, installations: List[dict]) -> Optional[str]:
        """
        Let user interactively select WordPress installation

        Args:
            installations: List of WordPress installations

        Returns:
            Selected path or None
        """
        if not installations:
            return None

        if len(installations) == 1:
            return installations[0]['path']

        from rich.console import Console
        from rich.prompt import IntPrompt
        from rich.table import Table

        console = Console()

        console.print("\n[bold cyan]Multiple WordPress installations found:[/bold cyan]\n")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=3)
        table.add_column("Path", style="cyan")
        table.add_column("Version", style="green")
        table.add_column("Status", style="yellow")

        for idx, install in enumerate(installations, 1):
            version = install.get('version', 'unknown')
            status = "✓ Valid" if install.get('valid') else "? Unknown"
            table.add_row(str(idx), install['path'], version, status)

        console.print(table)
        console.print()

        try:
            choice = IntPrompt.ask(
                "Select WordPress installation",
                default=1,
                choices=[str(i) for i in range(1, len(installations) + 1)]
            )

            return installations[choice - 1]['path']

        except (KeyboardInterrupt, EOFError):
            return None
