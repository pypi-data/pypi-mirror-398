"""Tests for PraisonAI WordPress integration"""
import os
from unittest.mock import Mock, patch

import pytest

# Check if AI features are available
try:
    from praisonaiwp.ai.integration import PraisonAIWPIntegration
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    PraisonAIWPIntegration = None


@pytest.mark.skipif(not AI_AVAILABLE, reason="AI features not installed")
class TestPraisonAIWPIntegration:
    """Test PraisonAI WordPress integration class"""

    @pytest.fixture
    def mock_wp_client(self):
        """Create a mock WordPress client"""
        client = Mock()
        client.create_post = Mock(return_value=123)
        client.update_post = Mock(return_value=True)
        return client

    @pytest.fixture
    def integration(self, mock_wp_client):
        """Create integration instance"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test123'}):
            return PraisonAIWPIntegration(mock_wp_client)

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test123'})
    def test_init(self, mock_wp_client):
        """Test integration initialization"""
        integration = PraisonAIWPIntegration(mock_wp_client)
        assert integration.wp_client == mock_wp_client
        # Check defaults are set
        assert integration.config['model'] == 'gpt-4o-mini'
        assert integration.config['verbose'] == 0
        assert integration.config['status'] == 'draft'

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test123'})
    def test_init_with_config(self, mock_wp_client):
        """Test initialization with config"""
        config = {'model': 'gpt-4o-mini', 'verbose': 1}
        integration = PraisonAIWPIntegration(mock_wp_client, **config)
        assert integration.config['model'] == 'gpt-4o-mini'
        assert integration.config['verbose'] == 1

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test123'})
    @patch('praisonaiwp.ai.integration.check_ai_available')
    def test_check_ai_available_called(self, mock_check, mock_wp_client):
        """Test that AI availability is checked on init"""
        mock_check.return_value = True
        PraisonAIWPIntegration(mock_wp_client)
        mock_check.assert_called_once()

    @patch('praisonaiwp.ai.integration.Agent')
    @patch('praisonaiwp.ai.integration.Task')
    @patch('praisonaiwp.ai.integration.PraisonAIAgents')
    def test_generate_basic(self, mock_agents_class, mock_task_class, mock_agent_class, integration):
        """Test basic content generation"""
        # Setup mocks
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent

        mock_task = Mock()
        mock_task_class.return_value = mock_task

        mock_agents = Mock()
        mock_agents.start = Mock(return_value="Generated content about AI")
        mock_agents_class.return_value = mock_agents

        # Call generate with skip_validation
        result = integration.generate("AI Trends", skip_validation=True)

        # Verify agent was created
        mock_agent_class.assert_called_once()
        call_kwargs = mock_agent_class.call_args[1]
        assert call_kwargs['name'] == "WordPress Writer"
        assert "AI Trends" in call_kwargs['goal']

        # Verify task was created
        mock_task_class.assert_called_once()
        task_kwargs = mock_task_class.call_args[1]
        assert "AI Trends" in task_kwargs['description']
        assert task_kwargs['agent'] == mock_agent

        # Verify agents orchestrator was created
        mock_agents_class.assert_called_once()

        # Verify result
        assert result['content'] == "Generated content about AI"

    @patch('praisonaiwp.ai.integration.Agent')
    @patch('praisonaiwp.ai.integration.Task')
    @patch('praisonaiwp.ai.integration.PraisonAIAgents')
    def test_generate_with_auto_publish(
        self,
        mock_agents_class,
        mock_task_class,
        mock_agent_class,
        integration,
        mock_wp_client
    ):
        """Test generation with auto-publish"""
        # Setup mocks
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent

        mock_task = Mock()
        mock_task_class.return_value = mock_task

        mock_agents = Mock()
        mock_agents.start = Mock(return_value="Generated content")
        mock_agents_class.return_value = mock_agents

        # Call generate with auto_publish and skip_validation
        integration.generate(
            "AI Trends",
            title="The Future of AI",
            auto_publish=True,
            skip_validation=True
        )

        # Verify task has callback
        task_kwargs = mock_task_class.call_args[1]
        assert task_kwargs['callback'] is not None

        # Simulate callback execution
        mock_output = Mock()
        mock_output.raw = "Generated content"
        callback = task_kwargs['callback']
        callback_result = callback(mock_output)

        # Verify post was created
        mock_wp_client.create_post.assert_called_once()
        assert callback_result['post_id'] == 123

    @patch('praisonaiwp.ai.integration.Agent')
    @patch('praisonaiwp.ai.integration.Task')
    @patch('praisonaiwp.ai.integration.PraisonAIAgents')
    def test_generate_uses_gpt4o_mini_by_default(
        self,
        mock_agents_class,
        mock_task_class,
        mock_agent_class,
        integration
    ):
        """Test that gpt-4o-mini is used by default"""
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent

        mock_task = Mock()
        mock_task_class.return_value = mock_task

        mock_agents = Mock()
        mock_agents.start = Mock(return_value="Content")
        mock_agents_class.return_value = mock_agents

        # Generate without specifying model, skip validation
        integration.generate("Test Topic", skip_validation=True)

        # Verify agent was created with gpt-4o-mini
        call_kwargs = mock_agent_class.call_args[1]
        assert call_kwargs['llm'] == 'gpt-4o-mini'

    def test_publish_callback(self, integration, mock_wp_client):
        """Test the publish callback function"""
        integration.current_title = "Test Title"
        integration.config = {'status': 'publish'}

        # Create mock task output
        mock_output = Mock()
        mock_output.raw = "Test content"

        # Call callback
        result = integration._publish_callback(mock_output)

        # Verify post was created
        mock_wp_client.create_post.assert_called_once_with(
            post_title="Test Title",
            post_content="Test content",
            post_status='publish'
        )

        # Verify result
        assert result['post_id'] == 123
        assert result['content'] == "Test content"

    def test_create_wordpress_tools(self, integration):
        """Test creating WordPress tool functions"""
        tools = integration.create_wordpress_tools()

        assert isinstance(tools, list)
        assert len(tools) >= 2
        assert all(callable(tool) for tool in tools)
