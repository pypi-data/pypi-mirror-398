"""Pipeline execution models for progress tracking and logging."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class RunStatus(str, Enum):
    """Status of a pipeline run."""

    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


class ActionStatus(str, Enum):
    """Status of an individual action."""

    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    SKIPPED = 'skipped'


class LogLevel(str, Enum):
    """Log level for pipeline logs."""

    DEBUG = 'debug'
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'


@dataclass
class ActionProgress:
    """Progress state for a single action.

    Attributes:
        name: Action name/identifier.
        status: Current action status.
        progress: Progress percentage (0.0 to 1.0).
        progress_category: Optional category for multi-phase progress.
        message: Optional status message.
        metrics: Optional metrics dictionary.
        started_at: When the action started.
        completed_at: When the action completed.
        error: Error message if failed.
    """

    name: str
    status: ActionStatus = ActionStatus.PENDING
    progress: float = 0.0
    progress_category: str | None = None
    message: str | None = None
    metrics: dict[str, Any] = field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API serialization."""
        return {
            'name': self.name,
            'status': self.status.value,
            'progress': self.progress,
            'progress_category': self.progress_category,
            'message': self.message,
            'metrics': self.metrics,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error': self.error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'ActionProgress':
        """Create from dictionary."""
        return cls(
            name=data['name'],
            status=ActionStatus(data.get('status', 'pending')),
            progress=data.get('progress', 0.0),
            progress_category=data.get('progress_category'),
            message=data.get('message'),
            metrics=data.get('metrics', {}),
            started_at=datetime.fromisoformat(data['started_at']) if data.get('started_at') else None,
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
            error=data.get('error'),
        )


@dataclass
class PipelineProgress:
    """Overall pipeline execution progress.

    Attributes:
        run_id: Unique identifier for this run.
        pipeline_id: Identifier of the pipeline being executed.
        status: Overall pipeline status.
        current_action: Name of currently executing action.
        current_action_index: Index of current action (0-based).
        actions: List of action progress states.
        started_at: When the pipeline started.
        completed_at: When the pipeline completed.
        error: Error message if failed.
    """

    run_id: str
    pipeline_id: str
    status: RunStatus = RunStatus.PENDING
    current_action: str | None = None
    current_action_index: int = 0
    actions: list[ActionProgress] = field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None

    @property
    def overall_progress(self) -> float:
        """Calculate overall pipeline progress (0.0 to 1.0)."""
        if not self.actions:
            return 0.0

        total_progress = sum(a.progress for a in self.actions)
        return total_progress / len(self.actions)

    @property
    def completed_actions(self) -> int:
        """Count of completed actions."""
        return sum(1 for a in self.actions if a.status == ActionStatus.COMPLETED)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API serialization."""
        return {
            'run_id': self.run_id,
            'pipeline_id': self.pipeline_id,
            'status': self.status.value,
            'current_action': self.current_action,
            'current_action_index': self.current_action_index,
            'actions': [a.to_dict() for a in self.actions],
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error': self.error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'PipelineProgress':
        """Create from dictionary."""
        return cls(
            run_id=data['run_id'],
            pipeline_id=data['pipeline_id'],
            status=RunStatus(data.get('status', 'pending')),
            current_action=data.get('current_action'),
            current_action_index=data.get('current_action_index', 0),
            actions=[ActionProgress.from_dict(a) for a in data.get('actions', [])],
            started_at=datetime.fromisoformat(data['started_at']) if data.get('started_at') else None,
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
            error=data.get('error'),
        )


@dataclass
class LogEntry:
    """A single log entry from pipeline execution.

    Attributes:
        message: Log message content.
        level: Log level.
        action_name: Name of action that produced this log.
        timestamp: When the log was created.
    """

    message: str
    level: LogLevel = LogLevel.INFO
    action_name: str | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API serialization."""
        return {
            'message': self.message,
            'level': self.level.value,
            'action_name': self.action_name,
            'timestamp': self.timestamp.isoformat(),
        }


@dataclass
class Checkpoint:
    """Checkpoint for pipeline resume capability.

    Attributes:
        run_id: Run this checkpoint belongs to.
        action_name: Name of the action.
        action_index: Index of the action in the pipeline.
        status: Status of the action when checkpointed.
        params_snapshot: Parameters at time of checkpoint.
        result: Result from the action if completed.
        artifacts_path: Path to any saved artifacts.
        created_at: When checkpoint was created.
    """

    run_id: str
    action_name: str
    action_index: int
    status: ActionStatus
    params_snapshot: dict[str, Any] = field(default_factory=dict)
    result: dict[str, Any] | None = None
    artifacts_path: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API serialization."""
        return {
            'run_id': self.run_id,
            'action_name': self.action_name,
            'action_index': self.action_index,
            'status': self.status.value,
            'params_snapshot': self.params_snapshot,
            'result': self.result,
            'artifacts_path': self.artifacts_path,
            'created_at': self.created_at.isoformat(),
        }


__all__ = [
    'RunStatus',
    'ActionStatus',
    'LogLevel',
    'ActionProgress',
    'PipelineProgress',
    'LogEntry',
    'Checkpoint',
]
