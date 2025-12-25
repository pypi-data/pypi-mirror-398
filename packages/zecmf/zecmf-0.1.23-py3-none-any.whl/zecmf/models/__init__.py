"""ZecMF framework models package.

Contains all SQLAlchemy ORM models provided by the ZecMF framework.
"""

from zecmf.models.task_monitoring import TaskExecution, TaskExecutionLog

__all__ = [
    "TaskExecution",
    "TaskExecutionLog",
]


def get_all_models() -> list:
    """Get all available framework models.

    Returns:
        List of all model classes that should be included in migrations.

    """
    return [TaskExecution, TaskExecutionLog]
