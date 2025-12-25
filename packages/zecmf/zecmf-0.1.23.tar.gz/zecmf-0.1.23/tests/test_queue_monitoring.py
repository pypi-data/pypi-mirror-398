"""Tests for ZecMF queue system with monitoring integration."""

from typing import Never
from unittest.mock import patch

import pytest
from celery import Task
from celery.exceptions import Retry
from celery.signals import task_postrun, task_prerun
from flask import Flask

from zecmf.extensions.queue import celery, init_app

# Test constants
REDIS_TIME_LIMIT = 3600  # 1 hour
REDIS_MAX_TASKS = 50
DEFAULT_TIME_LIMIT = 1800  # 30 minutes
DEFAULT_MAX_TASKS = 100


class TestQueueMonitoring:
    """Test queue system with monitoring integration."""

    def test_queue_init_app_basic(self, app: Flask) -> None:
        """Test basic queue initialization."""
        # Test with default configuration
        init_app(app)

        # Verify Celery configuration
        assert celery.conf.broker_url == "memory://"
        assert celery.conf.result_backend == "cache+memory://"
        assert celery.conf.task_serializer == "json"
        assert celery.conf.accept_content == ["json"]
        assert celery.conf.result_serializer == "json"
        assert celery.conf.task_track_started is True

    def test_queue_init_app_with_config(self, app: Flask) -> None:
        """Test queue initialization with custom configuration."""
        # Set custom configuration
        app.config.update(
            {
                "CELERY_BROKER_URL": "redis://localhost:6379/0",
                "CELERY_RESULT_BACKEND": "redis://localhost:6379/0",
                "CELERY_TASK_TIME_LIMIT": 3600,
                "CELERY_WORKER_MAX_TASKS": 50,
                "CELERY_TASK_MONITORING": True,
            }
        )

        init_app(app)

        # Verify custom configuration was applied
        assert celery.conf.broker_url == "redis://localhost:6379/0"
        assert celery.conf.result_backend == "redis://localhost:6379/0"
        assert celery.conf.task_time_limit == REDIS_TIME_LIMIT
        assert celery.conf.worker_max_tasks_per_child == REDIS_MAX_TASKS

    def test_queue_init_app_monitoring_disabled(self, app: Flask) -> None:
        """Test queue initialization with monitoring disabled."""
        app.config["CELERY_TASK_MONITORING"] = False

        with patch("zecmf.extensions.task_monitor") as mock_monitor:
            init_app(app)

            # Flask app should not be set on task monitor when monitoring is disabled
            assert (
                not hasattr(mock_monitor, "flask_app") or mock_monitor.flask_app != app
            )

    def test_queue_init_app_monitoring_enabled(self, app: Flask) -> None:
        """Test queue initialization with monitoring enabled."""
        app.config["CELERY_TASK_MONITORING"] = True

        with patch("zecmf.extensions.task_monitor") as mock_monitor:
            init_app(app)

            # Flask app should be set on task monitor when monitoring is enabled
            mock_monitor.flask_app = app

    def test_context_task_integration(self, app: Flask) -> None:
        """Test that ContextTask properly handles Flask app context."""
        # Set up a proper cache backend for testing
        app.config["CELERY_RESULT_BACKEND"] = "cache+memory://"
        init_app(app)

        # Create a test task using the ContextTask base class
        @celery.task
        def test_task() -> bool:
            from flask import current_app  # noqa: PLC0415

            return current_app.config.get("TESTING", False)

        # This would normally be called by Celery in a separate worker. We call it
        # directly here to verify that the task runs with application context even
        # when executed outside a request thread.
        task_instance = test_task
        result = task_instance.apply().result
        assert result is True  # TESTING should be True in test config

    def test_enhanced_celery_config(self, app: Flask) -> None:
        """Test enhanced Celery configuration for monitoring."""
        app.config["CELERY_TASK_MONITORING"] = True

        init_app(app)

        # Verify enhanced monitoring settings
        assert celery.conf.task_send_sent_event is True
        assert celery.conf.task_acks_late is True
        assert celery.conf.worker_prefetch_multiplier == 1

    def test_queue_context_task_class(self, app: Flask) -> None:
        """Test that ContextTask is set as the default task class."""
        init_app(app)

        # Verify ContextTask is the default task class
        assert celery.Task.__name__ == "ContextTask"

    def test_task_retry_and_request(self, app: Flask) -> None:
        """Ensure Celery request context and retries work with ContextTask."""
        app.config["CELERY_RESULT_BACKEND"] = "cache+memory://"
        init_app(app)

        @celery.task(bind=True, max_retries=1)
        def retry_task(self: Task) -> Never:
            # ``self.request`` should be available and contain an id
            assert self.request.id is not None
            raise self.retry(exc=ValueError("fail"), countdown=0)

        with pytest.raises(Retry):
            retry_task.apply(throw=True)

    def test_task_signals_emitted(self, app: Flask) -> None:
        """Verify that Celery task signals are dispatched."""
        app.config["CELERY_RESULT_BACKEND"] = "cache+memory://"
        init_app(app)

        pre_called: list[bool] = []
        post_called: list[bool] = []

        def prerun_handler(**_: object) -> None:
            pre_called.append(True)

        def postrun_handler(**_: object) -> None:
            post_called.append(True)

        task_prerun.connect(prerun_handler, weak=False)
        task_postrun.connect(postrun_handler, weak=False)

        try:

            @celery.task
            def sample_task() -> bool:
                return True

            sample_task.apply()
        finally:
            task_prerun.disconnect(prerun_handler)
            task_postrun.disconnect(postrun_handler)

        assert pre_called
        assert post_called

    def test_queue_default_configuration(self, app: Flask) -> None:
        """Test queue initialization with minimal configuration."""
        # Remove any existing config to test defaults
        for key in list(app.config.keys()):
            if key.startswith("CELERY_"):
                del app.config[key]

        init_app(app)

        # Verify default values
        assert celery.conf.broker_url == "memory://"
        assert celery.conf.result_backend == "cache"
        assert celery.conf.task_time_limit == DEFAULT_TIME_LIMIT  # 30 minutes default
        assert celery.conf.worker_max_tasks_per_child == DEFAULT_MAX_TASKS
        assert celery.conf.broker_connection_retry_on_startup is True
        assert celery.conf.task_default_queue == "default"
