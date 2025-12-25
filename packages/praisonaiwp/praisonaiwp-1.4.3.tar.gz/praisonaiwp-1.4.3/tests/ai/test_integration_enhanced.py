"""Tests for enhanced PraisonAI WordPress integration"""
import os
import pytest
from unittest.mock import Mock, patch

# Check if AI features are available
try:
    from praisonaiwp.ai.integration import PraisonAIWPIntegration
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    PraisonAIWPIntegration = None


@pytest.mark.skipif(not AI_AVAILABLE, reason="AI features not installed")
class TestEnhancedIntegration:
    """Test enhanced integration features"""

    @pytest.fixture
    def mock_wp_client(self):
        """Create a mock WordPress client"""
        client = Mock()
        client.create_post = Mock(return_value=123)
        return client

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test123'})
    def test_init_validates_api_key(self, mock_wp_client):
        """Test that API key is validated on init"""
        # Should not raise with valid key
        integration = PraisonAIWPIntegration(mock_wp_client)
        assert integration is not None

    @patch.dict(os.environ, {}, clear=True)
    def test_init_fails_without_api_key(self, mock_wp_client):
        """Test that init fails without API key"""
        with pytest.raises(ValueError) as exc_info:
            PraisonAIWPIntegration(mock_wp_client)
        assert "OPENAI_API_KEY" in str(exc_info.value)

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test123'})
    def test_init_with_custom_config(self, mock_wp_client):
        """Test initialization with custom config"""
        integration = PraisonAIWPIntegration(
            mock_wp_client,
            min_length=200,
            max_length=5000,
            enable_rate_limiting=False
        )
        assert integration.config['min_length'] == 200
        assert integration.config['max_length'] == 5000
        assert integration.rate_limiter is None

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test123'})
    def test_cost_tracker_initialized(self, mock_wp_client):
        """Test that cost tracker is initialized"""
        integration = PraisonAIWPIntegration(mock_wp_client)
        assert integration.cost_tracker is not None
        assert integration.cost_tracker.total_cost == 0.0

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test123'})
    def test_content_validator_initialized(self, mock_wp_client):
        """Test that content validator is initialized"""
        integration = PraisonAIWPIntegration(mock_wp_client)
        assert integration.content_validator is not None
        assert integration.content_validator.min_length == 100

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test123'})
    def test_rate_limiter_initialized(self, mock_wp_client):
        """Test that rate limiter is initialized by default"""
        integration = PraisonAIWPIntegration(mock_wp_client)
        assert integration.rate_limiter is not None

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test123'})
    def test_rate_limiter_disabled(self, mock_wp_client):
        """Test disabling rate limiter"""
        integration = PraisonAIWPIntegration(
            mock_wp_client,
            enable_rate_limiting=False
        )
        assert integration.rate_limiter is None

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test123'})
    @patch('praisonaiwp.ai.integration.Agent')
    @patch('praisonaiwp.ai.integration.Task')
    @patch('praisonaiwp.ai.integration.PraisonAIAgents')
    def test_generate_returns_enhanced_result(
        self,
        mock_agents_class,
        mock_task_class,
        mock_agent_class,
        mock_wp_client
    ):
        """Test that generate returns enhanced result with cost and metadata"""
        # Setup mocks
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent

        mock_task = Mock()
        mock_task_class.return_value = mock_task

        mock_agents = Mock()
        # Return content with proper paragraph structure
        mock_agents.start = Mock(return_value=(
            "First paragraph about AI.\n\n"
            "Second paragraph with more details.\n\n"
            "Third paragraph concluding the post."
        ))
        mock_agents_class.return_value = mock_agents

        integration = PraisonAIWPIntegration(mock_wp_client)

        result = integration.generate("AI Trends")

        # Verify enhanced result structure
        assert 'content' in result
        assert 'cost' in result
        assert 'duration' in result
        assert 'model' in result
        assert 'metadata' in result

        # Verify metadata
        assert result['metadata']['topic'] == "AI Trends"
        assert result['metadata']['length'] > 0
        assert result['metadata']['word_count'] > 0

        # Verify cost tracking
        assert result['cost'] > 0
        assert integration.last_generation_cost > 0

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test123'})
    @patch('praisonaiwp.ai.integration.Agent')
    @patch('praisonaiwp.ai.integration.Task')
    @patch('praisonaiwp.ai.integration.PraisonAIAgents')
    def test_content_validation_fails_short_content(
        self,
        mock_agents_class,
        mock_task_class,
        mock_agent_class,
        mock_wp_client
    ):
        """Test that content validation catches short content"""
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent

        mock_task = Mock()
        mock_task_class.return_value = mock_task

        mock_agents = Mock()
        mock_agents.start = Mock(return_value="Too short")
        mock_agents_class.return_value = mock_agents

        integration = PraisonAIWPIntegration(mock_wp_client)

        with pytest.raises(ValueError) as exc_info:
            integration.generate("AI Trends")

        assert "validation failed" in str(exc_info.value).lower()
        assert "too short" in str(exc_info.value).lower()

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test123'})
    @patch('praisonaiwp.ai.integration.Agent')
    @patch('praisonaiwp.ai.integration.Task')
    @patch('praisonaiwp.ai.integration.PraisonAIAgents')
    def test_skip_validation(
        self,
        mock_agents_class,
        mock_task_class,
        mock_agent_class,
        mock_wp_client
    ):
        """Test skipping content validation"""
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent

        mock_task = Mock()
        mock_task_class.return_value = mock_task

        mock_agents = Mock()
        mock_agents.start = Mock(return_value="Short")
        mock_agents_class.return_value = mock_agents

        integration = PraisonAIWPIntegration(mock_wp_client)

        # Should not raise when validation is skipped
        result = integration.generate("AI", skip_validation=True)
        assert result['content'] == "Short"

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test123'})
    def test_get_cost_summary(self, mock_wp_client):
        """Test getting cost summary"""
        integration = PraisonAIWPIntegration(mock_wp_client)

        # Track some costs manually
        integration.cost_tracker.track('gpt-4o-mini', 500, 500)
        integration.cost_tracker.track('gpt-4o-mini', 1000, 1000)

        summary = integration.get_cost_summary()

        assert summary['total_generations'] == 2
        assert summary['total_cost'] > 0
        assert summary['average_cost'] > 0
