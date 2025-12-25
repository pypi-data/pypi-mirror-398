"""Server routing for automatic server selection based on website URLs"""

from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

from praisonaiwp.utils.logger import get_logger

logger = get_logger(__name__)


class ServerRouter:
    """Automatically route commands to correct server based on context"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize ServerRouter

        Args:
            config: Configuration dictionary with servers
        """
        self.config = config
        self.servers = config.get('servers', {})
        self.auto_route = config.get('settings', {}).get('auto_route', False)

    def find_server_by_website(self, url_or_domain: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        Find server configuration by website URL or domain

        Args:
            url_or_domain: Full URL or just domain (e.g., "biblerevelation.org")

        Returns:
            tuple: (server_name, server_config) or (None, None)
        """
        # Normalize input
        if not url_or_domain.startswith('http'):
            url_or_domain = f"https://{url_or_domain}"

        parsed = urlparse(url_or_domain)
        domain = parsed.netloc.lower()

        # Remove www. prefix for matching
        domain_without_www = domain.replace('www.', '')

        # Search through all servers
        for server_name, server_config in self.servers.items():
            # Check primary website
            if 'website' in server_config:
                server_url = urlparse(server_config['website'])
                server_domain = server_url.netloc.lower().replace('www.', '')

                if domain_without_www == server_domain:
                    logger.info(f"Found server '{server_name}' by website: {url_or_domain}")
                    return server_name, server_config

            # Check aliases
            if 'aliases' in server_config:
                for alias in server_config['aliases']:
                    alias_url = urlparse(alias)
                    alias_domain = alias_url.netloc.lower().replace('www.', '')

                    if domain_without_www == alias_domain:
                        logger.info(f"Found server '{server_name}' by alias: {url_or_domain}")
                        return server_name, server_config

        logger.debug(f"No server found for website: {url_or_domain}")
        return None, None

    def find_server_by_keywords(self, text: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        Find server by searching for website domains in text

        Args:
            text: Content text (e.g., post title, content)

        Returns:
            tuple: (server_name, server_config) or (None, None)
        """
        text_lower = text.lower()

        # Search for domain mentions in text
        for server_name, server_config in self.servers.items():
            if 'website' not in server_config:
                continue

            website_url = server_config['website']
            domain = urlparse(website_url).netloc.replace('www.', '').lower()

            # Check if domain is mentioned in text
            if domain in text_lower:
                logger.info(f"Found server '{server_name}' by keyword: {domain}")
                return server_name, server_config

            # Check aliases
            if 'aliases' in server_config:
                for alias in server_config['aliases']:
                    alias_domain = urlparse(alias).netloc.replace('www.', '').lower()
                    if alias_domain in text_lower:
                        logger.info(f"Found server '{server_name}' by alias keyword: {alias_domain}")
                        return server_name, server_config

        logger.debug("No server found by keywords in text")
        return None, None

    def get_server_info(self, server_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get human-readable server information

        Args:
            server_name: Specific server name, or None for all servers

        Returns:
            Server info dictionary or dict of all servers
        """
        if server_name:
            config = self.servers.get(server_name)
            if config:
                return {
                    'name': server_name,
                    'website': config.get('website', 'N/A'),
                    'description': config.get('description', 'N/A'),
                    'hostname': config.get('hostname', 'N/A'),
                }
            return {}

        # Return all servers
        return {
            name: {
                'website': cfg.get('website', 'N/A'),
                'description': cfg.get('description', 'N/A'),
            }
            for name, cfg in self.servers.items()
        }
