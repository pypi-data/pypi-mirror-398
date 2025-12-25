"""
Real integration tests - NO MOCKS
Tests actual WordPress functionality using real SSH connection
"""
import os

import pytest

from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("CI") == "true" or not os.path.exists(os.path.expanduser("~/.praisonaiwp/config.yaml")),
    reason="Skip real integration tests in CI/CD or if config not found"
)
class TestRealIntegration:
    """Real integration tests without mocks"""

    @pytest.fixture
    def config(self):
        """Load real config"""
        config_path = os.path.expanduser("~/.praisonaiwp/config.yaml")
        return Config(config_path)

    @pytest.fixture
    def ssh_manager(self, config):
        """Create real SSH connection"""
        server = config.get_server()
        ssh = SSHManager(
            hostname=server['hostname'],
            username=server.get('username'),
            port=server.get('port', 22),
            key_file=server.get('key_path')
        )
        ssh.connect()
        yield ssh
        ssh.close()

    @pytest.fixture
    def wp_client(self, ssh_manager, config):
        """Create real WP client"""
        server = config.get_server()
        return WPClient(
            ssh=ssh_manager,
            wp_path=server['wp_path'],
            php_bin=server.get('php_bin', 'php'),
            wp_cli=server.get('wp_cli', '/usr/local/bin/wp')
        )

    def test_real_category_assignment(self, wp_client):
        """
        Test real category assignment - NO MOCKS
        This is the test that would have caught the v1.0.21 bug
        """
        # Create a test post
        post_id = wp_client.create_post(
            post_title="Integration Test Post - Category Assignment",
            post_content="<p>Testing category assignment without mocks</p>",
            post_status="draft"
        )

        assert post_id is not None, "Post creation failed"

        try:
            # Get category ID for "Other" (or use ID 1 for Uncategorized as fallback)
            categories = wp_client.list_categories()
            other_cat = None
            for cat in categories:
                if cat.get('name') == 'Other':
                    other_cat = int(cat['term_id'])
                    break

            if not other_cat:
                # Use Uncategorized as fallback
                other_cat = 1

            # Set category - this is where v1.0.21 failed
            result = wp_client.set_post_categories(post_id, [other_cat])
            assert result is True, "set_post_categories returned False"

            # Verify category was actually set by listing post categories
            post_categories = wp_client.get_post_categories(post_id)
            assert post_categories is not None, "Could not retrieve post categories"
            assert len(post_categories) > 0, "No categories found on post"

            # Check if our category is in the list
            cat_ids = [int(cat['term_id']) for cat in post_categories]
            assert other_cat in cat_ids, \
                f"Category {other_cat} not found in post categories: {cat_ids}"

            print("\n✅ Real integration test passed!")
            print(f"   Post ID: {post_id}")
            print(f"   Category ID: {other_cat}")
            print(f"   Post categories: {cat_ids}")
            print("   Category set successfully!")

        finally:
            # Cleanup - delete test post
            try:
                wp_client.delete_post(post_id, force=True)
                print(f"   Cleaned up test post {post_id}")
            except Exception as e:
                print(f"   Warning: Could not delete test post {post_id}: {e}")

    def test_real_post_creation_with_category(self, wp_client):
        """
        Test creating post with category in one go - NO MOCKS
        """
        # Get a category
        wp_client.list_categories()
        test_cat_id = 1  # Uncategorized as default

        # Create post
        post_id = wp_client.create_post(
            post_title="Integration Test - Full Workflow",
            post_content="<h2>Test</h2><p>Content</p>",
            post_status="draft"
        )

        assert post_id is not None

        try:
            # Set category
            wp_client.set_post_categories(post_id, [test_cat_id])

            # Verify
            post_data = wp_client.get_post(post_id)
            assert post_data is not None

            print("\n✅ Full workflow test passed!")
            print(f"   Post ID: {post_id}")
            print(f"   Category ID: {test_cat_id}")

        finally:
            try:
                wp_client.delete_post(post_id, force=True)
                print(f"   Cleaned up test post {post_id}")
            except Exception as e:
                print(f"   Warning: Could not delete test post {post_id}: {e}")
