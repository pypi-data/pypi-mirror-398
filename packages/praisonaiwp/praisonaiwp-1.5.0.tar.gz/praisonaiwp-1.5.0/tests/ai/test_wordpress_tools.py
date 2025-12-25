"""Tests for WordPress tools integration with PraisonAI"""
from unittest.mock import Mock

import pytest

from praisonaiwp.ai.tools.wordpress_tools import WordPressTools


class TestWordPressTools:
    """Test WordPress tools for PraisonAI agents"""

    @pytest.fixture
    def mock_wp_client(self):
        """Create a mock WordPress client"""
        client = Mock()
        client.create_post = Mock(return_value=123)
        client.update_post = Mock(return_value=True)
        client.list_posts = Mock(return_value=[
            {'ID': 1, 'post_title': 'Test Post', 'post_content': 'Content'}
        ])
        return client

    @pytest.fixture
    def wp_tools(self, mock_wp_client):
        """Create WordPressTools instance"""
        return WordPressTools(mock_wp_client)

    def test_init(self, mock_wp_client):
        """Test WordPressTools initialization"""
        tools = WordPressTools(mock_wp_client)
        assert tools.wp_client == mock_wp_client

    def test_create_post(self, wp_tools, mock_wp_client):
        """Test create_post method"""
        result = wp_tools.create_post(
            title="Test Post",
            content="Test content",
            status="draft"
        )

        # Verify WP client was called correctly
        mock_wp_client.create_post.assert_called_once_with(
            post_title="Test Post",
            post_content="Test content",
            post_status="draft"
        )

        # Verify return value
        assert result['post_id'] == 123
        assert result['status'] == 'draft'
        assert 'message' in result

    def test_create_post_default_status(self, wp_tools, mock_wp_client):
        """Test create_post with default status"""
        wp_tools.create_post(
            title="Test",
            content="Content"
        )

        # Should default to 'draft'
        mock_wp_client.create_post.assert_called_once()
        call_args = mock_wp_client.create_post.call_args[1]
        assert call_args['post_status'] == 'draft'

    def test_update_post(self, wp_tools, mock_wp_client):
        """Test update_post method"""
        result = wp_tools.update_post(
            post_id=123,
            title="Updated Title",
            content="Updated content"
        )

        # Verify WP client was called
        mock_wp_client.update_post.assert_called_once_with(
            post_id=123,
            post_title="Updated Title",
            post_content="Updated content"
        )

        # Verify return value
        assert result['post_id'] == 123
        assert result['updated'] is True

    def test_update_post_partial(self, wp_tools, mock_wp_client):
        """Test updating only title or content"""
        # Update only title
        wp_tools.update_post(post_id=123, title="New Title")

        call_args = mock_wp_client.update_post.call_args[1]
        assert call_args['post_title'] == "New Title"
        assert 'post_content' not in call_args

    def test_list_posts(self, wp_tools, mock_wp_client):
        """Test list_posts method"""
        result = wp_tools.list_posts(limit=10)

        # Verify WP client was called
        mock_wp_client.list_posts.assert_called_once()

        # Verify return value
        assert len(result) == 1
        assert result[0]['ID'] == 1

    def test_get_tool_functions(self, wp_tools):
        """Test getting tool functions for agent"""
        tools = wp_tools.get_tool_functions()

        # Should return list of callable functions
        assert isinstance(tools, list)
        assert len(tools) >= 2
        assert callable(tools[0])
        assert callable(tools[1])

    def test_create_post_error_handling(self, wp_tools, mock_wp_client):
        """Test error handling in create_post"""
        mock_wp_client.create_post.side_effect = Exception("Connection error")

        with pytest.raises(Exception) as exc_info:
            wp_tools.create_post("Title", "Content")

        assert "Connection error" in str(exc_info.value)
