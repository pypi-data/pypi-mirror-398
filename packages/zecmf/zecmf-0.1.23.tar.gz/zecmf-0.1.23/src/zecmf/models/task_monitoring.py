"""Task monitoring models for ZecMF queue system.

Provides comprehensive tracking for asynchronous task executions including
execution status, timing, retry counts, and detailed logging.
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, Index
from sqlalchemy import Enum as SQLAEnum

from zecmf.extensions.database import db


class TaskExecutionStatus(StrEnum):
    """Status values for task executions."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"
    REVOKED = "revoked"


class TaskExecutionLogLevel(StrEnum):
    """Log level values for task execution logs."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class TaskExecution(db.Model):
    """Model for tracking all async task executions."""

    __tablename__ = "task_executions"
    __allow_unmapped__ = True

    id: int = db.Column(db.Integer, primary_key=True)
    task_id: str = db.Column(db.String(255), nullable=False, unique=True, index=True)
    task_name: str = db.Column(db.String(255), nullable=False, index=True)
    status: TaskExecutionStatus = db.Column(
        SQLAEnum(TaskExecutionStatus, native_enum=False, length=30),
        nullable=False,
        default=TaskExecutionStatus.PENDING,
        index=True,
    )

    # Execution details
    started_at: datetime = db.Column(db.DateTime, nullable=True)
    completed_at: datetime = db.Column(db.DateTime, nullable=True)
    duration_seconds: float = db.Column(db.Float, nullable=True)
    retry_count: int = db.Column(db.Integer, default=0)

    # Task metadata - using JSON type for structured data
    args: dict[str, Any] | list[Any] | None = db.Column(JSON, nullable=True)
    kwargs: dict[str, Any] | None = db.Column(JSON, nullable=True)
    result: dict[str, Any] | None = db.Column(JSON, nullable=True)
    error_message: str = db.Column(db.Text, nullable=True)
    traceback: str = db.Column(db.Text, nullable=True)

    # Context information (optional - applications can add more specific context)
    worker_name: str = db.Column(db.String(255), nullable=True)

    # Application-specific context fields
    context_id: int = db.Column(db.Integer, nullable=True, index=True)
    context_type: str = db.Column(db.String(50), nullable=True, index=True)
    context_step: int = db.Column(db.Integer, nullable=True)

    # Timestamps
    created_at: datetime = db.Column(
        db.DateTime, default=lambda: datetime.now(UTC), index=True
    )
    updated_at: datetime = db.Column(
        db.DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationship to logs
    logs = db.relationship(
        "TaskExecutionLog",
        back_populates="task_execution",
        cascade="all, delete-orphan",
        order_by="TaskExecutionLog.timestamp",
    )

    # Composite indexes for common query patterns
    __table_args__ = (
        Index("ix_task_executions_context", "context_type", "context_id"),
        Index("ix_task_executions_status_created", "status", "created_at"),
    )

    def __repr__(self) -> str:
        """Return string representation of the task execution."""
        return f"<TaskExecution {self.id}: {self.task_name} ({self.status.value})>"

    def to_dict(self) -> dict[str, Any]:
        """Convert the model instance to a dictionary."""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "task_name": self.task_name,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "duration_seconds": self.duration_seconds,
            "retry_count": self.retry_count,
            "args": self.args,
            "kwargs": self.kwargs,
            "result": self.result,
            "error_message": self.error_message,
            "traceback": self.traceback,
            "worker_name": self.worker_name,
            "context_id": self.context_id,
            "context_type": self.context_type,
            "context_step": self.context_step,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "log_count": len(self.logs) if self.logs else 0,
        }


class TaskExecutionLog(db.Model):
    """Model for storing detailed logs from task executions."""

    __tablename__ = "task_execution_logs"
    __allow_unmapped__ = True

    id: int = db.Column(db.Integer, primary_key=True)
    task_execution_id: int = db.Column(
        db.Integer, db.ForeignKey("task_executions.id"), nullable=False, index=True
    )
    level: TaskExecutionLogLevel = db.Column(
        SQLAEnum(TaskExecutionLogLevel, native_enum=False, length=20),
        nullable=False,
        default=TaskExecutionLogLevel.INFO,
        index=True,
    )
    message: str = db.Column(db.Text, nullable=False)
    timestamp: datetime = db.Column(
        db.DateTime, default=lambda: datetime.now(UTC), index=True
    )

    # Optional metadata - using JSON for structured context
    context: dict[str, Any] | None = db.Column(JSON, nullable=True)

    # Relationship
    task_execution = db.relationship("TaskExecution", back_populates="logs")

    def __repr__(self) -> str:
        """Return string representation of the task execution log."""
        return f"<TaskExecutionLog {self.id}: {self.level.value} - {self.message[:50]}>"

    def to_dict(self) -> dict[str, Any]:
        """Convert the model instance to a dictionary."""
        return {
            "id": self.id,
            "task_execution_id": self.task_execution_id,
            "level": self.level.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
        }
