"""Codebot service schemas for typed query parameters."""

from dataclasses import dataclass
from typing import Any

from .client_requests import HttpQueryParams


@dataclass
class ProfileListQueryParams(HttpQueryParams):
    """Query parameters for listing profiles."""

    sort: str | None = None
    order: str | None = None


@dataclass
class ProfileJsonRequest:
    """Typed request structure for profile creation/update."""

    name: str
    assistant_type: str
    docker_image: str
    claude_auth_type: str | None = None
    api_key: str | None = None
    claude_auth_token: str | None = None
    claude_refresh_token: str | None = None
    claude_token_expires_at: str | None = None
    claude_subscription_type: str | None = None
    claude_account_uuid: str | None = None
    claude_account_email: str | None = None
    claude_organization_uuid: str | None = None
    claude_organization_name: str | None = None
    claude_organization_role: str | None = None
    claude_workspace_role: str | None = None
    model: str | None = None
    openai_organization: str | None = None
    mcp_config: dict[str, Any] | None = None
    environment_variables: list[dict[str, str]] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: dict[str, Any] = {
            "name": self.name,
            "assistant_type": self.assistant_type,
            "docker_image": self.docker_image,
        }

        # Add optional fields if they have values
        optional_fields = [
            "claude_auth_type",
            "api_key",
            "claude_auth_token",
            "claude_refresh_token",
            "claude_token_expires_at",
            "claude_subscription_type",
            "claude_account_uuid",
            "claude_account_email",
            "claude_organization_uuid",
            "claude_organization_name",
            "claude_organization_role",
            "claude_workspace_role",
            "model",
            "openai_organization",
            "mcp_config",
            "environment_variables",
        ]

        for field in optional_fields:
            value = getattr(self, field)
            if value is not None:
                result[field] = value

        return result


@dataclass
class TaskCreateJsonRequest:
    """Typed request structure for task creation."""

    profile_id: int
    instructions: str
    workspace_path: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "profile_id": self.profile_id,
            "instructions": self.instructions,
            "workspace_path": self.workspace_path,
        }
