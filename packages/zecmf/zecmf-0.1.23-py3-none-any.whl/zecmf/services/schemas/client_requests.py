"""Schemas for HTTP client request structures."""

from dataclasses import dataclass


@dataclass
class HttpRequestHeaders:
    """Typed headers for HTTP requests."""

    authorization: str
    content_type: str = "application/json"
    accept: str = "application/json"

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary for requests library."""
        return {
            "Authorization": self.authorization,
            "Content-Type": self.content_type,
            "Accept": self.accept,
        }


@dataclass
class HttpQueryParams:
    """Base class for typed query parameters."""

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary for requests library, excluding None values."""
        result = {}
        for key, value in self.__dict__.items():
            if value is not None:
                result[key] = str(value)
        return result
