#!/usr/bin/env python3
"""
Example: Create a single WordPress post

This example demonstrates how to use PraisonAIWP programmatically
to create a single post.
"""

from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient


def main():
    # Load configuration
    config = Config()
    server_config = config.get_server()  # Uses default server

    print(f"Connecting to {server_config['hostname']}...")

    # Connect to server
    with SSHManager(
        hostname=server_config['hostname'],
        username=server_config['username'],
        key_file=server_config['key_file'],
        port=server_config.get('port', 22)
    ) as ssh:

        # Create WP client
        wp = WPClient(
            ssh=ssh,
            wp_path=server_config['wp_path'],
            php_bin=server_config.get('php_bin', 'php'),
            wp_cli=server_config.get('wp_cli', '/usr/local/bin/wp')
        )

        # Create post
        print("Creating post...")
        post_id = wp.create_post(
            post_title="My First Post via PraisonAIWP",
            post_content="<p>This post was created programmatically using PraisonAIWP!</p>",
            post_status="publish",
            post_type="post"
        )

        print("✓ Post created successfully!")
        print(f"Post ID: {post_id}")

        # Get the created post
        post_data = wp.get_post(post_id)
        print(f"Title: {post_data['post_title']}")
        print(f"Status: {post_data['post_status']}")


if __name__ == "__main__":
    main()
