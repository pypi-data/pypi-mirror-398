"""Tests for JWT initialization and functionality."""

from http import HTTPStatus

import pytest
from flask import Flask, Response, jsonify
from flask_jwt_extended import (
    create_access_token,
    get_jwt,
    get_jwt_identity,
    verify_jwt_in_request,
)

from zecmf.auth import init_jwt


def test_jwt_initialization() -> None:
    """Test that JWT is properly initialized with the application."""
    app = Flask("test")
    app.config["JWT_SECRET_KEY"] = "test-secret"
    app.config["JWT_ALGORITHM"] = "HS256"  # Use HS256 for testing

    init_jwt(app)

    assert "flask-jwt-extended" in app.extensions


@pytest.mark.parametrize(
    ("auth_header", "expected_status"),
    [
        (None, HTTPStatus.UNAUTHORIZED),  # No token
        ("Not a real token", HTTPStatus.UNAUTHORIZED),  # Invalid format
        ("Bearer invalid.token.format", HTTPStatus.UNAUTHORIZED),  # Invalid token
    ],
)
def test_jwt_invalid_tokens(auth_header: str | None, expected_status: int) -> None:
    """Test handling of various invalid token scenarios."""
    # Create a test app with JWT configured
    app = Flask("test")
    app.config["JWT_SECRET_KEY"] = "test-secret"
    app.config["JWT_ALGORITHM"] = "HS256"  # Use HS256 for testing
    init_jwt(app)

    @app.route("/protected")
    def protected() -> Response:
        verify_jwt_in_request()
        return jsonify({"status": "authenticated"})

    # Test client
    client = app.test_client()
    headers = {"Authorization": auth_header} if auth_header else {}

    response = client.get("/protected", headers=headers)
    assert response.status_code == expected_status


def test_jwt_user_identity_and_roles() -> None:
    """Test that user identity and roles are properly extracted from JWT."""
    # Create a test app with JWT configured
    app = Flask("test")
    app.config["JWT_SECRET_KEY"] = "test-secret"
    app.config["JWT_ALGORITHM"] = "HS256"  # Use HS256 for testing
    init_jwt(app)

    # Add a test route that accesses JWT identity and claims
    @app.route("/user-info")
    def user_info() -> Response:
        verify_jwt_in_request()
        # Access identity and claims
        claims = get_jwt()
        return jsonify(
            {
                "user_id": get_jwt_identity(),
                "roles": claims.get("roles", []),
            }
        )

    # Create a token with identity and roles
    with app.app_context():
        token = create_access_token(
            identity="test-user", additional_claims={"roles": ["admin", "user"]}
        )

    # Test client
    client = app.test_client()

    # Make request with token
    response = client.get("/user-info", headers={"Authorization": f"Bearer {token}"})

    # Verify response
    assert response.status_code == HTTPStatus.OK
    data = response.json or {}
    assert data["user_id"] == "test-user"
    assert "admin" in data["roles"]
    assert "user" in data["roles"]
