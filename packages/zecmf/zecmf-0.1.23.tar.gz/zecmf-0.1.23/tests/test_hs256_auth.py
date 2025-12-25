"""Tests for HS256 JWT authentication functionality."""

from http import HTTPStatus

import pytest
from flask import Flask, Response, jsonify
from flask.testing import FlaskClient
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity

from zecmf import create_app
from zecmf.auth.decorators import public_endpoint, require_role


@pytest.fixture
def hs256_app() -> Flask:
    """Create a Flask application with HS256 JWT auth for testing."""
    test_app = create_app("testing", [], app_config_module="zecmf.config")

    # Configure app to use HS256 authentication
    test_app.config["JWT_ALGORITHM"] = "HS256"
    test_app.config["JWT_SECRET_KEY"] = "test-hs256-secret-key"

    # Add test routes
    @test_app.route("/protected")
    def protected_route() -> Response:
        """Protected route requiring authentication."""
        # Get JWT claims and user info to verify they're properly set
        current_user = get_jwt_identity()
        jwt_claims = get_jwt()

        return jsonify(
            {
                "status": "authenticated",
                "user_id": current_user,
                "roles": jwt_claims.get("roles", []),
            }
        )

    @test_app.route("/public")
    @public_endpoint()
    def public_route() -> Response:
        """Public route that doesn't require authentication."""
        return jsonify({"status": "public"})

    @test_app.route("/admin-only")
    @require_role("admin")
    def admin_route() -> Response:
        """Route requiring admin role."""
        return jsonify({"status": "admin access"})

    @test_app.route("/user-only")
    @require_role("user")
    def user_route() -> Response:
        """Route requiring user role."""
        return jsonify({"status": "user access"})

    @test_app.route("/multi-role")
    @require_role("admin")
    @require_role("user")
    def multi_role_route() -> Response:
        """Route requiring both admin and user roles."""
        return jsonify({"status": "multi-role access"})

    return test_app


@pytest.fixture
def hs256_client(hs256_app: Flask) -> FlaskClient:
    """Create a test client for the auth application."""
    return hs256_app.test_client()


@pytest.fixture
def admin_token(hs256_app: Flask) -> str:
    """Create a JWT token with admin role."""
    with hs256_app.app_context():
        return create_access_token(
            identity="admin-user", additional_claims={"roles": ["admin", "user"]}
        )


@pytest.fixture
def user_token(hs256_app: Flask) -> str:
    """Create a JWT token with user role only."""
    with hs256_app.app_context():
        return create_access_token(
            identity="regular-user", additional_claims={"roles": ["user"]}
        )


@pytest.fixture
def no_roles_token(hs256_app: Flask) -> str:
    """Create a JWT token with no roles."""
    with hs256_app.app_context():
        return create_access_token(
            identity="no-roles-user", additional_claims={"roles": []}
        )


def test_hs256_algorithm_configured(hs256_app: Flask) -> None:
    """Test that HS256 algorithm is properly configured."""
    assert hs256_app.config["JWT_ALGORITHM"] == "HS256"
    assert hs256_app.config["JWT_SECRET_KEY"] == "test-hs256-secret-key"


def test_protected_route_without_token(hs256_client: FlaskClient) -> None:
    """Test that protected routes require authentication."""
    response = hs256_client.get("/protected")
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert b"Missing Authorization header or token" in response.data


def test_protected_route_with_token(hs256_client: FlaskClient, user_token: str) -> None:
    """Test accessing a protected route with a valid token."""
    response = hs256_client.get(
        "/protected", headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json or {}

    # Verify the response contains the correct user info
    assert data["status"] == "authenticated"
    assert data["user_id"] == "regular-user"
    assert "user" in data["roles"]
    assert "admin" not in data["roles"]


def test_protected_route_with_admin_token(
    hs256_client: FlaskClient, admin_token: str
) -> None:
    """Test accessing a protected route with an admin token."""
    response = hs256_client.get(
        "/protected", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json or {}

    # Verify the response contains the correct user info with both roles
    assert data["status"] == "authenticated"
    assert data["user_id"] == "admin-user"
    assert "user" in data["roles"]
    assert "admin" in data["roles"]


def test_public_route_without_token(hs256_client: FlaskClient) -> None:
    """Test that public routes don't require authentication."""
    response = hs256_client.get("/public")
    assert response.status_code == HTTPStatus.OK
    assert response.json
    assert response.json["status"] == "public"


def test_role_based_access_admin_success(
    hs256_client: FlaskClient, admin_token: str
) -> None:
    """Test that admin can access admin-only routes."""
    response = hs256_client.get(
        "/admin-only", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json
    assert response.json["status"] == "admin access"


def test_role_based_access_user_failure(
    hs256_client: FlaskClient, user_token: str
) -> None:
    """Test that regular user cannot access admin-only routes."""
    response = hs256_client.get(
        "/admin-only", headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert b"Requires role: admin" in response.data


def test_user_route_with_admin_token(
    hs256_client: FlaskClient, admin_token: str
) -> None:
    """Test that admin with user role can access user-only routes."""
    response = hs256_client.get(
        "/user-only", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json
    assert response.json["status"] == "user access"


def test_user_route_with_user_token(hs256_client: FlaskClient, user_token: str) -> None:
    """Test that user can access user-only routes."""
    response = hs256_client.get(
        "/user-only", headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json
    assert response.json["status"] == "user access"


def test_multi_role_route_requires_both_roles(
    hs256_client: FlaskClient, user_token: str, admin_token: str, no_roles_token: str
) -> None:
    """Test that multi-role route requires both admin and user roles."""
    # Test with user role only - should fail
    response = hs256_client.get(
        "/multi-role", headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert b"Requires role: admin" in response.data

    # Test with no roles - should fail
    response = hs256_client.get(
        "/multi-role", headers={"Authorization": f"Bearer {no_roles_token}"}
    )
    assert response.status_code == HTTPStatus.FORBIDDEN

    # Test with admin role (which includes user role) - should succeed
    response = hs256_client.get(
        "/multi-role", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json
    assert response.json["status"] == "multi-role access"


def test_swagger_requires_auth(hs256_client: FlaskClient) -> None:
    """Test that Swagger docs require authentication in the refactored framework."""
    response = hs256_client.get("/api/v1/swagger.json")
    # In the refactored framework, Swagger docs require authentication
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_options_requests_bypass_auth(hs256_client: FlaskClient) -> None:
    """Test that OPTIONS requests bypass authentication."""
    response = hs256_client.options("/protected")
    # OPTIONS should pass through without 401
    assert response.status_code != HTTPStatus.UNAUTHORIZED
