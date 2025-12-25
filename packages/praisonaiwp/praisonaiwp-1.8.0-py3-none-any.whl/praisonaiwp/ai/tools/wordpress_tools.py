"""WordPress tools for PraisonAI agents"""
from typing import Any, Dict, List, Optional


class WordPressTools:
    """WordPress tools that can be used by PraisonAI agents"""

    def __init__(self, wp_client):
        """Initialize WordPress tools with a WP client

        Args:
            wp_client: WordPress client instance (WPClient)
        """
        self.wp_client = wp_client

    def create_post(
        self,
        title: str,
        content: str,
        status: str = "draft"
    ) -> Dict[str, Any]:
        """Create a WordPress post

        Args:
            title: Post title
            content: Post content
            status: Post status (draft, publish, private)

        Returns:
            dict: Post ID, status, and message
        """
        post_id = self.wp_client.create_post(
            post_title=title,
            post_content=content,
            post_status=status
        )

        return {
            "post_id": post_id,
            "status": status,
            "message": f"Post created successfully with ID: {post_id}"
        }

    def update_post(
        self,
        post_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update an existing WordPress post

        Args:
            post_id: ID of the post to update
            title: New title (optional)
            content: New content (optional)

        Returns:
            dict: Update status and post ID
        """
        update_args = {"post_id": post_id}

        if title is not None:
            update_args["post_title"] = title

        if content is not None:
            update_args["post_content"] = content

        success = self.wp_client.update_post(**update_args)

        return {
            "post_id": post_id,
            "updated": success,
            "message": f"Post {post_id} updated successfully" if success else "Update failed"
        }

    def list_posts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List WordPress posts

        Args:
            limit: Maximum number of posts to return

        Returns:
            list: List of posts with ID, title, and content
        """
        posts = self.wp_client.list_posts()
        return posts[:limit] if posts else []

    def get_tool_functions(self) -> List:
        """Get list of tool functions for PraisonAI agents

        Returns:
            list: List of callable tool functions
        """
        return [
            self.create_post,
            self.update_post,
            self.list_posts
        ]
