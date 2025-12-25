"""Authentication decorators for role-based access control."""

from collections.abc import Callable, Sequence
from functools import wraps
from typing import Any, TypeVar, cast

from flask import g
from werkzeug.exceptions import Forbidden

# Type variable for generic functions
F = TypeVar("F", bound=Callable[..., Any])


class DecoratorFactory:
    """Factory to create decorators only when needed in a request context."""

    @staticmethod
    def require_role(role: str) -> Callable[[F], F]:
        """Create a decorator to require a specific role."""

        def decorator(f: F) -> F:
            @wraps(f)
            def wrapper(*args: object, **kwargs: object) -> object:
                # Check if user has the required role
                if not hasattr(g, "user_roles") or role not in g.user_roles:
                    raise Forbidden(f"Requires role: {role}")

                return f(*args, **kwargs)

            return cast("F", wrapper)

        return decorator

    @staticmethod
    def require_roles(roles: Sequence[str]) -> Callable[[F], F]:
        """Create a decorator to require all of the specified roles."""

        def decorator(f: F) -> F:
            @wraps(f)
            def wrapper(*args: object, **kwargs: object) -> object:
                # Check if user has all the required roles
                if not hasattr(g, "user_roles"):
                    raise Forbidden(f"Requires all roles: {', '.join(roles)}")

                user_roles = set(g.user_roles)
                required_roles = set(roles)
                missing_roles = required_roles - user_roles

                if missing_roles:
                    raise Forbidden(
                        f"Requires all roles: {', '.join(sorted(missing_roles))}"
                    )

                return f(*args, **kwargs)

            return cast("F", wrapper)

        return decorator

    @staticmethod
    def require_any_role(roles: Sequence[str]) -> Callable[[F], F]:
        """Create a decorator to require at least one of the specified roles."""

        def decorator(f: F) -> F:
            @wraps(f)
            def wrapper(*args: object, **kwargs: object) -> object:
                # Check if user has at least one of the required roles
                if not hasattr(g, "user_roles"):
                    raise Forbidden(f"Requires one of roles: {', '.join(roles)}")

                user_roles = set(g.user_roles)
                required_roles = set(roles)

                if not user_roles.intersection(required_roles):
                    raise Forbidden(
                        f"Requires one of roles: {', '.join(sorted(roles))}"
                    )

                return f(*args, **kwargs)

            return cast("F", wrapper)

        return decorator

    @staticmethod
    def public_endpoint() -> Callable[[F], F]:
        """Create a decorator to mark an endpoint as public.

        This decorator can be applied to:
        - Regular Flask routes (function-based views)
        - Specific HTTP methods in Flask-RESTX Resources (apply to method)

        Note: For Flask-RESTX Resource classes, do not apply this decorator directly to
        the class. Instead, apply it to individual methods.
        """

        def decorator(f: F) -> F:
            # Mark the original function as public
            f.is_public = True  # type: ignore

            @wraps(f)
            def wrapper(*args: object, **kwargs: object) -> object:
                return f(*args, **kwargs)

            # Mark the wrapper function as public
            wrapper.is_public = True  # type: ignore

            return cast("F", wrapper)

        return decorator


# Create decorator factory instance
decorator_factory = DecoratorFactory()


def require_role(role: str) -> Callable[[F], F]:
    """Require a specific role for an endpoint."""
    return decorator_factory.require_role(role)


def require_roles(roles: Sequence[str]) -> Callable[[F], F]:
    """Require all of the specified roles for an endpoint."""
    return decorator_factory.require_roles(roles)


def require_any_role(roles: Sequence[str]) -> Callable[[F], F]:
    """Require at least one of the specified roles for an endpoint."""
    return decorator_factory.require_any_role(roles)


def public_endpoint() -> Callable[[F], F]:
    """Mark an endpoint as public, exempt from authentication requirements."""
    return decorator_factory.public_endpoint()


# Pre-defined role decorators for convenience
require_admin_role = require_role("admin")
require_user_role = require_role("user")
require_agent_role = require_role("agent")
