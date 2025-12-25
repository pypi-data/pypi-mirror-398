"""Tests for configuration validation, particularly JWT public key validation."""

import pytest

from zecmf.config.base import BaseConfig


class _TestingConfig(BaseConfig):
    """Test configuration that skips validation during initialization."""

    SKIP_VALIDATION = True
    DEBUG = True
    SECRET_KEY = "test-secret"


class TestJWTPublicKeyValidation:
    """Test JWT public key format validation."""

    def test_valid_public_key_passes_validation(self) -> None:
        """Test that a properly formatted public key passes validation."""
        valid_key = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA1234567890abcdef
ghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdef
-----END PUBLIC KEY-----"""

        # Create a test config with minimal setup
        config = _TestingConfig()

        # This should not raise an exception
        config._validate_public_key_format(valid_key)

    def test_missing_begin_marker_raises_error(self) -> None:
        """Test that missing BEGIN marker raises a validation error."""
        invalid_key = """MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA1234567890abcdef
ghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdef
-----END PUBLIC KEY-----"""

        config = _TestingConfig()

        with pytest.raises(
            ValueError, match="must start with '-----BEGIN PUBLIC KEY-----'"
        ):
            config._validate_public_key_format(invalid_key)

    def test_missing_end_marker_raises_error(self) -> None:
        """Test that missing END marker raises a validation error."""
        invalid_key = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA1234567890abcdef
ghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdef"""

        config = _TestingConfig()

        with pytest.raises(
            ValueError, match="must end with '-----END PUBLIC KEY-----'"
        ):
            config._validate_public_key_format(invalid_key)

    def test_malformed_end_marker_raises_error(self) -> None:
        """Test that malformed END marker (like the user's case) raises a validation error."""
        # This is the exact case the user experienced: missing one dash
        invalid_key = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA1234567890abcdef
ghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdef
-----END PUBLIC KEY----"""

        config = _TestingConfig()

        with pytest.raises(
            ValueError, match="must end with '-----END PUBLIC KEY-----'"
        ):
            config._validate_public_key_format(invalid_key)

    def test_empty_key_content_raises_error(self) -> None:
        """Test that key with no content between markers raises a validation error."""
        invalid_key = """-----BEGIN PUBLIC KEY-----
-----END PUBLIC KEY-----"""

        config = _TestingConfig()

        with pytest.raises(ValueError, match="appears to be empty"):
            config._validate_public_key_format(invalid_key)

    def test_invalid_base64_content_raises_error(self) -> None:
        """Test that key with invalid base64 content raises a validation error."""
        invalid_key = """-----BEGIN PUBLIC KEY-----
This is not valid base64 content! @#$%^&*()
-----END PUBLIC KEY-----"""

        config = _TestingConfig()

        with pytest.raises(ValueError, match="contains invalid characters"):
            config._validate_public_key_format(invalid_key)

    def test_whitespace_is_handled_correctly(self) -> None:
        """Test that leading/trailing whitespace doesn't affect validation."""
        valid_key = """   -----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA1234567890abcdef
ghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdef
-----END PUBLIC KEY-----   """

        config = _TestingConfig()

        # This should not raise an exception
        config._validate_public_key_format(valid_key)


class TestRS256ConfigValidation:
    """Test RS256 configuration validation that includes public key validation."""

    def test_rs256_with_invalid_public_key_raises_error(self) -> None:
        """Test that RS256 config with invalid public key format raises error."""
        # Create a custom config class with the invalid key directly
        invalid_key = """-----BEGIN PUBLIC KEY-----
Invalid content here!
-----END PUBLIC KEY----"""  # Missing one dash at the end

        class TestConfig(BaseConfig):
            DEBUG = True
            SECRET_KEY = "test-secret"
            JWT_PUBLIC_KEY = invalid_key

        with pytest.raises(
            ValueError, match="must end with '-----END PUBLIC KEY-----'"
        ):
            TestConfig()

    def test_rs256_with_valid_public_key_succeeds(self) -> None:
        """Test that RS256 config with valid public key format succeeds."""
        valid_key = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA1234567890abcdef
ghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdef
-----END PUBLIC KEY-----"""

        class TestConfig(BaseConfig):
            DEBUG = True
            SECRET_KEY = "test-secret"
            JWT_PUBLIC_KEY = valid_key

        # This should not raise an exception
        config = TestConfig()
        assert valid_key == config.JWT_PUBLIC_KEY
        assert config.JWT_ALGORITHM == "RS256"
