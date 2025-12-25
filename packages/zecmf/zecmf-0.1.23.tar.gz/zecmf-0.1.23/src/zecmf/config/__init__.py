"""Configuration module for micro-framework."""

import importlib
import logging

from zecmf.config.base import (
    BaseConfig,
    BaseDevelopmentConfig,
    BaseProductionConfig,
    BaseTestingConfig,
)
from zecmf.config.base import (
    BaseTestingConfig as TestingConfig,  # Alias required for tests
)

logger = logging.getLogger(__name__)


def get_config(config_name: str, app_config_module: str) -> type[BaseConfig]:
    """Get the configuration class by name, with optional app-specific overrides.

    This function allows application-specific configurations to extend the
    framework's base configurations. It will look for a class with the same name
    as the requested config_name in the app config module and return it if found.

    Args:
        config_name: The name of the configuration to get ("development", "testing", etc.).
        app_config_module: The module path for the app-specific configuration.

    Returns:
        The appropriate configuration class, with app overrides if available.

    """
    try:
        app_config = importlib.import_module(app_config_module)
        app_config_class_name = f"{config_name.capitalize()}Config"
        if not hasattr(app_config, app_config_class_name):
            raise AttributeError(
                f"Config class {app_config_class_name} not found in {app_config_module}."
            )

        app_config_class = getattr(app_config, app_config_class_name)
        base_class = getattr(app_config, "BaseConfig", BaseConfig)
        if not issubclass(app_config_class, base_class):
            raise TypeError(
                f"App config class {app_config_class_name} is not a subclass of BaseConfig."
            )

    except ImportError as e:
        raise ImportError(
            f"Failed to import app config module '{app_config_module}': {e}"
        ) from e
    else:
        logger.debug(f"Using app config class: {app_config_class.__name__}")
        return app_config_class


__all__ = [
    "BaseConfig",
    "BaseDevelopmentConfig",
    "BaseProductionConfig",
    "BaseTestingConfig",
    "TestingConfig",
    "get_config",
]
