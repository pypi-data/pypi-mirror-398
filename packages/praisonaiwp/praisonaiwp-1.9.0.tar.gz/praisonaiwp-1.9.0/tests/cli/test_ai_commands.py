"""Tests for AI CLI commands"""
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

# Check if AI features are available
try:
    from praisonaiwp.ai.integration import PraisonAIWPIntegration
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

from praisonaiwp.cli.commands.ai_commands import ai


@pytest.mark.skipif(not AI_AVAILABLE, reason="AI features not installed")
class TestAICommands:
    """Test AI CLI commands"""

    @pytest.fixture
    def runner(self):
        """Create CLI runner"""
        return CliRunner()

    @pytest.fixture
    def mock_config(self):
        """Mock config object"""
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

    @patch('praisonaiwp.cli.commands.ai_commands.AI_AVAILABLE', True)
    @patch('praisonaiwp.cli.commands.ai_commands.Config')
    @patch('praisonaiwp.cli.commands.ai_commands.SSHManager')
    def test_ai_generate_basic(
        self,
        mock_ssh_manager_class,
        mock_config_class,
        runner,
        mock_config
    ):
        """Test basic ai generate command"""
        # Setup mocks
        mock_config_class.return_value = mock_config
        mock_ssh_manager = Mock()
        mock_ssh_manager_class.return_value = mock_ssh_manager

        mock_integration = Mock()
        mock_integration.generate = Mock(return_value={
            'content': 'Generated content about AI',
            'post_id': None
        })

        # Run command - patch where it's imported (inside the function)
        with patch('praisonaiwp.ai.integration.PraisonAIWPIntegration', return_value=mock_integration):
            with patch('praisonaiwp.core.wp_client.WPClient'):
                result = runner.invoke(ai, ['generate', 'AI Trends'])

        # Verify
        assert result.exit_code == 0
        assert 'Generated content about AI' in result.output

        # Verify integration was called correctly
        mock_integration.generate.assert_called_once()
        call_args = mock_integration.generate.call_args
        assert call_args[1]['topic'] == 'AI Trends'

    @patch('praisonaiwp.cli.commands.ai_commands.AI_AVAILABLE', True)
    @patch('praisonaiwp.cli.commands.ai_commands.load_config')
    @patch('praisonaiwp.cli.commands.ai_commands.WPClient')
    @patch('praisonaiwp.ai.integration.PraisonAIWPIntegration')
    def test_ai_generate_with_title(
        self,
        mock_integration_class,
        mock_wp_client_class,
        mock_load_config,
        runner,
        mock_config
    ):
        """Test ai generate with custom title"""
        mock_load_config.return_value = mock_config
        mock_wp_client = Mock()
        mock_wp_client_class.return_value = mock_wp_client

        mock_integration = Mock()
        mock_integration.generate = Mock(return_value={
            'content': 'Content',
            'post_id': None
        })
        mock_integration_class.return_value = mock_integration

        # Run with title
        result = runner.invoke(ai, [
            'generate',
            'AI Trends',
            '--title',
            'The Future of AI'
        ])

        assert result.exit_code == 0

        # Verify title was passed
        call_kwargs = mock_integration.generate.call_args[1]
        assert call_kwargs['title'] == 'The Future of AI'

    @patch('praisonaiwp.cli.commands.ai_commands.AI_AVAILABLE', True)
    @patch('praisonaiwp.cli.commands.ai_commands.load_config')
    @patch('praisonaiwp.cli.commands.ai_commands.WPClient')
    @patch('praisonaiwp.ai.integration.PraisonAIWPIntegration')
    def test_ai_generate_with_auto_publish(
        self,
        mock_integration_class,
        mock_wp_client_class,
        mock_load_config,
        runner,
        mock_config
    ):
        """Test ai generate with auto-publish"""
        mock_load_config.return_value = mock_config
        mock_wp_client = Mock()
        mock_wp_client_class.return_value = mock_wp_client

        mock_integration = Mock()
        mock_integration.generate = Mock(return_value={
            'content': 'Content',
            'post_id': 123
        })
        mock_integration_class.return_value = mock_integration

        # Run with auto-publish
        result = runner.invoke(ai, [
            'generate',
            'AI Trends',
            '--auto-publish'
        ])

        assert result.exit_code == 0
        assert 'Published' in result.output
        assert '123' in result.output

        # Verify auto_publish was passed
        call_kwargs = mock_integration.generate.call_args[1]
        assert call_kwargs['auto_publish'] is True

    @patch('praisonaiwp.cli.commands.ai_commands.AI_AVAILABLE', True)
    @patch('praisonaiwp.cli.commands.ai_commands.load_config')
    @patch('praisonaiwp.cli.commands.ai_commands.WPClient')
    @patch('praisonaiwp.ai.integration.PraisonAIWPIntegration')
    def test_ai_generate_with_status(
        self,
        mock_integration_class,
        mock_wp_client_class,
        mock_load_config,
        runner,
        mock_config
    ):
        """Test ai generate with custom status"""
        mock_load_config.return_value = mock_config
        mock_wp_client = Mock()
        mock_wp_client_class.return_value = mock_wp_client

        mock_integration = Mock()
        mock_integration.generate = Mock(return_value={
            'content': 'Content',
            'post_id': 123
        })
        mock_integration_class.return_value = mock_integration

        # Run with publish status
        result = runner.invoke(ai, [
            'generate',
            'AI Trends',
            '--auto-publish',
            '--status',
            'publish'
        ])

        assert result.exit_code == 0

        # Verify integration was initialized with status
        init_kwargs = mock_integration_class.call_args[1]
        assert init_kwargs['status'] == 'publish'

    @patch('praisonaiwp.cli.commands.ai_commands.AI_AVAILABLE', False)
    def test_ai_generate_without_ai_installed(self, runner):
        """Test error when AI not installed"""
        result = runner.invoke(ai, ['generate', 'AI Trends'])

        assert result.exit_code != 0
        assert 'AI features not available' in result.output

    @patch('praisonaiwp.cli.commands.ai_commands.AI_AVAILABLE', True)
    @patch('praisonaiwp.cli.commands.ai_commands.load_config')
    def test_ai_generate_without_config(self, mock_load_config, runner):
        """Test error when config not found"""
        mock_load_config.return_value = None

        result = runner.invoke(ai, ['generate', 'AI Trends'])

        assert result.exit_code != 0
        assert 'Configuration not found' in result.output

    @patch('praisonaiwp.cli.commands.ai_commands.AI_AVAILABLE', True)
    @patch('praisonaiwp.cli.commands.ai_commands.load_config')
    @patch('praisonaiwp.cli.commands.ai_commands.WPClient')
    @patch('praisonaiwp.ai.integration.PraisonAIWPIntegration')
    def test_ai_generate_with_verbose(
        self,
        mock_integration_class,
        mock_wp_client_class,
        mock_load_config,
        runner,
        mock_config
    ):
        """Test ai generate with verbose flag"""
        mock_load_config.return_value = mock_config
        mock_wp_client = Mock()
        mock_wp_client_class.return_value = mock_wp_client

        mock_integration = Mock()
        mock_integration.generate = Mock(return_value={
            'content': 'Content',
            'post_id': None
        })
        mock_integration_class.return_value = mock_integration

        # Run with verbose
        result = runner.invoke(ai, [
            'generate',
            'AI Trends',
            '--verbose'
        ])

        assert result.exit_code == 0

        # Verify verbose was passed to integration
        init_kwargs = mock_integration_class.call_args[1]
        assert init_kwargs['verbose'] == 1
