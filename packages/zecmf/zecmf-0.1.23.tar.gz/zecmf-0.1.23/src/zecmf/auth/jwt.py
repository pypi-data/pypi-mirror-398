"""JWT authentication module for micro-framework."""

from collections.abc import Callable
from typing import Any, TypeVar

from flask import Flask, Response, current_app, g, request
from flask_jwt_extended import (
    JWTManager,
    get_jwt,
    get_jwt_identity,
    verify_jwt_in_request,
)
from flask_jwt_extended.exceptions import (
    CSRFError,
    FreshTokenRequired,
    InvalidHeaderError,
    InvalidQueryParamError,
    JWTDecodeError,
    NoAuthorizationError,
    RevokedTokenError,
    UserClaimsVerificationError,
    UserLookupError,
    WrongTokenError,
)
from jwt.exceptions import (
    DecodeError,
    ExpiredSignatureError,
    ImmatureSignatureError,
    InvalidAlgorithmError,
    InvalidAudienceError,
    InvalidIssuedAtError,
    InvalidIssuerError,
    InvalidJTIError,
    InvalidKeyError,
    InvalidSignatureError,
    InvalidSubjectError,
    InvalidTokenError,
    MissingCryptographyError,
    MissingRequiredClaimError,
    PyJWKClientConnectionError,
    PyJWKClientError,
    PyJWKError,
    PyJWKSetError,
    PyJWTError,
)
from werkzeug.exceptions import Unauthorized

# Type variable for generic functions
F = TypeVar("F", bound=Callable[..., Any])


jwt = JWTManager()


def _check_public_endpoint(endpoint_func: Callable[..., Any]) -> bool:
    """Check if an endpoint is marked as public."""
    # Check if it's a class-based view (like Flask-RESTX resources)
    if hasattr(endpoint_func, "view_class"):
        view_class = endpoint_func.view_class

        # Check class for the is_public attribute
        if hasattr(view_class, "is_public") and view_class.is_public:
            return True

        # Check the specific method for the is_public attribute
        method = request.method.lower()
        if hasattr(view_class, method):
            handler = getattr(view_class, method)
            if hasattr(handler, "is_public") and handler.is_public:
                return True

    # For regular function-based views
    elif hasattr(endpoint_func, "is_public") and endpoint_func.is_public:
        return True

    return False


def _unauthorized_with_debug(err: Exception, message: str, debug: bool) -> Unauthorized:
    """Return Unauthorized exception, optionally with debug data."""
    e = Unauthorized(message)
    if debug:
        e.data = {"message": message, "original_message": str(err)}  # type: ignore[attr-defined]
    return e


def _authenticate_request(debug: bool = False) -> None:  # noqa: C901, PLR0912, PLR0915
    """Authenticate the current request using JWT with granular error handling."""
    try:
        verify_jwt_in_request()

        # Get JWT claims
        claims = get_jwt()
        user_roles = claims.get("roles", [])

        # Store user info in flask g object for use in the request
        g.user_id = get_jwt_identity()
        g.user_roles = user_roles

    # Flask-JWT-Extended exceptions with custom messages
    except NoAuthorizationError as err:
        raise _unauthorized_with_debug(
            err, "Missing Authorization header or token", debug
        ) from err
    except InvalidHeaderError as err:
        raise _unauthorized_with_debug(
            err, "Invalid Authorization header", debug
        ) from err
    except WrongTokenError as err:
        raise _unauthorized_with_debug(err, "Wrong type of token", debug) from err
    except RevokedTokenError as err:
        raise _unauthorized_with_debug(err, "Token has been revoked", debug) from err
    except FreshTokenRequired as err:
        raise _unauthorized_with_debug(err, "Fresh token required", debug) from err
    except CSRFError as err:
        raise _unauthorized_with_debug(
            err, "CSRF token missing or invalid", debug
        ) from err
    except JWTDecodeError as err:
        raise _unauthorized_with_debug(err, "Failed to decode JWT", debug) from err
    except InvalidQueryParamError as err:
        raise _unauthorized_with_debug(
            err, "Invalid JWT in query parameter", debug
        ) from err
    except UserLookupError as err:
        raise _unauthorized_with_debug(err, "User not found", debug) from err
    except UserClaimsVerificationError as err:
        raise _unauthorized_with_debug(
            err, "User claims verification failed", debug
        ) from err

    # PyJWT exceptions with custom messages
    except ExpiredSignatureError as err:
        raise _unauthorized_with_debug(err, "JWT has expired", debug) from err
    except InvalidSignatureError as err:
        raise _unauthorized_with_debug(err, "JWT signature is invalid", debug) from err
    except DecodeError as err:
        raise _unauthorized_with_debug(err, "JWT decode error", debug) from err
    except InvalidAudienceError as err:
        raise _unauthorized_with_debug(err, "JWT audience is invalid", debug) from err
    except InvalidIssuerError as err:
        raise _unauthorized_with_debug(err, "JWT issuer is invalid", debug) from err
    except InvalidIssuedAtError as err:
        raise _unauthorized_with_debug(
            err, "JWT 'iat' claim is invalid", debug
        ) from err
    except ImmatureSignatureError as err:
        raise _unauthorized_with_debug(
            err, "JWT is not yet valid (nbf)", debug
        ) from err
    except InvalidKeyError as err:
        raise _unauthorized_with_debug(err, "JWT key is invalid", debug) from err
    except InvalidAlgorithmError as err:
        raise _unauthorized_with_debug(err, "JWT algorithm is invalid", debug) from err
    except MissingRequiredClaimError as err:
        raise _unauthorized_with_debug(err, str(err), debug) from err
    except InvalidSubjectError as err:
        raise _unauthorized_with_debug(err, "JWT subject is invalid", debug) from err
    except InvalidJTIError as err:
        raise _unauthorized_with_debug(err, "JWT JTI is invalid", debug) from err
    except MissingCryptographyError as err:
        raise _unauthorized_with_debug(
            err, "Cryptography library missing for JWT", debug
        ) from err
    except PyJWKError as err:
        raise _unauthorized_with_debug(err, "JWT JWK error", debug) from err
    except PyJWKSetError as err:
        raise _unauthorized_with_debug(err, "JWT JWK set error", debug) from err
    except PyJWKClientConnectionError as err:
        raise _unauthorized_with_debug(
            err, "JWT JWK client connection error", debug
        ) from err
    except PyJWKClientError as err:
        raise _unauthorized_with_debug(err, "JWT JWK client error", debug) from err
    except InvalidTokenError as err:
        raise _unauthorized_with_debug(err, "JWT is invalid", debug) from err
    except PyJWTError as err:
        raise _unauthorized_with_debug(err, "JWT error", debug) from err
    except Exception as err:
        raise _unauthorized_with_debug(
            err, "Unknown authentication error", debug
        ) from err


def init_jwt(app: Flask) -> None:
    """Initialize JWT manager with the Flask app."""
    jwt.init_app(app)

    # Register before_request handler to enforce authentication by default
    @app.before_request
    def enforce_authentication() -> Response | None:
        """Enforce authentication for each request unless marked as public."""
        # Skip OPTIONS requests for CORS support
        if request.method == "OPTIONS":
            return None

        # Allow access to swagger.json only in debug mode
        if app.debug and request.path.endswith("/swagger.json"):
            return None

        # Check if the endpoint is public
        if request.endpoint is not None:
            endpoint_func = current_app.view_functions.get(request.endpoint)
            if endpoint_func is not None and _check_public_endpoint(endpoint_func):
                return None

        # If we're here, authentication is required
        _authenticate_request(app.debug)
        return None
