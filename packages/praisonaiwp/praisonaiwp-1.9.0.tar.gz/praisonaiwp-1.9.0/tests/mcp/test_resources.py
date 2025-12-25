"""
Tests for MCP Resources - Read-only data sources for WordPress

TDD: These tests define the expected behavior of MCP resources.
"""

from unittest.mock import Mock, patch


class TestMCPResources:
    """Test MCP resources for WordPress data"""

    def test_get_wordpress_info_exists(self):
        """Test that get_wordpress_info resource is defined"""
        from praisonaiwp.mcp.resources import get_wordpress_info
        assert callable(get_wordpress_info)

    def test_get_wordpress_info_returns_dict(self):
        """Test get_wordpress_info returns WordPress info"""
        from praisonaiwp.mcp.resources import get_wordpress_info

        with patch('praisonaiwp.mcp.resources.get_wp_client') as mock_get_client:
            mock_client = Mock()
            mock_client.get_core_version.return_value = "6.4.2"
            mock_client.get_option.return_value = "https://example.com"
            mock_get_client.return_value = mock_client

            result = get_wordpress_info()

            assert isinstance(result, dict)
            assert "version" in result

    def test_get_post_resource_exists(self):
        """Test that get_post_resource is defined"""
        from praisonaiwp.mcp.resources import get_post_resource
        assert callable(get_post_resource)

    def test_get_post_resource_returns_content(self):
        """Test get_post_resource returns post content"""
        from praisonaiwp.mcp.resources import get_post_resource

        with patch('praisonaiwp.mcp.resources.get_wp_client') as mock_get_client:
            mock_client = Mock()
            mock_client.get_post.return_value = {
                "ID": 123,
                "post_title": "Test Post",
                "post_content": "<p>Content</p>"
            }
            mock_get_client.return_value = mock_client

            result = get_post_resource(post_id=123)

            assert isinstance(result, str) or isinstance(result, dict)

    def test_get_posts_list_exists(self):
        """Test that get_posts_list resource is defined"""
        from praisonaiwp.mcp.resources import get_posts_list
        assert callable(get_posts_list)

    def test_get_categories_resource_exists(self):
        """Test that get_categories_resource is defined"""
        from praisonaiwp.mcp.resources import get_categories_resource
        assert callable(get_categories_resource)

    def test_get_users_resource_exists(self):
        """Test that get_users_resource is defined"""
        from praisonaiwp.mcp.resources import get_users_resource
        assert callable(get_users_resource)

    def test_get_plugins_resource_exists(self):
        """Test that get_plugins_resource is defined"""
        from praisonaiwp.mcp.resources import get_plugins_resource
        assert callable(get_plugins_resource)

    def test_get_themes_resource_exists(self):
        """Test that get_themes_resource is defined"""
        from praisonaiwp.mcp.resources import get_themes_resource
        assert callable(get_themes_resource)

    def test_get_config_resource_exists(self):
        """Test that get_config_resource is defined"""
        from praisonaiwp.mcp.resources import get_config_resource
        assert callable(get_config_resource)
