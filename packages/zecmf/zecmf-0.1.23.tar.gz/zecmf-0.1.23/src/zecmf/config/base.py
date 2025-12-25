"""Base configuration classes for the application."""

import logging
import os
import re
from pathlib import Path
from typing import Any, ClassVar

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path.cwd() / ".env")

logger = logging.getLogger(__name__)


class BaseConfig:
    """Base configuration class with shared settings for all applications.

    This contains all common settings that are shared across all applications.
    Applications should only need to define app-specific settings or override
    settings that differ from these defaults.
    """

    # Flask settings
    SECRET_KEY: str | None = os.getenv(
        "SECRET_KEY"
    )  # Required in production, default in dev/test
    DEBUG: bool = False
    TESTING: bool = False

    # Database settings
    SQLALCHEMY_DATABASE_URI: str | None = os.getenv("DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ENGINE_OPTIONS: ClassVar[dict[str, Any]] = {
        "pool_recycle": 3600,
        "pool_pre_ping": True,
    }

    # API settings
    API_TITLE: str = "API"
    API_VERSION: str = "1.0"
    API_DESCRIPTION: str = "REST API Service"
    API_PREFIX: str = "/api/v1"
    API_VERSION_HEADER: bool = True

    # File upload settings
    MAX_CONTENT_LENGTH: int = 1024 * 1024  # 1MB

    # JWT settings - supporting both public key (RS256) and secret key (HS256) methods
    JWT_PUBLIC_KEY: str | None = os.getenv("JWT_PUBLIC_KEY")
    JWT_PUBLIC_KEY_PATH: str | None = os.getenv("JWT_PUBLIC_KEY_PATH")
    JWT_SECRET_KEY: str | None = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM: str = "RS256"
    JWT_TOKEN_LOCATION: ClassVar[list[str]] = ["headers"]
    JWT_HEADER_NAME: str = "Authorization"
    JWT_HEADER_TYPE: str = "Bearer"
    JWT_ACCESS_TOKEN_EXPIRES: int = 30 * 60  # seconds
    JWT_REFRESH_TOKEN_EXPIRES: int = 30 * 24 * 60 * 60  # seconds

    # LLM client settings
    CLIENT_LLM_URL: str | None = os.getenv("CLIENT_LLM_URL")
    CLIENT_LLM_KEY: str | None = os.getenv("CLIENT_LLM_KEY")
    CLIENT_LLM_TIMEOUT: int = int(os.getenv("CLIENT_LLM_TIMEOUT", "1200"))

    # Answering Machine client settings
    CLIENT_ANSWERING_MACHINE_URL: str | None = os.getenv("CLIENT_ANSWERING_MACHINE_URL")
    CLIENT_ANSWERING_MACHINE_KEY: str | None = os.getenv("CLIENT_ANSWERING_MACHINE_KEY")
    CLIENT_ANSWERING_MACHINE_TIMEOUT: int = int(
        os.getenv("CLIENT_ANSWERING_MACHINE_TIMEOUT", "100")
    )

    # Codebot client settings
    CLIENT_CODEBOT_URL: str | None = os.getenv("CLIENT_CODEBOT_URL")
    CLIENT_CODEBOT_KEY: str | None = os.getenv("CLIENT_CODEBOT_KEY")
    CLIENT_CODEBOT_TIMEOUT: int = int(os.getenv("CLIENT_CODEBOT_TIMEOUT", "100"))

    # CORS settings - disabled by default for security
    CORS_ORIGINS: str | None = os.getenv("CORS_ORIGINS")  # None = CORS disabled
    CORS_METHODS: str = os.getenv(
        "CORS_METHODS", "GET,HEAD,PUT,PATCH,POST,DELETE,OPTIONS"
    )
    CORS_ALLOW_HEADERS: str = os.getenv("CORS_ALLOW_HEADERS", "*")
    CORS_EXPOSE_HEADERS: str | None = os.getenv("CORS_EXPOSE_HEADERS")
    CORS_SUPPORTS_CREDENTIALS: bool = (
        os.getenv("CORS_SUPPORTS_CREDENTIALS", "false").lower() == "true"
    )
    CORS_MAX_AGE: int | None = None

    # Celery configuration settings
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "memory://")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "cache+memory://")
    CELERY_TASK_MONITORING: bool = (
        os.getenv("CELERY_TASK_MONITORING", "true").lower() == "true"
    )
    CELERY_TASK_TIME_LIMIT: int = int(
        os.getenv("CELERY_TASK_TIME_LIMIT", "1800")
    )  # 30 minutes
    CELERY_TASK_SOFT_TIME_LIMIT: int = int(
        os.getenv("CELERY_TASK_SOFT_TIME_LIMIT", "1500")
    )  # 25 minutes
    CELERY_WORKER_MAX_TASKS: int = int(
        os.getenv("CELERY_WORKER_MAX_TASKS", "100")
    )  # Max tasks before worker restart
    CELERY_TASK_SERIALIZER: str = os.getenv("CELERY_TASK_SERIALIZER", "json")
    CELERY_RESULT_SERIALIZER: str = os.getenv("CELERY_RESULT_SERIALIZER", "json")
    CELERY_ACCEPT_CONTENT: ClassVar[list[str]] = ["json"]
    CELERY_TASK_TRACK_STARTED: bool = (
        os.getenv("CELERY_TASK_TRACK_STARTED", "true").lower() == "true"
    )
    CELERY_TASK_SEND_SENT_EVENT: bool = (
        os.getenv("CELERY_TASK_SEND_SENT_EVENT", "true").lower() == "true"
    )
    CELERY_TASK_ACKS_LATE: bool = (
        os.getenv("CELERY_TASK_ACKS_LATE", "true").lower() == "true"
    )
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = int(
        os.getenv("CELERY_WORKER_PREFETCH_MULTIPLIER", "1")
    )
    CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP: bool = (
        os.getenv("CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP", "true").lower() == "true"
    )
    CELERY_TASK_DEFAULT_QUEUE: str = os.getenv("CELERY_TASK_DEFAULT_QUEUE", "default")
    CELERY_TIMEZONE: str = os.getenv("CELERY_TIMEZONE", "UTC")
    CELERY_ENABLE_UTC: bool = os.getenv("CELERY_ENABLE_UTC", "true").lower() == "true"
    # Broker transport options - for Redis broker, set visibility_timeout to prevent
    # task re-delivery for long-running tasks with acks_late=True
    CELERY_BROKER_TRANSPORT_OPTIONS: ClassVar[dict[str, Any]] = {
        "visibility_timeout": int(
            os.getenv("CELERY_VISIBILITY_TIMEOUT", "21600")
        ),  # 6 hours default
    }

    def __init__(self) -> None:
        """Initialize configuration with validation.

        This validates the configuration based on the selected algorithm:
        - For RS256: requires either JWT_PUBLIC_KEY or JWT_PUBLIC_KEY_PATH
        - For HS256: requires JWT_SECRET_KEY
        """
        # Parse CORS_MAX_AGE from environment if set
        cors_max_age_str = os.getenv("CORS_MAX_AGE")
        if cors_max_age_str:
            try:
                self.CORS_MAX_AGE = int(cors_max_age_str)
            except ValueError:
                logger.warning(
                    f"Invalid CORS_MAX_AGE value: {cors_max_age_str}. Using None."
                )
                self.CORS_MAX_AGE = None

        # Skip validation for testing
        if getattr(self, "SKIP_VALIDATION", False):
            return

        # Secret key must be set in production
        if not self.DEBUG and not self.SECRET_KEY:
            raise ValueError("SECRET_KEY must be set in production environments.")

        # For RS256 (asymmetric) authentication
        if self.JWT_ALGORITHM == "RS256":
            self._validate_rs256_config()
        # For HS256 (symmetric) authentication
        elif self.JWT_ALGORITHM == "HS256":
            self._validate_hs256_config()
        else:
            raise ValueError(
                f"Unsupported JWT algorithm: {self.JWT_ALGORITHM}. "
                "Supported algorithms are 'RS256' and 'HS256'."
            )

    def _validate_public_key_format(self, public_key: str) -> None:
        """Validate that the public key has proper PEM format.

        Args:
            public_key: The public key string to validate

        Raises:
            ValueError: If the public key format is invalid

        """
        # Remove leading/trailing whitespace for validation
        key = public_key.strip()

        # Check for proper PEM format markers
        if not key.startswith("-----BEGIN PUBLIC KEY-----"):
            raise ValueError(
                "JWT_PUBLIC_KEY must start with '-----BEGIN PUBLIC KEY-----'. "
                "Found malformed public key format."
            )

        if not key.endswith("-----END PUBLIC KEY-----"):
            raise ValueError(
                "JWT_PUBLIC_KEY must end with '-----END PUBLIC KEY-----'. "
                "Found malformed public key format."
            )

        # Additional validation: check that there's actual content between headers
        lines = key.split("\n")
        # Filter out the BEGIN/END lines and empty lines
        content_lines = [
            line.strip()
            for line in lines
            if line.strip() and not line.startswith("-----")
        ]

        if not content_lines:
            raise ValueError(
                "JWT_PUBLIC_KEY appears to be empty. "
                "The key must contain valid base64-encoded key data between the PEM headers."
            )

        # Basic base64 validation - check if content looks like base64
        base64_pattern = re.compile(r"^[A-Za-z0-9+/=\s]+$")
        key_content = "".join(content_lines)
        if not base64_pattern.match(key_content):
            raise ValueError(
                "JWT_PUBLIC_KEY contains invalid characters. "
                "The key content must be valid base64-encoded data."
            )

    def _validate_rs256_config(self) -> None:
        """Validate RS256 configuration settings."""
        if self.JWT_PUBLIC_KEY and self.JWT_PUBLIC_KEY_PATH:
            raise ValueError(
                "Both JWT_PUBLIC_KEY and JWT_PUBLIC_KEY_PATH are set. "
                "Please provide only one of them."
            )
        elif not self.JWT_PUBLIC_KEY and not self.JWT_PUBLIC_KEY_PATH:
            raise ValueError(
                "Either JWT_PUBLIC_KEY or JWT_PUBLIC_KEY_PATH must be set "
                "when using RS256."
            )
        elif self.JWT_PUBLIC_KEY_PATH and not self.JWT_PUBLIC_KEY:
            path = Path(self.JWT_PUBLIC_KEY_PATH)
            if path.exists():
                with open(path, encoding="utf-8") as f:
                    self.JWT_PUBLIC_KEY = f.read()
            else:
                raise ValueError(f"JWT_PUBLIC_KEY_PATH '{path}' does not exist.")

        # Validate the public key format after loading it
        if self.JWT_PUBLIC_KEY:
            self._validate_public_key_format(self.JWT_PUBLIC_KEY)

    def _validate_hs256_config(self) -> None:
        """Validate HS256 configuration settings."""
        if not self.JWT_SECRET_KEY:
            raise ValueError(
                "JWT_SECRET_KEY must be set in production when using HS256 algorithm."
            )


class BaseDevelopmentConfig(BaseConfig):
    """Development configuration for local development environments.

    Provides defaults that make development easier with minimal setup.
    """

    # Enable debugging features
    DEBUG: bool = True

    # Default database is SQLite for easy development
    SQLALCHEMY_DATABASE_URI: str = os.getenv("DATABASE_URI", "sqlite:///dev.sqlite3")

    # Default secret key for development (DO NOT use in production)
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-key-not-for-production")

    # Development-friendly Celery settings
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "memory://")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "cache+memory://")
    CELERY_TASK_TIME_LIMIT: int = int(
        os.getenv("CELERY_TASK_TIME_LIMIT", "300")
    )  # 5 minutes for dev
    CELERY_TASK_SOFT_TIME_LIMIT: int = int(
        os.getenv("CELERY_TASK_SOFT_TIME_LIMIT", "240")
    )  # 4 minutes for dev


class BaseProductionConfig(BaseConfig):
    """Production configuration for deployment.

    Prioritizes security and requires proper environment configuration.
    """

    # Disable debugging features in production
    DEBUG: bool = False
    TESTING: bool = False

    # These need to be explicitly set from environment in production
    # SECRET_KEY = os.getenv("SECRET_KEY")  # This is intentionally not set to force proper configuration
    # SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI")  # This is intentionally not set to force proper configuration

    # Production-optimized Celery settings
    # Use Redis or RabbitMQ in production, not memory broker
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv(
        "CELERY_RESULT_BACKEND", "redis://localhost:6379/0"
    )
    CELERY_TASK_TIME_LIMIT: int = int(
        os.getenv("CELERY_TASK_TIME_LIMIT", "18000")
    )  # 5 hours for production
    CELERY_TASK_SOFT_TIME_LIMIT: int = int(
        os.getenv("CELERY_TASK_SOFT_TIME_LIMIT", "16200")
    )  # 4.5 hours for production
    CELERY_WORKER_MAX_TASKS: int = int(
        os.getenv("CELERY_WORKER_MAX_TASKS", "1000")
    )  # Higher for production workloads
    CELERY_RESULT_EXPIRES: int = int(
        os.getenv("CELERY_RESULT_EXPIRES", "21600")
    )  # 6 hours - results persist longer than max task time
    # For production, visibility_timeout should exceed the maximum task time limit
    CELERY_BROKER_TRANSPORT_OPTIONS: ClassVar[dict[str, Any]] = {
        "visibility_timeout": int(
            os.getenv("CELERY_VISIBILITY_TIMEOUT", "21600")
        ),  # 6 hours default, exceeds 5h task limit
    }


class BaseTestingConfig(BaseConfig):
    """Testing configuration for unit and integration tests.

    Provides fast, isolated test environment with in-memory database.
    """

    # Enable testing features
    TESTING: bool = True
    DEBUG: bool = False

    # Use in-memory SQLite for speed
    # Match the BaseConfig type for compatibility
    SQLALCHEMY_DATABASE_URI: str | None = "sqlite:///:memory:"

    # Fixed secret key for test reproducibility
    # Match the BaseConfig type for compatibility
    SECRET_KEY: str | None = "testing-secret-key"

    # HS256 is easier for testing
    JWT_ALGORITHM: str = "HS256"
    # Match the BaseConfig type for compatibility
    JWT_SECRET_KEY: str | None = "testing-secret-key"

    # Skip validation in tests
    SKIP_VALIDATION: bool = True

    # Shortened token expiration for faster testing
    JWT_ACCESS_TOKEN_EXPIRES: int = 60  # 1 minute

    # Testing-specific Celery settings
    CELERY_BROKER_URL: str = "memory://"
    CELERY_RESULT_BACKEND: str = "cache+memory://"
    CELERY_TASK_TIME_LIMIT: int = 60  # 1 minute for tests
    CELERY_TASK_SOFT_TIME_LIMIT: int = 50  # 50 seconds for tests
    CELERY_WORKER_MAX_TASKS: int = 10  # Lower for tests
    CELERY_TASK_ALWAYS_EAGER: bool = True  # Execute tasks synchronously in tests
    CELERY_TASK_EAGER_PROPAGATES: bool = True  # Propagate exceptions in eager mode
