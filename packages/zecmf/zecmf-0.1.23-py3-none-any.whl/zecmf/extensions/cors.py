"""CORS extension module.

Provides optional CORS support for ZecMF applications via Flask configuration.
"""

from typing import Any

from flask import Flask
from flask_cors import CORS


def _parse_comma_separated_list(value: str | None) -> list[str]:
    """Parse a comma-separated string into a list of stripped values.

    Args:
        value: Comma-separated string or None.

    Returns:
        List of stripped values, empty if input is None or empty.

    """
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_allow_headers(cors_allow_headers: str) -> list[str] | str | None:
    """Parse CORS_ALLOW_HEADERS configuration value.

    Args:
        cors_allow_headers: The allow headers value.

    Returns:
        List of headers, "*" for all headers, or None for default.

    """
    if cors_allow_headers == "*":
        return "*"
    if cors_allow_headers:
        return _parse_comma_separated_list(cors_allow_headers)
    return None


def _build_cors_config(
    origins_list: list[str],
    methods_list: list[str],
    allow_headers: list[str] | str | None,
    expose_headers_list: list[str] | None,
    supports_credentials: bool,
    max_age_value: int | None,
) -> dict[str, Any]:
    """Build CORS configuration dictionary.

    Args:
        origins_list: List of allowed origins.
        methods_list: List of allowed methods.
        allow_headers: Allowed headers (list, "*", or None).
        expose_headers_list: Headers to expose or None.
        supports_credentials: Whether to support credentials.
        max_age_value: Max age value or None.

    Returns:
        CORS configuration dictionary.

    """
    cors_config: dict[str, Any] = {
        "origins": origins_list,
        "methods": methods_list,
        "supports_credentials": supports_credentials,
    }

    if allow_headers is not None:
        cors_config["allow_headers"] = allow_headers

    if expose_headers_list is not None:
        cors_config["expose_headers"] = expose_headers_list

    if max_age_value is not None:
        cors_config["max_age"] = max_age_value

    return cors_config


def init_app(app: Flask) -> None:
    """Initialize CORS extension if enabled via Flask configuration.

    CORS is only enabled if the CORS_ORIGINS configuration value is set.
    If CORS_ORIGINS is not set, CORS will not be enabled.

    Configuration values (can be set in config classes or environment variables):
        CORS_ORIGINS: Comma-separated list of allowed origins.
                     If not set, CORS is disabled.
        CORS_METHODS: Comma-separated list of allowed methods.
                     Defaults to "GET,HEAD,PUT,PATCH,POST,DELETE,OPTIONS"
        CORS_ALLOW_HEADERS: Comma-separated list of allowed headers.
                           Defaults to "*"
        CORS_EXPOSE_HEADERS: Comma-separated list of headers to expose.
                            Defaults to None
        CORS_SUPPORTS_CREDENTIALS: Whether to support credentials.
                                  Defaults to False
        CORS_MAX_AGE: Maximum age for preflight cache in seconds.
                     Defaults to None

    Args:
        app: The Flask application.

    """
    # Only enable CORS if CORS_ORIGINS is explicitly set in configuration
    cors_origins = app.config.get("CORS_ORIGINS")
    if not cors_origins:
        return

    # Parse origins
    origins_list = _parse_comma_separated_list(cors_origins)
    if not origins_list:
        return

    # Parse CORS configuration from Flask config
    methods_list = _parse_comma_separated_list(app.config.get("CORS_METHODS"))
    allow_headers = _parse_allow_headers(app.config.get("CORS_ALLOW_HEADERS", "*"))
    expose_headers_list = _parse_comma_separated_list(
        app.config.get("CORS_EXPOSE_HEADERS")
    )
    supports_credentials = app.config.get("CORS_SUPPORTS_CREDENTIALS", False)
    max_age_value = app.config.get("CORS_MAX_AGE")

    # Build and apply CORS configuration
    cors_config = _build_cors_config(
        origins_list,
        methods_list,
        allow_headers,
        expose_headers_list,
        supports_credentials,
        max_age_value,
    )

    CORS(app, **cors_config)
    app.logger.info(f"CORS enabled with origins: {origins_list}")
