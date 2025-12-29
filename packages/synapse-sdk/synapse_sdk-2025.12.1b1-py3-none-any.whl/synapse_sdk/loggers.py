from __future__ import annotations

import time
from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol


class LoggerBackend(Protocol):
    """Protocol for logger backends that handle data synchronization."""

    def publish_progress(self, job_id: str, progress: ProgressData) -> None: ...
    def publish_metrics(self, job_id: str, metrics: dict[str, Any]) -> None: ...
    def publish_log(self, job_id: str, log_entry: LogEntry) -> None: ...


@dataclass
class ProgressData:
    """Immutable progress data snapshot."""

    percent: float
    time_remaining: float | None = None
    elapsed_time: float | None = None
    status: str = 'running'


@dataclass
class LogEntry:
    """Single log entry."""

    event: str
    data: dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    file: str | None = None


class BaseLogger(ABC):
    """Base class for logging progress, metrics, and events.

    All state is instance-level to prevent cross-instance contamination.
    Uses composition over inheritance for backend communication.
    """

    _start_time: float
    _progress: dict[str, ProgressData]
    _metrics: dict[str, dict[str, Any]]
    _category_start_times: dict[str, float]
    _current_category: str | None
    _is_finished: bool

    def __init__(self) -> None:
        self._start_time = time.monotonic()
        self._progress = {}
        self._metrics = {}
        self._category_start_times = {}
        self._current_category = None
        self._is_finished = False

    def _raise_if_finished(self) -> None:
        if self._is_finished:
            raise RuntimeError('Cannot log to a finished logger')

    def log(self, event: str, data: dict[str, Any], file: str | None = None) -> None:
        """Log an event with data.

        Args:
            event: Event name/type.
            data: Dictionary of event data.
            file: Optional file path associated with the event.

        Raises:
            TypeError: If data is not a dictionary.
            RuntimeError: If logger is already finished.
        """
        self._raise_if_finished()

        if not isinstance(data, Mapping):
            raise TypeError(f'data must be a dict, got {type(data).__name__}')

        data = dict(data)  # Copy to avoid mutating input
        self._log_impl(event, data, file)

    def info(self, message: str) -> None:
        """Log an info message."""
        self.log('info', {'message': message})

    def debug(self, message: str) -> None:
        """Log a debug message."""
        self.log('debug', {'message': message})

    def warning(self, message: str) -> None:
        """Log a warning message."""
        self.log('warning', {'message': message})

    def error(self, message: str) -> None:
        """Log an error message."""
        self.log('error', {'message': message})

    def set_progress(
        self,
        current: int,
        total: int,
        category: str | None = None,
    ) -> None:
        """Set progress for the current operation.

        Args:
            current: Current progress value (0 to total).
            total: Total progress value.
            category: Optional category name for multi-phase progress.

        Raises:
            ValueError: If current/total values are invalid.
            RuntimeError: If logger is already finished.
        """
        self._raise_if_finished()

        if total <= 0:
            raise ValueError(f'total must be > 0, got {total}')
        if not 0 <= current <= total:
            raise ValueError(f'current must be between 0 and {total}, got {current}')

        key = category or '__default__'
        now = time.monotonic()

        # Initialize start time on first call for this category
        if key not in self._category_start_times or current == 0:
            self._category_start_times[key] = now

        elapsed = now - self._category_start_times[key]
        percent = round((current / total) * 100, 2)

        # Calculate time remaining
        time_remaining = None
        if current > 0:
            rate = elapsed / current
            time_remaining = round(rate * (total - current), 2)

        progress = ProgressData(
            percent=percent,
            time_remaining=time_remaining,
            elapsed_time=round(elapsed, 2),
        )

        self._progress[key] = progress
        self._current_category = category
        self._on_progress(progress, category)

    def set_progress_failed(self, category: str | None = None) -> None:
        """Mark progress as failed.

        Args:
            category: Optional category name.

        Raises:
            RuntimeError: If logger is already finished.
        """
        self._raise_if_finished()

        key = category or '__default__'
        elapsed = None

        if key in self._category_start_times:
            elapsed = round(time.monotonic() - self._category_start_times[key], 2)

        progress = ProgressData(
            percent=0.0,
            time_remaining=None,
            elapsed_time=elapsed,
            status='failed',
        )

        self._progress[key] = progress
        self._current_category = category
        self._on_progress(progress, category)

    def set_metrics(self, value: dict[str, Any], category: str) -> None:
        """Set metrics for a category.

        Args:
            value: Dictionary of metric values.
            category: Non-empty category name.

        Raises:
            ValueError: If category is empty.
            TypeError: If value is not a dictionary.
            RuntimeError: If logger is already finished.
        """
        self._raise_if_finished()

        if not category:
            raise ValueError('category must be a non-empty string')
        if not isinstance(value, Mapping):
            raise TypeError(f'value must be a dict, got {type(value).__name__}')

        data = dict(value)  # Copy

        if category not in self._metrics:
            self._metrics[category] = {}
        self._metrics[category].update(data)

        self._on_metrics(category, self._metrics[category])

    def get_progress(self, category: str | None = None) -> ProgressData | None:
        """Get progress for a category."""
        key = category or '__default__'
        return self._progress.get(key)

    def get_metrics(self, category: str | None = None) -> dict[str, Any]:
        """Get metrics, optionally filtered by category."""
        if category:
            return dict(self._metrics.get(category, {}))
        return {k: dict(v) for k, v in self._metrics.items()}

    def finish(self) -> None:
        """Mark the logger as finished. No further logging is allowed."""
        self._is_finished = True
        self._on_finish()

    @abstractmethod
    def _log_impl(self, event: str, data: dict[str, Any], file: str | None) -> None:
        """Implementation-specific log handling."""
        ...

    def _on_progress(self, progress: ProgressData, category: str | None) -> None:
        """Hook called when progress is updated. Override in subclasses."""
        pass

    def _on_metrics(self, category: str, metrics: dict[str, Any]) -> None:
        """Hook called when metrics are updated. Override in subclasses."""
        pass

    def _on_finish(self) -> None:
        """Hook called when logger is finished. Override in subclasses."""
        pass


class ConsoleLogger(BaseLogger):
    """Logger that prints to console."""

    def _log_impl(self, event: str, data: dict[str, Any], file: str | None) -> None:
        print(event, data)

    def _on_progress(self, progress: ProgressData, category: str | None) -> None:
        prefix = f'[{category}] ' if category else ''
        print(f'{prefix}Progress: {progress.percent}% | ETA: {progress.time_remaining}s')

    def _on_metrics(self, category: str, metrics: dict[str, Any]) -> None:
        print(f'[{category}] Metrics: {metrics}')


class BackendLogger(BaseLogger):
    """Logger that syncs with a remote backend.

    Uses a backend interface for decoupled communication.
    """

    _backend: LoggerBackend | None
    _job_id: str
    _log_queue: list[LogEntry]

    def __init__(self, backend: LoggerBackend | None, job_id: str) -> None:
        super().__init__()
        self._backend = backend
        self._job_id = job_id
        self._log_queue = []

    def _log_impl(self, event: str, data: dict[str, Any], file: str | None) -> None:
        entry = LogEntry(event=event, data=data, file=file)
        self._log_queue.append(entry)
        self._flush_logs()

    def _on_progress(self, progress: ProgressData, category: str | None) -> None:
        if self._backend is None:
            return

        try:
            self._backend.publish_progress(self._job_id, progress)
        except Exception as e:
            print(f'Failed to publish progress: {e}')

    def _on_metrics(self, category: str, metrics: dict[str, Any]) -> None:
        if self._backend is None:
            return

        try:
            self._backend.publish_metrics(self._job_id, {category: metrics})
        except Exception as e:
            print(f'Failed to publish metrics: {e}')

    def _flush_logs(self) -> None:
        if self._backend is None or not self._log_queue:
            return

        try:
            for entry in self._log_queue:
                self._backend.publish_log(self._job_id, entry)
            self._log_queue.clear()
        except Exception as e:
            print(f'Failed to flush logs: {e}')

    def _on_finish(self) -> None:
        self._flush_logs()


class NoOpLogger(BaseLogger):
    """Logger that does nothing. Useful for testing or disabled logging."""

    def _log_impl(self, event: str, data: dict[str, Any], file: str | None) -> None:
        pass


__all__ = [
    'BaseLogger',
    'BackendLogger',
    'ConsoleLogger',
    'LogEntry',
    'LoggerBackend',
    'NoOpLogger',
    'ProgressData',
]
