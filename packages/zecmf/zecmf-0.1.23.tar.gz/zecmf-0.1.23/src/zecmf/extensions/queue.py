"""Queue extension module.

Sets up Celery for asynchronous task processing with Flask integration
and comprehensive task monitoring capabilities.
"""

from celery import Celery, Task
from flask import Flask

celery = Celery()


def init_app(app: Flask) -> None:
    """Initialize Celery with the Flask app and task monitoring."""
    # Build Celery configuration from Flask app config
    # Use get() with defaults for backward compatibility
    celery_config = {
        "broker_url": app.config.get("CELERY_BROKER_URL", "memory://"),
        "result_backend": app.config.get("CELERY_RESULT_BACKEND", "cache"),
        "task_serializer": app.config.get("CELERY_TASK_SERIALIZER", "json"),
        "result_serializer": app.config.get("CELERY_RESULT_SERIALIZER", "json"),
        "accept_content": app.config.get("CELERY_ACCEPT_CONTENT", ["json"]),
        "task_track_started": app.config.get("CELERY_TASK_TRACK_STARTED", True),
        "task_time_limit": app.config.get("CELERY_TASK_TIME_LIMIT", 1800),
        "task_soft_time_limit": app.config.get("CELERY_TASK_SOFT_TIME_LIMIT", 1500),
        "worker_max_tasks_per_child": app.config.get("CELERY_WORKER_MAX_TASKS", 100),
        "broker_connection_retry_on_startup": app.config.get(
            "CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP", True
        ),
        "task_default_queue": app.config.get("CELERY_TASK_DEFAULT_QUEUE", "default"),
        "timezone": app.config.get("CELERY_TIMEZONE", "UTC"),
        "enable_utc": app.config.get("CELERY_ENABLE_UTC", True),
        "result_expires": app.config.get("CELERY_RESULT_EXPIRES", 3600),
        # Enhanced monitoring settings
        "task_send_sent_event": app.config.get("CELERY_TASK_SEND_SENT_EVENT", True),
        "task_acks_late": app.config.get("CELERY_TASK_ACKS_LATE", True),
        "worker_prefetch_multiplier": app.config.get(
            "CELERY_WORKER_PREFETCH_MULTIPLIER", 1
        ),
    }

    # Add broker_transport_options if configured (primarily for Redis broker)
    # This is critical for preventing task re-delivery with acks_late=True
    broker_transport_options = app.config.get("CELERY_BROKER_TRANSPORT_OPTIONS")
    if broker_transport_options:
        celery_config["broker_transport_options"] = broker_transport_options

    # Add testing-specific settings if present
    if "CELERY_TASK_ALWAYS_EAGER" in app.config:
        celery_config["task_always_eager"] = app.config["CELERY_TASK_ALWAYS_EAGER"]
    if "CELERY_TASK_EAGER_PROPAGATES" in app.config:
        celery_config["task_eager_propagates"] = app.config[
            "CELERY_TASK_EAGER_PROPAGATES"
        ]

    celery.conf.update(celery_config)

    class ContextTask(Task):
        """Base task class that ensures tasks run within a Flask app context."""

        def __call__(self, *args: object, **kwargs: object) -> object:
            """Execute task within the Flask application context.

            Wrapping ``super().__call__`` instead of calling ``self.run``
            directly preserves Celery's built-in request handling, retries and
            signal dispatching while still ensuring that a Flask application
            context is active during task execution.
            """
            with app.app_context():
                return super().__call__(*args, **kwargs)

    # Assign ContextTask directly to the Celery application
    celery.Task = ContextTask

    # Set up task monitoring if enabled
    if app.config.get("CELERY_TASK_MONITORING", True):
        # Make Flask app available to task monitor
        from zecmf.extensions import task_monitor  # noqa: PLC0415

        task_monitor.flask_app = app
