"""Tests for ZecMF task monitoring system."""

from typing import Any, Never
from unittest.mock import patch

import pytest
from celery import Task
from celery.exceptions import Retry
from flask import Flask
from sqlalchemy import asc

from zecmf.extensions import task_monitor
from zecmf.extensions.database import db
from zecmf.extensions.task_monitor import (
    TaskLogger,
    create_task_execution,
    ensure_task_execution_exists,
    get_task_execution,
    log_task_message,
    monitored_task,
    update_task_status_by_id,
    with_app_context,
)
from zecmf.models.task_monitoring import (
    TaskExecution,
    TaskExecutionLog,
    TaskExecutionLogLevel,
    TaskExecutionStatus,
)
from zecmf.services.schemas.task_monitoring import (
    ContextType,
    RetryStrategy,
    TaskContext,
    TaskError,
)

# Test constants
EXPECTED_LOG_COUNT = 2
EXPECTED_LOG_COUNT_MULTIPLE = 5
TEST_CONTEXT_ID_123 = 123
TEST_CONTEXT_ID_456 = 456
TEST_CONTEXT_ID_100 = 100
TEST_CONTEXT_ID_200 = 200
TEST_CONTEXT_ID_999 = 999
TEST_CONTEXT_STEP_5 = 5
TEST_CONTEXT_STEP_3 = 3
TEST_RETRY_BASE_DELAY = 60
TEST_RETRY_DELAY_120 = 120
TEST_RETRY_DELAY_180 = 180
TEST_RETRY_DELAY_240 = 240


class TestTaskMonitoringModels:
    """Test task monitoring database models."""

    def test_task_execution_creation(self, app: Flask) -> None:
        """Test creating a TaskExecution instance."""
        with app.app_context():
            task_execution = TaskExecution(
                task_id="test-task-123",
                task_name="test_task",
                status=TaskExecutionStatus.PENDING,
            )
            db.session.add(task_execution)
            db.session.commit()

            assert task_execution.id is not None
            assert task_execution.task_id == "test-task-123"
            assert task_execution.task_name == "test_task"
            assert task_execution.status == TaskExecutionStatus.PENDING
            assert task_execution.retry_count == 0

    def test_task_execution_to_dict(self, app: Flask) -> None:
        """Test TaskExecution to_dict method."""
        with app.app_context():
            task_execution = TaskExecution(
                task_id="test-task-123",
                task_name="test_task",
                status=TaskExecutionStatus.SUCCESS,
                args=[1, 2, 3],
                kwargs={"key": "value"},
                result={"status": "ok"},
            )
            db.session.add(task_execution)
            db.session.commit()

            task_dict = task_execution.to_dict()
            assert task_dict["task_id"] == "test-task-123"
            assert task_dict["task_name"] == "test_task"
            assert task_dict["status"] == TaskExecutionStatus.SUCCESS.value
            assert task_dict["args"] == [1, 2, 3]
            assert task_dict["kwargs"] == {"key": "value"}
            assert task_dict["result"] == {"status": "ok"}

    def test_task_execution_log_creation(self, app: Flask) -> None:
        """Test creating a TaskExecutionLog instance."""
        with app.app_context():
            # Create parent task execution
            task_execution = TaskExecution(
                task_id="test-task-123",
                task_name="test_task",
                status=TaskExecutionStatus.RUNNING,
            )
            db.session.add(task_execution)
            db.session.commit()

            # Create log entry
            log_entry = TaskExecutionLog(
                task_execution_id=task_execution.id,
                level=TaskExecutionLogLevel.INFO,
                message="Task started",
                context={"step": 1},
            )
            db.session.add(log_entry)
            db.session.commit()

            assert log_entry.id is not None
            assert log_entry.task_execution_id == task_execution.id
            assert log_entry.level == TaskExecutionLogLevel.INFO
            assert log_entry.message == "Task started"
            assert log_entry.context == {"step": 1}

    def test_task_execution_log_relationship(self, app: Flask) -> None:
        """Test TaskExecution and TaskExecutionLog relationship."""
        with app.app_context():
            # Create parent task execution
            task_execution = TaskExecution(
                task_id="test-task-123",
                task_name="test_task",
                status=TaskExecutionStatus.RUNNING,
            )
            db.session.add(task_execution)
            db.session.commit()

            # Create multiple log entries
            log1 = TaskExecutionLog(
                task_execution_id=task_execution.id,
                level=TaskExecutionLogLevel.INFO,
                message="Task started",
            )
            log2 = TaskExecutionLog(
                task_execution_id=task_execution.id,
                level=TaskExecutionLogLevel.INFO,
                message="Task progress",
            )
            db.session.add_all([log1, log2])
            db.session.commit()

            # Test relationship
            assert len(task_execution.logs) == EXPECTED_LOG_COUNT
            assert log1.task_execution == task_execution
            assert log2.task_execution == task_execution

    def test_task_execution_enum_persistence(self, app: Flask) -> None:
        """Test that TaskExecutionStatus enum persists correctly to database."""
        with app.app_context():
            # Create task with enum status
            task = TaskExecution(
                task_id="test-enum-123",
                task_name="test_enum_task",
                status=TaskExecutionStatus.RUNNING,
            )
            db.session.add(task)
            db.session.commit()
            task_id = task.id

            # Clear session to force reload from DB
            db.session.expunge_all()

            # Reload and verify enum type is preserved
            reloaded = db.session.query(TaskExecution).filter_by(id=task_id).first()
            assert reloaded is not None
            assert isinstance(reloaded.status, TaskExecutionStatus)
            assert reloaded.status == TaskExecutionStatus.RUNNING
            assert reloaded.status.value == "running"

    def test_task_execution_log_level_enum_persistence(self, app: Flask) -> None:
        """Test that TaskExecutionLogLevel enum persists correctly to database."""
        with app.app_context():
            # Create task execution and log
            task = TaskExecution(
                task_id="test-log-enum-123",
                task_name="test_log_enum",
                status=TaskExecutionStatus.RUNNING,
            )
            db.session.add(task)
            db.session.commit()

            log = TaskExecutionLog(
                task_execution_id=task.id,
                level=TaskExecutionLogLevel.WARNING,
                message="Test warning",
            )
            db.session.add(log)
            db.session.commit()
            log_id = log.id

            # Clear session to force reload
            db.session.expunge_all()

            # Reload and verify enum type
            reloaded = db.session.query(TaskExecutionLog).filter_by(id=log_id).first()
            assert reloaded is not None
            assert isinstance(reloaded.level, TaskExecutionLogLevel)
            assert reloaded.level == TaskExecutionLogLevel.WARNING
            assert reloaded.level.value == "warning"

    def test_task_execution_json_column_persistence(self, app: Flask) -> None:
        """Test that JSON columns persist correctly without manual serialization."""
        with app.app_context():
            # Create task with complex JSON data
            complex_args = [1, "string", {"nested": "dict"}, [1, 2, 3]]
            complex_kwargs = {
                "key1": "value1",
                "key2": 123,
                "key3": {"nested": True},
                "key4": [1, 2, 3],
            }
            complex_result = {
                "status": "completed",
                "data": {"items": [1, 2, 3], "count": 3},
            }

            task = TaskExecution(
                task_id="test-json-123",
                task_name="test_json_task",
                status=TaskExecutionStatus.SUCCESS,
                args=complex_args,
                kwargs=complex_kwargs,
                result=complex_result,
            )
            db.session.add(task)
            db.session.commit()
            task_id = task.id

            # Clear session
            db.session.expunge_all()

            # Reload and verify JSON data is intact
            reloaded = db.session.query(TaskExecution).filter_by(id=task_id).first()
            assert reloaded is not None
            assert reloaded.args == complex_args
            assert reloaded.kwargs == complex_kwargs
            assert reloaded.result == complex_result
            assert isinstance(reloaded.args, list)
            assert isinstance(reloaded.kwargs, dict)
            assert isinstance(reloaded.result, dict)

    def test_task_execution_log_json_context_persistence(self, app: Flask) -> None:
        """Test that log context JSON column persists correctly."""
        with app.app_context():
            task = TaskExecution(
                task_id="test-log-json-123",
                task_name="test_log_json",
                status=TaskExecutionStatus.RUNNING,
            )
            db.session.add(task)
            db.session.commit()

            # Create log with complex JSON context
            complex_context = {
                "step": 1,
                "action": "processing",
                "metadata": {"user_id": 123, "items": [1, 2, 3]},
            }
            log = TaskExecutionLog(
                task_execution_id=task.id,
                level=TaskExecutionLogLevel.INFO,
                message="Processing step",
                context=complex_context,
            )
            db.session.add(log)
            db.session.commit()
            log_id = log.id

            # Clear session
            db.session.expunge_all()

            # Reload and verify
            reloaded = db.session.query(TaskExecutionLog).filter_by(id=log_id).first()
            assert reloaded is not None
            assert reloaded.context == complex_context
            assert isinstance(reloaded.context, dict)


class TestTaskContext:
    """Test TaskContext schema."""

    def test_task_context_creation(self) -> None:
        """Test creating a TaskContext instance."""
        context = TaskContext(
            context_id=TEST_CONTEXT_ID_123,
            context_type=ContextType.PROJECT,
            context_step=TEST_CONTEXT_STEP_5,
        )
        assert context.context_id == TEST_CONTEXT_ID_123
        assert context.context_type == ContextType.PROJECT
        assert context.context_step == TEST_CONTEXT_STEP_5

    def test_task_context_to_dict(self) -> None:
        """Test TaskContext to_dict method."""
        context = TaskContext(
            context_id=TEST_CONTEXT_ID_456,
            context_type=ContextType.USER,
        )
        context_dict = context.to_dict()
        assert context_dict["context_id"] == TEST_CONTEXT_ID_456
        assert context_dict["context_type"] == "user"
        assert context_dict["context_step"] is None


class TestRetryStrategy:
    """Test RetryStrategy schema."""

    def test_exponential_backoff(self) -> None:
        """Test exponential backoff strategy."""
        strategy = RetryStrategy(
            max_retries=3,
            base_delay_seconds=TEST_RETRY_BASE_DELAY,
            strategy="exponential",
        )
        assert strategy.calculate_countdown(0) == TEST_RETRY_BASE_DELAY
        assert strategy.calculate_countdown(1) == TEST_RETRY_DELAY_120
        assert strategy.calculate_countdown(2) == TEST_RETRY_DELAY_240

    def test_linear_backoff(self) -> None:
        """Test linear backoff strategy."""
        strategy = RetryStrategy(
            max_retries=3,
            base_delay_seconds=TEST_RETRY_BASE_DELAY,
            strategy="linear",
        )
        assert strategy.calculate_countdown(0) == TEST_RETRY_BASE_DELAY
        assert strategy.calculate_countdown(1) == TEST_RETRY_DELAY_120
        assert strategy.calculate_countdown(2) == TEST_RETRY_DELAY_180

    def test_constant_backoff(self) -> None:
        """Test constant backoff strategy."""
        strategy = RetryStrategy(
            max_retries=3,
            base_delay_seconds=TEST_RETRY_BASE_DELAY,
            strategy="constant",
        )
        assert strategy.calculate_countdown(0) == TEST_RETRY_BASE_DELAY
        assert strategy.calculate_countdown(1) == TEST_RETRY_BASE_DELAY
        assert strategy.calculate_countdown(2) == TEST_RETRY_BASE_DELAY


class TestTaskMonitorUtilities:
    """Test task monitoring utility functions."""

    def test_with_app_context_decorator(self, app: Flask) -> None:
        """Test with_app_context decorator."""

        @with_app_context
        def test_function() -> str:
            return "success"

        # Test with app context
        with app.app_context():
            result = test_function()
            assert result == "success"

        # Test with flask_app fallback
        original_flask_app = task_monitor.flask_app
        task_monitor.flask_app = app
        with app.app_context():
            result = test_function()
            assert result == "success"
        task_monitor.flask_app = original_flask_app

    def test_create_task_execution(self, app: Flask) -> None:
        """Test create_task_execution function."""
        with app.app_context():
            context = TaskContext(
                context_id=TEST_CONTEXT_ID_100,
                context_type=ContextType.PROJECT,
                context_step=1,
            )
            task_execution = create_task_execution(
                task_id="test-task-456",
                task_name="test_create_task",
                args=[1, 2, 3],
                kwargs={"key": "value"},
                context=context,
            )

            assert task_execution is not None
            assert task_execution.task_id == "test-task-456"
            assert task_execution.task_name == "test_create_task"
            assert task_execution.status == TaskExecutionStatus.PENDING
            assert task_execution.args == [1, 2, 3]
            assert task_execution.kwargs == {"key": "value"}
            assert task_execution.context_id == TEST_CONTEXT_ID_100
            assert task_execution.context_type == "project"
            assert task_execution.context_step == 1

    def test_get_task_execution(self, app: Flask) -> None:
        """Test get_task_execution function."""
        with app.app_context():
            # Create a task execution
            original = create_task_execution(
                task_id="test-task-789", task_name="test_get_task"
            )

            # Get it back
            retrieved = get_task_execution("test-task-789")
            assert retrieved is not None
            assert original is not None
            assert retrieved.task_id == original.task_id
            assert retrieved.task_name == original.task_name

            # Test non-existent task
            non_existent = get_task_execution("non-existent")
            assert non_existent is None

    def test_ensure_task_execution_exists(self, app: Flask) -> None:
        """Test ensure_task_execution_exists function."""
        with app.app_context():
            context = TaskContext(
                context_id=TEST_CONTEXT_ID_200, context_type=ContextType.USER
            )
            # First call should create the task
            ensure_task_execution_exists(
                task_id="test-ensure-123",
                task_name="test_ensure_task",
                args=[1, 2],
                kwargs={"test": True},
                context=context,
            )

            task = get_task_execution("test-ensure-123")
            assert task is not None
            assert task.task_name == "test_ensure_task"
            assert task.context_id == TEST_CONTEXT_ID_200
            assert task.context_type == "user"

            # Second call should not create duplicate
            ensure_task_execution_exists(
                task_id="test-ensure-123",
                task_name="test_ensure_task_updated",
            )

            # Should still be the original task
            task = get_task_execution("test-ensure-123")
            assert task is not None
            assert task.task_name == "test_ensure_task"  # Original name preserved

    def test_update_task_status_by_id(self, app: Flask) -> None:
        """Test update_task_status_by_id function."""
        with app.app_context():
            # Create a task execution
            create_task_execution(
                task_id="test-update-456", task_name="test_update_task"
            )

            # Update to running
            update_task_status_by_id(
                task_id="test-update-456",
                status=TaskExecutionStatus.RUNNING,
            )

            updated_task = get_task_execution("test-update-456")
            assert updated_task is not None
            assert updated_task.status == TaskExecutionStatus.RUNNING
            assert updated_task.started_at is not None

            # Update to success with result
            update_task_status_by_id(
                task_id="test-update-456",
                status=TaskExecutionStatus.SUCCESS,
                result={"output": "success"},
            )

            updated_task = get_task_execution("test-update-456")
            assert updated_task is not None
            assert updated_task.status == TaskExecutionStatus.SUCCESS
            assert updated_task.completed_at is not None
            assert updated_task.duration_seconds is not None
            assert updated_task.result == {"output": "success"}

    def test_log_task_message(self, app: Flask) -> None:
        """Test log_task_message function."""
        with app.app_context():
            # Create a task execution
            task = create_task_execution(
                task_id="test-log-789", task_name="test_log_task"
            )

            # Log a message
            log_task_message(
                task_id="test-log-789",
                level=TaskExecutionLogLevel.INFO,
                message="Test log message",
                context={"step": 1, "action": "test"},
            )

            # Verify the log was created
            assert task is not None
            log_entry = (
                db.session.query(TaskExecutionLog)
                .filter_by(task_execution_id=task.id)
                .first()
            )
            assert log_entry is not None
            assert log_entry.level == TaskExecutionLogLevel.INFO
            assert log_entry.message == "Test log message"
            assert log_entry.context == {"step": 1, "action": "test"}

    def test_task_logger_class(self, app: Flask) -> None:
        """Test TaskLogger class."""
        with app.app_context():
            # Create a task execution
            task = create_task_execution(
                task_id="test-logger-123", task_name="test_logger_task"
            )

            # Create logger and test different log levels
            assert task is not None
            logger = TaskLogger(task.id)
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            logger.critical("Critical message")

            # Verify all logs were created
            assert task is not None
            logs = (
                db.session.query(TaskExecutionLog)
                .filter_by(task_execution_id=task.id)
                .order_by(asc("timestamp"))
                .all()
            )
            assert len(logs) == EXPECTED_LOG_COUNT_MULTIPLE
            assert logs[0].level == TaskExecutionLogLevel.DEBUG
            assert logs[1].level == TaskExecutionLogLevel.INFO
            assert logs[2].level == TaskExecutionLogLevel.WARNING
            assert logs[3].level == TaskExecutionLogLevel.ERROR
            assert logs[4].level == TaskExecutionLogLevel.CRITICAL

    def test_task_logger_exception_method(self, app: Flask) -> None:
        """Test TaskLogger exception method."""
        with app.app_context():
            # Create a task execution
            task = create_task_execution(
                task_id="test-exception-123", task_name="test_exception_task"
            )

            assert task is not None
            logger = TaskLogger(task.id)

            # Test with current exception context
            try:
                raise ValueError("Test exception")  # noqa: TRY301
            except ValueError:
                logger.exception("An error occurred")

            # Test with custom context
            try:
                raise RuntimeError("Another test exception")  # noqa: TRY301
            except RuntimeError as e:
                logger.exception("Custom error", exc_info=e, context={"custom": "data"})

            # Test with exc_info=False (no exception info)
            logger.exception("No exception info", exc_info=False)

            # Verify logs were created
            logs = (
                db.session.query(TaskExecutionLog)
                .filter_by(task_execution_id=task.id)
                .order_by(asc("timestamp"))
                .all()
            )

            assert len(logs) == 3  # noqa: PLR2004

            # Check first log (with automatic exception info)
            assert logs[0].level == TaskExecutionLogLevel.ERROR
            assert logs[0].message == "An error occurred"
            context1 = logs[0].context
            assert context1 is not None
            assert context1["exception_type"] == "ValueError"
            assert context1["exception_message"] == "Test exception"
            assert "traceback" in context1

            # Check second log (with explicit exception and custom context)
            assert logs[1].level == TaskExecutionLogLevel.ERROR
            assert logs[1].message == "Custom error"
            context2 = logs[1].context
            assert context2 is not None
            assert context2["exception_type"] == "RuntimeError"
            assert context2["exception_message"] == "Another test exception"
            assert "traceback" in context2
            assert context2["custom"] == "data"

            # Check third log (no exception info)
            assert logs[2].level == TaskExecutionLogLevel.ERROR
            assert logs[2].message == "No exception info"
            # Context should be empty or minimal when exc_info=False
            if logs[2].context:
                context3 = logs[2].context
                assert "exception_type" not in context3
                assert "traceback" not in context3


class TestRetryEdgeCases:
    """Test retry strategy edge cases."""

    def test_retry_max_retries_reached(self, app: Flask) -> None:
        """Test that task fails when max retries is reached."""
        with app.app_context():
            retry_strategy = RetryStrategy(
                max_retries=3,
                base_delay_seconds=10,
                strategy="constant",
            )

            class MockTaskInstance:
                def __init__(self) -> None:
                    self.request = type("obj", (object,), {"retries": 3})()

                def retry(self, countdown: int, exc: Exception) -> None:
                    # Should not be called when retries exhausted
                    msg = "Retry should not be called when max retries reached"
                    raise AssertionError(msg)

            @monitored_task(retry_strategy=retry_strategy)
            def test_max_retry_task(self: MockTaskInstance) -> Never:
                raise ValueError("Always fails")

            with patch("zecmf.extensions.task_monitor.current_task") as mock_current:
                mock_current.request.id = "test-max-retry-123"
                mock_current.request.retries = 3

                mock_instance = MockTaskInstance()

                # Should raise ValueError, not Retry
                with pytest.raises(ValueError, match="Always fails"):
                    test_max_retry_task(mock_instance)

                # Task should be marked as FAILURE
                task_execution = get_task_execution("test-max-retry-123")
                assert task_execution is not None
                assert task_execution.status == TaskExecutionStatus.FAILURE

    def test_retry_with_non_retryable_task_error(self, app: Flask) -> None:
        """Test that TaskError with retry=False does not retry."""
        with app.app_context():

            class MockTaskInstance:
                def __init__(self) -> None:
                    self.request = type("obj", (object,), {"retries": 0})()

                def retry(self, countdown: int, exc: Exception) -> None:
                    msg = "Retry should not be called for non-retryable TaskError"
                    raise AssertionError(msg)

            @monitored_task()
            def test_non_retryable_task(self: MockTaskInstance) -> Never:
                raise TaskError("Non-retryable error", retry=False)

            with patch("zecmf.extensions.task_monitor.current_task") as mock_current:
                mock_current.request.id = "test-non-retryable-123"
                mock_current.request.retries = 0

                mock_instance = MockTaskInstance()

                with pytest.raises(TaskError, match="Non-retryable error"):
                    test_non_retryable_task(mock_instance)

                # Should be marked as FAILURE, not RETRY
                task_execution = get_task_execution("test-non-retryable-123")
                assert task_execution is not None
                assert task_execution.status == TaskExecutionStatus.FAILURE

    def test_retry_strategy_with_zero_delay(self, app: Flask) -> None:
        """Test retry strategy with zero base delay."""
        strategy = RetryStrategy(
            max_retries=3,
            base_delay_seconds=0,
            strategy="exponential",
        )
        assert strategy.calculate_countdown(0) == 0
        assert strategy.calculate_countdown(1) == 0
        assert strategy.calculate_countdown(2) == 0

    def test_retry_preserves_original_exception(self, app: Flask) -> None:
        """Test that retry preserves original exception information."""
        with app.app_context():

            class MockTaskInstance:
                def __init__(self) -> None:
                    self.request = type("obj", (object,), {"retries": 0})()
                    self.retry_exc: Exception | None = None

                def retry(self, countdown: int, exc: Exception) -> None:
                    # Capture the exception passed to retry
                    self.retry_exc = exc
                    raise Retry("Retrying", exc=exc)

            @monitored_task()
            def test_exception_preservation(self: MockTaskInstance) -> Never:
                raise ValueError("Original error message")

            with patch("zecmf.extensions.task_monitor.current_task") as mock_current:
                mock_current.request.id = "test-exception-preserve-123"
                mock_current.request.retries = 0

                mock_instance = MockTaskInstance()

                with pytest.raises(Retry):
                    test_exception_preservation(mock_instance)

                # Verify original exception was preserved
                assert mock_instance.retry_exc is not None
                assert isinstance(mock_instance.retry_exc, ValueError)
                assert str(mock_instance.retry_exc) == "Original error message"


class TestMonitoredTaskDecorator:
    """Test the monitored_task decorator."""

    def test_monitored_task_success(self, app: Flask) -> None:
        """Test monitored_task decorator with successful task."""
        with app.app_context():

            @monitored_task()
            def test_successful_task(x: int, y: int) -> dict[str, int]:
                return {"result": x + y}

            # Mock current_task
            with patch("zecmf.extensions.task_monitor.current_task") as mock_task:
                mock_task.request.id = "test-success-123"
                mock_task.request.retries = 0

                result = test_successful_task(5, 3)

                assert result == {"result": 8}

                # Verify task execution was created and updated
                task_execution = get_task_execution("test-success-123")
                assert task_execution is not None
                assert task_execution.status == TaskExecutionStatus.SUCCESS
                assert task_execution.result == {"result": 8}

    def test_monitored_task_with_context(self, app: Flask) -> None:
        """Test monitored_task decorator with explicit context."""
        with app.app_context():
            context = TaskContext(
                context_id=TEST_CONTEXT_ID_999,
                context_type=ContextType.PROJECT,
                context_step=TEST_CONTEXT_STEP_3,
            )

            @monitored_task(context=context)
            def test_context_task(value: int) -> dict[str, int]:
                return {"value": value * 2}

            with patch("zecmf.extensions.task_monitor.current_task") as mock_task:
                mock_task.request.id = "test-context-123"
                mock_task.request.retries = 0

                result = test_context_task(10)

                assert result == {"value": 20}

                task_execution = get_task_execution("test-context-123")
                assert task_execution is not None
                assert task_execution.context_id == TEST_CONTEXT_ID_999
                assert task_execution.context_type == "project"
                assert task_execution.context_step == TEST_CONTEXT_STEP_3

    def test_monitored_task_failure(self, app: Flask) -> None:
        """Test monitored_task decorator with failing task."""
        with app.app_context():

            @monitored_task()
            def test_failing_task() -> Never:
                raise ValueError("Test error")

            # Mock current_task
            with patch("zecmf.extensions.task_monitor.current_task") as mock_task:
                mock_task.request.id = "test-failure-456"
                mock_task.request.retries = 0

                with pytest.raises(ValueError, match="Test error"):
                    test_failing_task()

                # Verify task execution was marked as failed
                task_execution = get_task_execution("test-failure-456")
                assert task_execution is not None
                assert task_execution.status == TaskExecutionStatus.FAILURE
                assert "Test error" in task_execution.error_message

    def test_monitored_task_with_custom_retry_strategy(self, app: Flask) -> None:
        """Test monitored_task with custom retry strategy."""
        with app.app_context():
            retry_strategy = RetryStrategy(
                max_retries=5,
                base_delay_seconds=30,
                strategy="linear",
            )

            # Create a mock task instance with retry method
            class MockTaskInstance:
                def __init__(self) -> None:
                    self.request = type("obj", (object,), {"retries": 0})()

                def retry(self, countdown: int, exc: Exception) -> None:
                    # Verify countdown is calculated correctly (linear strategy)
                    expected_countdown = 30 * (0 + 1)  # first retry
                    assert countdown == expected_countdown
                    raise Retry("Retrying", exc=exc)

            @monitored_task(retry_strategy=retry_strategy)
            def test_retry_task(
                self: MockTaskInstance, should_fail: bool = True
            ) -> dict[str, str]:
                if should_fail:
                    raise ValueError("Retry me")
                return {"status": "ok"}

            with patch("zecmf.extensions.task_monitor.current_task") as mock_current:
                mock_current.request.id = "test-retry-123"
                mock_current.request.retries = 0

                mock_instance = MockTaskInstance()

                with pytest.raises(Retry):
                    # Call with self parameter to simulate bind=True
                    test_retry_task(mock_instance, should_fail=True)

                # Verify retry status was set
                task_execution = get_task_execution("test-retry-123")
                assert task_execution is not None
                assert task_execution.status == TaskExecutionStatus.RETRY

    def test_monitored_task_with_task_error(self, app: Flask) -> None:
        """Test monitored_task with TaskError exception."""
        with app.app_context():

            @monitored_task()
            def test_task_error() -> Never:
                raise TaskError("Task failed", context={"reason": "test"}, retry=False)

            with patch("zecmf.extensions.task_monitor.current_task") as mock_task:
                mock_task.request.id = "test-task-error-123"
                mock_task.request.retries = 0

                with pytest.raises(TaskError):
                    test_task_error()

                task_execution = get_task_execution("test-task-error-123")
                assert task_execution is not None
                assert task_execution.status == TaskExecutionStatus.FAILURE
                assert "Task failed" in task_execution.error_message

    def test_monitored_task_without_celery_context(self, app: Flask) -> None:
        """Test monitored_task decorator without Celery task context."""
        with app.app_context():

            @monitored_task()
            def test_no_context_task() -> str:
                return "success"

            # Test without mocking current_task (simulates no Celery context)
            result = test_no_context_task()
            assert result == "success"

            # No task execution should be created since there's no task_id
            tasks = db.session.query(TaskExecution).all()
            assert len(tasks) == 0

    def test_monitored_task_non_dict_result(self, app: Flask) -> None:
        """Test monitored_task with non-dict return value."""
        with app.app_context():

            @monitored_task()
            def test_string_result_task() -> str:
                return "simple string result"

            with patch("zecmf.extensions.task_monitor.current_task") as mock_task:
                mock_task.request.id = "test-string-result-123"
                mock_task.request.retries = 0

                result = test_string_result_task()

                assert result == "simple string result"

                task_execution = get_task_execution("test-string-result-123")
                assert task_execution is not None
                assert task_execution.status == TaskExecutionStatus.SUCCESS
                assert task_execution.result == {"result": "simple string result"}


class TestLoggingWithJSONContext:
    """Test logging with complex JSON context data."""

    def test_logger_with_nested_json_context(self, app: Flask) -> None:
        """Test TaskLogger with deeply nested JSON context."""
        with app.app_context():
            task = create_task_execution(
                task_id="test-nested-json-123", task_name="test_nested_json"
            )
            assert task is not None
            logger = TaskLogger(task.id)

            nested_context = {
                "level1": {
                    "level2": {
                        "level3": {"data": [1, 2, 3], "flag": True},
                        "items": ["a", "b", "c"],
                    },
                    "count": 42,
                },
                "metadata": {"user_id": 123, "session_id": "abc-123"},
            }

            logger.info("Nested context test", context=nested_context)

            logs = (
                db.session.query(TaskExecutionLog)
                .filter_by(task_execution_id=task.id)
                .all()
            )
            assert len(logs) == 1
            assert logs[0].context == nested_context

    def test_logger_with_empty_context(self, app: Flask) -> None:
        """Test TaskLogger with None and empty dict context."""
        with app.app_context():
            task = create_task_execution(
                task_id="test-empty-context-123", task_name="test_empty_context"
            )
            assert task is not None
            logger = TaskLogger(task.id)

            logger.info("Message with no context")
            logger.info("Message with empty dict", context={})
            logger.info("Message with None", context=None)

            logs = (
                db.session.query(TaskExecutionLog)
                .filter_by(task_execution_id=task.id)
                .order_by(asc("timestamp"))
                .all()
            )
            assert len(logs) == 3  # noqa: PLR2004
            assert logs[0].context is None
            assert logs[1].context == {}
            assert logs[2].context is None

    def test_logger_with_unicode_and_special_chars(self, app: Flask) -> None:
        """Test TaskLogger with unicode and special characters in context."""
        with app.app_context():
            task = create_task_execution(
                task_id="test-unicode-123", task_name="test_unicode"
            )
            assert task is not None
            logger = TaskLogger(task.id)

            unicode_context = {
                "message": "Hello 世界 🌍",
                "special": "Special chars: <>\"'&\n\t",
                "emoji": "✅ ❌ ⚠️",
            }

            logger.info("Unicode test", context=unicode_context)

            logs = (
                db.session.query(TaskExecutionLog)
                .filter_by(task_execution_id=task.id)
                .all()
            )
            assert len(logs) == 1
            assert logs[0].context == unicode_context

    def test_logger_exception_with_complex_context(self, app: Flask) -> None:
        """Test exception logging with complex context."""
        with app.app_context():
            task = create_task_execution(
                task_id="test-exception-context-123", task_name="test_exception_context"
            )
            assert task is not None
            logger = TaskLogger(task.id)

            custom_context = {
                "request_id": "req-123",
                "user_data": {"id": 456, "role": "admin"},
                "operation": "data_processing",
            }

            try:
                raise RuntimeError("Test exception with context")  # noqa: TRY301
            except RuntimeError:
                logger.exception("Operation failed", context=custom_context)

            logs = (
                db.session.query(TaskExecutionLog)
                .filter_by(task_execution_id=task.id)
                .all()
            )
            assert len(logs) == 1
            log_context = logs[0].context
            assert log_context is not None
            assert log_context["exception_type"] == "RuntimeError"
            assert "traceback" in log_context
            assert log_context["request_id"] == "req-123"
            assert log_context["user_data"] == {"id": 456, "role": "admin"}

    def test_multiple_loggers_same_task(self, app: Flask) -> None:
        """Test multiple TaskLogger instances for same task."""
        with app.app_context():
            task = create_task_execution(
                task_id="test-multi-logger-123", task_name="test_multi_logger"
            )
            assert task is not None

            logger1 = TaskLogger(task.id)
            logger2 = TaskLogger(task.id)

            logger1.info("Message from logger 1", context={"source": "logger1"})
            logger2.warning("Message from logger 2", context={"source": "logger2"})

            logs = (
                db.session.query(TaskExecutionLog)
                .filter_by(task_execution_id=task.id)
                .order_by(asc("timestamp"))
                .all()
            )
            assert len(logs) == EXPECTED_LOG_COUNT
            assert logs[0].context == {"source": "logger1"}
            assert logs[1].context == {"source": "logger2"}


class TestTaskMonitoringIntegration:
    """Integration tests for complete task monitoring workflows."""

    def test_complete_task_lifecycle_with_context_and_logging(self, app: Flask) -> None:
        """Test complete task lifecycle with context, logging, and retry."""
        with app.app_context():
            context = TaskContext(
                context_id=100,
                context_type=ContextType.PROJECT,
                context_step=1,
            )

            retry_strategy = RetryStrategy(
                max_retries=2, base_delay_seconds=5, strategy="linear"
            )

            @monitored_task(context=context, retry_strategy=retry_strategy)
            def integration_task(self: Task, data: dict[str, Any]) -> dict[str, Any]:
                task_exec = get_task_execution(self.request.id)
                if task_exec:
                    logger = TaskLogger(task_exec.id)
                    logger.info("Task started", context={"data": data})
                    logger.debug("Processing step 1", context={"step": 1})
                    logger.info("Task completed", context={"result": "success"})
                return {"status": "completed", "processed": data}

            with patch("zecmf.extensions.task_monitor.current_task") as mock_task:
                mock_task.request.id = "test-integration-123"
                mock_task.request.retries = 0

                result = integration_task(mock_task, {"input": "test_data"})

                assert result == {
                    "status": "completed",
                    "processed": {"input": "test_data"},
                }

                # Verify task execution
                task_exec = get_task_execution("test-integration-123")
                assert task_exec is not None
                assert task_exec.status == TaskExecutionStatus.SUCCESS
                assert task_exec.context_id == 100  # noqa: PLR2004
                assert task_exec.context_type == "project"
                assert task_exec.context_step == 1

                # Verify logs (decorator adds automatic logs)
                logs = (
                    db.session.query(TaskExecutionLog)
                    .filter_by(task_execution_id=task_exec.id)
                    .order_by(asc("timestamp"))
                    .all()
                )
                assert len(logs) == 5  # noqa: PLR2004
                # Check our custom logs (skip decorator's automatic logs)
                assert logs[1].message == "Task started"
                assert logs[2].message == "Processing step 1"
                assert logs[3].message == "Task completed"

    def test_task_with_all_status_transitions(self, app: Flask) -> None:
        """Test task status transitions through multiple retries."""
        with app.app_context():
            # Create initial task
            task = create_task_execution(
                task_id="test-transitions-123",
                task_name="test_transitions",
            )
            assert task is not None
            assert task.status == TaskExecutionStatus.PENDING

            # Update to RUNNING
            update_task_status_by_id(
                task_id="test-transitions-123",
                status=TaskExecutionStatus.RUNNING,
            )
            task = get_task_execution("test-transitions-123")
            assert task is not None
            assert task.status == TaskExecutionStatus.RUNNING
            assert task.started_at is not None

            # Update to RETRY
            update_task_status_by_id(
                task_id="test-transitions-123",
                status=TaskExecutionStatus.RETRY,
                error_message="Temporary error",
            )
            task = get_task_execution("test-transitions-123")
            assert task is not None
            assert task.status == TaskExecutionStatus.RETRY

            # Update to RUNNING again
            update_task_status_by_id(
                task_id="test-transitions-123",
                status=TaskExecutionStatus.RUNNING,
            )

            # Finally to SUCCESS
            update_task_status_by_id(
                task_id="test-transitions-123",
                status=TaskExecutionStatus.SUCCESS,
                result={"final": "result"},
            )
            task = get_task_execution("test-transitions-123")
            assert task is not None
            assert task.status == TaskExecutionStatus.SUCCESS
            assert task.completed_at is not None
            assert task.duration_seconds is not None
            assert task.result == {"final": "result"}
