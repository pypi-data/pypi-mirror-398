"""Answering Machine service schemas for typed query parameters."""

from dataclasses import dataclass
from typing import Any

from .client_requests import HttpQueryParams


@dataclass
class MessageCreateJsonRequest:
    """Typed request structure for message creation."""

    content: str
    message_type: str | None = None
    subject: str | None = None
    arguments: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: dict[str, Any] = {"content": self.content}

        if self.message_type is not None:
            result["message_type"] = self.message_type
        if self.subject is not None:
            result["subject"] = self.subject
        if self.arguments is not None:
            result["arguments"] = self.arguments

        return result


@dataclass
class MessageListQueryParams(HttpQueryParams):
    """Query parameters for listing messages."""

    page: int = 1
    per_page: int = 20
    read: bool | None = None
    agent_id: str | None = None
    message_type: str | None = None

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary for requests library, with special handling for boolean."""
        result = {"page": str(self.page), "per_page": str(self.per_page)}

        if self.read is not None:
            result["read"] = "true" if self.read else "false"
        if self.agent_id is not None:
            result["agent_id"] = self.agent_id
        if self.message_type is not None:
            result["message_type"] = self.message_type

        return result
