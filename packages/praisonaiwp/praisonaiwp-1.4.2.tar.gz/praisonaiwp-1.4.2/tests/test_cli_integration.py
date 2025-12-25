"""
Integration tests for CLI commands.

These tests ensure that:
1. All CLI commands can be imported without errors
2. CLI help commands work
3. Package installation works correctly
4. No broken imports or missing modules
"""

import subprocess
import sys
import pytest


class TestCLIImports:
    """Test that all CLI modules can be imported"""
    
    def test_main_cli_import(self):
        """Test main CLI can be imported"""
        from praisonaiwp.cli.main import cli
        assert cli is not None
    
    def test_create_command_import(self):
        """Test create command can be imported"""
        from praisonaiwp.cli.commands.create import create_command
        assert create_command is not None
    
    def test_update_command_import(self):
        """Test update command can be imported"""
        from praisonaiwp.cli.commands.update import update_command
        assert update_command is not None
    
    def test_list_command_import(self):
        """Test list command can be imported"""
        from praisonaiwp.cli.commands.list import list_command
        assert list_command is not None
    
    def test_find_command_import(self):
        """Test find command can be imported"""
        from praisonaiwp.cli.commands.find import find_command
        assert find_command is not None
    
    def test_category_command_import(self):
        """Test category command can be imported"""
        from praisonaiwp.cli.commands.category import category_command
        assert category_command is not None
    
    def test_media_command_import(self):
        """Test media command can be imported"""
        from praisonaiwp.cli.commands.media import media_command
        assert media_command is not None
    
    def test_init_command_import(self):
        """Test init command can be imported"""
        from praisonaiwp.cli.commands.init import init_command
        assert init_command is not None


class TestCLIHelp:
    """Test CLI help commands work"""
    
    def test_main_help(self):
        """Test main --help works"""
        result = subprocess.run(
            [sys.executable, '-m', 'praisonaiwp.cli.main', '--help'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'Usage:' in result.stdout or 'Commands:' in result.stdout
    
    def test_create_help(self):
        """Test create --help works"""
        result = subprocess.run(
            [sys.executable, '-m', 'praisonaiwp.cli.main', 'create', '--help'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'create' in result.stdout.lower()
    
    def test_update_help(self):
        """Test update --help works"""
        result = subprocess.run(
            [sys.executable, '-m', 'praisonaiwp.cli.main', 'update', '--help'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'update' in result.stdout.lower()
    
    def test_list_help(self):
        """Test list --help works"""
        result = subprocess.run(
            [sys.executable, '-m', 'praisonaiwp.cli.main', 'list', '--help'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'list' in result.stdout.lower()
    
    def test_find_help(self):
        """Test find --help works"""
        result = subprocess.run(
            [sys.executable, '-m', 'praisonaiwp.cli.main', 'find', '--help'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'find' in result.stdout.lower()
    
    def test_media_help(self):
        """Test media --help works"""
        result = subprocess.run(
            [sys.executable, '-m', 'praisonaiwp.cli.main', 'media', '--help'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'media' in result.stdout.lower()
        assert '--post-id' in result.stdout
        assert '--title' in result.stdout
        assert '--alt' in result.stdout


class TestCoreImports:
    """Test core module imports"""
    
    def test_ssh_manager_import(self):
        """Test SSHManager can be imported"""
        from praisonaiwp.core.ssh_manager import SSHManager
        assert SSHManager is not None
    
    def test_wp_client_import(self):
        """Test WPClient can be imported"""
        from praisonaiwp.core.wp_client import WPClient
        assert WPClient is not None
    
    def test_config_import(self):
        """Test Config can be imported"""
        from praisonaiwp.core.config import Config
        assert Config is not None
    
    def test_content_editor_import(self):
        """Test ContentEditor can be imported from correct location"""
        from praisonaiwp.editors.content_editor import ContentEditor
        assert ContentEditor is not None


class TestUtilsImports:
    """Test utils module imports"""
    
    def test_logger_import(self):
        """Test logger can be imported"""
        from praisonaiwp.utils.logger import get_logger
        assert get_logger is not None
    
    def test_exceptions_import(self):
        """Test exceptions can be imported"""
        from praisonaiwp.utils.exceptions import (
            PraisonAIWPError,
            SSHConnectionError,
            WPCLIError,
            ConfigNotFoundError
        )
        assert PraisonAIWPError is not None
        assert SSHConnectionError is not None
        assert WPCLIError is not None
        assert ConfigNotFoundError is not None
    
    def test_block_converter_import(self):
        """Test block converter can be imported"""
        from praisonaiwp.utils.block_converter import convert_to_blocks, has_blocks
        assert convert_to_blocks is not None
        assert has_blocks is not None


class TestNewFeatures:
    """Test new features are accessible"""
    
    def test_no_block_conversion_flag_in_create(self):
        """Test --no-block-conversion flag exists in create command"""
        result = subprocess.run(
            [sys.executable, '-m', 'praisonaiwp.cli.main', 'create', '--help'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert '--no-block-conversion' in result.stdout
        assert 'Disable automatic HTML to Gutenberg blocks conversion' in result.stdout
    
    def test_no_block_conversion_flag_in_update(self):
        """Test --no-block-conversion flag exists in update command"""
        result = subprocess.run(
            [sys.executable, '-m', 'praisonaiwp.cli.main', 'update', '--help'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert '--no-block-conversion' in result.stdout
        assert 'Disable automatic HTML to Gutenberg blocks conversion' in result.stdout
    
    def test_block_conversion_enabled_by_default(self):
        """Test that block conversion is enabled by default (opt-out design)"""
        # This is a design test - the flag is --no-block-conversion (opt-out)
        # not --convert-to-blocks (opt-in)
        result = subprocess.run(
            [sys.executable, '-m', 'praisonaiwp.cli.main', 'create', '--help'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        # Should have --no-block-conversion (opt-out), not --convert-to-blocks (opt-in)
        assert '--no-block-conversion' in result.stdout
        assert '--convert-to-blocks' not in result.stdout


class TestVersionInfo:
    """Test version information"""
    
    def test_version_import(self):
        """Test version can be imported"""
        from praisonaiwp.__version__ import __version__
        assert __version__ is not None
        assert isinstance(__version__, str)
        assert len(__version__) > 0
    
    def test_version_format(self):
        """Test version follows semantic versioning"""
        from praisonaiwp.__version__ import __version__
        parts = __version__.split('.')
        assert len(parts) >= 2  # At least major.minor
        assert parts[0].isdigit()  # Major version is a number
        assert parts[1].isdigit()  # Minor version is a number


class TestPackageStructure:
    """Test package structure is correct"""
    
    def test_package_init(self):
        """Test package __init__ works"""
        import praisonaiwp
        assert praisonaiwp is not None
    
    def test_cli_package_init(self):
        """Test CLI package __init__ works"""
        import praisonaiwp.cli
        assert praisonaiwp.cli is not None
    
    def test_core_package_init(self):
        """Test core package __init__ works"""
        import praisonaiwp.core
        assert praisonaiwp.core is not None
    
    def test_utils_package_init(self):
        """Test utils package __init__ works"""
        import praisonaiwp.utils
        assert praisonaiwp.utils is not None
    
    def test_editors_package_init(self):
        """Test editors package __init__ works"""
        import praisonaiwp.editors
        assert praisonaiwp.editors is not None


class TestCriticalPaths:
    """Test critical import paths that caused v1.0.17 failure"""
    
    def test_update_command_content_editor_import(self):
        """
        Test that update.py imports ContentEditor from correct location.
        This was the bug in v1.0.17.
        """
        # This will fail if the import path is wrong
        from praisonaiwp.cli.commands.update import update_command
        
        # Verify the module has access to ContentEditor
        import praisonaiwp.cli.commands.update as update_module
        assert hasattr(update_module, 'ContentEditor')
    
    def test_create_command_block_converter_import(self):
        """Test that create.py imports block converter correctly"""
        from praisonaiwp.cli.commands.create import create_command
        
        # Verify the module has access to block converter functions
        import praisonaiwp.cli.commands.create as create_module
        assert hasattr(create_module, 'html_to_blocks')
        assert hasattr(create_module, 'has_blocks')
    
    def test_all_cli_commands_importable_together(self):
        """Test that all CLI commands can be imported together"""
        # This simulates what happens when the CLI starts
        from praisonaiwp.cli.main import cli
        from praisonaiwp.cli.commands.create import create_command
        from praisonaiwp.cli.commands.update import update_command
        from praisonaiwp.cli.commands.list import list_command
        from praisonaiwp.cli.commands.find import find_command
        from praisonaiwp.cli.commands.category import category_command
        from praisonaiwp.cli.commands.init import init_command
        from praisonaiwp.cli.commands.media import media_command
        
        # All should be importable without errors
        assert all([
            cli, create_command, update_command, list_command,
            find_command, category_command, init_command, media_command
        ])


class TestRegressionPrevention:
    """Tests to prevent regression of known issues"""
    
    def test_no_core_content_editor(self):
        """
        Ensure ContentEditor is NOT in core/ (v1.0.17 bug).
        It should only be in editors/
        """
        with pytest.raises(ModuleNotFoundError):
            from praisonaiwp.core.content_editor import ContentEditor
    
    def test_content_editor_in_editors(self):
        """Ensure ContentEditor IS in editors/ (correct location)"""
        from praisonaiwp.editors.content_editor import ContentEditor
        assert ContentEditor is not None
    
    def test_block_converter_in_utils(self):
        """Ensure block_converter is in utils/ (correct location)"""
        from praisonaiwp.utils.block_converter import BlockConverter
        assert BlockConverter is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
