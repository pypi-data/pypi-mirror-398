"""Tests for the LLMClient and related configuration logic."""

import pytest
import requests
from flask import Flask

from zecmf.clients import llm
from zecmf.clients.llm import (
    CompletionMessage,
    CompletionRequest,
    LLMClient,
    LLMModel,
    Provider,
    _LLMConfig,  # noqa: PLC2701
)


class DummyResponse:
    """A dummy response object to mock requests.Response for testing."""

    def __init__(self, json_data: object, status_code: int = 200) -> None:
        """Initialize DummyResponse with JSON data and status code."""
        self._json = json_data
        self.status_code = status_code
        self.text = str(json_data)

    def json(self) -> object:
        """Return the stored JSON data."""
        return self._json

    def raise_for_status(self) -> None:
        """Raise HTTPError if status code indicates an error."""
        if self.status_code >= HTTP_ERROR_STATUS:
            # Type ignore: DummyResponse is not a real requests.Response
            raise requests.exceptions.HTTPError(response=None)  # type: ignore[arg-type]


# Test constants
PROVIDER_COUNT = 2
MODEL_COUNT = 2
COMPLETION_TOTAL_TOKENS = 5
HTTP_ERROR_STATUS = 400
TIMEOUT_APP_CONFIG = 42
TIMEOUT_DIRECT_ARGS = 5


def test_llmclient_init_with_app(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test LLMClient initialization using Flask app config via init_app."""
    app = Flask("test")
    app.config["CLIENT_LLM_URL"] = "https://llm.example.com"
    app.config["CLIENT_LLM_KEY"] = "test-key"
    app.config["CLIENT_LLM_TIMEOUT"] = TIMEOUT_APP_CONFIG
    llm.init_app(app)
    client = LLMClient()
    assert client.base_url == "https://llm.example.com"
    assert client.api_key == "test-key"
    assert client.timeout == TIMEOUT_APP_CONFIG


def test_llmclient_init_with_direct_args() -> None:
    """Test LLMClient initialization with direct arguments."""
    client = LLMClient(
        base_url="https://direct.example.com",
        api_key="direct-key",
        timeout=TIMEOUT_DIRECT_ARGS,
    )
    assert client.base_url == "https://direct.example.com"
    assert client.api_key == "direct-key"
    assert client.timeout == TIMEOUT_DIRECT_ARGS


def test_llmclient_init_missing_config() -> None:
    """Test LLMClient raises ValueError if config is missing."""
    _LLMConfig.base_url = None
    _LLMConfig.api_key = None
    _LLMConfig.timeout = 100
    # No init_app called, no direct args
    with pytest.raises(ValueError, match="LLM API base URL not configured"):
        LLMClient()


def test_llmclient_list_providers(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test list_providers returns Provider objects."""
    app = Flask("test")
    app.config["CLIENT_LLM_URL"] = "https://llm.example.com"
    app.config["CLIENT_LLM_KEY"] = "test-key"
    llm.init_app(app)
    client = LLMClient()
    providers_data = [
        {"id": 1, "provider_type": "openai", "display_name": "OpenAI"},
        {"id": 2, "provider_type": "anthropic", "display_name": "Anthropic"},
    ]
    monkeypatch.setattr(requests, "get", lambda *a, **k: DummyResponse(providers_data))
    providers = client.list_providers()
    assert len(providers) == PROVIDER_COUNT
    assert isinstance(providers[0], Provider)
    assert providers[0].display_name == "OpenAI"


def test_llmclient_list_models(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test list_models returns LLMModel objects."""
    app = Flask("test")
    app.config["CLIENT_LLM_URL"] = "https://llm.example.com"
    app.config["CLIENT_LLM_KEY"] = "test-key"
    llm.init_app(app)
    client = LLMClient()
    models_data = [
        {"id": 1, "name": "gpt-3", "display_name": "GPT-3", "provider_id": 1},
        {"id": 2, "name": "claude", "display_name": "Claude", "provider_id": 2},
    ]
    monkeypatch.setattr(requests, "get", lambda *a, **k: DummyResponse(models_data))
    models = client.list_models()
    assert len(models) == MODEL_COUNT
    assert isinstance(models[0], LLMModel)
    assert models[0].display_name == "GPT-3"


def test_llmclient_create_completion(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test create_completion returns CompletionResponse object."""
    app = Flask("test")
    app.config["CLIENT_LLM_URL"] = "https://llm.example.com"
    app.config["CLIENT_LLM_KEY"] = "test-key"
    llm.init_app(app)
    client = LLMClient()
    completion_data = {
        "id": "abc123",
        "model": {"id": 1, "name": "gpt-3", "provider": "openai"},
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "Hello!"},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
        "created": 1234567890,
    }
    monkeypatch.setattr(
        requests, "post", lambda *a, **k: DummyResponse(completion_data)
    )
    req = CompletionRequest(
        messages=[CompletionMessage(role="user", content="Hi!")],
        model_display_name="Creative Best",
    )
    resp = client.create_completion(req)
    assert resp.id == "abc123"
    assert resp.choices[0].message.content == "Hello!"
    assert resp.usage.total_tokens == COMPLETION_TOTAL_TOKENS


def test_llmclient_error_handling(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that HTTP errors are raised properly."""
    app = Flask("test")
    app.config["CLIENT_LLM_URL"] = "https://llm.example.com"
    app.config["CLIENT_LLM_KEY"] = "test-key"
    llm.init_app(app)
    client = LLMClient()
    monkeypatch.setattr(
        requests,
        "get",
        lambda *a, **k: DummyResponse({"error": "fail"}, status_code=401),
    )
    with pytest.raises(requests.exceptions.HTTPError):
        client.list_providers()


def test_llmclient_completion_with_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test create_completion includes cache parameter when specified."""
    app = Flask("test")
    app.config["CLIENT_LLM_URL"] = "https://llm.example.com"
    app.config["CLIENT_LLM_KEY"] = "test-key"
    llm.init_app(app)
    client = LLMClient()

    # Track the JSON payload sent in the request
    sent_payload: dict[str, object] = {}

    def mock_post(*args: object, **kwargs: object) -> DummyResponse:
        nonlocal sent_payload
        json_data = kwargs.get("json", {})
        if isinstance(json_data, dict):
            sent_payload = json_data
        return DummyResponse(
            {
                "id": "test123",
                "model": {"id": 1, "name": "gpt-3", "provider": "openai"},
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "Cached response"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 3,
                    "completion_tokens": 2,
                    "total_tokens": 5,
                },
                "created": 1234567890,
            }
        )

    monkeypatch.setattr(requests, "post", mock_post)

    # Test with cache=True
    req = CompletionRequest(
        messages=[CompletionMessage(role="user", content="Test with cache")],
        cache=True,
    )
    resp = client.create_completion(req)
    assert sent_payload.get("cache") is True
    assert resp.choices[0].message.content == "Cached response"

    # Test with cache=False
    req = CompletionRequest(
        messages=[CompletionMessage(role="user", content="Test without cache")],
        cache=False,
    )
    client.create_completion(req)
    assert sent_payload.get("cache") is False

    # Test with cache=None (should not be included in payload)
    req = CompletionRequest(
        messages=[CompletionMessage(role="user", content="Test default cache")],
    )
    client.create_completion(req)
    assert "cache" not in sent_payload


def test_llmclient_completion_message_serialization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that CompletionMessage dataclasses are properly serialized to JSON."""
    app = Flask("test")
    app.config["CLIENT_LLM_URL"] = "https://llm.example.com"
    app.config["CLIENT_LLM_KEY"] = "test-key"
    llm.init_app(app)
    client = LLMClient()

    # Track the JSON payload sent in the request
    sent_payload: dict[str, object] = {}

    def mock_post(*args: object, **kwargs: object) -> DummyResponse:
        nonlocal sent_payload
        json_data = kwargs.get("json", {})
        if isinstance(json_data, dict):
            sent_payload = json_data
        return DummyResponse(
            {
                "id": "test123",
                "model": {"id": 1, "name": "gpt-3", "provider": "openai"},
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "Response"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 5,
                    "completion_tokens": 3,
                    "total_tokens": 8,
                },
                "created": 1234567890,
            }
        )

    monkeypatch.setattr(requests, "post", mock_post)

    # Create a request with multiple messages
    expected_message_count = 2
    expected_model_id = 42
    expected_temperature = 0.7

    req = CompletionRequest(
        messages=[
            CompletionMessage(role="system", content="You are a helpful assistant"),
            CompletionMessage(role="user", content="Hello!"),
        ],
        model_id=expected_model_id,
        temperature=expected_temperature,
    )

    resp = client.create_completion(req)

    # Verify the response is correct
    assert resp.id == "test123"
    assert resp.choices[0].message.content == "Response"

    # Verify the sent payload has properly serialized messages as dicts
    assert "messages" in sent_payload
    messages = sent_payload["messages"]
    assert isinstance(messages, list)
    assert len(messages) == expected_message_count

    # First message should be a dict with role and content
    assert isinstance(messages[0], dict)
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == "You are a helpful assistant"

    # Second message should also be a dict
    assert isinstance(messages[1], dict)
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "Hello!"

    # Other parameters should be present
    assert sent_payload["model_id"] == expected_model_id
    assert sent_payload["temperature"] == expected_temperature
