"""
MCP Resources for WordPress

Resources provide read-only data to LLMs for context.
They are similar to GET endpoints - they provide data but don't perform actions.
"""

from typing import Any, Dict


def get_wp_client():
    """Get WP client from server module to avoid circular imports"""
    from praisonaiwp.mcp.server import get_wp_client as _get_wp_client
    return _get_wp_client()


def get_wordpress_info() -> Dict[str, Any]:
    """
    Get WordPress installation information.

    Returns:
        Dictionary with WordPress version, site URL, and other info
    """
    client = get_wp_client()

    version = client.get_core_version()
    site_url = client.get_option('siteurl')
    home_url = client.get_option('home')
    blog_name = client.get_option('blogname')
    blog_description = client.get_option('blogdescription')

    return {
        "version": version,
        "site_url": site_url,
        "home_url": home_url,
        "blog_name": blog_name,
        "blog_description": blog_description,
        "is_installed": client.core_is_installed(),
    }


def get_post_resource(post_id: int) -> str:
    """
    Get post content by ID.

    Args:
        post_id: The post ID

    Returns:
        Post content as formatted string
    """
    client = get_wp_client()
    post = client.get_post(post_id)

    # Format post data as readable string
    content = f"""# {post.get('post_title', 'Untitled')}

**ID:** {post.get('ID')}
**Status:** {post.get('post_status')}
**Type:** {post.get('post_type')}
**Date:** {post.get('post_date')}
**Author:** {post.get('post_author')}

## Content

{post.get('post_content', '')}

## Excerpt

{post.get('post_excerpt', 'No excerpt')}
"""
    return content


def get_posts_list() -> str:
    """
    Get list of recent posts.

    Returns:
        Formatted list of recent posts
    """
    client = get_wp_client()
    posts = client.list_posts(posts_per_page=20, format='json')

    lines = ["# Recent Posts\n"]
    for post in posts:
        lines.append(f"- **{post.get('post_title')}** (ID: {post.get('ID')}, Status: {post.get('post_status')})")

    return "\n".join(lines)


def get_categories_resource() -> str:
    """
    Get all categories.

    Returns:
        Formatted list of categories
    """
    client = get_wp_client()
    categories = client.list_categories()

    lines = ["# Categories\n"]
    for cat in categories:
        lines.append(f"- **{cat.get('name')}** (ID: {cat.get('term_id')}, Slug: {cat.get('slug')})")

    return "\n".join(lines)


def get_users_resource() -> str:
    """
    Get all users.

    Returns:
        Formatted list of users
    """
    client = get_wp_client()
    users = client.list_users()

    lines = ["# Users\n"]
    for user in users:
        lines.append(f"- **{user.get('display_name')}** ({user.get('user_login')}) - Role: {user.get('roles', ['unknown'])[0] if user.get('roles') else 'unknown'}")

    return "\n".join(lines)


def get_plugins_resource() -> str:
    """
    Get installed plugins.

    Returns:
        Formatted list of plugins
    """
    client = get_wp_client()
    plugins = client.list_plugins()

    lines = ["# Installed Plugins\n"]
    for plugin in plugins:
        status = "✅ Active" if plugin.get('status') == 'active' else "❌ Inactive"
        lines.append(f"- **{plugin.get('name')}** ({plugin.get('version')}) - {status}")

    return "\n".join(lines)


def get_themes_resource() -> str:
    """
    Get installed themes.

    Returns:
        Formatted list of themes
    """
    client = get_wp_client()
    themes = client.list_themes()

    lines = ["# Installed Themes\n"]
    for theme in themes:
        status = "✅ Active" if theme.get('status') == 'active' else "❌ Inactive"
        lines.append(f"- **{theme.get('name')}** ({theme.get('version')}) - {status}")

    return "\n".join(lines)


def get_config_resource() -> str:
    """
    Get server configuration (sanitized).

    Returns:
        Formatted configuration info
    """
    from praisonaiwp.core.config import Config

    config = Config()

    try:
        server_config = config.get_server()
        # Sanitize sensitive info
        sanitized = {
            "hostname": server_config.get('hostname', 'Not configured'),
            "wp_path": server_config.get('wp_path', 'Not configured'),
            "php_bin": server_config.get('php_bin', 'php'),
            "wp_cli": server_config.get('wp_cli', '/usr/local/bin/wp'),
        }
    except Exception:
        sanitized = {"error": "Configuration not found"}

    lines = ["# Server Configuration\n"]
    for key, value in sanitized.items():
        lines.append(f"- **{key}:** {value}")

    return "\n".join(lines)
