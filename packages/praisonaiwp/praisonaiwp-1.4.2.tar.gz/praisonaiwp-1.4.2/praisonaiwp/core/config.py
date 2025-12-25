"""Configuration management for PraisonAIWP"""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from praisonaiwp.utils.logger import get_logger
from praisonaiwp.utils.exceptions import ConfigNotFoundError

logger = get_logger(__name__)


class Config:
    """Configuration manager"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration
        
        Args:
            config_path: Path to config file (optional, uses default if not provided)
        """
        self.config_path = config_path or self._default_config_path()
        self.config_dir = Path(self.config_path).parent
        self.data = self._load_config() if self.exists() else {}
        
        logger.debug(f"Config path: {self.config_path}")
    
    @staticmethod
    def _default_config_path() -> str:
        """Get default config path"""
        return str(Path.home() / ".praisonaiwp" / "config.yaml")
    
    def exists(self) -> bool:
        """Check if config file exists"""
        return os.path.exists(self.config_path)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if not self.exists():
            raise ConfigNotFoundError(
                f"Configuration not found at {self.config_path}. "
                "Run 'praisonaiwp init' first."
            )
        
        try:
            with open(self.config_path) as f:
                config = yaml.safe_load(f)
                logger.info("Configuration loaded successfully")
                return config or {}
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise ConfigNotFoundError(f"Failed to load config: {e}")
    
    def save(self):
        """Save configuration to file"""
        # Create config directory if it doesn't exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(self.data, f, default_flow_style=False)
            
            # Set file permissions to 600 (owner read/write only)
            os.chmod(self.config_path, 0o600)
            
            logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise
    
    def get_server(self, name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get server configuration
        
        Args:
            name: Server name (uses default if not provided)
            
        Returns:
            Server configuration dictionary
        """
        if not name:
            name = self.data.get('default_server', 'default')
        
        servers = self.data.get('servers', {})
        
        if name not in servers:
            raise ConfigNotFoundError(f"Server '{name}' not found in configuration")
        
        server_config = servers[name].copy()
        
        # If ssh_host is specified, load SSH config and merge
        if 'ssh_host' in server_config:
            ssh_config = self._load_ssh_config(server_config['ssh_host'])
            # SSH config values take precedence if not already set
            for key in ['hostname', 'username', 'key_file', 'port']:
                if key not in server_config and key in ssh_config:
                    server_config[key] = ssh_config[key]
        
        return server_config
    
    def _load_ssh_config(self, host: str) -> Dict[str, Any]:
        """
        Load configuration from SSH config file
        
        Args:
            host: SSH config host name
            
        Returns:
            Dictionary with hostname, username, key_file, port
        """
        import subprocess
        import os
        
        try:
            # Use ssh -G to get the effective configuration for the host
            result = subprocess.run(
                ['ssh', '-G', host],
                capture_output=True,
                text=True,
                check=True
            )
            
            config = {}
            for line in result.stdout.splitlines():
                parts = line.split(None, 1)
                if len(parts) == 2:
                    key, value = parts
                    if key == 'hostname':
                        config['hostname'] = value
                    elif key == 'user':
                        config['username'] = value
                    elif key == 'identityfile':
                        # Expand ~ to home directory
                        config['key_file'] = os.path.expanduser(value)
                    elif key == 'port':
                        config['port'] = int(value)
            
            logger.info(f"Loaded SSH config for host: {host}")
            return config
            
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to load SSH config for host '{host}': {e}")
            return {}
        except Exception as e:
            logger.warning(f"Error parsing SSH config for host '{host}': {e}")
            return {}
    
    def add_server(self, name: str, config: Dict[str, Any]):
        """
        Add or update server configuration
        
        Args:
            name: Server name
            config: Server configuration
        """
        if 'servers' not in self.data:
            self.data['servers'] = {}
        
        self.data['servers'][name] = config
        
        # Set as default if it's the first server
        if 'default_server' not in self.data:
            self.data['default_server'] = name
        
        logger.info(f"Added server: {name}")
    
    def list_servers(self) -> list:
        """Get list of configured servers"""
        return list(self.data.get('servers', {}).keys())
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value
        
        Args:
            key: Setting key
            default: Default value if not found
            
        Returns:
            Setting value
        """
        return self.data.get('settings', {}).get(key, default)
    
    def set_setting(self, key: str, value: Any):
        """
        Set a setting value
        
        Args:
            key: Setting key
            value: Setting value
        """
        if 'settings' not in self.data:
            self.data['settings'] = {}
        
        self.data['settings'][key] = value
        logger.debug(f"Set setting: {key} = {value}")
    
    def initialize_default_config(self):
        """Initialize with default configuration"""
        self.data = {
            'version': '1.0',
            'default_server': 'default',
            'servers': {},
            'settings': {
                'auto_backup': True,
                'parallel_threshold': 10,
                'parallel_workers': 10,
                'ssh_timeout': 30,
                'retry_attempts': 3,
                'log_level': 'INFO',
            }
        }
        
        # Create necessary directories
        (self.config_dir / "logs").mkdir(parents=True, exist_ok=True)
        (self.config_dir / "backups").mkdir(parents=True, exist_ok=True)
        (self.config_dir / "templates").mkdir(parents=True, exist_ok=True)
        
        logger.info("Initialized default configuration")
