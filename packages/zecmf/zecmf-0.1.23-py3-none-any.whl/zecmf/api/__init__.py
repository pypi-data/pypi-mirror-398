"""API module for Flask-RESTX integration."""

from typing import Any

from flask import Blueprint, Flask
from flask_restx import Api


def init_api(
    app: Flask,
) -> Api:
    """Initialize the API on the Flask app.

    Args:
        app: The Flask application

    Returns:
        The configured API instance

    """
    # Get API configuration from app.config with defaults
    prefix = app.config.get("API_PREFIX", "/api")
    title = app.config.get("API_TITLE", "API")
    version = app.config.get("API_VERSION", "1.0.0")
    description = app.config.get("API_DESCRIPTION", "...")

    # Create API blueprint with prefix
    blueprint = Blueprint("api", __name__, url_prefix=prefix)

    # Configure API with provided settings
    api_config: dict[str, Any] = {
        "doc": False,
        "authorizations": {
            "Bearer": {"type": "apiKey", "in": "header", "name": "Authorization"}
        },
        "security": "Bearer",
        "title": title,
        "version": version,
        "description": description,
    }

    # Create and register API
    api = Api(blueprint, **api_config)
    app.register_blueprint(blueprint)

    # Store API instance for later access (e.g., CLI commands)
    # Flask-RESTX only stores internal state in ``app.extensions['restx']``
    # which doesn't expose the ``Api`` object itself.  Persist the Api
    # instance under a separate key so utilities like ``extract-swagger`` can
    # retrieve the schema without making HTTP requests.
    app.extensions["restx/api"] = api

    return api


__all__ = ["init_api"]
