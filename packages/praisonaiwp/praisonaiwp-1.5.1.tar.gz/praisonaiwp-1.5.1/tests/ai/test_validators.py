"""Tests for AI validators and utilities"""
import os
from unittest.mock import patch

import pytest

from praisonaiwp.ai.utils.validators import (
    APIKeyValidator,
    ContentValidator,
    validate_api_key,
    validate_content,
)


class TestAPIKeyValidator:
    """Test API key validation"""

    def test_validate_missing_key(self):
        """Test error when API key is missing"""
        with patch.dict(os.environ, {}, clear=True):
            validator = APIKeyValidator()
            is_valid, error = validator.validate()
            assert not is_valid
            assert "OPENAI_API_KEY not set" in error

    def test_validate_invalid_format(self):
        """Test error for invalid key format"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'invalid-key'}):
            validator = APIKeyValidator()
            is_valid, error = validator.validate()
            assert not is_valid
            assert "Invalid format" in error

    def test_validate_valid_format(self):
        """Test valid key format"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test123'}):
            validator = APIKeyValidator()
            is_valid, error = validator.validate()
            assert is_valid
            assert error is None

    def test_validate_function(self):
        """Test standalone validate function"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                validate_api_key()
            assert "OPENAI_API_KEY" in str(exc_info.value)


class TestContentValidator:
    """Test content validation"""

    def test_validate_too_short(self):
        """Test content too short"""
        validator = ContentValidator(min_length=100)
        is_valid, errors = validator.validate("Short content")
        assert not is_valid
        assert any("too short" in err.lower() for err in errors)

    def test_validate_too_long(self):
        """Test content too long"""
        validator = ContentValidator(max_length=100)
        content = "x" * 200
        is_valid, errors = validator.validate(content)
        assert not is_valid
        assert any("too long" in err.lower() for err in errors)

    def test_validate_valid_length(self):
        """Test valid content length"""
        validator = ContentValidator(min_length=10, max_length=1000)
        content = ("First paragraph with content.\n\n"
                   "Second paragraph with more content.\n\n"
                   "Third paragraph to complete the post.")
        is_valid, errors = validator.validate(content)
        assert is_valid
        assert len(errors) == 0

    def test_validate_no_paragraphs(self):
        """Test content without paragraph structure"""
        validator = ContentValidator(min_length=10)
        content = "This is all one paragraph without breaks"
        is_valid, errors = validator.validate(content)
        assert not is_valid
        assert any("paragraph" in err.lower() for err in errors)

    def test_validate_with_paragraphs(self):
        """Test content with proper paragraphs"""
        validator = ContentValidator(min_length=10)
        content = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        is_valid, errors = validator.validate(content)
        assert is_valid

    def test_validate_placeholder_text(self):
        """Test detection of placeholder text"""
        validator = ContentValidator(min_length=10)
        content = "This has [INSERT TEXT HERE] placeholder.\n\nAnother paragraph."
        is_valid, errors = validator.validate(content)
        assert not is_valid
        assert any("placeholder" in err.lower() for err in errors)

    def test_validate_function(self):
        """Test standalone validate function"""
        content = "x" * 50
        with pytest.raises(ValueError) as exc_info:
            validate_content(content, min_length=100)
        assert "too short" in str(exc_info.value).lower()

    def test_validate_multiple_errors(self):
        """Test multiple validation errors"""
        validator = ContentValidator(min_length=100, max_length=1000)
        content = "Short [TODO] content"
        is_valid, errors = validator.validate(content)
        assert not is_valid
        assert len(errors) >= 2  # Too short + placeholder
