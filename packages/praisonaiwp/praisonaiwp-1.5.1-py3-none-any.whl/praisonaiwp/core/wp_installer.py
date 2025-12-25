"""WP-CLI installer for PraisonAIWP"""

from typing import Optional, Tuple

from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.utils.exceptions import WPCLIError
from praisonaiwp.utils.logger import get_logger

logger = get_logger(__name__)


class WPCLIInstaller:
    """Automatic WP-CLI installer with OS detection"""

    def __init__(self, ssh: SSHManager):
        """
        Initialize WP-CLI Installer

        Args:
            ssh: SSH Manager instance
        """
        self.ssh = ssh
        self.os_type = None
        self.os_version = None

    def detect_os(self) -> Tuple[str, str]:
        """
        Detect remote server OS

        Returns:
            Tuple of (os_type, os_version)
            os_type: 'ubuntu', 'debian', 'centos', 'rhel', 'fedora', 'alpine', 'macos', 'unknown'
        """
        logger.info("Detecting remote OS...")

        try:
            # Try to read /etc/os-release (most Linux distributions)
            stdout, stderr = self.ssh.execute("cat /etc/os-release 2>/dev/null || echo 'not found'")

            if 'not found' not in stdout:
                os_info = stdout.lower()

                if 'ubuntu' in os_info:
                    self.os_type = 'ubuntu'
                    # Extract version
                    for line in stdout.split('\n'):
                        if 'VERSION_ID' in line:
                            self.os_version = line.split('=')[1].strip('"')
                            break

                elif 'debian' in os_info:
                    self.os_type = 'debian'
                    for line in stdout.split('\n'):
                        if 'VERSION_ID' in line:
                            self.os_version = line.split('=')[1].strip('"')
                            break

                elif 'centos' in os_info:
                    self.os_type = 'centos'
                    for line in stdout.split('\n'):
                        if 'VERSION_ID' in line:
                            self.os_version = line.split('=')[1].strip('"')
                            break

                elif 'rhel' in os_info or 'red hat' in os_info:
                    self.os_type = 'rhel'
                    for line in stdout.split('\n'):
                        if 'VERSION_ID' in line:
                            self.os_version = line.split('=')[1].strip('"')
                            break

                elif 'fedora' in os_info:
                    self.os_type = 'fedora'
                    for line in stdout.split('\n'):
                        if 'VERSION_ID' in line:
                            self.os_version = line.split('=')[1].strip('"')
                            break

                elif 'alpine' in os_info:
                    self.os_type = 'alpine'
                    for line in stdout.split('\n'):
                        if 'VERSION_ID' in line:
                            self.os_version = line.split('=')[1].strip('"')
                            break

            # Try macOS detection
            if not self.os_type:
                stdout, stderr = self.ssh.execute("sw_vers 2>/dev/null || echo 'not found'")
                if 'not found' not in stdout and 'ProductName' in stdout:
                    self.os_type = 'macos'
                    for line in stdout.split('\n'):
                        if 'ProductVersion' in line:
                            self.os_version = line.split(':')[1].strip()
                            break

            # Fallback: check uname
            if not self.os_type:
                stdout, stderr = self.ssh.execute("uname -s")
                if 'Linux' in stdout:
                    self.os_type = 'linux'
                elif 'Darwin' in stdout:
                    self.os_type = 'macos'
                else:
                    self.os_type = 'unknown'

            logger.info(f"Detected OS: {self.os_type} {self.os_version or ''}")
            return self.os_type, self.os_version or 'unknown'

        except Exception as e:
            logger.warning(f"Failed to detect OS: {e}")
            self.os_type = 'unknown'
            return 'unknown', 'unknown'

    def check_wp_cli_installed(self, wp_cli_path: str = '/usr/local/bin/wp') -> bool:
        """
        Check if WP-CLI is already installed

        Args:
            wp_cli_path: Path to check for WP-CLI

        Returns:
            True if WP-CLI is installed and working
        """
        try:
            stdout, stderr = self.ssh.execute(f"test -f {wp_cli_path} && echo 'exists' || echo 'not found'")

            if 'exists' in stdout:
                # Test if it's executable
                stdout, stderr = self.ssh.execute(f"{wp_cli_path} --version 2>&1")
                if 'WP-CLI' in stdout:
                    logger.info(f"WP-CLI already installed: {stdout.strip()}")
                    return True

            return False

        except Exception as e:
            logger.warning(f"Failed to check WP-CLI: {e}")
            return False

    def install_wp_cli(
        self,
        install_path: str = '/usr/local/bin/wp',
        use_sudo: bool = True,
        php_bin: Optional[str] = None
    ) -> bool:
        """
        Install WP-CLI automatically based on detected OS

        Args:
            install_path: Where to install WP-CLI (default: /usr/local/bin/wp)
            use_sudo: Whether to use sudo for installation (default: True)
            php_bin: PHP binary to test with (optional)

        Returns:
            True if installation successful

        Raises:
            WPCLIError: If installation fails
        """
        if not self.os_type:
            self.detect_os()

        logger.info(f"Installing WP-CLI on {self.os_type}...")

        sudo = 'sudo ' if use_sudo else ''

        try:
            # Step 1: Download WP-CLI
            logger.info("Downloading WP-CLI...")
            download_cmd = (
                "curl -sS -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar"
            )
            stdout, stderr = self.ssh.execute(download_cmd)

            if stderr and 'curl' in stderr.lower() and 'not found' in stderr.lower():
                # Try wget as fallback
                logger.info("curl not found, trying wget...")
                download_cmd = (
                    "wget -q https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar"
                )
                stdout, stderr = self.ssh.execute(download_cmd)

            # Step 2: Verify download
            stdout, stderr = self.ssh.execute("test -f wp-cli.phar && echo 'exists' || echo 'not found'")
            if 'not found' in stdout:
                raise WPCLIError("Failed to download WP-CLI")

            logger.info("✓ WP-CLI downloaded")

            # Step 3: Test the phar file
            logger.info("Testing WP-CLI...")
            php_cmd = php_bin or 'php'
            stdout, stderr = self.ssh.execute(f"{php_cmd} wp-cli.phar --version")

            if 'WP-CLI' not in stdout:
                raise WPCLIError(f"Downloaded WP-CLI is not working: {stderr}")

            logger.info(f"✓ WP-CLI test successful: {stdout.strip()}")

            # Step 4: Make executable
            logger.info("Making WP-CLI executable...")
            stdout, stderr = self.ssh.execute("chmod +x wp-cli.phar")
            logger.info("✓ WP-CLI is executable")

            # Step 5: Move to install path
            logger.info(f"Installing to {install_path}...")
            stdout, stderr = self.ssh.execute(f"{sudo}mv wp-cli.phar {install_path}")

            if stderr and 'Permission denied' in stderr:
                raise WPCLIError(
                    f"Permission denied installing to {install_path}\n"
                    f"Try running with sudo or choose a different install path"
                )

            logger.info(f"✓ WP-CLI installed to {install_path}")

            # Step 6: Verify installation
            stdout, stderr = self.ssh.execute(f"{install_path} --version")

            if 'WP-CLI' in stdout:
                logger.info(f"✓ Installation successful: {stdout.strip()}")
                return True
            else:
                raise WPCLIError(f"Installation verification failed: {stderr}")

        except WPCLIError:
            raise
        except Exception as e:
            raise WPCLIError(f"Failed to install WP-CLI: {e}")

    def install_dependencies(self, use_sudo: bool = True) -> bool:
        """
        Install required dependencies (curl/wget, php) based on OS

        Args:
            use_sudo: Whether to use sudo (default: True)

        Returns:
            True if successful
        """
        if not self.os_type:
            self.detect_os()

        logger.info(f"Installing dependencies for {self.os_type}...")

        sudo = 'sudo ' if use_sudo else ''

        try:
            if self.os_type in ['ubuntu', 'debian']:
                # Update package list
                logger.info("Updating package list...")
                self.ssh.execute(f"{sudo}apt-get update -qq")

                # Install curl and php-cli
                logger.info("Installing curl and php-cli...")
                stdout, stderr = self.ssh.execute(
                    f"{sudo}apt-get install -y curl php-cli php-mysql"
                )
                logger.info("✓ Dependencies installed")
                return True

            elif self.os_type in ['centos', 'rhel', 'fedora']:
                # Install curl and php-cli
                logger.info("Installing curl and php-cli...")
                stdout, stderr = self.ssh.execute(
                    f"{sudo}yum install -y curl php-cli php-mysql"
                )
                logger.info("✓ Dependencies installed")
                return True

            elif self.os_type == 'alpine':
                # Install curl and php
                logger.info("Installing curl and php...")
                stdout, stderr = self.ssh.execute(
                    f"{sudo}apk add --no-cache curl php php-cli php-mysqli"
                )
                logger.info("✓ Dependencies installed")
                return True

            elif self.os_type == 'macos':
                # Check if Homebrew is installed
                stdout, stderr = self.ssh.execute("which brew")
                if stdout:
                    logger.info("Installing with Homebrew...")
                    self.ssh.execute("brew install php")
                    logger.info("✓ Dependencies installed")
                    return True
                else:
                    logger.warning("Homebrew not found, skipping dependency installation")
                    return False

            else:
                logger.warning(f"Unknown OS type: {self.os_type}, skipping dependency installation")
                return False

        except Exception as e:
            logger.warning(f"Failed to install dependencies: {e}")
            return False

    def auto_install(
        self,
        install_path: str = '/usr/local/bin/wp',
        use_sudo: bool = True,
        install_deps: bool = False,
        php_bin: Optional[str] = None
    ) -> bool:
        """
        Automatically detect OS and install WP-CLI

        Args:
            install_path: Where to install WP-CLI
            use_sudo: Whether to use sudo
            install_deps: Whether to install dependencies (curl, php)
            php_bin: PHP binary to test with

        Returns:
            True if successful
        """
        logger.info("Starting automatic WP-CLI installation...")

        # Detect OS
        os_type, os_version = self.detect_os()
        logger.info(f"Detected: {os_type} {os_version}")

        # Check if already installed
        if self.check_wp_cli_installed(install_path):
            logger.info("WP-CLI is already installed!")
            return True

        # Install dependencies if requested
        if install_deps:
            self.install_dependencies(use_sudo)

        # Install WP-CLI
        return self.install_wp_cli(install_path, use_sudo, php_bin)
