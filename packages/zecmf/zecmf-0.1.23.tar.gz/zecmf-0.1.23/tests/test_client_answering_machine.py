"""Tests for the AnsweringMachineClient and related configuration logic."""

import pytest
import requests
from flask import Flask

from zecmf.clients import answering_machine
from zecmf.clients.answering_machine import (
    AnsweringMachineClient,
    MessageCreate,
    _AnsweringMachineConfig,  # noqa: PLC2701
)

HTTP_ERROR_STATUS = 400
EXPECTED_MESSAGE_COUNT = 2
EXPECTED_MESSAGE_ID_1 = 1
EXPECTED_MESSAGE_ID_2 = 2
EXPECTED_TOTAL_STATS = 100
EXPECTED_READ_STATS = 75
EXPECTED_UNREAD_STATS = 25
EXPECTED_RESPONDED_STATS = 60
EXPECTED_UNREPLIED_STATS = 40


class DummyResponse:
    """A dummy response object to mock requests.Response for testing."""

    def __init__(self, json_data: object, status_code: int = 201) -> None:
        """Initialize DummyResponse.

        Args:
            json_data: The JSON data to return from .json().
            status_code: The HTTP status code to simulate.

        """
        self._json = json_data
        self.status_code = status_code
        self.text = str(json_data)

    def json(self) -> object:
        """Return the stored JSON data."""
        return self._json

    def raise_for_status(self) -> None:
        """Raise HTTPError if status code indicates an error."""
        if self.status_code >= HTTP_ERROR_STATUS:
            raise requests.exceptions.HTTPError(response=None)  # type: ignore[arg-type]


TIMEOUT_APP_CONFIG = 42
TIMEOUT_DIRECT_ARGS = 5


def test_answering_machine_client_init_with_app(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test initialization of AnsweringMachineClient using Flask app config."""
    app = Flask("test")
    app.config["CLIENT_ANSWERING_MACHINE_URL"] = "https://am.example.com"
    app.config["CLIENT_ANSWERING_MACHINE_KEY"] = "test-key"
    app.config["CLIENT_ANSWERING_MACHINE_TIMEOUT"] = TIMEOUT_APP_CONFIG
    answering_machine.init_app(app)
    client = AnsweringMachineClient()
    assert client.base_url == "https://am.example.com"
    assert client.api_key == "test-key"
    assert client.timeout == TIMEOUT_APP_CONFIG


def test_answering_machine_client_init_with_direct_args() -> None:
    """Test initialization of AnsweringMachineClient using direct arguments."""
    client = AnsweringMachineClient(
        base_url="https://direct.example.com",
        api_key="direct-key",
        timeout=TIMEOUT_DIRECT_ARGS,
    )
    assert client.base_url == "https://direct.example.com"
    assert client.api_key == "direct-key"
    assert client.timeout == TIMEOUT_DIRECT_ARGS


def test_answering_machine_client_init_missing_config() -> None:
    """Test that missing configuration raises ValueError."""
    _AnsweringMachineConfig.base_url = None
    _AnsweringMachineConfig.api_key = None
    _AnsweringMachineConfig.timeout = 100
    with pytest.raises(
        ValueError, match="Answering Machine API base URL not configured"
    ):
        AnsweringMachineClient()


def test_answering_machine_client_create_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test creating a message using the AnsweringMachineClient."""
    app = Flask("test")
    app.config["CLIENT_ANSWERING_MACHINE_URL"] = "https://am.example.com"
    app.config["CLIENT_ANSWERING_MACHINE_KEY"] = "test-key"
    answering_machine.init_app(app)
    client = AnsweringMachineClient()
    message_data = {
        "id": 1,
        "content": "Hello!",
        "agent_id": "agent-123",
        "created_at": "2025-05-28T12:00:00Z",
        "read": False,
    }
    monkeypatch.setattr(requests, "post", lambda *a, **k: DummyResponse(message_data))
    req = MessageCreate(content="Hello!")
    resp = client.create_message(req)
    assert resp.id == 1
    assert resp.content == "Hello!"
    assert resp.agent_id == "agent-123"
    assert resp.read is False


def test_answering_machine_client_error_handling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test error handling when the AnsweringMachineClient receives an error response."""
    app = Flask("test")
    app.config["CLIENT_ANSWERING_MACHINE_URL"] = "https://am.example.com"
    app.config["CLIENT_ANSWERING_MACHINE_KEY"] = "test-key"
    answering_machine.init_app(app)
    client = AnsweringMachineClient()
    monkeypatch.setattr(
        requests,
        "post",
        lambda *a, **k: DummyResponse({"error": "fail"}, status_code=401),
    )
    req = MessageCreate(content="fail")
    with pytest.raises(requests.exceptions.HTTPError):
        client.create_message(req)


def test_answering_machine_client_create_message_with_optional_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test creating a message with optional fields."""
    app = Flask("test")
    app.config["CLIENT_ANSWERING_MACHINE_URL"] = "https://am.example.com"
    app.config["CLIENT_ANSWERING_MACHINE_KEY"] = "test-key"
    answering_machine.init_app(app)
    client = AnsweringMachineClient()
    message_data = {
        "id": 1,
        "content": "Hello!",
        "agent_id": "agent-123",
        "created_at": "2025-05-28T12:00:00Z",
        "read": False,
        "message_type": "general",
        "subject": "Test Message",
        "arguments": {"key": "value"},
        "responded": False,
    }
    monkeypatch.setattr(requests, "post", lambda *a, **k: DummyResponse(message_data))
    req = MessageCreate(
        content="Hello!",
        message_type="general",
        subject="Test Message",
        arguments={"key": "value"},
    )
    resp = client.create_message(req)
    assert resp.id == 1
    assert resp.content == "Hello!"
    assert resp.message_type == "general"
    assert resp.subject == "Test Message"
    assert resp.arguments == {"key": "value"}
    assert resp.responded is False


def test_answering_machine_client_list_messages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test listing messages."""
    app = Flask("test")
    app.config["CLIENT_ANSWERING_MACHINE_URL"] = "https://am.example.com"
    app.config["CLIENT_ANSWERING_MACHINE_KEY"] = "test-key"
    answering_machine.init_app(app)
    client = AnsweringMachineClient()
    messages_data = [
        {
            "id": 1,
            "content": "Message 1",
            "agent_id": "agent-123",
            "created_at": "2025-05-28T12:00:00Z",
            "read": False,
        },
        {
            "id": 2,
            "content": "Message 2",
            "agent_id": "agent-456",
            "created_at": "2025-05-28T13:00:00Z",
            "read": True,
        },
    ]
    monkeypatch.setattr(requests, "get", lambda *a, **k: DummyResponse(messages_data))
    messages = client.list_messages(read=False, page=1, per_page=10)
    assert len(messages) == EXPECTED_MESSAGE_COUNT
    assert messages[0].id == EXPECTED_MESSAGE_ID_1
    assert messages[1].id == EXPECTED_MESSAGE_ID_2


def test_answering_machine_client_get_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test getting a specific message."""
    app = Flask("test")
    app.config["CLIENT_ANSWERING_MACHINE_URL"] = "https://am.example.com"
    app.config["CLIENT_ANSWERING_MACHINE_KEY"] = "test-key"
    answering_machine.init_app(app)
    client = AnsweringMachineClient()
    message_data = {
        "id": 1,
        "content": "Hello!",
        "agent_id": "agent-123",
        "created_at": "2025-05-28T12:00:00Z",
        "read": False,
    }
    monkeypatch.setattr(requests, "get", lambda *a, **k: DummyResponse(message_data))
    message = client.get_message(1)
    assert message.id == 1
    assert message.content == "Hello!"


def test_answering_machine_client_delete_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test deleting a message."""
    app = Flask("test")
    app.config["CLIENT_ANSWERING_MACHINE_URL"] = "https://am.example.com"
    app.config["CLIENT_ANSWERING_MACHINE_KEY"] = "test-key"
    answering_machine.init_app(app)
    client = AnsweringMachineClient()
    monkeypatch.setattr(
        requests, "delete", lambda *a, **k: DummyResponse("", status_code=204)
    )
    client.delete_message(1)  # Should not raise


def test_answering_machine_client_mark_message_responded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test marking a message as responded."""
    app = Flask("test")
    app.config["CLIENT_ANSWERING_MACHINE_URL"] = "https://am.example.com"
    app.config["CLIENT_ANSWERING_MACHINE_KEY"] = "test-key"
    answering_machine.init_app(app)
    client = AnsweringMachineClient()
    message_data = {
        "id": 1,
        "content": "Hello!",
        "agent_id": "agent-123",
        "created_at": "2025-05-28T12:00:00Z",
        "read": False,
        "responded": True,
    }
    monkeypatch.setattr(requests, "patch", lambda *a, **k: DummyResponse(message_data))
    message = client.mark_message_responded(1)
    assert message.id == 1
    assert message.responded is True


def test_answering_machine_client_get_message_stats(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test getting message statistics."""
    app = Flask("test")
    app.config["CLIENT_ANSWERING_MACHINE_URL"] = "https://am.example.com"
    app.config["CLIENT_ANSWERING_MACHINE_KEY"] = "test-key"
    answering_machine.init_app(app)
    client = AnsweringMachineClient()
    stats_data = {
        "total": 100,
        "read": 75,
        "unread": 25,
        "responded": 60,
        "unreplied": 40,
    }
    monkeypatch.setattr(requests, "get", lambda *a, **k: DummyResponse(stats_data))
    stats = client.get_message_stats()
    assert stats.total == EXPECTED_TOTAL_STATS
    assert stats.read == EXPECTED_READ_STATS
    assert stats.unread == EXPECTED_UNREAD_STATS
    assert stats.responded == EXPECTED_RESPONDED_STATS
    assert stats.unreplied == EXPECTED_UNREPLIED_STATS


def test_answering_machine_client_get_message_types(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test getting available message types."""
    app = Flask("test")
    app.config["CLIENT_ANSWERING_MACHINE_URL"] = "https://am.example.com"
    app.config["CLIENT_ANSWERING_MACHINE_KEY"] = "test-key"
    answering_machine.init_app(app)
    client = AnsweringMachineClient()
    types_data = ["general", "architect_approval"]
    monkeypatch.setattr(requests, "get", lambda *a, **k: DummyResponse(types_data))
    types = client.get_message_types()
    assert types == ["general", "architect_approval"]
