"""Tests for the CodebotClient and related configuration logic."""

from typing import Any

import pytest
import requests
from flask import Flask

from zecmf.clients import codebot
from zecmf.clients.codebot import (
    CodebotClient,
    EnvironmentVariable,
    ProfileInput,
    TaskCreate,
    _CodebotConfig,  # noqa: PLC2701
)

# Test constants
HTTP_ERROR_STATUS = 400
EXPECTED_PROFILE_COUNT = 2
EXPECTED_PROFILE_ID_1 = 1
EXPECTED_PROFILE_ID_2 = 2
EXPECTED_TASK_ID = 1
TIMEOUT_APP_CONFIG = 42
TIMEOUT_DIRECT_ARGS = 5
TASK_TIMEOUT_SECONDS = 300
TASK_DURATION_SECONDS = 5.2


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


def test_codebot_client_init_with_app(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test CodebotClient initialization using Flask app config via init_app."""
    app = Flask("test")
    app.config["CLIENT_CODEBOT_URL"] = "https://codebot.example.com"
    app.config["CLIENT_CODEBOT_KEY"] = "test-key"
    app.config["CLIENT_CODEBOT_TIMEOUT"] = TIMEOUT_APP_CONFIG
    codebot.init_app(app)
    client = CodebotClient()
    assert client.base_url == "https://codebot.example.com"
    assert client.api_key == "test-key"
    assert client.timeout == TIMEOUT_APP_CONFIG


def test_codebot_client_init_with_direct_args() -> None:
    """Test CodebotClient initialization with direct arguments."""
    client = CodebotClient(
        base_url="https://direct.example.com",
        api_key="direct-key",
        timeout=TIMEOUT_DIRECT_ARGS,
    )
    assert client.base_url == "https://direct.example.com"
    assert client.api_key == "direct-key"
    assert client.timeout == TIMEOUT_DIRECT_ARGS


def test_codebot_client_init_missing_config() -> None:
    """Test CodebotClient raises ValueError if config is missing."""
    _CodebotConfig.base_url = None
    _CodebotConfig.api_key = None
    _CodebotConfig.timeout = 100
    # No init_app called, no direct args
    with pytest.raises(ValueError, match="Codebot API base URL not configured"):
        CodebotClient()


def test_codebot_client_create_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test creating a profile using the CodebotClient."""
    app = Flask("test")
    app.config["CLIENT_CODEBOT_URL"] = "https://codebot.example.com"
    app.config["CLIENT_CODEBOT_KEY"] = "test-key"
    codebot.init_app(app)
    client = CodebotClient()
    profile_data = {
        "id": 1,
        "name": "Test Profile",
        "assistant_type": "CLAUDE_CODE",
        "docker_image": "myorg/claude-code:latest",
        "created_at": "2025-05-28T12:00:00Z",
    }
    monkeypatch.setattr(
        requests, "post", lambda *a, **k: DummyResponse(profile_data, 201)
    )
    req = ProfileInput(
        name="Test Profile",
        assistant_type="CLAUDE_CODE",
        docker_image="myorg/claude-code:latest",
    )
    resp = client.create_profile(req)
    assert resp.id == 1
    assert resp.name == "Test Profile"
    assert resp.assistant_type == "CLAUDE_CODE"
    assert resp.docker_image == "myorg/claude-code:latest"


def test_codebot_client_create_profile_with_optional_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test creating a profile with optional fields."""
    app = Flask("test")
    app.config["CLIENT_CODEBOT_URL"] = "https://codebot.example.com"
    app.config["CLIENT_CODEBOT_KEY"] = "test-key"
    codebot.init_app(app)
    client = CodebotClient()
    profile_data = {
        "id": 1,
        "name": "Test Profile",
        "assistant_type": "CLAUDE_CODE",
        "docker_image": "myorg/claude-code:latest",
        "claude_auth_type": "API_KEY",
        "api_key": "claude-api-key",
        "model": "claude-opus-4",
        "mcp_config": {"servers": []},
        "environment_variables": [{"name": "TEST_VAR", "value": "test_value"}],
        "created_at": "2025-05-28T12:00:00Z",
    }
    monkeypatch.setattr(
        requests, "post", lambda *a, **k: DummyResponse(profile_data, 201)
    )
    req = ProfileInput(
        name="Test Profile",
        assistant_type="CLAUDE_CODE",
        docker_image="myorg/claude-code:latest",
        claude_auth_type="API_KEY",
        api_key="claude-api-key",
        model="claude-opus-4",
        mcp_config={"servers": []},
        environment_variables=[
            EnvironmentVariable(name="TEST_VAR", value="test_value")
        ],
    )
    resp = client.create_profile(req)
    assert resp.id == 1
    assert resp.claude_auth_type == "API_KEY"
    assert resp.api_key == "claude-api-key"
    assert resp.model == "claude-opus-4"
    assert resp.mcp_config == {"servers": []}
    assert resp.environment_variables == [{"name": "TEST_VAR", "value": "test_value"}]


def test_codebot_client_list_profiles(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test listing profiles using the CodebotClient."""
    app = Flask("test")
    app.config["CLIENT_CODEBOT_URL"] = "https://codebot.example.com"
    app.config["CLIENT_CODEBOT_KEY"] = "test-key"
    codebot.init_app(app)
    client = CodebotClient()
    profiles_data = [
        {
            "id": 1,
            "name": "Profile 1",
            "assistant_type": "CLAUDE_CODE",
            "docker_image": "myorg/claude-code:latest",
        },
        {
            "id": 2,
            "name": "Profile 2",
            "assistant_type": "CODEX",
            "docker_image": "myorg/codex:latest",
        },
    ]
    monkeypatch.setattr(requests, "get", lambda *a, **k: DummyResponse(profiles_data))
    profiles = client.list_profiles()
    assert len(profiles) == EXPECTED_PROFILE_COUNT
    assert profiles[0].id == EXPECTED_PROFILE_ID_1
    assert profiles[1].id == EXPECTED_PROFILE_ID_2


def test_codebot_client_list_profiles_with_params(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test listing profiles with sorting parameters."""
    app = Flask("test")
    app.config["CLIENT_CODEBOT_URL"] = "https://codebot.example.com"
    app.config["CLIENT_CODEBOT_KEY"] = "test-key"
    codebot.init_app(app)
    client = CodebotClient()
    profiles_data: list[dict[str, Any]] = []

    # Capture the params passed to requests.get
    captured_params: dict[str, str] = {}

    def mock_get(*args: object, **kwargs: dict[str, Any]) -> DummyResponse:
        captured_params.update(kwargs.get("params", {}))
        return DummyResponse(profiles_data)

    monkeypatch.setattr(requests, "get", mock_get)
    client.list_profiles(sort="name", order="desc")
    assert captured_params["sort"] == "name"
    assert captured_params["order"] == "desc"


def test_codebot_client_get_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test getting a specific profile."""
    app = Flask("test")
    app.config["CLIENT_CODEBOT_URL"] = "https://codebot.example.com"
    app.config["CLIENT_CODEBOT_KEY"] = "test-key"
    codebot.init_app(app)
    client = CodebotClient()
    profile_data = {
        "id": 1,
        "name": "Test Profile",
        "assistant_type": "CLAUDE_CODE",
        "docker_image": "myorg/claude-code:latest",
    }
    monkeypatch.setattr(requests, "get", lambda *a, **k: DummyResponse(profile_data))
    profile = client.get_profile(1)
    assert profile.id == 1
    assert profile.name == "Test Profile"


def test_codebot_client_update_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test updating a profile."""
    app = Flask("test")
    app.config["CLIENT_CODEBOT_URL"] = "https://codebot.example.com"
    app.config["CLIENT_CODEBOT_KEY"] = "test-key"
    codebot.init_app(app)
    client = CodebotClient()
    profile_data = {
        "id": 1,
        "name": "Updated Profile",
        "assistant_type": "CLAUDE_CODE",
        "docker_image": "myorg/claude-code:v2",
    }
    monkeypatch.setattr(requests, "patch", lambda *a, **k: DummyResponse(profile_data))
    req = ProfileInput(
        name="Updated Profile",
        assistant_type="CLAUDE_CODE",
        docker_image="myorg/claude-code:v2",
    )
    profile = client.update_profile(1, req)
    assert profile.name == "Updated Profile"
    assert profile.docker_image == "myorg/claude-code:v2"


def test_codebot_client_delete_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test deleting a profile."""
    app = Flask("test")
    app.config["CLIENT_CODEBOT_URL"] = "https://codebot.example.com"
    app.config["CLIENT_CODEBOT_KEY"] = "test-key"
    codebot.init_app(app)
    client = CodebotClient()
    monkeypatch.setattr(requests, "delete", lambda *a, **k: DummyResponse({}, 204))
    # Should not raise an exception
    client.delete_profile(1)


def test_codebot_client_create_task(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test creating a task."""
    app = Flask("test")
    app.config["CLIENT_CODEBOT_URL"] = "https://codebot.example.com"
    app.config["CLIENT_CODEBOT_KEY"] = "test-key"
    codebot.init_app(app)
    client = CodebotClient()
    task_data = {
        "id": 1,
        "profile_id": 1,
        "instructions": "Write a test",
        "status": "pending",
        "created_at": "2025-05-28T12:00:00Z",
    }
    monkeypatch.setattr(requests, "post", lambda *a, **k: DummyResponse(task_data, 201))
    req = TaskCreate(profile_id=1, instructions="Write a test")
    task = client.create_task(req)
    assert task.id == 1
    assert task.profile_id == 1
    assert task.instructions == "Write a test"
    assert task.status == "pending"


def test_codebot_client_list_tasks(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test listing tasks."""
    app = Flask("test")
    app.config["CLIENT_CODEBOT_URL"] = "https://codebot.example.com"
    app.config["CLIENT_CODEBOT_KEY"] = "test-key"
    codebot.init_app(app)
    client = CodebotClient()
    tasks_data = [
        {
            "id": 1,
            "profile_id": 1,
            "instructions": "Task 1",
            "status": "completed",
        },
        {
            "id": 2,
            "profile_id": 2,
            "instructions": "Task 2",
            "status": "running",
        },
    ]
    monkeypatch.setattr(requests, "get", lambda *a, **k: DummyResponse(tasks_data))
    tasks = client.list_tasks()
    assert len(tasks) == EXPECTED_PROFILE_COUNT
    assert tasks[0].id == 1
    assert tasks[1].status == "running"


def test_codebot_client_get_task(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test getting a specific task."""
    app = Flask("test")
    app.config["CLIENT_CODEBOT_URL"] = "https://codebot.example.com"
    app.config["CLIENT_CODEBOT_KEY"] = "test-key"
    codebot.init_app(app)
    client = CodebotClient()
    task_data = {
        "id": 1,
        "profile_id": 1,
        "instructions": "Write a test",
        "status": "completed",
        "task_details": {
            "workspace_path": "/workspace",
            "timeout_seconds": TASK_TIMEOUT_SECONDS,
        },
        "result_summary": {
            "status": "completed",
            "message": "Task completed successfully",
        },
    }
    monkeypatch.setattr(requests, "get", lambda *a, **k: DummyResponse(task_data))
    task = client.get_task(1)
    assert task.id == 1
    assert task.task_details is not None
    assert task.task_details.workspace_path == "/workspace"
    assert task.task_details.timeout_seconds == TASK_TIMEOUT_SECONDS
    assert task.result_summary is not None
    assert task.result_summary.status == "completed"


def test_codebot_client_delete_task(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test deleting a task."""
    app = Flask("test")
    app.config["CLIENT_CODEBOT_URL"] = "https://codebot.example.com"
    app.config["CLIENT_CODEBOT_KEY"] = "test-key"
    codebot.init_app(app)
    client = CodebotClient()
    monkeypatch.setattr(requests, "delete", lambda *a, **k: DummyResponse({}, 204))
    # Should not raise an exception
    client.delete_task(1)


def test_codebot_client_cancel_task(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test canceling a task."""
    app = Flask("test")
    app.config["CLIENT_CODEBOT_URL"] = "https://codebot.example.com"
    app.config["CLIENT_CODEBOT_KEY"] = "test-key"
    codebot.init_app(app)
    client = CodebotClient()
    monkeypatch.setattr(requests, "post", lambda *a, **k: DummyResponse({}, 200))
    # Should not raise an exception
    client.cancel_task(1)


def test_codebot_client_get_task_status(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test getting task status."""
    app = Flask("test")
    app.config["CLIENT_CODEBOT_URL"] = "https://codebot.example.com"
    app.config["CLIENT_CODEBOT_KEY"] = "test-key"
    codebot.init_app(app)
    client = CodebotClient()
    status_data = {
        "status": "completed",
        "message": "Task completed successfully",
        "execution_details": {
            "status": "completed",
            "container_id": "abc123",
            "duration": TASK_DURATION_SECONDS,
            "logs": {
                "stdout": "Task output",
                "stderr": "",
            },
        },
    }
    monkeypatch.setattr(requests, "get", lambda *a, **k: DummyResponse(status_data))
    result = client.get_task_status(1)
    assert result.status == "completed"
    assert result.message == "Task completed successfully"
    assert result.execution_details is not None
    assert result.execution_details.duration == TASK_DURATION_SECONDS
    assert result.execution_details.logs is not None
    assert result.execution_details.logs.stdout == "Task output"


def test_codebot_client_error_handling(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test error handling when the CodebotClient receives an error response."""
    app = Flask("test")
    app.config["CLIENT_CODEBOT_URL"] = "https://codebot.example.com"
    app.config["CLIENT_CODEBOT_KEY"] = "test-key"
    codebot.init_app(app)
    client = CodebotClient()
    monkeypatch.setattr(
        requests,
        "post",
        lambda *a, **k: DummyResponse({"error": "Invalid request"}, status_code=400),
    )
    req = ProfileInput(
        name="Test",
        assistant_type="INVALID",
        docker_image="test",
    )
    with pytest.raises(requests.exceptions.HTTPError):
        client.create_profile(req)


def test_codebot_client_profile_with_claude_account_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test creating a profile with Claude account fields."""
    app = Flask("test")
    app.config["CLIENT_CODEBOT_URL"] = "https://codebot.example.com"
    app.config["CLIENT_CODEBOT_KEY"] = "test-key"
    codebot.init_app(app)
    client = CodebotClient()
    profile_data = {
        "id": 1,
        "name": "Claude Account Profile",
        "assistant_type": "CLAUDE_CODE",
        "docker_image": "myorg/claude-code:latest",
        "claude_auth_type": "CLAUDE_ACCOUNT",
        "claude_auth_token": "test-auth-token",
        "claude_refresh_token": "test-refresh-token",
        "claude_token_expires_at": "2025-06-01T12:00:00Z",
        "claude_subscription_type": "max",
        "claude_account_uuid": "test-account-uuid",
        "claude_account_email": "test@example.com",
        "claude_organization_uuid": "test-org-uuid",
        "claude_organization_name": "Test Organization",
        "claude_organization_role": "admin",
        "claude_workspace_role": "owner",
        "created_at": "2025-05-28T12:00:00Z",
    }
    monkeypatch.setattr(
        requests, "post", lambda *a, **k: DummyResponse(profile_data, 201)
    )
    req = ProfileInput(
        name="Claude Account Profile",
        assistant_type="CLAUDE_CODE",
        docker_image="myorg/claude-code:latest",
        claude_auth_type="CLAUDE_ACCOUNT",
        claude_auth_token="test-auth-token",
        claude_refresh_token="test-refresh-token",
        claude_token_expires_at="2025-06-01T12:00:00Z",
        claude_subscription_type="max",
        claude_account_uuid="test-account-uuid",
        claude_account_email="test@example.com",
        claude_organization_uuid="test-org-uuid",
        claude_organization_name="Test Organization",
        claude_organization_role="admin",
        claude_workspace_role="owner",
    )
    resp = client.create_profile(req)
    assert resp.id == 1
    assert resp.name == "Claude Account Profile"
    assert resp.claude_auth_type == "CLAUDE_ACCOUNT"
    assert resp.claude_account_uuid == "test-account-uuid"
    assert resp.claude_account_email == "test@example.com"
    assert resp.claude_organization_uuid == "test-org-uuid"
    assert resp.claude_organization_name == "Test Organization"
    assert resp.claude_organization_role == "admin"
    assert resp.claude_workspace_role == "owner"
