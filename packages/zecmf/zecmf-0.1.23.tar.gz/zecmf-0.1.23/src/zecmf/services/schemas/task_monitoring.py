"""Task monitoring service schemas for internal data structures."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Literal


class ContextType(StrEnum):
    """Supported task context types."""

    PROJECT = "project"
    USER = "user"
    ORGANIZATION = "organization"
    GENERIC = "generic"


@dataclass
class TaskContext:
    """Explicit task context for linking tasks to domain objects.

    Use this to explicitly specify task context instead of relying on
    automatic extraction from arguments.
    """

    context_id: int
    context_type: ContextType | str
    context_step: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "context_id": self.context_id,
            "context_type": self.context_type.value
            if isinstance(self.context_type, ContextType)
            else self.context_type,
            "context_step": self.context_step,
        }


@dataclass
class RetryStrategy:
    """Configuration for task retry behavior."""

    max_retries: int = 3
    base_delay_seconds: int = 60
    strategy: Literal["exponential", "linear", "constant"] = "exponential"

    def calculate_countdown(self, current_retry: int) -> int:
        """Calculate delay before next retry attempt."""
        if self.strategy == "exponential":
            return self.base_delay_seconds * (2**current_retry)
        elif self.strategy == "linear":
            return self.base_delay_seconds * (current_retry + 1)
        else:  # constant
            return self.base_delay_seconds


@dataclass
class ExceptionContext:
    """Typed structure for exception context information."""

    exception_type: str | None = None
    exception_message: str | None = None
    traceback: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {}
        if self.exception_type is not None:
            result["exception_type"] = self.exception_type
        if self.exception_message is not None:
            result["exception_message"] = self.exception_message
        if self.traceback is not None:
            result["traceback"] = self.traceback
        return result

    def is_empty(self) -> bool:
        """Check if the exception context is empty."""
        return (
            self.exception_type is None
            and self.exception_message is None
            and self.traceback is None
        )


class TaskError(Exception):
    """Raise this exception to mark a task as failed with proper tracking.

    This exception will be caught by the monitoring system and properly
    logged with full context. It supports retry based on the task's
    retry strategy.
    """

    def __init__(
        self, message: str, context: dict[str, Any] | None = None, retry: bool = True
    ) -> None:
        """Initialize task error.

        Args:
            message: Error description
            context: Additional context data
            retry: Whether this error should trigger a retry

        """
        super().__init__(message)
        self.context = context or {}
        self.should_retry = retry
