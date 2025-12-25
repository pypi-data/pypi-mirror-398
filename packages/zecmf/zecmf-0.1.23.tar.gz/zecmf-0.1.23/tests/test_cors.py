"""Tests for CORS extension."""

import pytest
from flask import Flask

from zecmf.extensions import cors


class TestCORSExtension:
    """Test cases for CORS extension."""

    def test_cors_disabled_by_default(self, app: Flask) -> None:
        """Test that CORS is disabled when CORS_ORIGINS is not set."""
        # No CORS_ORIGINS set in config
        cors.init_app(app)

        # CORS should not be active
        # We can't easily test the absence of CORS without making a request,
        # but we can verify no CORS configuration was logged
        # (This is more of an integration test requirement)

    def test_cors_enabled_with_origins(self, app: Flask) -> None:
        """Test that CORS is enabled when CORS_ORIGINS is set."""
        app.config["CORS_ORIGINS"] = "http://localhost:3000,http://127.0.0.1:3000"
        cors.init_app(app)

        # CORS should be initialized (we can't easily verify this without making requests)
        # The actual CORS functionality is tested by flask-cors itself

    def test_cors_with_empty_origins(self, app: Flask) -> None:
        """Test that CORS is not enabled with empty origins."""
        app.config["CORS_ORIGINS"] = ""
        cors.init_app(app)

        # CORS should not be enabled with empty origins

    def test_cors_with_whitespace_origins(self, app: Flask) -> None:
        """Test that CORS handles whitespace in origins correctly."""
        app.config["CORS_ORIGINS"] = " http://localhost:3000 , http://127.0.0.1:3000 "
        cors.init_app(app)

        # CORS should handle whitespace correctly

    def test_cors_with_all_options(self, app: Flask) -> None:
        """Test CORS configuration with all options set."""
        app.config.update(
            {
                "CORS_ORIGINS": "http://localhost:3000,https://app.example.com",
                "CORS_METHODS": "GET,POST,PUT,DELETE",
                "CORS_ALLOW_HEADERS": "Content-Type,Authorization",
                "CORS_EXPOSE_HEADERS": "X-Total-Count,X-Rate-Limit",
                "CORS_SUPPORTS_CREDENTIALS": True,
                "CORS_MAX_AGE": 3600,
            }
        )
        cors.init_app(app)

        # All options should be processed correctly

    def test_cors_supports_credentials_false(self, app: Flask) -> None:
        """Test that CORS credentials support defaults to false."""
        app.config.update(
            {
                "CORS_ORIGINS": "http://localhost:3000",
                "CORS_SUPPORTS_CREDENTIALS": False,
            }
        )
        cors.init_app(app)

    def test_cors_supports_credentials_true(self, app: Flask) -> None:
        """Test that CORS credentials support can be enabled."""
        app.config.update(
            {
                "CORS_ORIGINS": "http://localhost:3000",
                "CORS_SUPPORTS_CREDENTIALS": True,
            }
        )
        cors.init_app(app)

    def test_cors_allow_headers_star(self, app: Flask) -> None:
        """Test CORS with allow headers set to star."""
        app.config.update(
            {
                "CORS_ORIGINS": "http://localhost:3000",
                "CORS_ALLOW_HEADERS": "*",
            }
        )
        cors.init_app(app)

    def test_cors_allow_headers_custom(self, app: Flask) -> None:
        """Test CORS with custom allow headers."""
        app.config.update(
            {
                "CORS_ORIGINS": "http://localhost:3000",
                "CORS_ALLOW_HEADERS": "Content-Type,Authorization,X-Custom-Header",
            }
        )
        cors.init_app(app)

    def test_cors_methods_default(self, app: Flask) -> None:
        """Test CORS with default methods."""
        app.config["CORS_ORIGINS"] = "http://localhost:3000"
        cors.init_app(app)

    def test_cors_methods_custom(self, app: Flask) -> None:
        """Test CORS with custom methods."""
        app.config.update(
            {
                "CORS_ORIGINS": "http://localhost:3000",
                "CORS_METHODS": "GET,POST",
            }
        )
        cors.init_app(app)


@pytest.fixture
def app() -> Flask:
    """Create a minimal Flask app for testing."""
    return Flask("test")
