"""Task monitoring utilities for ZecMF queue system.

Provides decorators and functions for tracking Celery task executions with
comprehensive monitoring, logging, and retry capabilities.
"""

import functools
import sys
import traceback
from collections.abc import Callable
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, ParamSpec, TypeVar

from celery import current_task
from celery.exceptions import Retry
from flask import Flask, has_app_context

if TYPE_CHECKING:
    from celery import Task

from zecmf.extensions.database import db
from zecmf.models.task_monitoring import (
    TaskExecution,
    TaskExecutionLog,
    TaskExecutionLogLevel,
    TaskExecutionStatus,
)
from zecmf.services.schemas.task_monitoring import (
    ExceptionContext,
    RetryStrategy,
    TaskContext,
    TaskError,
)

# Global app instance set by application workers
flask_app: Flask | None = None

# Type variables for decorator
P = ParamSpec("P")
T = TypeVar("T")


def with_app_context(func: Callable[P, T]) -> Callable[P, T | None]:  # noqa: UP047
    """Ensure Flask app context is available for task functions."""

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T | None:
        if has_app_context():
            return func(*args, **kwargs)
        elif flask_app:
            with flask_app.app_context():
                return func(*args, **kwargs)
        else:
            # No app context available, skip monitoring
            return None

    return wrapper


class TaskLogger:
    """Logger for task execution events with batched writes."""

    def __init__(self, task_execution_id: int) -> None:
        """Initialize the task logger with a task execution ID."""
        self.task_execution_id = task_execution_id
        self._pending_logs: list[TaskExecutionLog] = []

    @with_app_context
    def log(
        self,
        level: TaskExecutionLogLevel,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Add a log entry for the task execution."""
        log_entry = TaskExecutionLog(
            task_execution_id=self.task_execution_id,
            level=level,
            message=message,
            context=context,
        )
        db.session.add(log_entry)
        db.session.commit()

    def debug(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Log a debug message."""
        self.log(TaskExecutionLogLevel.DEBUG, message, context)

    def info(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Log an info message."""
        self.log(TaskExecutionLogLevel.INFO, message, context)

    def warning(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Log a warning message."""
        self.log(TaskExecutionLogLevel.WARNING, message, context)

    def error(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Log an error message."""
        self.log(TaskExecutionLogLevel.ERROR, message, context)

    def critical(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Log a critical message."""
        self.log(TaskExecutionLogLevel.CRITICAL, message, context)

    def exception(
        self,
        message: str,
        exc_info: bool | tuple | BaseException = True,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Log an error message with exception information.

        Args:
            message: The error message to log.
            exc_info: If True, exception info is added to the logging message.
                     Can also be an exception tuple or an exception instance.
            context: Additional context data to include with the log entry.

        """
        # Extract exception context using typed schema
        exc_context = ExceptionContext()
        if exc_info:
            if exc_info is True:
                # Get current exception info from sys
                exc_type, exc_value, exc_traceback = sys.exc_info()
                if exc_type:
                    exc_context = ExceptionContext(
                        exception_type=exc_type.__name__,
                        exception_message=str(exc_value),
                        traceback=traceback.format_exc(),
                    )
            elif isinstance(exc_info, tuple) and len(exc_info) == 3:  # noqa: PLR2004
                # exc_info is a tuple (type, value, traceback)
                exc_type, exc_value, exc_traceback = exc_info
                if exc_type:
                    exc_context = ExceptionContext(
                        exception_type=exc_type.__name__ if exc_type else None,
                        exception_message=str(exc_value) if exc_value else None,
                        traceback="".join(
                            traceback.format_exception(
                                exc_type, exc_value, exc_traceback
                            )
                        ),
                    )
            elif isinstance(exc_info, BaseException):
                # exc_info is an exception instance
                exc_context = ExceptionContext(
                    exception_type=type(exc_info).__name__,
                    exception_message=str(exc_info),
                    traceback="".join(
                        traceback.format_exception(
                            type(exc_info), exc_info, exc_info.__traceback__
                        )
                    ),
                )

        # Build final context with exception information
        final_context = context.copy() if context else {}
        if not exc_context.is_empty():
            final_context.update(exc_context.to_dict())

        # Log as error level with exception context
        self.log(TaskExecutionLogLevel.ERROR, message, final_context)


@with_app_context
def get_task_execution(task_id: str) -> TaskExecution | None:
    """Get a task execution record by task ID."""
    task_execution = db.session.query(TaskExecution).filter_by(task_id=task_id).first()
    if task_execution:
        # Ensure it's merged into the current session to avoid DetachedInstanceError
        task_execution = db.session.merge(task_execution)
    return task_execution


@with_app_context
def create_task_execution(
    task_id: str,
    task_name: str,
    args: list[Any] | None = None,
    kwargs: dict[str, Any] | None = None,
    context: TaskContext | None = None,
) -> TaskExecution:
    """Create a new task execution record.

    Args:
        task_id: Unique Celery task ID
        task_name: Name of the task function
        args: Task positional arguments (must be JSON-serializable)
        kwargs: Task keyword arguments (must be JSON-serializable)
        context: Explicit task context for linking to domain objects

    """
    task_execution = TaskExecution(
        task_id=task_id,
        task_name=task_name,
        status=TaskExecutionStatus.PENDING,
        args=args,
        kwargs=kwargs,
        context_id=context.context_id if context else None,
        context_type=context.context_type if context else None,
        context_step=context.context_step if context else None,
    )
    db.session.add(task_execution)
    db.session.commit()
    return task_execution


@with_app_context
def update_task_status(
    task_execution: TaskExecution,
    status: TaskExecutionStatus,
    result: dict[str, Any] | None = None,
    error_message: str | None = None,
    traceback_str: str | None = None,
) -> None:
    """Update task execution status and related fields."""
    # Merge the object to the current session to avoid DetachedInstanceError
    task_execution = db.session.merge(task_execution)

    task_execution.status = status
    task_execution.updated_at = datetime.now(UTC)

    if status == TaskExecutionStatus.RUNNING and not task_execution.started_at:
        task_execution.started_at = datetime.now(UTC)

    if status in {TaskExecutionStatus.SUCCESS, TaskExecutionStatus.FAILURE}:
        task_execution.completed_at = datetime.now(UTC)
        if task_execution.started_at:
            # Ensure both datetimes have the same timezone handling
            started_at = task_execution.started_at
            completed_at = task_execution.completed_at

            # If started_at is naive, make it UTC-aware
            if started_at.tzinfo is None:
                started_at = started_at.replace(tzinfo=UTC)

            # If completed_at is naive, make it UTC-aware
            if completed_at.tzinfo is None:
                completed_at = completed_at.replace(tzinfo=UTC)

            duration = completed_at - started_at
            task_execution.duration_seconds = duration.total_seconds()

    if result is not None:
        task_execution.result = result

    if error_message:
        task_execution.error_message = error_message

    if traceback_str:
        task_execution.traceback = traceback_str

    db.session.commit()


def _handle_task_retry(
    task_id: str,
    task_name: str,
    task_instance: "Task | None",
    exc: Exception,
    retry_strategy: RetryStrategy,
) -> None:
    """Handle retry logic for failed tasks. Raises Retry exception if retrying."""
    if not (task_instance and hasattr(task_instance, "request")):
        return

    current_retries = getattr(task_instance.request, "retries", 0)

    # Check if we should skip retry for TaskError with retry=False
    if isinstance(exc, TaskError) and not exc.should_retry:
        return

    if current_retries >= retry_strategy.max_retries:
        return

    # Log the retry attempt
    log_task_message(
        task_id,
        TaskExecutionLogLevel.WARNING,
        f"Task {task_name} failed, attempting retry {current_retries + 1}/{retry_strategy.max_retries + 1}: {exc}",
        {"retry_count": current_retries + 1, "error": str(exc)},
    )

    # Update status to retry
    update_task_status_by_id(
        task_id,
        TaskExecutionStatus.RETRY,
        error_message=str(exc),
        retry_count=current_retries + 1,
    )

    # Calculate countdown using retry strategy
    countdown = retry_strategy.calculate_countdown(current_retries)

    # Trigger retry (this will raise Retry exception)
    task_instance.retry(countdown=countdown, exc=exc)


def _filter_serializable_args(args: tuple) -> list[Any]:
    """Filter out non-serializable task instances from arguments."""
    serializable_args = []
    for i, arg in enumerate(args):
        # Skip the first argument if it looks like a task instance (from bind=True)
        if i == 0 and (
            hasattr(arg, "retry")
            or hasattr(arg, "request")
            or "task" in str(type(arg)).lower()
            or hasattr(arg, "__name__")
        ):
            continue
        serializable_args.append(arg)
    return serializable_args


def monitored_task(  # noqa: C901
    context: TaskContext | None = None,
    retry_strategy: RetryStrategy | None = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Monitor Celery task execution with comprehensive tracking.

    Args:
        context: Explicit task context for linking to domain objects.
                If not provided, context won't be extracted automatically.
        retry_strategy: Custom retry strategy. Defaults to exponential backoff
                       with 3 retries.

    Example:
        ```python
        @celery.task(bind=True)
        @monitored_task(
            context=TaskContext(context_id=project_id, context_type=ContextType.PROJECT),
            retry_strategy=RetryStrategy(max_retries=5, strategy="linear")
        )
        def process_project(self, project_id: int) -> dict[str, Any]:
            # Task implementation
            return {"status": "completed"}
        ```

    """
    if retry_strategy is None:
        retry_strategy = RetryStrategy()

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Get task info
            task_id = (
                getattr(current_task.request, "id", None) if current_task else None
            )
            task_name = func.__name__

            # Filter serializable args for logging
            serializable_args = _filter_serializable_args(args)  # type: ignore[arg-type]

            # Initialize monitoring
            if task_id:
                ensure_task_execution_exists(
                    task_id=task_id,
                    task_name=task_name,
                    args=serializable_args,
                    kwargs=dict(kwargs),
                    context=context,
                )

            try:
                # Update status to running
                if task_id:
                    # Get current retry count from Celery
                    current_retries = (
                        getattr(current_task.request, "retries", 0)
                        if current_task
                        else 0
                    )
                    update_task_status_by_id(
                        task_id,
                        TaskExecutionStatus.RUNNING,
                        retry_count=current_retries,
                    )
                    log_task_message(
                        task_id,
                        TaskExecutionLogLevel.INFO,
                        f"Started task {task_name}",
                        {"args": serializable_args, "kwargs": dict(kwargs)},
                    )

                # Execute the actual task
                result = func(*args, **kwargs)

                # Task completed successfully
                if task_id:
                    # Convert result to dict if possible, otherwise store as-is
                    result_dict = (
                        result if isinstance(result, dict) else {"result": result}
                    )  # type: ignore[dict-item]
                    update_task_status_by_id(
                        task_id,
                        TaskExecutionStatus.SUCCESS,
                        result=result_dict,  # type: ignore[arg-type]
                    )
                    log_task_message(
                        task_id,
                        TaskExecutionLogLevel.INFO,
                        f"Completed task {task_name} successfully",
                        {"result": result_dict},
                    )
            except Retry:
                # Don't catch Celery's Retry exception - let it propagate
                raise
            except Exception as e:
                error_message = str(e)
                traceback_str = traceback.format_exc()

                # Try to retry if applicable
                if task_id:
                    task_instance = (
                        args[0]  # type: ignore[misc]
                        if args and hasattr(args[0], "retry")
                        else None
                    )
                    # Attempt retry - raises Retry exception if successful
                    _handle_task_retry(
                        task_id, task_name, task_instance, e, retry_strategy
                    )
                    # If we get here, retry was not triggered - mark as failure
                    update_task_status_by_id(
                        task_id,
                        TaskExecutionStatus.FAILURE,
                        error_message=error_message,
                        traceback_str=traceback_str,
                    )
                    log_task_message(
                        task_id,
                        TaskExecutionLogLevel.CRITICAL,
                        f"Task {task_name} failed: {error_message}",
                        {"traceback": traceback_str},
                    )

                # Re-raise the exception
                raise
            else:
                return result

        return wrapper  # type: ignore[return-value]

    return decorator


@with_app_context
def ensure_task_execution_exists(
    task_id: str,
    task_name: str,
    args: list[Any] | None = None,
    kwargs: dict[str, Any] | None = None,
    context: TaskContext | None = None,
) -> None:
    """Ensure a task execution record exists."""
    existing = db.session.query(TaskExecution).filter_by(task_id=task_id).first()
    if not existing:
        task_execution = TaskExecution(
            task_id=task_id,
            task_name=task_name,
            status=TaskExecutionStatus.PENDING,
            args=args,
            kwargs=kwargs,
            context_id=context.context_id if context else None,
            context_type=context.context_type if context else None,
            context_step=context.context_step if context else None,
        )
        db.session.add(task_execution)
        db.session.commit()


@with_app_context
def update_task_status_by_id(
    task_id: str,
    status: TaskExecutionStatus,
    result: dict[str, Any] | None = None,
    error_message: str | None = None,
    traceback_str: str | None = None,
    retry_count: int | None = None,
) -> None:
    """Update task execution status by task ID."""
    task_execution = db.session.query(TaskExecution).filter_by(task_id=task_id).first()
    if not task_execution:
        return  # Task not found, skip silently

    task_execution.status = status
    task_execution.updated_at = datetime.now(UTC)

    if retry_count is not None:
        task_execution.retry_count = retry_count

    # Update timing based on status
    _update_task_timing(task_execution, status)

    if result is not None:
        task_execution.result = result

    if error_message:
        task_execution.error_message = error_message

    if traceback_str:
        task_execution.traceback = traceback_str

    db.session.commit()


def _update_task_timing(
    task_execution: TaskExecution, status: TaskExecutionStatus
) -> None:
    """Update task timing based on status."""
    if status == TaskExecutionStatus.RUNNING and not task_execution.started_at:
        task_execution.started_at = datetime.now(UTC)

    if status in {TaskExecutionStatus.SUCCESS, TaskExecutionStatus.FAILURE}:
        task_execution.completed_at = datetime.now(UTC)
        if task_execution.started_at:
            # Ensure both datetimes have the same timezone handling
            started_at = task_execution.started_at
            completed_at = task_execution.completed_at

            # If started_at is naive, make it UTC-aware
            if started_at.tzinfo is None:
                started_at = started_at.replace(tzinfo=UTC)

            # If completed_at is naive, make it UTC-aware
            if completed_at.tzinfo is None:
                completed_at = completed_at.replace(tzinfo=UTC)

            duration = completed_at - started_at
            task_execution.duration_seconds = duration.total_seconds()


@with_app_context
def log_task_message(
    task_id: str,
    level: TaskExecutionLogLevel,
    message: str,
    context: dict[str, Any] | None = None,
) -> None:
    """Log a message for a task by task ID."""
    # Get the task execution ID
    task_execution = db.session.query(TaskExecution).filter_by(task_id=task_id).first()
    if not task_execution:
        return  # Task not found, skip silently

    log_entry = TaskExecutionLog(
        task_execution_id=task_execution.id,
        level=level,
        message=message,
        context=context,
    )
    db.session.add(log_entry)
    db.session.commit()


def log_task_event(
    task_id: str,
    level: TaskExecutionLogLevel,
    message: str,
    context: dict[str, Any] | None = None,
) -> None:
    """Log an event for a specific task."""
    log_task_message(task_id, level, message, context)
