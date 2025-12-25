"""Codebot API client and data models for interacting with the Codebot service.

This module provides the CodebotClient class for communicating with the Codebot API, as well as dataclasses for Profile, Task, and related entities.
"""

from dataclasses import dataclass
from typing import Any

import requests
from flask import Flask

from zecmf.services.schemas.client_requests import HttpRequestHeaders
from zecmf.services.schemas.codebot import (
    ProfileJsonRequest,
    ProfileListQueryParams,
    TaskCreateJsonRequest,
)


@dataclass
class EnvironmentVariable:
    """Represents an environment variable for Docker containers."""

    name: str
    value: str


@dataclass
class ProfileInput:
    """Represents a request payload for creating or updating a profile."""

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
    environment_variables: list[EnvironmentVariable] | None = None


@dataclass
class Profile:
    """Represents a coder profile returned by the Codebot API."""

    id: int
    name: str
    assistant_type: str
    docker_image: str | None = None
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
    created_at: str | None = None


@dataclass
class TaskCreate:
    """Represents a request payload for creating a task."""

    profile_id: int
    instructions: str
    workspace_path: str = "/tmp"  # noqa: S108


@dataclass
class ExecutionLogs:
    """Represents execution logs with stdout and stderr."""

    stdout: str | None = None
    stderr: str | None = None


@dataclass
class ExecutionDetails:
    """Represents detailed execution results."""

    status: str | None = None
    container_id: str | None = None
    duration: float | None = None
    logs: ExecutionLogs | None = None


@dataclass
class TaskResultSummary:
    """Represents task execution results summary."""

    status: str | None = None
    message: str | None = None
    error: str | None = None
    error_type: str | None = None
    execution_details: ExecutionDetails | None = None


@dataclass
class TaskDetails:
    """Represents task configuration details."""

    workspace_path: str | None = None
    environment_variables: dict[str, str] | None = None
    mcp_config: dict[str, Any] | None = None
    docker_image_override: str | None = None
    timeout_seconds: int | None = None


@dataclass
class Task:
    """Represents a task returned by the Codebot API."""

    id: int
    profile_id: int
    instructions: str
    status: str
    task_details: TaskDetails | None = None
    result_summary: TaskResultSummary | None = None
    started_at: str | None = None
    finished_at: str | None = None
    created_at: str | None = None


@dataclass
class TaskResult:
    """Represents the status and results of a specific task."""

    status: str
    message: str | None = None
    error: str | None = None
    error_type: str | None = None
    execution_details: ExecutionDetails | None = None


class _CodebotConfig:
    """Singleton config holder for Codebot client settings."""

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
    """Register the Flask app for Codebot client configuration.

    This must be called before using CodebotClient if you want to use app config values.

    Args:
        app (Flask): The Flask application instance to register.

    """
    base_url = app.config.get("CLIENT_CODEBOT_URL")
    api_key = app.config.get("CLIENT_CODEBOT_KEY")
    timeout = app.config.get("CLIENT_CODEBOT_TIMEOUT", 100)
    if not base_url:
        raise ValueError("CLIENT_CODEBOT_URL must be set in app config.")
    if not api_key:
        raise ValueError("CLIENT_CODEBOT_KEY must be set in app config.")
    _CodebotConfig.set_config(base_url, api_key, timeout)


class CodebotClient:
    """Client for interacting with the Codebot API endpoints."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: int | None = None,
    ) -> None:
        """Initialize the CodebotClient.

        You can either provide base_url, api_key, and timeout directly, or call init_app(app) beforehand to use Flask config values.
        Direct arguments take precedence over config.

        Args:
            base_url (str, optional): Base URL of the Codebot API.
            api_key (str, optional): API key for authentication.
            timeout (int, optional): Timeout for requests in seconds.

        Raises:
            ValueError: If required config values are missing or init_app was not called.

        """
        self.base_url = None
        self.api_key = None
        self.timeout = None
        if base_url is not None:
            self.base_url = base_url
        elif _CodebotConfig.is_configured() and _CodebotConfig.base_url is not None:
            self.base_url = _CodebotConfig.base_url

        if api_key is not None:
            self.api_key = api_key
        elif _CodebotConfig.is_configured() and _CodebotConfig.api_key is not None:
            self.api_key = _CodebotConfig.api_key

        if timeout is not None:
            self.timeout = timeout
        elif _CodebotConfig.is_configured() and _CodebotConfig.timeout is not None:
            self.timeout = _CodebotConfig.timeout

        if not self.base_url:
            raise ValueError("Codebot API base URL not configured (CLIENT_CODEBOT_URL)")
        if not self.api_key:
            raise ValueError("Codebot API key not configured (CLIENT_CODEBOT_KEY)")

    def _headers(self) -> HttpRequestHeaders:
        """Return the HTTP headers for API requests."""
        return HttpRequestHeaders(authorization=f"Bearer {self.api_key}")

    def _build_profile_json(self, payload: ProfileInput) -> ProfileJsonRequest:
        """Build typed JSON request from ProfileInput."""
        # Convert environment variables to dict format
        env_vars = None
        if payload.environment_variables is not None:
            env_vars = [
                {"name": ev.name, "value": ev.value}
                for ev in payload.environment_variables
            ]

        return ProfileJsonRequest(
            name=payload.name,
            assistant_type=payload.assistant_type,
            docker_image=payload.docker_image,
            claude_auth_type=payload.claude_auth_type,
            api_key=payload.api_key,
            claude_auth_token=payload.claude_auth_token,
            claude_refresh_token=payload.claude_refresh_token,
            claude_token_expires_at=payload.claude_token_expires_at,
            claude_subscription_type=payload.claude_subscription_type,
            claude_account_uuid=payload.claude_account_uuid,
            claude_account_email=payload.claude_account_email,
            claude_organization_uuid=payload.claude_organization_uuid,
            claude_organization_name=payload.claude_organization_name,
            claude_organization_role=payload.claude_organization_role,
            claude_workspace_role=payload.claude_workspace_role,
            model=payload.model,
            openai_organization=payload.openai_organization,
            mcp_config=payload.mcp_config,
            environment_variables=env_vars,
        )

    def create_profile(self, payload: ProfileInput) -> Profile:
        """Create a new coder profile.

        Args:
            payload (ProfileInput): The profile creation payload.

        Returns:
            Profile: The created profile object.

        """
        json_request = self._build_profile_json(payload)
        resp = requests.post(
            f"{self.base_url}/api/v1/profiles",
            headers=self._headers().to_dict(),
            json=json_request.to_dict(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return Profile(**resp.json())

    def list_profiles(
        self, sort: str | None = None, order: str | None = None
    ) -> list[Profile]:
        """List all coder profiles.

        Args:
            sort (str, optional): Sort field (created_at, name).
            order (str, optional): Sort order (asc, desc).

        Returns:
            list[Profile]: List of profile objects.

        """
        query_params = ProfileListQueryParams(sort=sort, order=order)

        resp = requests.get(
            f"{self.base_url}/api/v1/profiles",
            headers=self._headers().to_dict(),
            params=query_params.to_dict(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return [Profile(**item) for item in resp.json()]

    def get_profile(self, profile_id: int) -> Profile:
        """Get details of a specific profile.

        Args:
            profile_id (int): The profile identifier.

        Returns:
            Profile: The profile object.

        """
        resp = requests.get(
            f"{self.base_url}/api/v1/profiles/{profile_id}",
            headers=self._headers().to_dict(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return Profile(**resp.json())

    def update_profile(self, profile_id: int, payload: ProfileInput) -> Profile:
        """Update a specific profile with full object replacement.

        Args:
            profile_id (int): The profile identifier.
            payload (ProfileInput): The profile update payload.

        Returns:
            Profile: The updated profile object.

        """
        json_request = self._build_profile_json(payload)
        resp = requests.patch(
            f"{self.base_url}/api/v1/profiles/{profile_id}",
            headers=self._headers().to_dict(),
            json=json_request.to_dict(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return Profile(**resp.json())

    def delete_profile(self, profile_id: int) -> None:
        """Delete a specific profile.

        Args:
            profile_id (int): The profile identifier.

        """
        resp = requests.delete(
            f"{self.base_url}/api/v1/profiles/{profile_id}",
            headers=self._headers().to_dict(),
            timeout=self.timeout,
        )
        resp.raise_for_status()

    def create_task(self, payload: TaskCreate) -> Task:
        """Create a new coding task.

        Args:
            payload (TaskCreate): The task creation payload.

        Returns:
            Task: The created task object.

        """
        json_request = TaskCreateJsonRequest(
            profile_id=payload.profile_id,
            instructions=payload.instructions,
            workspace_path=payload.workspace_path,
        )

        resp = requests.post(
            f"{self.base_url}/api/v1/tasks",
            headers=self._headers().to_dict(),
            json=json_request.to_dict(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return self._parse_task(resp.json())

    def list_tasks(self) -> list[Task]:
        """Get all tasks.

        Returns:
            list[Task]: List of task objects.

        """
        resp = requests.get(
            f"{self.base_url}/api/v1/tasks",
            headers=self._headers().to_dict(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return [self._parse_task(item) for item in resp.json()]

    def get_task(self, task_id: int) -> Task:
        """Get a specific task.

        Args:
            task_id (int): The task identifier.

        Returns:
            Task: The task object.

        """
        resp = requests.get(
            f"{self.base_url}/api/v1/tasks/{task_id}",
            headers=self._headers().to_dict(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return self._parse_task(resp.json())

    def delete_task(self, task_id: int) -> None:
        """Delete a specific task.

        Args:
            task_id (int): The task identifier.

        """
        resp = requests.delete(
            f"{self.base_url}/api/v1/tasks/{task_id}",
            headers=self._headers().to_dict(),
            timeout=self.timeout,
        )
        resp.raise_for_status()

    def cancel_task(self, task_id: int) -> None:
        """Cancel a running task.

        Args:
            task_id (int): The task identifier.

        """
        resp = requests.post(
            f"{self.base_url}/api/v1/tasks/{task_id}/cancel",
            headers=self._headers().to_dict(),
            timeout=self.timeout,
        )
        resp.raise_for_status()

    def get_task_status(self, task_id: int) -> TaskResult:
        """Get the status and results of a specific task.

        Args:
            task_id (int): The task identifier.

        Returns:
            TaskResult: The task result object.

        """
        resp = requests.get(
            f"{self.base_url}/api/v1/tasks/{task_id}/status",
            headers=self._headers().to_dict(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return self._parse_task_result(resp.json())

    def _parse_task(self, data: dict[str, Any]) -> Task:
        """Parse a task response from the API."""
        # Parse nested objects
        task_details = None
        if data.get("task_details"):
            task_details = TaskDetails(**data["task_details"])

        result_summary = None
        if data.get("result_summary"):
            result_summary = self._parse_task_result_summary(data["result_summary"])

        return Task(
            id=data["id"],
            profile_id=data["profile_id"],
            instructions=data["instructions"],
            status=data["status"],
            task_details=task_details,
            result_summary=result_summary,
            started_at=data.get("started_at"),
            finished_at=data.get("finished_at"),
            created_at=data.get("created_at"),
        )

    def _parse_task_result_summary(self, data: dict[str, Any]) -> TaskResultSummary:
        """Parse a task result summary from the API."""
        execution_details = None
        if data.get("execution_details"):
            execution_details = self._parse_execution_details(data["execution_details"])

        return TaskResultSummary(
            status=data.get("status"),
            message=data.get("message"),
            error=data.get("error"),
            error_type=data.get("error_type"),
            execution_details=execution_details,
        )

    def _parse_execution_details(self, data: dict[str, Any]) -> ExecutionDetails:
        """Parse execution details from the API."""
        logs = None
        if data.get("logs"):
            logs = ExecutionLogs(**data["logs"])

        return ExecutionDetails(
            status=data.get("status"),
            container_id=data.get("container_id"),
            duration=data.get("duration"),
            logs=logs,
        )

    def _parse_task_result(self, data: dict[str, Any]) -> TaskResult:
        """Parse a task result response from the API."""
        execution_details = None
        if data.get("execution_details"):
            execution_details = self._parse_execution_details(data["execution_details"])

        return TaskResult(
            status=data["status"],
            message=data.get("message"),
            error=data.get("error"),
            error_type=data.get("error_type"),
            execution_details=execution_details,
        )
