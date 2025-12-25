"""Tests for AI agent with ServerRouter integration"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from praisonaiwp.ai.smart_agent import SmartContentAgent
from praisonaiwp.core.router import ServerRouter


class TestSmartContentAgent:
    """Test SmartContentAgent with auto-routing capabilities"""

    def test_agent_detects_server_from_title(self):
        """Test that agent can detect server from post title"""
        config = {
            'servers': {
                'biblerevelation': {
                    'website': 'https://biblerevelation.org',
                    'hostname': 'christsong.in',
                }
            },
            'settings': {'auto_route': True}
        }
        
        wp_client = Mock()
        agent = SmartContentAgent(wp_client, config)
        
        title = "New post for biblerevelation.org"
        server_name = agent.detect_server_from_context(title=title)
        
        assert server_name == 'biblerevelation'

    def test_agent_detects_server_from_content(self):
        """Test that agent can detect server from post content"""
        config = {
            'servers': {
                'default': {
                    'website': 'https://mer.vin',
                    'aliases': ['https://praison.com'],
                }
            },
            'settings': {'auto_route': True}
        }
        
        wp_client = Mock()
        agent = SmartContentAgent(wp_client, config)
        
        content = "Check out my blog at praison.com"
        server_name = agent.detect_server_from_context(content=content)
        
        assert server_name == 'default'

    def test_agent_detects_server_from_tags(self):
        """Test that agent can detect server from content tags"""
        config = {
            'servers': {
                'biblerevelation': {
                    'website': 'https://biblerevelation.org',
                    'tags': ['bible', 'christian', 'teaching'],
                }
            },
            'settings': {'auto_route': True}
        }
        
        wp_client = Mock()
        agent = SmartContentAgent(wp_client, config)
        
        context = {
            'title': 'Understanding Scripture',
            'tags': ['bible', 'teaching']
        }
        server_name = agent.detect_server_from_context(**context)
        
        assert server_name == 'biblerevelation'

    def test_agent_uses_explicit_server_when_provided(self):
        """Test that explicit server parameter takes precedence"""
        config = {
            'servers': {
                'default': {'website': 'https://mer.vin'},
                'biblerevelation': {'website': 'https://biblerevelation.org'},
            }
        }
        
        wp_client = Mock()
        agent = SmartContentAgent(wp_client, config)
        
        # Even though content mentions biblerevelation.org, explicit server should win
        server_name = agent.detect_server_from_context(
            content="Post for biblerevelation.org",
            server='default'
        )
        
        assert server_name == 'default'

    def test_agent_falls_back_to_default_server(self):
        """Test that agent falls back to default when no match found"""
        config = {
            'default_server': 'default',
            'servers': {
                'default': {'website': 'https://mer.vin'},
            }
        }
        
        wp_client = Mock()
        agent = SmartContentAgent(wp_client, config)
        
        server_name = agent.detect_server_from_context(
            title="Generic post title",
            content="Generic content"
        )
        
        assert server_name == 'default'

    def test_agent_suggests_server_with_confidence(self):
        """Test that agent provides confidence score for suggestions"""
        config = {
            'servers': {
                'biblerevelation': {
                    'website': 'https://biblerevelation.org',
                    'tags': ['bible', 'christian'],
                }
            }
        }
        
        wp_client = Mock()
        agent = SmartContentAgent(wp_client, config)
        
        result = agent.suggest_server({
            'title': 'Post about biblerevelation.org',
            'tags': ['bible']
        })
        
        assert result['server'] == 'biblerevelation'
        assert result['confidence'] > 0.8
        assert 'reason' in result

    def test_agent_integrates_with_wordpress_tools(self):
        """Test that agent can create posts with auto-routing"""
        config = {
            'servers': {
                'biblerevelation': {
                    'website': 'https://biblerevelation.org',
                    'author': 'praison',
                    'category': 'AI',
                }
            },
            'settings': {'auto_route': True}
        }
        
        wp_client = Mock()
        wp_client.create_post = Mock(return_value={'id': 123})
        
        agent = SmartContentAgent(wp_client, config)
        
        result = agent.create_post_with_routing(
            title="Post for biblerevelation.org",
            content="<p>Test content</p>",
            status='draft'
        )
        
        assert result['post_id'] == 123
        assert result['server'] == 'biblerevelation'
        assert wp_client.create_post.called

    def test_agent_respects_auto_route_setting(self):
        """Test that agent only auto-routes when setting is enabled"""
        config = {
            'default_server': 'default',
            'servers': {
                'default': {'website': 'https://mer.vin'},
                'biblerevelation': {'website': 'https://biblerevelation.org'},
            },
            'settings': {'auto_route': False}
        }
        
        wp_client = Mock()
        agent = SmartContentAgent(wp_client, config)
        
        # Should use default even though content mentions biblerevelation
        server_name = agent.detect_server_from_context(
            content="Post for biblerevelation.org"
        )
        
        assert server_name == 'default'

    def test_agent_applies_server_defaults(self):
        """Test that agent applies server-specific defaults (author, category)"""
        config = {
            'servers': {
                'biblerevelation': {
                    'website': 'https://biblerevelation.org',
                    'author': 'praison',
                    'category': 'AI',
                }
            }
        }
        
        wp_client = Mock()
        agent = SmartContentAgent(wp_client, config)
        
        post_options = agent.get_server_defaults('biblerevelation')
        
        assert post_options['author'] == 'praison'
        assert post_options['category'] == 'AI'

    def test_agent_generates_content_with_context(self):
        """Test that agent generates content with server context"""
        config = {
            'servers': {
                'biblerevelation': {
                    'website': 'https://biblerevelation.org',
                    'description': 'Bible teaching website',
                    'tags': ['bible', 'christian'],
                }
            }
        }
        
        wp_client = Mock()
        
        # Mock AI integration
        with patch.object(SmartContentAgent, 'ai_integration') as mock_ai:
            mock_ai.generate_post.return_value = {
                'title': 'Test Post',
                'content': '<p>Generated content</p>'
            }
            
            agent = SmartContentAgent(wp_client, config)
            agent._ai_integration = mock_ai
            
            result = agent.generate_content(
                topic="Immanuel",
                server='biblerevelation'
            )
            
            assert 'title' in result
            assert 'content' in result
            assert mock_ai.generate_post.called
