"""Tests for API functionality with Flask-RESTX integration."""

from flask import Flask
from flask_restx import Api

from zecmf.api import init_api


def test_api_initialization() -> None:
    """Test API initialization with basic config."""
    app = Flask("test")
    app.config["API_TITLE"] = "Test API"
    app.config["API_VERSION"] = "1.0"
    app.config["API_PREFIX"] = "/v2"
    api = init_api(app)

    # Verify API was created
    assert api is not None
    assert isinstance(api, Api)

    # Check api was registered as a blueprint
    assert "api" in app.blueprints

    # Verify blueprint has the custom prefix
    assert app.blueprints["api"].url_prefix == "/v2"

    # Check configuration was applied from app.config
    assert api.authorizations == {
        "Bearer": {"type": "apiKey", "in": "header", "name": "Authorization"}
    }
    assert api.security == "Bearer"
    assert api.title == "Test API"
    assert api.version == "1.0"

    # The API instance should be accessible via Flask's extensions for
    # utilities that need direct access (e.g., swagger extraction).
    assert app.extensions["restx/api"] is api
