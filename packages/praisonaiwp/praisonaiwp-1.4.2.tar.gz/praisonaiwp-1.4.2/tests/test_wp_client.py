"""Tests for WPClient (with mocking)"""

import pytest
from unittest.mock import Mock, MagicMock
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.utils.exceptions import WPCLIError


class TestWPClient:
    """Test WPClient functionality"""
    
    @pytest.fixture
    def mock_ssh(self):
        """Create mock SSH manager"""
        ssh = Mock()
        ssh.execute = Mock(return_value=("output", ""))
        return ssh
    
    @pytest.fixture
    def wp_client(self, mock_ssh):
        """Create WP client with mock SSH"""
        return WPClient(
            ssh=mock_ssh,
            wp_path="/var/www/html",
            php_bin="php",
            wp_cli="/usr/local/bin/wp"
        )
    
    def test_execute_wp_success(self, wp_client, mock_ssh):
        """Test successful WP-CLI execution"""
        mock_ssh.execute.return_value = ("Success", "")
        
        result = wp_client._execute_wp("post list")
        
        assert result == "Success"
        # Note: execute is called multiple times due to _verify_installation()
        # We just verify the last call was our command
        assert mock_ssh.execute.call_count >= 1
        last_call = mock_ssh.execute.call_args[0][0]
        assert "post list" in last_call
    
    def test_execute_wp_error(self, wp_client, mock_ssh):
        """Test WP-CLI execution with error"""
        mock_ssh.execute.return_value = ("", "Error: Something went wrong")
        
        with pytest.raises(WPCLIError):
            wp_client._execute_wp("post list")
    
    def test_get_post_with_field(self, wp_client, mock_ssh):
        """Test getting specific post field"""
        mock_ssh.execute.return_value = ("Post content here", "")
        
        content = wp_client.get_post(123, field='post_content')
        
        assert content == "Post content here"
        assert "post get 123 --field=post_content" in mock_ssh.execute.call_args[0][0]
    
    def test_get_post_json(self, wp_client, mock_ssh):
        """Test getting post as JSON"""
        import json
        post_data = {"ID": 123, "post_title": "Test"}
        mock_ssh.execute.return_value = (json.dumps(post_data), "")
        
        result = wp_client.get_post(123)
        
        assert result == post_data
        assert "--format=json" in mock_ssh.execute.call_args[0][0]
    
    def test_create_post(self, wp_client, mock_ssh):
        """Test creating post"""
        mock_ssh.execute.return_value = ("456", "")
        
        post_id = wp_client.create_post(
            post_title="Test Post",
            post_content="Content",
            post_status="publish"
        )
        
        assert post_id == 456
        call_args = mock_ssh.execute.call_args[0][0]
        assert "post create" in call_args
        assert "--porcelain" in call_args
    
    def test_update_post(self, wp_client, mock_ssh):
        """Test updating post"""
        mock_ssh.execute.return_value = ("Success", "")
        
        result = wp_client.update_post(
            123,
            post_title="Updated Title"
        )
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "post update 123" in call_args
    
    def test_list_posts(self, wp_client, mock_ssh):
        """Test listing posts"""
        import json
        posts = [{"ID": 1, "post_title": "Post 1"}]
        mock_ssh.execute.return_value = (json.dumps(posts), "")
        
        result = wp_client.list_posts(post_type='page')
        
        assert result == posts
        call_args = mock_ssh.execute.call_args[0][0]
        assert "post list" in call_args
        assert "--post_type=page" in call_args
    
    def test_db_query(self, wp_client, mock_ssh):
        """Test database query"""
        mock_ssh.execute.return_value = ("Query result", "")
        
        result = wp_client.db_query("SELECT * FROM wp_posts")
        
        assert result == "Query result"
        call_args = mock_ssh.execute.call_args[0][0]
        assert "db query" in call_args
    
    def test_delete_post(self, wp_client, mock_ssh):
        """Test delete post"""
        mock_ssh.execute.return_value = ("Success: Trashed post 123.", "")
        
        result = wp_client.delete_post(123)
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "post delete 123" in call_args
    
    def test_delete_post_force(self, wp_client, mock_ssh):
        """Test force delete post"""
        mock_ssh.execute.return_value = ("Success: Deleted post 123.", "")
        
        result = wp_client.delete_post(123, force=True)
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "post delete 123 --force" in call_args
    
    def test_post_exists_true(self, wp_client, mock_ssh):
        """Test post exists returns True"""
        mock_ssh.execute.return_value = ("", "")
        
        result = wp_client.post_exists(123)
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "post exists 123" in call_args
    
    def test_post_exists_false(self, wp_client, mock_ssh):
        """Test post exists returns False"""
        from praisonaiwp.utils.exceptions import WPCLIError
        mock_ssh.execute.side_effect = WPCLIError("Post does not exist")
        
        result = wp_client.post_exists(999)
        
        assert result is False
    
    def test_get_post_meta(self, wp_client, mock_ssh):
        """Test get post meta"""
        mock_ssh.execute.return_value = ("meta_value", "")
        
        result = wp_client.get_post_meta(123, "custom_key")
        
        assert result == "meta_value"
        call_args = mock_ssh.execute.call_args[0][0]
        assert "post meta get 123 custom_key" in call_args
    
    def test_get_post_meta_all(self, wp_client, mock_ssh):
        """Test get all post meta"""
        mock_ssh.execute.return_value = ('[{"meta_key": "key1", "meta_value": "value1"}]', "")
        
        result = wp_client.get_post_meta(123)
        
        assert isinstance(result, list)
        call_args = mock_ssh.execute.call_args[0][0]
        assert "post meta list 123" in call_args
    
    def test_set_post_meta(self, wp_client, mock_ssh):
        """Test set post meta"""
        mock_ssh.execute.return_value = ("Success: Updated custom field", "")
        
        result = wp_client.set_post_meta(123, "custom_key", "custom_value")
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "post meta set 123 custom_key" in call_args
    
    def test_update_post_meta(self, wp_client, mock_ssh):
        """Test update post meta"""
        mock_ssh.execute.return_value = ("Success: Updated custom field", "")
        
        result = wp_client.update_post_meta(123, "custom_key", "new_value")
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "post meta update 123 custom_key" in call_args
    
    def test_delete_post_meta(self, wp_client, mock_ssh):
        """Test delete post meta"""
        mock_ssh.execute.return_value = ("Success: Deleted custom field", "")
        
        result = wp_client.delete_post_meta(123, "custom_key")
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "post meta delete 123 custom_key" in call_args
    
    def test_list_users(self, wp_client, mock_ssh):
        """Test list users"""
        mock_ssh.execute.return_value = ('[{"ID": 1, "user_login": "admin"}]', "")
        
        result = wp_client.list_users()
        
        assert isinstance(result, list)
        assert len(result) == 1
        call_args = mock_ssh.execute.call_args[0][0]
        assert "user list" in call_args
    
    def test_get_user(self, wp_client, mock_ssh):
        """Test get user"""
        mock_ssh.execute.return_value = ('{"ID": 1, "user_login": "admin"}', "")
        
        result = wp_client.get_user(1)
        
        assert isinstance(result, dict)
        assert result["ID"] == 1
        call_args = mock_ssh.execute.call_args[0][0]
        assert "user get 1" in call_args
    
    def test_create_user(self, wp_client, mock_ssh):
        """Test create user"""
        mock_ssh.execute.return_value = ("123", "")
        
        result = wp_client.create_user("testuser", "test@example.com", role="editor")
        
        assert result == 123
        call_args = mock_ssh.execute.call_args[0][0]
        assert "user create testuser test@example.com" in call_args
        assert "--role='editor'" in call_args
    
    def test_update_user(self, wp_client, mock_ssh):
        """Test update user"""
        mock_ssh.execute.return_value = ("Success: Updated user", "")
        
        result = wp_client.update_user(123, display_name="Test User")
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "user update 123" in call_args
        assert "--display_name='Test User'" in call_args
    
    def test_delete_user(self, wp_client, mock_ssh):
        """Test delete user"""
        mock_ssh.execute.return_value = ("Success: Deleted user", "")
        
        result = wp_client.delete_user(123, reassign=1)
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "user delete 123" in call_args
        assert "--reassign=1" in call_args
    
    def test_get_option(self, wp_client, mock_ssh):
        """Test get option"""
        mock_ssh.execute.return_value = ("option_value", "")
        
        result = wp_client.get_option("blogname")
        
        assert result == "option_value"
        call_args = mock_ssh.execute.call_args[0][0]
        assert "option get blogname" in call_args
    
    def test_set_option(self, wp_client, mock_ssh):
        """Test set option"""
        mock_ssh.execute.return_value = ("Success: Updated option", "")
        
        result = wp_client.set_option("blogname", "My Blog")
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "option set blogname" in call_args
    
    def test_delete_option(self, wp_client, mock_ssh):
        """Test delete option"""
        mock_ssh.execute.return_value = ("Success: Deleted option", "")
        
        result = wp_client.delete_option("custom_option")
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "option delete custom_option" in call_args
    
    def test_list_plugins(self, wp_client, mock_ssh):
        """Test list plugins"""
        mock_ssh.execute.return_value = ('[{"name": "akismet", "status": "active"}]', "")
        
        result = wp_client.list_plugins(status="active")
        
        assert isinstance(result, list)
        assert len(result) == 1
        call_args = mock_ssh.execute.call_args[0][0]
        assert "plugin list" in call_args
        assert "--status=active" in call_args
    
    def test_list_themes(self, wp_client, mock_ssh):
        """Test list themes"""
        mock_ssh.execute.return_value = ('[{"name": "twentytwentyfour", "status": "active"}]', "")
        
        result = wp_client.list_themes()
        
        assert isinstance(result, list)
        assert len(result) == 1
        call_args = mock_ssh.execute.call_args[0][0]
        assert "theme list" in call_args
    
    def test_import_media(self, wp_client, mock_ssh):
        """Test import media"""
        mock_ssh.execute.return_value = ("456", "")
        
        result = wp_client.import_media("/path/to/image.jpg", post_id=123, title="Test Image")
        
        assert result == 456
        call_args = mock_ssh.execute.call_args[0][0]
        assert "media import" in call_args
        assert "/path/to/image.jpg" in call_args
        assert "--post_id=123" in call_args
    
    def test_list_comments(self, wp_client, mock_ssh):
        """Test list comments"""
        mock_ssh.execute.return_value = ('[{"comment_ID": "1", "comment_content": "Test"}]', "")
        
        result = wp_client.list_comments(status="approve")
        
        assert isinstance(result, list)
        assert len(result) == 1
        call_args = mock_ssh.execute.call_args[0][0]
        assert "comment list" in call_args
    
    def test_get_comment(self, wp_client, mock_ssh):
        """Test get comment"""
        mock_ssh.execute.return_value = ('{"comment_ID": "1"}', "")
        
        result = wp_client.get_comment(1)
        
        assert isinstance(result, dict)
        call_args = mock_ssh.execute.call_args[0][0]
        assert "comment get 1" in call_args
    
    def test_create_comment(self, wp_client, mock_ssh):
        """Test create comment"""
        mock_ssh.execute.return_value = ("789", "")
        
        result = wp_client.create_comment(123, comment_content="Great post!")
        
        assert result == 789
        call_args = mock_ssh.execute.call_args[0][0]
        assert "comment create 123" in call_args
    
    def test_update_comment(self, wp_client, mock_ssh):
        """Test update comment"""
        mock_ssh.execute.return_value = ("Success: Updated comment", "")
        
        result = wp_client.update_comment(1, comment_content="Updated")
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "comment update 1" in call_args
    
    def test_delete_comment(self, wp_client, mock_ssh):
        """Test delete comment"""
        mock_ssh.execute.return_value = ("Success: Deleted comment", "")
        
        result = wp_client.delete_comment(1, force=True)
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "comment delete 1" in call_args
        assert "--force" in call_args
    
    def test_approve_comment(self, wp_client, mock_ssh):
        """Test approve comment"""
        mock_ssh.execute.return_value = ("Success: Approved comment", "")
        
        result = wp_client.approve_comment(1)
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "comment approve 1" in call_args
    
    def test_activate_plugin(self, wp_client, mock_ssh):
        """Test activate plugin"""
        mock_ssh.execute.return_value = ("Success: Activated plugin", "")
        
        result = wp_client.activate_plugin("akismet")
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "plugin activate akismet" in call_args
    
    def test_deactivate_plugin(self, wp_client, mock_ssh):
        """Test deactivate plugin"""
        mock_ssh.execute.return_value = ("Success: Deactivated plugin", "")
        
        result = wp_client.deactivate_plugin("akismet")
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "plugin deactivate akismet" in call_args
    
    def test_update_plugin_single(self, wp_client, mock_ssh):
        """Test update single plugin"""
        mock_ssh.execute.return_value = ("Success: Updated 1 plugin", "")
        
        result = wp_client.update_plugin("akismet")
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "plugin update akismet" in call_args
        assert "--all" not in call_args
    
    def test_update_plugin_all(self, wp_client, mock_ssh):
        """Test update all plugins"""
        mock_ssh.execute.return_value = ("Success: Updated 5 plugins", "")
        
        result = wp_client.update_plugin("all")
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "plugin update --all" in call_args
    
    def test_update_plugin_default(self, wp_client, mock_ssh):
        """Test update plugin with default parameter"""
        mock_ssh.execute.return_value = ("Success: Updated 5 plugins", "")
        
        result = wp_client.update_plugin()
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "plugin update --all" in call_args
    
    def test_activate_theme(self, wp_client, mock_ssh):
        """Test activate theme"""
        mock_ssh.execute.return_value = ("Success: Activated theme", "")
        
        result = wp_client.activate_theme("twentytwentyfour")
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "theme activate twentytwentyfour" in call_args
    
    def test_get_user_meta(self, wp_client, mock_ssh):
        """Test get user meta"""
        mock_ssh.execute.return_value = ("meta_value", "")
        
        result = wp_client.get_user_meta(1, "nickname")
        
        assert result == "meta_value"
        call_args = mock_ssh.execute.call_args[0][0]
        assert "user meta get 1 nickname" in call_args
    
    def test_set_user_meta(self, wp_client, mock_ssh):
        """Test set user meta"""
        mock_ssh.execute.return_value = ("Success: Added meta", "")
        
        result = wp_client.set_user_meta(1, "custom_key", "value")
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "user meta add 1 custom_key" in call_args
    
    def test_update_user_meta(self, wp_client, mock_ssh):
        """Test update user meta"""
        mock_ssh.execute.return_value = ("Success: Updated meta", "")
        
        result = wp_client.update_user_meta(1, "custom_key", "new_value")
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "user meta update 1 custom_key" in call_args
    
    def test_delete_user_meta(self, wp_client, mock_ssh):
        """Test delete user meta"""
        mock_ssh.execute.return_value = ("Success: Deleted meta", "")
        
        result = wp_client.delete_user_meta(1, "custom_key")
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "user meta delete 1 custom_key" in call_args
    
    def test_flush_cache(self, wp_client, mock_ssh):
        """Test flush cache"""
        mock_ssh.execute.return_value = ("Success: Flushed cache", "")
        
        result = wp_client.flush_cache()
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "cache flush" in call_args
    
    def test_get_cache_type(self, wp_client, mock_ssh):
        """Test get cache type"""
        mock_ssh.execute.return_value = ("Default", "")
        
        result = wp_client.get_cache_type()
        
        assert result == "Default"
        call_args = mock_ssh.execute.call_args[0][0]
        assert "cache type" in call_args
    
    def test_get_transient(self, wp_client, mock_ssh):
        """Test get transient"""
        mock_ssh.execute.return_value = ("transient_value", "")
        
        result = wp_client.get_transient("test_key")
        
        assert result == "transient_value"
        call_args = mock_ssh.execute.call_args[0][0]
        assert "transient get test_key" in call_args
    
    def test_set_transient(self, wp_client, mock_ssh):
        """Test set transient"""
        mock_ssh.execute.return_value = ("Success: Set transient", "")
        
        result = wp_client.set_transient("test_key", "value", 3600)
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "transient set test_key" in call_args
        assert "3600" in call_args
    
    def test_delete_transient(self, wp_client, mock_ssh):
        """Test delete transient"""
        mock_ssh.execute.return_value = ("Success: Deleted transient", "")
        
        result = wp_client.delete_transient("test_key")
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "transient delete test_key" in call_args
    
    def test_list_menus(self, wp_client, mock_ssh):
        """Test list menus"""
        mock_ssh.execute.return_value = ('[{"term_id": 2, "name": "Main Menu"}]', "")
        
        result = wp_client.list_menus()
        
        assert len(result) == 1
        assert result[0]["name"] == "Main Menu"
        call_args = mock_ssh.execute.call_args[0][0]
        assert "menu list --format=json" in call_args
    
    def test_create_menu(self, wp_client, mock_ssh):
        """Test create menu"""
        mock_ssh.execute.return_value = ("5", "")
        
        result = wp_client.create_menu("Footer Menu")
        
        assert result == 5
        call_args = mock_ssh.execute.call_args[0][0]
        assert "menu create" in call_args
        assert "Footer Menu" in call_args
    
    def test_delete_menu(self, wp_client, mock_ssh):
        """Test delete menu"""
        mock_ssh.execute.return_value = ("Success: Deleted menu", "")
        
        result = wp_client.delete_menu(5)
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "menu delete 5" in call_args
    
    def test_add_menu_item(self, wp_client, mock_ssh):
        """Test add menu item"""
        mock_ssh.execute.return_value = ("10", "")
        
        result = wp_client.add_menu_item(5, title="Home", url="https://example.com")
        
        assert result == 10
        call_args = mock_ssh.execute.call_args[0][0]
        assert "menu item add-custom 5" in call_args
        assert "--title=" in call_args
    
    def test_create_term(self, wp_client, mock_ssh):
        """Test create term"""
        mock_ssh.execute.return_value = ("15", "")
        
        result = wp_client.create_term("category", "New Category", slug="new-cat")
        
        assert result == 15
        call_args = mock_ssh.execute.call_args[0][0]
        assert "term create category" in call_args
        assert "New Category" in call_args
    
    def test_delete_term(self, wp_client, mock_ssh):
        """Test delete term"""
        mock_ssh.execute.return_value = ("Success: Deleted term", "")
        
        result = wp_client.delete_term("category", 15)
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "term delete category 15" in call_args
    
    def test_update_term(self, wp_client, mock_ssh):
        """Test update term"""
        mock_ssh.execute.return_value = ("Success: Updated term", "")
        
        result = wp_client.update_term("category", 15, name="Updated Category")
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "term update category 15" in call_args
    
    def test_get_core_version(self, wp_client, mock_ssh):
        """Test get core version"""
        mock_ssh.execute.return_value = ("6.4.2", "")
        
        result = wp_client.get_core_version()
        
        assert result == "6.4.2"
        call_args = mock_ssh.execute.call_args[0][0]
        assert "core version" in call_args
    
    def test_core_is_installed(self, wp_client, mock_ssh):
        """Test core is installed"""
        mock_ssh.execute.return_value = ("", "")
        
        result = wp_client.core_is_installed()
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "core is-installed" in call_args
    
    def test_wp_generic_command(self, wp_client, mock_ssh):
        """Test generic wp() method with simple command"""
        mock_ssh.execute.return_value = ("Success", "")
        
        result = wp_client.wp('cache', 'flush')
        
        assert result == "Success"
        call_args = mock_ssh.execute.call_args[0][0]
        assert "cache flush" in call_args
    
    def test_wp_with_kwargs(self, wp_client, mock_ssh):
        """Test generic wp() method with keyword arguments"""
        mock_ssh.execute.return_value = ('[{"ID": 1}]', "")
        
        result = wp_client.wp('post', 'list', status='publish', format='json')
        
        assert isinstance(result, list)
        assert result[0]["ID"] == 1
        call_args = mock_ssh.execute.call_args[0][0]
        assert "post list" in call_args
        assert "--status='publish'" in call_args
        assert "--format='json'" in call_args
    
    def test_wp_with_boolean_flag(self, wp_client, mock_ssh):
        """Test generic wp() method with boolean flags"""
        mock_ssh.execute.return_value = ("123", "")
        
        result = wp_client.wp('user', 'create', 'john', 'john@example.com', porcelain=True)
        
        assert result == "123"
        call_args = mock_ssh.execute.call_args[0][0]
        assert "user create john john@example.com" in call_args
        assert "--porcelain" in call_args
    
    def test_wp_underscore_to_hyphen(self, wp_client, mock_ssh):
        """Test generic wp() method converts underscores to hyphens"""
        mock_ssh.execute.return_value = ("Result", "")
        
        result = wp_client.wp('search-replace', 'old', 'new', dry_run=True)
        
        assert result == "Result"
        call_args = mock_ssh.execute.call_args[0][0]
        assert "search-replace old new" in call_args
        assert "--dry-run" in call_args
    
    def test_search_replace(self, wp_client, mock_ssh):
        """Test search and replace"""
        mock_ssh.execute.return_value = ("Replaced 5 occurrences", "")
        
        result = wp_client.search_replace("old", "new", dry_run=True)
        
        assert "Replaced" in result
        call_args = mock_ssh.execute.call_args[0][0]
        assert "search-replace" in call_args
        assert "--dry-run" in call_args
    
    def test_create_post_escapes_quotes(self, wp_client, mock_ssh):
        """Test that single quotes are properly escaped"""
        mock_ssh.execute.return_value = ("123", "")
        
        wp_client.create_post(
            post_title="Post with 'quotes'",
            post_content="Content with 'quotes'"
        )
        
        call_args = mock_ssh.execute.call_args[0][0]
        # Should escape single quotes
        assert "'\\''" in call_args or "\\'" in call_args
    
    def test_set_post_categories(self, wp_client, mock_ssh):
        """Test setting post categories"""
        mock_ssh.execute.return_value = ("Success", "")
        
        result = wp_client.set_post_categories(123, [1, 2, 3])
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "post update 123" in call_args
        assert "--post_category=1,2,3" in call_args
    
    def test_add_post_category(self, wp_client, mock_ssh):
        """Test adding a category to post"""
        mock_ssh.execute.return_value = ("Success", "")
        
        result = wp_client.add_post_category(123, 5)
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "post term add 123 category 5" in call_args
    
    def test_remove_post_category(self, wp_client, mock_ssh):
        """Test removing a category from post"""
        mock_ssh.execute.return_value = ("Success", "")
        
        result = wp_client.remove_post_category(123, 1)
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "post term remove 123 category 1" in call_args
    
    def test_list_categories(self, wp_client, mock_ssh):
        """Test listing categories"""
        import json
        categories = [
            {"term_id": "1", "name": "Uncategorized", "slug": "uncategorized", "parent": "0", "count": "5"},
            {"term_id": "2", "name": "News", "slug": "news", "parent": "0", "count": "10"}
        ]
        mock_ssh.execute.return_value = (json.dumps(categories), "")
        
        result = wp_client.list_categories()
        
        assert result == categories
        call_args = mock_ssh.execute.call_args[0][0]
        assert "term list category" in call_args
        assert "--format=json" in call_args
    
    def test_list_categories_with_search(self, wp_client, mock_ssh):
        """Test searching categories"""
        import json
        categories = [{"term_id": "2", "name": "News", "slug": "news", "parent": "0", "count": "10"}]
        mock_ssh.execute.return_value = (json.dumps(categories), "")
        
        result = wp_client.list_categories(search="News")
        
        assert result == categories
        call_args = mock_ssh.execute.call_args[0][0]
        assert "term list category" in call_args
        assert '--search="News"' in call_args
    
    def test_get_post_categories(self, wp_client, mock_ssh):
        """Test getting categories for a post"""
        import json
        categories = [
            {"term_id": "1", "name": "Uncategorized", "slug": "uncategorized", "parent": "0"},
            {"term_id": "2", "name": "News", "slug": "news", "parent": "0"}
        ]
        mock_ssh.execute.return_value = (json.dumps(categories), "")
        
        result = wp_client.get_post_categories(123)
        
        assert result == categories
        call_args = mock_ssh.execute.call_args[0][0]
        assert "post term list 123 category" in call_args
    
    def test_get_category_by_name(self, wp_client, mock_ssh):
        """Test getting category by name"""
        import json
        category = {"term_id": "2", "name": "News", "slug": "news", "parent": "0"}
        mock_ssh.execute.return_value = (json.dumps(category), "")
        
        result = wp_client.get_category_by_name("news")
        
        assert result == category
        call_args = mock_ssh.execute.call_args[0][0]
        assert "term get category 'news'" in call_args
    
    def test_get_category_by_id(self, wp_client, mock_ssh):
        """Test getting category by ID"""
        import json
        category = {"term_id": "2", "name": "News", "slug": "news", "parent": "0"}
        mock_ssh.execute.return_value = (json.dumps(category), "")
        
        result = wp_client.get_category_by_id(2)
        
        assert result == category
        call_args = mock_ssh.execute.call_args[0][0]
        assert "term get category 2" in call_args
    
    # Issue #1: Test author support in post creation
    def test_create_post_with_author(self, wp_client, mock_ssh):
        """Test creating post with author specified"""
        mock_ssh.execute.return_value = ("123", "")
        
        result = wp_client.create_post(
            title="Test Post",
            content="Test content",
            post_author=1
        )
        
        assert result == 123
        call_args = mock_ssh.execute.call_args[0][0]
        assert "post create" in call_args
        assert "--post_author=" in call_args  # Author parameter is passed
    
    # Issue #2: Test post content update
    def test_update_post_content_directly(self, wp_client, mock_ssh):
        """Test updating post content directly"""
        mock_ssh.execute.return_value = ("Success: Updated post 123", "")
        
        result = wp_client.update_post(123, post_content="New full content")
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "post update 123" in call_args
        assert "--post_content=" in call_args
    
    # Issue #3: Test search in list_posts
    def test_list_posts_with_search(self, wp_client, mock_ssh):
        """Test listing posts with search parameter"""
        import json
        posts = [{"ID": 123, "post_title": "Pricing Strategies"}]
        mock_ssh.execute.return_value = (json.dumps(posts), "")
        
        result = wp_client.list_posts(s="Pricing")
        
        assert result == posts
        call_args = mock_ssh.execute.call_args[0][0]
        assert "post list" in call_args
        assert "--s=" in call_args  # Search parameter is passed
    
    # v1.0.15: Test advanced create options
    def test_create_post_with_excerpt(self, wp_client, mock_ssh):
        """Test creating post with excerpt"""
        mock_ssh.execute.return_value = ("123", "")
        
        result = wp_client.create_post(
            post_title="Test Post",
            post_content="Content",
            post_excerpt="Short summary"
        )
        
        assert result == 123
        call_args = mock_ssh.execute.call_args[0][0]
        assert "post create" in call_args
        assert "--post_excerpt=" in call_args
    
    def test_create_post_with_custom_date(self, wp_client, mock_ssh):
        """Test creating post with custom date"""
        mock_ssh.execute.return_value = ("123", "")
        
        result = wp_client.create_post(
            post_title="Test Post",
            post_content="Content",
            post_date="2024-01-15 10:00:00"
        )
        
        assert result == 123
        call_args = mock_ssh.execute.call_args[0][0]
        assert "post create" in call_args
        assert "--post_date=" in call_args
    
    def test_create_post_with_tags(self, wp_client, mock_ssh):
        """Test creating post with tags"""
        mock_ssh.execute.return_value = ("123", "")
        
        result = wp_client.create_post(
            post_title="Test Post",
            post_content="Content",
            tags_input="python,wordpress"
        )
        
        assert result == 123
        call_args = mock_ssh.execute.call_args[0][0]
        assert "post create" in call_args
        assert "--tags_input=" in call_args
    
    def test_create_post_with_meta(self, wp_client, mock_ssh):
        """Test creating post with custom meta"""
        mock_ssh.execute.return_value = ("123", "")
        
        result = wp_client.create_post(
            post_title="Test Post",
            post_content="Content",
            meta_input='{"custom_field":"value","price":"99.99"}'
        )
        
        assert result == 123
        call_args = mock_ssh.execute.call_args[0][0]
        assert "post create" in call_args
        assert "--meta_input=" in call_args
    
    def test_create_post_with_comment_status(self, wp_client, mock_ssh):
        """Test creating post with comment status"""
        mock_ssh.execute.return_value = ("123", "")
        
        result = wp_client.create_post(
            post_title="Test Post",
            post_content="Content",
            comment_status="closed"
        )
        
        assert result == 123
        call_args = mock_ssh.execute.call_args[0][0]
        assert "post create" in call_args
        assert "--comment_status=" in call_args
    
    # v1.0.16: Test advanced update options
    def test_update_post_with_excerpt(self, wp_client, mock_ssh):
        """Test updating post excerpt"""
        mock_ssh.execute.return_value = ("Success: Updated post 123", "")
        
        result = wp_client.update_post(123, post_excerpt="New excerpt")
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "post update 123" in call_args
        assert "--post_excerpt=" in call_args
    
    def test_update_post_with_author(self, wp_client, mock_ssh):
        """Test updating post author"""
        mock_ssh.execute.return_value = ("Success: Updated post 123", "")
        
        result = wp_client.update_post(123, post_author=2)
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "post update 123" in call_args
        assert "--post_author=" in call_args
    
    def test_update_post_with_date(self, wp_client, mock_ssh):
        """Test updating post date"""
        mock_ssh.execute.return_value = ("Success: Updated post 123", "")
        
        result = wp_client.update_post(123, post_date="2024-01-15 10:00:00")
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "post update 123" in call_args
        assert "--post_date=" in call_args
    
    def test_update_post_with_tags(self, wp_client, mock_ssh):
        """Test updating post tags"""
        mock_ssh.execute.return_value = ("Success: Updated post 123", "")
        
        result = wp_client.update_post(123, tags_input="python,ai")
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "post update 123" in call_args
        assert "--tags_input=" in call_args
    
    def test_update_post_with_meta(self, wp_client, mock_ssh):
        """Test updating post meta"""
        mock_ssh.execute.return_value = ("Success: Updated post 123", "")
        
        result = wp_client.update_post(123, meta_input='{"views":"1000"}')
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "post update 123" in call_args
        assert "--meta_input=" in call_args
    
    def test_update_post_with_comment_status(self, wp_client, mock_ssh):
        """Test updating comment status"""
        mock_ssh.execute.return_value = ("Success: Updated post 123", "")
        
        result = wp_client.update_post(123, comment_status="closed")
        
        assert result is True
        call_args = mock_ssh.execute.call_args[0][0]
        assert "post update 123" in call_args
        assert "--comment_status=" in call_args
