"""
PraisonAIWP - AI-powered WordPress content management framework
"""

from praisonaiwp.__version__ import __version__
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.editors.content_editor import ContentEditor

__author__ = "Praison"

__all__ = [
    "SSHManager",
    "WPClient",
    "ContentEditor",
]
