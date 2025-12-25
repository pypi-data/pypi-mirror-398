"""Validators for AI operations"""
import os
from typing import List, Tuple


class APIKeyValidator:
    """Validate OpenAI API key"""

    def validate(self) -> Tuple[bool, str]:
        """Validate API key

        Returns:
            tuple: (is_valid, error_message)
        """
        api_key = os.getenv('OPENAI_API_KEY')

        if not api_key:
            return False, (
                "OPENAI_API_KEY not set. "
                "Get your key at: https://platform.openai.com/api-keys"
            )

        if not api_key.startswith('sk-'):
            return False, (
                "Invalid format. OpenAI API keys should start with 'sk-'"
            )

        return True, None


class ContentValidator:
    """Validate generated content quality"""

    def __init__(self, min_length: int = 100, max_length: int = 10000):
        """Initialize validator

        Args:
            min_length: Minimum content length in characters
            max_length: Maximum content length in characters
        """
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, content: str) -> Tuple[bool, List[str]]:
        """Validate content

        Args:
            content: Content to validate

        Returns:
            tuple: (is_valid, list_of_errors)
        """
        errors = []

        # Length checks
        if len(content) < self.min_length:
            errors.append(
                f"Content too short: {len(content)} chars "
                f"(minimum: {self.min_length})"
            )

        if len(content) > self.max_length:
            errors.append(
                f"Content too long: {len(content)} chars "
                f"(maximum: {self.max_length})"
            )

        # Paragraph structure check
        if content.count('\n\n') < 2:
            errors.append(
                "Content lacks paragraph structure "
                "(needs at least 2 paragraph breaks)"
            )

        # Placeholder text check
        placeholders = ['[INSERT', 'TODO', 'PLACEHOLDER', '[TBD]']
        for placeholder in placeholders:
            if placeholder in content.upper():
                errors.append(
                    f"Content contains placeholder text: {placeholder}"
                )
                break  # Only report first placeholder

        return len(errors) == 0, errors


def validate_api_key() -> None:
    """Validate API key and raise error if invalid

    Raises:
        ValueError: If API key is invalid
    """
    validator = APIKeyValidator()
    is_valid, error = validator.validate()

    if not is_valid:
        raise ValueError(error)


def validate_content(
    content: str,
    min_length: int = 100,
    max_length: int = 10000
) -> None:
    """Validate content and raise error if invalid

    Args:
        content: Content to validate
        min_length: Minimum length
        max_length: Maximum length

    Raises:
        ValueError: If content is invalid
    """
    validator = ContentValidator(min_length, max_length)
    is_valid, errors = validator.validate(content)

    if not is_valid:
        raise ValueError(
            "Content validation failed:\n" +
            "\n".join(f"  - {err}" for err in errors)
        )
