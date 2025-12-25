"""Answering Machine API client and data models for interacting with the Answering Machine service.

This module provides the AnsweringMachineClient class for communicating with the Answering Machine API, as well as dataclasses for MessageCreate and Message.
"""

from dataclasses import dataclass
from typing import Any

import requests
from flask import Flask

from zecmf.services.schemas.answering_machine import (
    MessageCreateJsonRequest,
    MessageListQueryParams,
)
from zecmf.services.schemas.client_requests import HttpRequestHeaders


@dataclass
class MessageCreate:
    """Represents a request payload for creating a message."""

    content: str
    message_type: str | None = None
    subject: str | None = None
    arguments: dict[str, Any] | None = None


@dataclass
class Message:
    """Represents a message returned by the Answering Machine API."""

    id: int
    content: str
    agent_id: str
    created_at: str
    read: bool
    message_type: str | None = None
    subject: str | None = None
    arguments: dict[str, Any] | None = None
    responded: bool | None = None


@dataclass
class MessageStats:
    """Represents message statistics returned by the API."""

    total: int
    read: int
    unread: int
    responded: int
    unreplied: int


class _AnsweringMachineConfig:
    """Singleton config holder for Answering Machine client settings."""

    base_url: str | None = None
    api_key: str | None = None
    timeout: int = 100

    @classmethod
    def set_config(cls, base_url: str, api_key: str, timeout: int = 100) -> None:
        cls.base_url = base_url
        cls.api_key = api_key
        cls.timeout = timeout

    @classmethod
    def is_configured(cls) -> bool:
        return cls.base_url is not None and cls.api_key is not None


def init_app(app: Flask) -> None:
    """Register the Flask app for Answering Machine client configuration."""
    base_url = app.config.get("CLIENT_ANSWERING_MACHINE_URL")
    api_key = app.config.get("CLIENT_ANSWERING_MACHINE_KEY")
    timeout = app.config.get("CLIENT_ANSWERING_MACHINE_TIMEOUT", 100)
    if not base_url:
        raise ValueError("CLIENT_ANSWERING_MACHINE_URL must be set in app config.")
    if not api_key:
        raise ValueError("CLIENT_ANSWERING_MACHINE_KEY must be set in app config.")
    _AnsweringMachineConfig.set_config(base_url, api_key, timeout)


class AnsweringMachineClient:
    """Client for interacting with the Answering Machine API endpoints."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: int | None = None,
    ) -> None:
        """Initialize the AnsweringMachineClient with configuration.

        Args:
            base_url: Optional base URL for the Answering Machine API.
            api_key: Optional API key for authentication.
            timeout: Optional request timeout in seconds.

        Raises:
            ValueError: If required configuration is missing.

        """
        self.base_url = None
        self.api_key = None
        self.timeout = None
        if base_url is not None:
            self.base_url = base_url
        elif (
            _AnsweringMachineConfig.is_configured()
            and _AnsweringMachineConfig.base_url is not None
        ):
            self.base_url = _AnsweringMachineConfig.base_url
        if api_key is not None:
            self.api_key = api_key
        elif (
            _AnsweringMachineConfig.is_configured()
            and _AnsweringMachineConfig.api_key is not None
        ):
            self.api_key = _AnsweringMachineConfig.api_key
        if timeout is not None:
            self.timeout = timeout
        elif (
            _AnsweringMachineConfig.is_configured()
            and _AnsweringMachineConfig.timeout is not None
        ):
            self.timeout = _AnsweringMachineConfig.timeout
        if not self.base_url:
            raise ValueError(
                "Answering Machine API base URL not configured (CLIENT_ANSWERING_MACHINE_URL)"
            )
        if not self.api_key:
            raise ValueError(
                "Answering Machine API key not configured (CLIENT_ANSWERING_MACHINE_KEY)"
            )

    def _headers(self) -> HttpRequestHeaders:
        return HttpRequestHeaders(authorization=f"Bearer {self.api_key}")

    def create_message(self, payload: MessageCreate) -> Message:
        """Create a new message (agent role required)."""
        json_request = MessageCreateJsonRequest(
            content=payload.content,
            message_type=payload.message_type,
            subject=payload.subject,
            arguments=payload.arguments,
        )

        resp = requests.post(
            f"{self.base_url}/api/v1/messages",
            headers=self._headers().to_dict(),
            json=json_request.to_dict(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return Message(**resp.json())

    def list_messages(
        self,
        read: bool | None = None,
        agent_id: str | None = None,
        message_type: str | None = None,
        page: int = 1,
        per_page: int = 10,
    ) -> list[Message]:
        """List all messages (user role required)."""
        query_params = MessageListQueryParams(
            page=page,
            per_page=per_page,
            read=read,
            agent_id=agent_id,
            message_type=message_type,
        )

        resp = requests.get(
            f"{self.base_url}/api/v1/messages",
            headers=self._headers().to_dict(),
            params=query_params.to_dict(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return [Message(**message) for message in resp.json()]

    def get_message(self, message_id: int) -> Message:
        """Get a specific message (user role required)."""
        resp = requests.get(
            f"{self.base_url}/api/v1/messages/{message_id}",
            headers=self._headers().to_dict(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return Message(**resp.json())

    def delete_message(self, message_id: int) -> None:
        """Delete a message (admin role required)."""
        resp = requests.delete(
            f"{self.base_url}/api/v1/messages/{message_id}",
            headers=self._headers().to_dict(),
            timeout=self.timeout,
        )
        resp.raise_for_status()

    def mark_message_responded(self, message_id: int) -> Message:
        """Mark a message as responded (user role required)."""
        resp = requests.patch(
            f"{self.base_url}/api/v1/messages/{message_id}/mark-responded",
            headers=self._headers().to_dict(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return Message(**resp.json())

    def get_message_stats(self) -> MessageStats:
        """Get message statistics (user role required)."""
        resp = requests.get(
            f"{self.base_url}/api/v1/messages/stats",
            headers=self._headers().to_dict(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return MessageStats(**resp.json())

    def get_message_types(self) -> list[str]:
        """Get available message types."""
        resp = requests.get(
            f"{self.base_url}/api/v1/messages/types",
            headers=self._headers().to_dict(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()
