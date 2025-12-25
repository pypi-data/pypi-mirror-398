"""LLM API client and data models for interacting with language model providers and completions.

This module provides the LLMClient class for communicating with the LLM API, as well as dataclasses for Provider, LLMModel, CompletionRequest, and CompletionResponse.
"""

from dataclasses import asdict, dataclass, field

import requests
from flask import Flask


@dataclass
class Provider:
    """Represents an LLM provider configuration and metadata."""

    id: int
    provider_type: str
    display_name: str
    base_url: str = ""
    has_api_key: bool = False
    is_active: bool = True
    created_at: str = ""
    updated_at: str = ""


@dataclass
class LLMModel:
    """Represents a language model and its configuration."""

    id: int
    name: str
    display_name: str
    provider_id: int
    provider_name: str = ""
    default_temperature: float = 1.0
    default_max_tokens: int = 0
    default_top_p: float = 1.0
    default_frequency_penalty: float = 0.0
    default_presence_penalty: float = 0.0
    default_instructions: str = ""
    max_context_length: int = 0
    supports_streaming: bool = True
    supports_function_calling: bool = False
    supports_vision: bool = False
    parameter_mappings: dict = field(default_factory=dict)
    supported_parameters: list = field(default_factory=list)
    is_active: bool = True
    cost_per_1k_input_tokens: float = 0.0
    cost_per_1k_output_tokens: float = 0.0
    created_at: str = ""
    updated_at: str = ""


@dataclass
class CompletionMessage:
    """Represents a message within a completion choice."""

    role: str
    content: str


@dataclass
class CompletionChoice:
    """Represents a completion choice within a completion response."""

    index: int
    message: CompletionMessage
    finish_reason: str


@dataclass
class CompletionModelInfo:
    """Represents model information within a completion response."""

    id: int
    name: str
    provider: str


@dataclass
class CompletionUsage:
    """Represents token usage information within a completion response."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class CompletionResponse:
    """Represents a response from a completion request."""

    id: str
    model: CompletionModelInfo
    choices: list[CompletionChoice]
    usage: CompletionUsage
    created: int


@dataclass
class CompletionRequest:
    """Represents a request payload for generating a completion.

    Attributes:
        messages: List of messages for the completion.
        model_id: Optional ID of the model to use.
        model_display_name: Optional display name of the model.
        temperature: Optional sampling temperature (0-2).
        max_tokens: Optional maximum number of tokens to generate.
        top_p: Optional nucleus sampling parameter.
        frequency_penalty: Optional frequency penalty (-2 to 2).
        presence_penalty: Optional presence penalty (-2 to 2).
        instructions: Optional system instructions.
        stream: Optional flag to enable streaming response.
        cache: Optional flag to enable/disable caching of the completion.

    """

    messages: list[CompletionMessage]
    model_id: int | None = None
    model_display_name: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    top_p: float | None = None
    frequency_penalty: float | None = None
    presence_penalty: float | None = None
    instructions: str | None = None
    stream: bool | None = None
    cache: bool | None = None


class _LLMConfig:
    """Singleton config holder for LLM client settings."""

    base_url: str | None = None
    api_key: str | None = None
    timeout: int = 1200

    @classmethod
    def set_config(cls, base_url: str, api_key: str, timeout: int = 1200) -> None:
        cls.base_url = base_url
        cls.api_key = api_key
        cls.timeout = timeout

    @classmethod
    def is_configured(cls) -> bool:
        return cls.base_url is not None and cls.api_key is not None


def init_app(app: Flask) -> None:
    """Register the Flask app for LLM client configuration.

    This must be called before using LLMClient if you want to use app config values.

    Args:
        app (Flask): The Flask application instance to register.

    """
    base_url = app.config.get("CLIENT_LLM_URL")
    api_key = app.config.get("CLIENT_LLM_KEY")
    timeout = app.config.get("CLIENT_LLM_TIMEOUT", 1200)
    if not base_url:
        raise ValueError("CLIENT_LLM_URL must be set in app config.")
    if not api_key:
        raise ValueError("CLIENT_LLM_KEY must be set in app config.")
    _LLMConfig.set_config(base_url, api_key, timeout)


class LLMClient:
    """Client for interacting with the LLM API endpoints."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: int | None = None,
    ) -> None:
        """Initialize the LLMClient.

        You can either provide base_url, api_key, and timeout directly, or call init_app(app) beforehand to use Flask config values.
        Direct arguments take precedence over config.

        Args:
            base_url (str, optional): Base URL of the LLM API.
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
        elif _LLMConfig.is_configured() and _LLMConfig.base_url is not None:
            self.base_url = _LLMConfig.base_url

        if api_key is not None:
            self.api_key = api_key
        elif _LLMConfig.is_configured() and _LLMConfig.api_key is not None:
            self.api_key = _LLMConfig.api_key

        if timeout is not None:
            self.timeout = timeout
        elif _LLMConfig.is_configured() and _LLMConfig.timeout is not None:
            self.timeout = _LLMConfig.timeout

        if not self.base_url:
            raise ValueError("LLM API base URL not configured (CLIENT_LLM_URL)")
        if not self.api_key:
            raise ValueError("LLM API key not configured (CLIENT_LLM_KEY)")

    def _headers(self) -> dict[str, str]:
        """Return the HTTP headers for API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def list_providers(
        self, search: str | None = None, active_only: bool | None = None
    ) -> list[Provider]:
        """Get all LLM providers, optionally filtered by search or active status.

        Args:
            search (str, optional): Search term for provider display name.
            active_only (bool, optional): Only return active providers.

        Returns:
            list[Provider]: List of provider objects.

        """
        params = {}
        if search:
            params["search"] = search
        if active_only is not None:
            params["active_only"] = str(active_only).lower()
        resp = requests.get(
            f"{self.base_url}/api/v1/providers",
            headers=self._headers(),
            params=params,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return [Provider(**item) for item in resp.json()]

    def get_provider(self, provider_id: int) -> Provider:
        """Get a specific provider by ID.

        Args:
            provider_id (int): The provider identifier.

        Returns:
            Provider: The provider object.

        """
        resp = requests.get(
            f"{self.base_url}/api/v1/providers/{provider_id}",
            headers=self._headers(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return Provider(**resp.json())

    def list_models(
        self,
        provider_id: int | None = None,
        search: str | None = None,
        active_only: bool | None = None,
    ) -> list[LLMModel]:
        """Get all models, optionally filtered by provider, search, or active status.

        Args:
            provider_id (int, optional): Filter by provider ID.
            search (str, optional): Search term for model name.
            active_only (bool, optional): Only return active models.

        Returns:
            list[LLMModel]: List of model objects.

        """
        params = {}
        if provider_id is not None:
            params["provider_id"] = str(provider_id)
        if search:
            params["search"] = search
        if active_only is not None:
            params["active_only"] = str(active_only).lower()
        resp = requests.get(
            f"{self.base_url}/api/v1/models",
            headers=self._headers(),
            params=params,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return [LLMModel(**item) for item in resp.json()]

    def get_model(self, model_id: int) -> LLMModel:
        """Get a specific model by ID.

        Args:
            model_id (int): The model identifier.

        Returns:
            LLMModel: The model object.

        """
        resp = requests.get(
            f"{self.base_url}/api/v1/models/{model_id}",
            headers=self._headers(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return LLMModel(**resp.json())

    def create_completion(self, payload: CompletionRequest) -> CompletionResponse:
        """Generate a completion using the specified model and payload.

        Args:
            payload (CompletionRequest): The completion request payload.

        Returns:
            CompletionResponse: The generated completion response.

        """
        # Convert dataclass to dict, which recursively handles nested dataclasses
        payload_dict = asdict(payload)
        # Remove None values
        payload_dict = {k: v for k, v in payload_dict.items() if v is not None}

        resp = requests.post(
            f"{self.base_url}/api/v1/complete",
            headers=self._headers(),
            json=payload_dict,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()

        # Parse nested objects according to the API specification
        model_info = CompletionModelInfo(**data["model"])
        usage_info = CompletionUsage(**data["usage"])
        choices = [
            CompletionChoice(
                index=choice["index"],
                message=CompletionMessage(**choice["message"]),
                finish_reason=choice["finish_reason"],
            )
            for choice in data["choices"]
        ]

        return CompletionResponse(
            id=data["id"],
            model=model_info,
            choices=choices,
            usage=usage_info,
            created=data["created"],
        )
