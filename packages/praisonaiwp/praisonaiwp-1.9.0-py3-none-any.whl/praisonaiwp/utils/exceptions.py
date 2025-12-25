"""Custom exceptions for PraisonAIWP"""


class PraisonAIWPError(Exception):
    """Base exception for PraisonAIWP"""
    pass


class SSHConnectionError(PraisonAIWPError):
    """Raised when SSH connection fails"""
    pass


class WPCLIError(PraisonAIWPError):
    """Raised when WP-CLI command fails"""
    pass


class ConfigNotFoundError(PraisonAIWPError):
    """Raised when configuration file is not found"""
    pass


class ValidationError(PraisonAIWPError):
    """Raised when input validation fails"""
    pass


class PostNotFoundError(PraisonAIWPError):
    """Raised when post is not found"""
    pass
