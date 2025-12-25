"""
MCP Server for PraisonAIWP

This module creates the FastMCP server and registers all tools, resources, and prompts.
"""

import os
from typing import Optional

try:
    from mcp.server.fastmcp import FastMCP
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    FastMCP = None

from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.utils.logger import get_logger

logger = get_logger(__name__)

# Global WP client cache
_wp_client: Optional[WPClient] = None
_ssh_manager: Optional[SSHManager] = None


def get_wp_client(server_name: Optional[str] = None) -> WPClient:
    """
    Get or create a WPClient instance.
    
    Args:
        server_name: Optional server name from config. Uses default if not specified.
        
    Returns:
        WPClient instance
    """
    global _wp_client, _ssh_manager
    
    if _wp_client is not None:
        return _wp_client
    
    # Load configuration
    config = Config()
    server_config = config.get_server(server_name or os.environ.get('PRAISONAIWP_SERVER'))
    
    # Create SSH connection
    _ssh_manager = SSHManager(
        hostname=server_config.get('hostname'),
        username=server_config.get('username'),
        key_file=server_config.get('key_file'),
        port=server_config.get('port', 22)
    )
    _ssh_manager.connect()  # Establish SSH connection
    
    # Create WP client
    _wp_client = WPClient(
        ssh=_ssh_manager,
        wp_path=server_config.get('wp_path'),
        php_bin=server_config.get('php_bin', 'php'),
        wp_cli=server_config.get('wp_cli', '/usr/local/bin/wp'),
        verify_installation=True
    )
    
    return _wp_client


def cleanup():
    """Cleanup resources on shutdown"""
    global _wp_client, _ssh_manager
    
    if _ssh_manager is not None:
        try:
            _ssh_manager.close()
        except Exception:
            pass
        _ssh_manager = None
    
    _wp_client = None


# Create MCP server if available
if MCP_AVAILABLE:
    mcp = FastMCP(
        name="PraisonAI WordPress",
        instructions="AI-powered WordPress content management via WP-CLI over SSH. Use the available tools to manage WordPress posts, users, plugins, themes, and more."
    )
    
    # Import and register tools
    from praisonaiwp.mcp.tools import (
        create_post,
        update_post,
        delete_post,
        get_post,
        list_posts,
        find_text,
        list_categories,
        set_post_categories,
        create_term,
        list_users,
        create_user,
        get_user,
        list_plugins,
        activate_plugin,
        deactivate_plugin,
        list_themes,
        activate_theme,
        import_media,
        flush_cache,
        get_core_version,
        db_query,
        search_replace,
        wp_cli,
    )
    
    # Register tools with MCP server
    mcp.tool()(create_post)
    mcp.tool()(update_post)
    mcp.tool()(delete_post)
    mcp.tool()(get_post)
    mcp.tool()(list_posts)
    mcp.tool()(find_text)
    mcp.tool()(list_categories)
    mcp.tool()(set_post_categories)
    mcp.tool()(create_term)
    mcp.tool()(list_users)
    mcp.tool()(create_user)
    mcp.tool()(get_user)
    mcp.tool()(list_plugins)
    mcp.tool()(activate_plugin)
    mcp.tool()(deactivate_plugin)
    mcp.tool()(list_themes)
    mcp.tool()(activate_theme)
    mcp.tool()(import_media)
    mcp.tool()(flush_cache)
    mcp.tool()(get_core_version)
    mcp.tool()(db_query)
    mcp.tool()(search_replace)
    mcp.tool()(wp_cli)
    
    # Import and register resources
    from praisonaiwp.mcp.resources import (
        get_wordpress_info,
        get_post_resource,
        get_posts_list,
        get_categories_resource,
        get_users_resource,
        get_plugins_resource,
        get_themes_resource,
        get_config_resource,
    )
    
    # Register resources with MCP server
    mcp.resource("wordpress://info")(get_wordpress_info)
    mcp.resource("wordpress://posts/{post_id}")(get_post_resource)
    mcp.resource("wordpress://posts")(get_posts_list)
    mcp.resource("wordpress://categories")(get_categories_resource)
    mcp.resource("wordpress://users")(get_users_resource)
    mcp.resource("wordpress://plugins")(get_plugins_resource)
    mcp.resource("wordpress://themes")(get_themes_resource)
    mcp.resource("wordpress://config")(get_config_resource)
    
    # Import and register prompts
    from praisonaiwp.mcp.prompts import (
        create_blog_post_prompt,
        update_content_prompt,
        bulk_update_prompt,
        seo_optimize_prompt,
    )
    
    # Register prompts with MCP server
    mcp.prompt()(create_blog_post_prompt)
    mcp.prompt()(update_content_prompt)
    mcp.prompt()(bulk_update_prompt)
    mcp.prompt()(seo_optimize_prompt)

else:
    # Create a placeholder if MCP is not installed
    class MCPPlaceholder:
        """Placeholder when MCP is not installed"""
        name = "PraisonAI WordPress (MCP not installed)"
        
        def run(self, *args, **kwargs):
            raise ImportError(
                "MCP SDK is not installed. Install it with: pip install praisonaiwp[mcp]"
            )
        
        def tool(self):
            def decorator(func):
                return func
            return decorator
        
        def resource(self, uri):
            def decorator(func):
                return func
            return decorator
        
        def prompt(self):
            def decorator(func):
                return func
            return decorator
    
    mcp = MCPPlaceholder()


def run_server(transport: str = "stdio"):
    """
    Run the MCP server
    
    Args:
        transport: Transport type ("stdio" or "streamable-http")
    """
    import logging
    import sys

    if not MCP_AVAILABLE:
        raise ImportError(
            "MCP SDK is not installed. Install it with: pip install praisonaiwp[mcp]"
        )

    # For stdio transport, redirect ALL logging to stderr to avoid interfering with JSON-RPC
    if transport == "stdio":
        # Suppress all logging to stdout - redirect to stderr with higher threshold
        logging.basicConfig(
            level=logging.WARNING,
            stream=sys.stderr,
            format='%(message)s',
            force=True
        )
        # Disable all praisonaiwp loggers
        for name in list(logging.Logger.manager.loggerDict.keys()):
            if 'praisonaiwp' in name or 'paramiko' in name:
                logging.getLogger(name).disabled = True

    try:
        mcp.run(transport=transport)
    finally:
        cleanup()


if __name__ == "__main__":
    run_server()
