"""LLM service schemas for typed query parameters."""

from dataclasses import dataclass
from typing import Any

from .client_requests import HttpQueryParams


@dataclass
class ProvidersListQueryParams(HttpQueryParams):
    """Query parameters for listing providers."""

    search: str | None = None
    active_only: bool = True

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary for requests library."""
        result = {"active_only": str(self.active_only).lower()}

        if self.search is not None:
            result["search"] = self.search

        return result


@dataclass
class ModelsListQueryParams(HttpQueryParams):
    """Query parameters for listing models."""

    provider_id: int | None = None
    search: str | None = None
    active_only: bool = True

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary for requests library."""
        result = {"active_only": str(self.active_only).lower()}

        if self.provider_id is not None:
            result["provider_id"] = str(self.provider_id)
        if self.search is not None:
            result["search"] = self.search

        return result


@dataclass
class CompletionCreateRequest:
    """Typed request structure for completion creation."""

    messages: list[dict[str, Any]]
    model_id: int
    stream: bool = False
    max_tokens: int | None = None
    temperature: float | None = None
    top_p: float | None = None
    frequency_penalty: float | None = None
    presence_penalty: float | None = None
    stop: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "messages": self.messages,
            "model_id": self.model_id,
            "stream": self.stream,
        }

        # Add optional fields
        optional_fields = [
            "max_tokens",
            "temperature",
            "top_p",
            "frequency_penalty",
            "presence_penalty",
            "stop",
        ]

        for field in optional_fields:
            value = getattr(self, field)
            if value is not None:
                result[field] = value

        return result
