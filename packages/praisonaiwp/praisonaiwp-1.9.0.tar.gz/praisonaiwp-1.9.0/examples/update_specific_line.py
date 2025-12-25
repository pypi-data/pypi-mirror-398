#!/usr/bin/env python3
"""
Example: Update specific line in a post

This example demonstrates how to replace text at a specific line number,
leaving other occurrences unchanged.
"""

from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.editors.content_editor import ContentEditor


def main():
    # Configuration
    POST_ID = 123  # Change this to your post ID
    LINE_NUMBER = 10  # Line to update
    FIND_TEXT = "Welcome to Our Site"
    REPLACE_TEXT = "My Website Title"

    # Load configuration
    config = Config()
    server_config = config.get_server()

    print(f"Connecting to {server_config['hostname']}...")

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

        # Get current content
        print(f"Fetching post {POST_ID}...")
        current_content = wp.get_post(POST_ID, field='post_content')

        # Show occurrences
        editor = ContentEditor()
        occurrences = editor.find_occurrences(current_content, FIND_TEXT)

        print(f"\nFound {len(occurrences)} occurrence(s) of '{FIND_TEXT}':")
        for line_num, line_content in occurrences:
            print(f"  Line {line_num}: {line_content[:60]}...")

        # Replace at specific line
        print(f"\nReplacing at line {LINE_NUMBER} only...")
        new_content = editor.replace_at_line(
            current_content,
            LINE_NUMBER,
            FIND_TEXT,
            REPLACE_TEXT
        )

        # Preview changes
        preview = editor.preview_changes(
            current_content,
            FIND_TEXT,
            REPLACE_TEXT,
            lambda c, o, n: new_content
        )

        print(f"\nChanges to be made: {preview['total_changes']}")
        for change in preview['changes']:
            print(f"\nLine {change['line']}:")
            print(f"  - {change['old']}")
            print(f"  + {change['new']}")

        # Confirm
        confirm = input("\nApply changes? (y/n): ")
        if confirm.lower() != 'y':
            print("Cancelled")
            return

        # Update post
        print("Updating post...")
        wp.update_post(POST_ID, post_content=new_content)

        print(f"✓ Post {POST_ID} updated successfully!")

        # Verify
        updated_content = wp.get_post(POST_ID, field='post_content')
        new_occurrences = editor.find_occurrences(updated_content, REPLACE_TEXT)
        print(f"\nVerification: Found {len(new_occurrences)} occurrence(s) of '{REPLACE_TEXT}'")


if __name__ == "__main__":
    main()
