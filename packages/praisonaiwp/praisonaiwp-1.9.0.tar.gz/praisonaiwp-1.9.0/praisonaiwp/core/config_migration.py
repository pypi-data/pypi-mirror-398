"""Configuration migration utilities for upgrading from v1.0 to v2.0"""

import re
from typing import Any, Dict

from praisonaiwp.utils.logger import get_logger

logger = get_logger(__name__)


def extract_website_from_wp_path(wp_path: str) -> str:
    """
    Extract website domain from WordPress path

    Args:
        wp_path: WordPress installation path (e.g., /var/www/vhosts/example.com/httpdocs)

    Returns:
        Website URL with https:// prefix
    """
    # Pattern to match /vhosts/domain.com/ in path
    match = re.search(r'/vhosts/([^/]+)/', wp_path)

    if match:
        domain = match.group(1)
        return f"https://{domain}"

    # Fallback: try to extract any domain-like pattern
    match = re.search(r'([a-zA-Z0-9-]+\.[a-zA-Z]{2,})', wp_path)
    if match:
        domain = match.group(1)
        return f"https://{domain}"

    return ""


def migrate_config_v1_to_v2(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrate configuration from v1.0 to v2.0

    Adds:
    - website field to each server (extracted from wp_path)
    - auto_route setting (default: False)
    - Updates version to 2.0

    Args:
        config: Configuration dictionary in v1.0 format

    Returns:
        Configuration dictionary in v2.0 format
    """
    migrated = config.copy()

    # Update version
    migrated['version'] = '2.0'

    # Process each server
    servers = migrated.get('servers', {})
    for server_name, server_config in servers.items():
        # Only add website if it doesn't exist
        if 'website' not in server_config:
            wp_path = server_config.get('wp_path', '')
            if wp_path:
                website = extract_website_from_wp_path(wp_path)
                if website:
                    server_config['website'] = website
                    logger.info(f"Migrated {server_name}: Added website={website}")

    # Add auto_route setting if not present
    if 'settings' not in migrated:
        migrated['settings'] = {}

    if 'auto_route' not in migrated['settings']:
        # Default to False for safety (user must explicitly enable)
        migrated['settings']['auto_route'] = False
        logger.info("Added auto_route setting (default: False)")

    return migrated


def needs_migration(config: Dict[str, Any]) -> bool:
    """
    Check if configuration needs migration

    Args:
        config: Configuration dictionary

    Returns:
        True if migration is needed, False otherwise
    """
    version = config.get('version', '1.0')

    # Check version
    if version == '1.0':
        return True

    # Check if any server is missing website field
    servers = config.get('servers', {})
    for server_config in servers.values():
        if 'website' not in server_config and 'wp_path' in server_config:
            return True

    return False
