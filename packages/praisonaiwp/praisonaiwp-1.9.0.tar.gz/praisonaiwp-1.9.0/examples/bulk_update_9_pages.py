#!/usr/bin/env python3
"""
Example: Bulk update 9 pages

This example demonstrates the real-world use case of updating
9 pages with different headings at line 10.
"""

from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.editors.content_editor import ContentEditor

# Configuration: 9 pages
UPDATES = [
    {"post_id": 116, "line": 10, "find": "Old Website Title", "replace": "New Title for Page 1"},
    {"post_id": 117, "line": 10, "find": "Old Website Title", "replace": "New Title for Page 2"},
    {"post_id": 118, "line": 10, "find": "Old Website Title", "replace": "New Title for Page 3"},
    {"post_id": 119, "line": 10, "find": "Old Website Title", "replace": "New Title for Page 4"},
    {"post_id": 120, "line": 10, "find": "Old Website Title", "replace": "New Title for Page 5"},
    {"post_id": 121, "line": 10, "find": "Old Website Title", "replace": "New Title for Page 6"},
    {"post_id": 122, "line": 10, "find": "Old Website Title", "replace": "New Title for Page 7"},
    {"post_id": 139, "line": 10, "find": "Old Website Title", "replace": "New Title for Page 8"},
    {"post_id": 140, "line": 10, "find": "Old Website Title", "replace": "New Title for Page 9"},
]


def main():
    # Load configuration
    config = Config()
    server_config = config.get_server()

    print(f"Connecting to {server_config['hostname']}...")
    print(f"Updating {len(UPDATES)} pages...\n")

    with SSHManager(
        hostname=server_config['hostname'],
        username=server_config['username'],
        key_file=server_config['key_file'],
        port=server_config.get('port', 22)
    ) as ssh:

        wp = WPClient(
            ssh=ssh,
            wp_path=server_config['wp_path'],
            php_bin=server_config.get('php_bin', 'php'),
            wp_cli=server_config.get('wp_cli', '/usr/local/bin/wp')
        )

        editor = ContentEditor()

        # Process each update
        for i, update in enumerate(UPDATES, 1):
            post_id = update['post_id']
            line = update['line']
            find_text = update['find']
            replace_text = update['replace']

            print(f"[{i}/{len(UPDATES)}] Updating post {post_id}...")

            try:
                # Get current content
                current_content = wp.get_post(post_id, field='post_content')

                # Replace at specific line
                new_content = editor.replace_at_line(
                    current_content,
                    line,
                    find_text,
                    replace_text
                )

                # Update post
                wp.update_post(post_id, post_content=new_content)

                print(f"  ✓ Updated: {replace_text}")

            except Exception as e:
                print(f"  ✗ Failed: {e}")

        print("\n✓ Bulk update complete!")
        print(f"Updated {len(UPDATES)} pages successfully")


if __name__ == "__main__":
    main()
