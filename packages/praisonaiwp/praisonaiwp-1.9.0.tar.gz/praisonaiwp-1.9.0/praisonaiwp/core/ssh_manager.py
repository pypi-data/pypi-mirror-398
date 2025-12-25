"""SSH connection management for PraisonAIWP"""

import os
from pathlib import Path
from typing import Optional, Tuple

import paramiko

from praisonaiwp.utils.exceptions import SSHConnectionError
from praisonaiwp.utils.logger import get_logger

logger = get_logger(__name__)


class SSHManager:
    """Manages SSH connections to remote WordPress servers"""

    def __init__(
        self,
        hostname: str,
        username: Optional[str] = None,
        key_file: Optional[str] = None,
        port: int = 22,
        timeout: int = 30,
        use_ssh_config: bool = True
    ):
        """
        Initialize SSH Manager

        Args:
            hostname: Server hostname, IP, or SSH config alias
            username: SSH username (optional if in SSH config)
            key_file: Path to SSH private key (optional if in SSH config)
            port: SSH port (default: 22, overridden by SSH config)
            timeout: Connection timeout in seconds (default: 30)
            use_ssh_config: Whether to use ~/.ssh/config (default: True)
        """
        self.original_hostname = hostname
        self.use_ssh_config = use_ssh_config

        # Load SSH config if enabled
        ssh_config = self._load_ssh_config() if use_ssh_config else {}

        # Apply SSH config values with fallbacks
        self.hostname = ssh_config.get('hostname', hostname)
        self.username = username or ssh_config.get('user')
        self.key_file = key_file or ssh_config.get('identityfile', [None])[0]
        self.port = ssh_config.get('port', port)
        self.timeout = timeout
        self.client: Optional[paramiko.SSHClient] = None

        # Expand ~ in key_file path
        if self.key_file:
            self.key_file = os.path.expanduser(self.key_file)

        logger.debug(f"Initialized SSHManager for {self.username}@{self.hostname}:{self.port}")
        if use_ssh_config and ssh_config:
            logger.debug(f"Using SSH config for host: {self.original_hostname}")

    def _load_ssh_config(self) -> dict:
        """
        Load SSH configuration from ~/.ssh/config

        Returns:
            Dictionary of SSH config values for the hostname
        """
        ssh_config_path = Path.home() / '.ssh' / 'config'

        if not ssh_config_path.exists():
            logger.debug("SSH config file not found")
            return {}

        try:
            ssh_config = paramiko.SSHConfig()
            with open(ssh_config_path) as f:
                ssh_config.parse(f)

            # Lookup config for this host
            host_config = ssh_config.lookup(self.original_hostname)

            logger.debug(f"Loaded SSH config for {self.original_hostname}")
            return host_config

        except Exception as e:
            logger.warning(f"Failed to load SSH config: {e}")
            return {}

    def connect(self) -> "SSHManager":
        """
        Establish SSH connection

        Returns:
            Self for chaining

        Raises:
            SSHConnectionError: If connection fails
        """
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            logger.info(f"Connecting to {self.username}@{self.hostname}:{self.port}")

            self.client.connect(
                hostname=self.hostname,
                username=self.username,
                key_filename=self.key_file,
                port=self.port,
                timeout=self.timeout,
                look_for_keys=True,
                allow_agent=True
            )

            logger.info("SSH connection established successfully")
            return self

        except paramiko.AuthenticationException as e:
            logger.error(f"Authentication failed: {e}")
            raise SSHConnectionError(f"Authentication failed: {e}")
        except paramiko.SSHException as e:
            logger.error(f"SSH error: {e}")
            raise SSHConnectionError(f"SSH error: {e}")
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise SSHConnectionError(f"Connection failed: {e}")

    def execute(self, command: str) -> Tuple[str, str]:
        """
        Execute command on remote server

        Args:
            command: Command to execute

        Returns:
            Tuple of (stdout, stderr)

        Raises:
            SSHConnectionError: If not connected or execution fails
        """
        if not self.client:
            raise SSHConnectionError("Not connected. Call connect() first.")

        try:
            logger.debug(f"Executing command: {command}")

            stdin, stdout, stderr = self.client.exec_command(command)

            stdout_str = stdout.read().decode('utf-8')
            stderr_str = stderr.read().decode('utf-8')

            if stderr_str and 'Error:' in stderr_str:
                # Don't warn about "Term doesn't exist" - it's expected when looking up categories by name
                if "Term doesn't exist" not in stderr_str:
                    logger.warning(f"Command stderr: {stderr_str}")

            logger.debug(f"Command completed with {len(stdout_str)} bytes output")

            return stdout_str, stderr_str

        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            raise SSHConnectionError(f"Command execution failed: {e}")

    def upload_file(self, local_path: str, remote_path: str) -> str:
        """
        Upload a local file to the remote server via SFTP

        Args:
            local_path: Path to local file
            remote_path: Path on remote server

        Returns:
            Remote path where file was uploaded

        Raises:
            SSHConnectionError: If not connected or upload fails
        """
        if not self.client:
            raise SSHConnectionError("Not connected. Call connect() first.")

        try:
            local_path = os.path.expanduser(local_path)

            if not os.path.exists(local_path):
                raise SSHConnectionError(f"Local file not found: {local_path}")

            logger.info(f"Uploading {local_path} to {remote_path}")

            sftp = self.client.open_sftp()
            sftp.put(local_path, remote_path)
            sftp.close()

            logger.info(f"File uploaded successfully to {remote_path}")
            return remote_path

        except Exception as e:
            logger.error(f"File upload failed: {e}")
            raise SSHConnectionError(f"File upload failed: {e}")

    def close(self):
        """Close SSH connection"""
        if self.client:
            self.client.close()
            logger.info("SSH connection closed")
            self.client = None

    def __enter__(self):
        """Context manager entry"""
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
        return False

    def __del__(self):
        """Cleanup on deletion"""
        self.close()

    @staticmethod
    def from_config(config, hostname: Optional[str] = None):
        """
        Create SSHManager from configuration

        Args:
            config: Config instance
            hostname: Server hostname (optional)

        Returns:
            SSHManager instance
        """
        if hostname:
            server_config = config.get_server(hostname)
        else:
            server_config = config.get_default_server()

        return SSHManager(
            hostname=server_config.get('hostname'),
            username=server_config.get('username'),
            key_file=server_config.get('key_filename'),
            port=server_config.get('port', 22),
            timeout=server_config.get('timeout', 30)
        )
