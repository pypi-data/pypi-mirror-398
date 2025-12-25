"""End-to-end test for AI features"""
import os
import pytest
from click.testing import CliRunner
from unittest.mock import Mock, patch, MagicMock

# Check if AI features are available
try:
    from praisonaiwp.ai.integration import PraisonAIWPIntegration
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

from praisonaiwp.cli.main import cli


@pytest.mark.skipif(not AI_AVAILABLE, reason="AI features not installed")
class TestE2EAI:
    """End-to-end AI integration tests"""

    @pytest.fixture
    def runner(self):
        """Create CLI runner"""
        return CliRunner()

    @pytest.fixture
    def mock_config(self):
        """Mock config"""
        config = Mock()
        config.exists = Mock(return_value=True)
        config.get_server = Mock(return_value={
            'hostname': 'example.com',
            'username': 'user',
            'key_file': '/path/to/key',
            'wp_path': '/var/www/html',
            'port': 22
        })
        return config

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test123'})
    @patch('praisonaiwp.cli.commands.ai_commands.Config')
    @patch('praisonaiwp.cli.commands.ai_commands.SSHManager')
    @patch('praisonaiwp.cli.commands.ai_commands.PraisonAIWPIntegration')
    def test_ai_generate_command_full_flow(
        self,
        mock_integration_class,
        mock_ssh_manager_class,
        mock_config_class,
        runner,
        mock_config
    ):
        """Test full AI generate command flow"""
        # Setup mocks
        mock_config_class.return_value = mock_config

        mock_ssh_manager = Mock()
        mock_ssh_manager_class.return_value = mock_ssh_manager

        mock_integration = Mock()
        mock_integration.generate = Mock(return_value={
            'content': (
                "First paragraph about AI trends.\n\n"
                "Second paragraph with detailed analysis.\n\n"
                "Third paragraph with conclusions."
            ),
            'post_id': 123,
            'cost': 0.0005,
            'duration': 2.5,
            'model': 'gpt-4o-mini',
            'metadata': {
                'topic': 'AI Trends',
                'title': 'The Future of AI',
                'length': 150,
                'word_count': 25
            }
        })
        mock_integration_class.return_value = mock_integration

        # Mock WPClient
        with patch('praisonaiwp.cli.commands.ai_commands.WPClient'):
            # Run command
            result = runner.invoke(cli, [
                'ai',
                'generate',
                'AI Trends',
                '--title', 'The Future of AI',
                '--auto-publish',
                '--status', 'publish',
                '--verbose'
            ])

        # Verify success
        assert result.exit_code == 0
        assert 'Generating content about: AI Trends' in result.output
        assert 'Generated Content:' in result.output
        assert 'Published to WordPress! Post ID: 123' in result.output

        # Verify integration was called correctly
        mock_integration.generate.assert_called_once()
        call_kwargs = mock_integration.generate.call_args[1]
        assert call_kwargs['topic'] == 'AI Trends'
        assert call_kwargs['title'] == 'The Future of AI'
        assert call_kwargs['auto_publish'] is True

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test123'})
    @patch('praisonaiwp.cli.commands.ai_commands.Config')
    @patch('praisonaiwp.cli.commands.ai_commands.SSHManager')
    @patch('praisonaiwp.cli.commands.ai_commands.PraisonAIWPIntegration')
    def test_ai_generate_without_publish(
        self,
        mock_integration_class,
        mock_ssh_manager_class,
        mock_config_class,
        runner,
        mock_config
    ):
        """Test AI generate without auto-publish"""
        mock_config_class.return_value = mock_config
        mock_ssh_manager = Mock()
        mock_ssh_manager_class.return_value = mock_ssh_manager

        mock_integration = Mock()
        mock_integration.generate = Mock(return_value={
            'content': "Generated content.\n\nMore content.\n\nEven more.",
            'post_id': None,
            'cost': 0.0003,
            'duration': 1.8,
            'model': 'gpt-4o-mini',
            'metadata': {'word_count': 10}
        })
        mock_integration_class.return_value = mock_integration

        with patch('praisonaiwp.cli.commands.ai_commands.WPClient'):
            result = runner.invoke(cli, [
                'ai',
                'generate',
                'Test Topic'
            ])

        assert result.exit_code == 0
        assert 'Generated Content:' in result.output
        assert 'not published' in result.output
        assert 'Use --auto-publish to publish' in result.output

    @patch.dict(os.environ, {}, clear=True)
    def test_ai_generate_without_api_key(self, runner):
        """Test error when API key is missing"""
        result = runner.invoke(cli, [
            'ai',
            'generate',
            'Test Topic'
        ])

        assert result.exit_code != 0
        assert 'AI features not available' in result.output

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test123'})
    @patch('praisonaiwp.cli.commands.ai_commands.Config')
    def test_ai_generate_without_config(self, mock_config_class, runner):
        """Test error when config not found"""
        mock_config = Mock()
        mock_config.exists = Mock(return_value=False)
        mock_config_class.return_value = mock_config

        result = runner.invoke(cli, [
            'ai',
            'generate',
            'Test Topic'
        ])

        assert result.exit_code != 0
        assert 'Configuration not found' in result.output
