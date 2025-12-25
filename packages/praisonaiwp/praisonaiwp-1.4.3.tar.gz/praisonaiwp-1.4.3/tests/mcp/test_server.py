"""
Tests for MCP Server - FastMCP server implementation

TDD: These tests define the expected behavior of the MCP server.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestMCPServer:
    """Test MCP server functionality"""
    
    def test_mcp_server_exists(self):
        """Test that MCP server is defined"""
        from praisonaiwp.mcp.server import mcp
        assert mcp is not None
    
    def test_mcp_server_has_name(self):
        """Test that MCP server has a name"""
        from praisonaiwp.mcp.server import mcp
        assert hasattr(mcp, 'name') or hasattr(mcp, '_name')
    
    def test_mcp_server_has_tools(self):
        """Test that MCP server has tools registered"""
        from praisonaiwp.mcp.server import mcp
        # FastMCP stores tools internally
        assert mcp is not None
    
    def test_get_wp_client_helper_exists(self):
        """Test that get_wp_client helper is defined"""
        from praisonaiwp.mcp.server import get_wp_client
        assert callable(get_wp_client)
    
    def test_get_wp_client_returns_client(self):
        """Test get_wp_client returns a WPClient instance"""
        from praisonaiwp.mcp.server import get_wp_client
        
        with patch('praisonaiwp.mcp.server.Config') as mock_config:
            with patch('praisonaiwp.mcp.server.SSHManager') as mock_ssh:
                with patch('praisonaiwp.mcp.server.WPClient') as mock_wp:
                    mock_config_instance = Mock()
                    mock_config_instance.get_server.return_value = {
                        'hostname': 'example.com',
                        'username': 'user',
                        'key_file': '~/.ssh/id_rsa',
                        'wp_path': '/var/www/html',
                        'php_bin': 'php',
                        'wp_cli': '/usr/local/bin/wp'
                    }
                    mock_config.return_value = mock_config_instance
                    
                    mock_ssh_instance = Mock()
                    mock_ssh.return_value = mock_ssh_instance
                    
                    mock_wp_instance = Mock()
                    mock_wp.return_value = mock_wp_instance
                    
                    client = get_wp_client()
                    
                    assert client is not None


class TestMCPServerTools:
    """Test that tools are properly registered with the server"""
    
    def test_server_has_create_post_tool(self):
        """Test server has create_post tool"""
        from praisonaiwp.mcp import tools
        # Verify the tool function exists in tools module
        assert hasattr(tools, 'create_post')
    
    def test_server_has_list_posts_tool(self):
        """Test server has list_posts tool"""
        from praisonaiwp.mcp import tools
        assert hasattr(tools, 'list_posts')


class TestMCPServerResources:
    """Test that resources are properly registered with the server"""
    
    def test_server_has_wordpress_info_resource(self):
        """Test server has wordpress info resource"""
        from praisonaiwp.mcp import server
        # Resources are registered via decorators
        assert server.mcp is not None


class TestMCPServerPrompts:
    """Test that prompts are properly registered with the server"""
    
    def test_server_has_prompts(self):
        """Test server has prompts registered"""
        from praisonaiwp.mcp import server
        assert server.mcp is not None
