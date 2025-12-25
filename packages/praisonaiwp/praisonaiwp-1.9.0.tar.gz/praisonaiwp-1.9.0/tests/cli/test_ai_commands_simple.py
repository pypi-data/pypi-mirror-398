"""Simplified tests for AI CLI commands"""
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from praisonaiwp.cli.commands.ai_commands import ai


class TestAICommandsSimple:
    """Simplified test AI CLI commands"""

    @pytest.fixture
    def runner(self):
        """Create CLI runner"""
        return CliRunner()

    @patch('praisonaiwp.cli.commands.ai_commands.AI_AVAILABLE', False)
    def test_ai_generate_without_ai_installed(self, runner):
        """Test error when AI not installed"""
        result = runner.invoke(ai, ['generate', 'AI Trends'])

        assert result.exit_code != 0
        assert 'AI features not available' in result.output

    @patch('praisonaiwp.cli.commands.ai_commands.AI_AVAILABLE', True)
    @patch('praisonaiwp.cli.commands.ai_commands.Config')
    def test_ai_generate_without_config(self, mock_config_class, runner):
        """Test error when config not found"""
        mock_config = Mock()
        mock_config.exists = Mock(return_value=False)
        mock_config_class.return_value = mock_config

        result = runner.invoke(ai, ['generate', 'AI Trends'])

        assert result.exit_code != 0
        assert 'Configuration not found' in result.output
