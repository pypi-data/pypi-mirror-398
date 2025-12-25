"""
MCP Tools for WordPress Operations

These tools are exposed via MCP and can be called by LLMs to perform
WordPress operations like creating posts, managing users, etc.
"""

from typing import Any, Dict, List, Optional


def get_wp_client():
    """Get WP client from server module to avoid circular imports"""
    from praisonaiwp.mcp.server import get_wp_client as _get_wp_client
    return _get_wp_client()


# =============================================================================
# Post Management Tools
# =============================================================================

def create_post(
    title: str,
    content: str,
    status: str = "draft",
    post_type: str = "post",
    author: Optional[str] = None,
    category: Optional[str] = None,
    excerpt: Optional[str] = None,
    tags: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a new WordPress post.

    Args:
        title: The post title
        content: The post content (HTML supported)
        status: Post status - 'draft', 'publish', 'private', 'pending'
        post_type: Post type - 'post', 'page', or custom post type
        author: Author username or ID (optional)
        category: Comma-separated category names or IDs (optional)
        excerpt: Post excerpt/summary (optional)
        tags: Comma-separated tag names (optional)

    Returns:
        Dictionary with post_id and success status
    """
    client = get_wp_client()

    kwargs = {
        'post_title': title,
        'post_content': content,
        'post_status': status,
        'post_type': post_type,
    }

    if author:
        kwargs['post_author'] = author
    if excerpt:
        kwargs['post_excerpt'] = excerpt

    post_id = client.create_post(**kwargs)

    # Set categories if provided
    if category:
        try:
            categories = [c.strip() for c in category.split(',')]
            client.set_post_categories(post_id, categories)
        except Exception:
            pass  # Category setting is optional

    # Set tags if provided
    if tags:
        try:
            tag_list = [t.strip() for t in tags.split(',')]
            client.wp('post', 'term', 'set', str(post_id), 'post_tag', *tag_list)
        except Exception:
            pass  # Tag setting is optional

    return {
        "post_id": post_id,
        "success": True,
        "message": f"Created post '{title}' with ID {post_id}"
    }


def update_post(
    post_id: int,
    title: Optional[str] = None,
    content: Optional[str] = None,
    status: Optional[str] = None,
    excerpt: Optional[str] = None,
    find_text: Optional[str] = None,
    replace_text: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update an existing WordPress post.

    Args:
        post_id: The ID of the post to update
        title: New post title (optional)
        content: New post content (optional)
        status: New post status (optional)
        excerpt: New post excerpt (optional)
        find_text: Text to find and replace (optional)
        replace_text: Replacement text (required if find_text is provided)

    Returns:
        Dictionary with success status
    """
    client = get_wp_client()

    kwargs = {}
    if title:
        kwargs['post_title'] = title
    if content:
        kwargs['post_content'] = content
    if status:
        kwargs['post_status'] = status
    if excerpt:
        kwargs['post_excerpt'] = excerpt

    # Handle find/replace
    if find_text and replace_text:
        current_content = client.get_post(post_id, field='post_content')
        new_content = current_content.replace(find_text, replace_text)
        kwargs['post_content'] = new_content

    if kwargs:
        client.update_post(post_id, **kwargs)

    return {
        "success": True,
        "post_id": post_id,
        "message": f"Updated post {post_id}"
    }


def delete_post(post_id: int, force: bool = False) -> Dict[str, Any]:
    """
    Delete a WordPress post.

    Args:
        post_id: The ID of the post to delete
        force: If True, permanently delete. If False, move to trash.

    Returns:
        Dictionary with success status
    """
    client = get_wp_client()
    client.delete_post(post_id, force=force)

    return {
        "success": True,
        "post_id": post_id,
        "message": f"Deleted post {post_id}" + (" permanently" if force else " (moved to trash)")
    }


def get_post(post_id: int) -> Dict[str, Any]:
    """
    Get details of a WordPress post.

    Args:
        post_id: The ID of the post to retrieve

    Returns:
        Dictionary with post data
    """
    client = get_wp_client()
    return client.get_post(post_id)


def list_posts(
    status: str = "publish",
    post_type: str = "post",
    limit: int = 10,
    search: Optional[str] = None,
    author: Optional[str] = None,
    category: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    List WordPress posts with filters.

    Args:
        status: Post status filter - 'publish', 'draft', 'all'
        post_type: Post type - 'post', 'page', 'all'
        limit: Maximum number of posts to return
        search: Search term to filter posts
        author: Filter by author username or ID
        category: Filter by category name or ID

    Returns:
        List of post dictionaries
    """
    client = get_wp_client()

    kwargs = {
        'post_status': status if status != 'all' else 'any',
        'post_type': post_type if post_type != 'all' else 'any',
        'posts_per_page': limit,
        'format': 'json',
    }

    if search:
        kwargs['s'] = search
    if author:
        kwargs['author'] = author
    if category:
        kwargs['category_name'] = category

    return client.list_posts(**kwargs)


def find_text(
    pattern: str,
    post_id: Optional[int] = None,
    post_type: str = "post",
    limit: int = 20,
) -> Dict[str, Any]:
    """
    Find text in WordPress posts.

    Args:
        pattern: Text pattern to search for
        post_id: Specific post ID to search in (optional)
        post_type: Post type to search - 'post', 'page', 'all'
        limit: Maximum number of results

    Returns:
        Dictionary with search results
    """
    client = get_wp_client()

    if post_id:
        # Search in specific post
        post = client.get_post(post_id)
        content = post.get('post_content', '')
        title = post.get('post_title', '')

        matches = []
        if pattern.lower() in content.lower():
            matches.append({"location": "content", "post_id": post_id})
        if pattern.lower() in title.lower():
            matches.append({"location": "title", "post_id": post_id})

        return {
            "pattern": pattern,
            "matches": matches,
            "count": len(matches)
        }
    else:
        # Search across all posts
        posts = client.list_posts(
            post_type=post_type if post_type != 'all' else 'any',
            s=pattern,
            posts_per_page=limit,
            format='json'
        )

        return {
            "pattern": pattern,
            "matches": [{"post_id": p.get('ID'), "title": p.get('post_title')} for p in posts],
            "count": len(posts)
        }


# =============================================================================
# Category/Term Management Tools
# =============================================================================

def list_categories() -> List[Dict[str, Any]]:
    """
    List all WordPress categories.

    Returns:
        List of category dictionaries
    """
    client = get_wp_client()
    return client.list_categories()


def set_post_categories(post_id: int, categories: str) -> Dict[str, Any]:
    """
    Set categories for a post (replaces existing categories).

    Args:
        post_id: The post ID
        categories: Comma-separated category names or IDs

    Returns:
        Dictionary with success status
    """
    client = get_wp_client()
    category_list = [c.strip() for c in categories.split(',')]
    client.set_post_categories(post_id, category_list)

    return {
        "success": True,
        "post_id": post_id,
        "categories": category_list,
        "message": f"Set categories for post {post_id}"
    }


def create_term(
    taxonomy: str,
    name: str,
    slug: Optional[str] = None,
    description: Optional[str] = None,
    parent: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Create a new term (category, tag, or custom taxonomy term).

    Args:
        taxonomy: Taxonomy name - 'category', 'post_tag', or custom
        name: Term name
        slug: Term slug (optional, auto-generated from name)
        description: Term description (optional)
        parent: Parent term ID for hierarchical taxonomies (optional)

    Returns:
        Dictionary with term_id and success status
    """
    client = get_wp_client()

    kwargs = {}
    if slug:
        kwargs['slug'] = slug
    if description:
        kwargs['description'] = description
    if parent:
        kwargs['parent'] = parent

    term_id = client.create_term(taxonomy, name, **kwargs)

    return {
        "term_id": term_id,
        "success": True,
        "message": f"Created term '{name}' in {taxonomy}"
    }


# =============================================================================
# User Management Tools
# =============================================================================

def list_users(
    role: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """
    List WordPress users.

    Args:
        role: Filter by role - 'administrator', 'editor', 'author', 'subscriber'
        search: Search term for username or email
        limit: Maximum number of users to return

    Returns:
        List of user dictionaries
    """
    client = get_wp_client()

    kwargs = {'number': limit}
    if role:
        kwargs['role'] = role
    if search:
        kwargs['search'] = f"*{search}*"

    return client.list_users(**kwargs)


def create_user(
    username: str,
    email: str,
    role: str = "subscriber",
    password: Optional[str] = None,
    display_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a new WordPress user.

    Args:
        username: Username for the new user
        email: Email address
        role: User role - 'administrator', 'editor', 'author', 'contributor', 'subscriber'
        password: User password (optional, auto-generated if not provided)
        display_name: Display name (optional)

    Returns:
        Dictionary with user_id and success status
    """
    client = get_wp_client()

    kwargs = {'role': role}
    if password:
        kwargs['user_pass'] = password
    if display_name:
        kwargs['display_name'] = display_name

    user_id = client.create_user(username, email, **kwargs)

    return {
        "user_id": user_id,
        "success": True,
        "message": f"Created user '{username}' with ID {user_id}"
    }


def get_user(user_id: int) -> Dict[str, Any]:
    """
    Get details of a WordPress user.

    Args:
        user_id: The user ID

    Returns:
        Dictionary with user data
    """
    client = get_wp_client()
    return client.get_user(user_id)


# =============================================================================
# Plugin/Theme Management Tools
# =============================================================================

def list_plugins(status: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List installed WordPress plugins.

    Args:
        status: Filter by status - 'active', 'inactive', 'all'

    Returns:
        List of plugin dictionaries
    """
    client = get_wp_client()

    kwargs = {}
    if status and status != 'all':
        kwargs['status'] = status

    return client.list_plugins(**kwargs)


def activate_plugin(plugin: str) -> Dict[str, Any]:
    """
    Activate a WordPress plugin.

    Args:
        plugin: Plugin slug or path (e.g., 'akismet' or 'akismet/akismet.php')

    Returns:
        Dictionary with success status
    """
    client = get_wp_client()
    client.activate_plugin(plugin)

    return {
        "success": True,
        "plugin": plugin,
        "message": f"Activated plugin '{plugin}'"
    }


def deactivate_plugin(plugin: str) -> Dict[str, Any]:
    """
    Deactivate a WordPress plugin.

    Args:
        plugin: Plugin slug or path

    Returns:
        Dictionary with success status
    """
    client = get_wp_client()
    client.deactivate_plugin(plugin)

    return {
        "success": True,
        "plugin": plugin,
        "message": f"Deactivated plugin '{plugin}'"
    }


def list_themes(status: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List installed WordPress themes.

    Args:
        status: Filter by status - 'active', 'inactive', 'all'

    Returns:
        List of theme dictionaries
    """
    client = get_wp_client()

    kwargs = {}
    if status and status != 'all':
        kwargs['status'] = status

    return client.list_themes(**kwargs)


def activate_theme(theme: str) -> Dict[str, Any]:
    """
    Activate a WordPress theme.

    Args:
        theme: Theme slug (e.g., 'twentytwentyfour')

    Returns:
        Dictionary with success status
    """
    client = get_wp_client()
    client.activate_theme(theme)

    return {
        "success": True,
        "theme": theme,
        "message": f"Activated theme '{theme}'"
    }


# =============================================================================
# Media Management Tools
# =============================================================================

def import_media(
    file_path: str,
    post_id: Optional[int] = None,
    title: Optional[str] = None,
    alt: Optional[str] = None,
    caption: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Import a media file to WordPress.

    Args:
        file_path: Path to the media file or URL
        post_id: Post ID to attach the media to (optional)
        title: Media title (optional)
        alt: Alt text for images (optional)
        caption: Media caption (optional)

    Returns:
        Dictionary with attachment_id and success status
    """
    client = get_wp_client()

    kwargs = {}
    if title:
        kwargs['title'] = title
    if alt:
        kwargs['alt'] = alt
    if caption:
        kwargs['caption'] = caption

    attachment_id = client.import_media(file_path, post_id=post_id, **kwargs)

    return {
        "attachment_id": attachment_id,
        "success": True,
        "message": f"Imported media with ID {attachment_id}"
    }


# =============================================================================
# Cache/Database Tools
# =============================================================================

def flush_cache() -> Dict[str, Any]:
    """
    Flush the WordPress object cache.

    Returns:
        Dictionary with success status
    """
    client = get_wp_client()
    client.flush_cache()

    return {
        "success": True,
        "message": "Cache flushed successfully"
    }


def get_core_version() -> Dict[str, Any]:
    """
    Get the WordPress core version.

    Returns:
        Dictionary with version information
    """
    client = get_wp_client()
    version = client.get_core_version()

    return {
        "version": version,
        "message": f"WordPress version: {version}"
    }


def db_query(query: str) -> Dict[str, Any]:
    """
    Execute a database query.

    WARNING: This executes raw SQL. Use with caution.

    Args:
        query: SQL query to execute

    Returns:
        Dictionary with query result
    """
    client = get_wp_client()
    result = client.db_query(query)

    return {
        "success": True,
        "result": result,
        "message": "Query executed"
    }


def search_replace(
    search: str,
    replace: str,
    dry_run: bool = True,
) -> Dict[str, Any]:
    """
    Search and replace in the WordPress database.

    Args:
        search: Text to search for
        replace: Replacement text
        dry_run: If True, only show what would be changed (default: True for safety)

    Returns:
        Dictionary with operation result
    """
    client = get_wp_client()
    result = client.search_replace(search, replace, dry_run=dry_run)

    return {
        "success": True,
        "dry_run": dry_run,
        "result": result,
        "message": f"Search-replace {'preview' if dry_run else 'completed'}: '{search}' -> '{replace}'"
    }


# =============================================================================
# Generic WP-CLI Tool
# =============================================================================

def wp_cli(command: str, args: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Execute any WP-CLI command directly.

    This is a powerful tool that gives access to ALL WP-CLI commands.

    Args:
        command: The WP-CLI command (e.g., 'cache', 'plugin', 'db')
        args: List of arguments for the command

    Returns:
        Dictionary with command output

    Examples:
        wp_cli("cache", ["flush"])
        wp_cli("plugin", ["list", "--status=active"])
        wp_cli("db", ["export", "backup.sql"])
    """
    client = get_wp_client()

    if args is None:
        args = []

    result = client.wp(command, *args)

    return {
        "success": True,
        "output": result,
        "command": f"wp {command} {' '.join(args)}"
    }
