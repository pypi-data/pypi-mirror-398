from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from synapse_sdk.plugins.context.env import PluginEnvironment

if TYPE_CHECKING:
    from synapse_sdk.clients.agent import AgentClient
    from synapse_sdk.clients.backend import BackendClient
    from synapse_sdk.loggers import BaseLogger


@dataclass
class RuntimeContext:
    """Runtime context injected into actions.

    Provides access to logging, environment, and client dependencies.
    All action dependencies are accessed through this context object.

    Attributes:
        logger: Logger instance for progress, metrics, and event logging.
        env: Environment variables and configuration as PluginEnvironment.
        job_id: Optional job identifier for tracking.
        client: Optional backend client for API access.
        agent_client: Optional agent client for Ray operations.
        checkpoint: Optional checkpoint info for pretrained models.
            Contains 'category' ('base' or fine-tuned) and 'path' to model.

    Example:
        >>> ctx = RuntimeContext(
        ...     logger=ConsoleLogger(),
        ...     env=PluginEnvironment.from_environ(),
        ...     job_id='job-123',
        ...     checkpoint={'category': 'base', 'path': '/models/yolov8n.pt'},
        ... )
        >>> ctx.set_progress(50, 100)
        >>> ctx.log('checkpoint', {'epoch': 5})
    """

    logger: BaseLogger
    env: PluginEnvironment
    job_id: str | None = None
    client: BackendClient | None = None
    agent_client: AgentClient | None = None
    checkpoint: dict[str, Any] | None = None

    def log(self, event: str, data: dict[str, Any], file: str | None = None) -> None:
        """Log an event with data.

        Args:
            event: Event name/type.
            data: Dictionary of event data.
            file: Optional file path associated with the event.
        """
        self.logger.log(event, data, file)

    def set_progress(self, current: int, total: int, category: str | None = None) -> None:
        """Set progress for the current operation.

        Args:
            current: Current progress value (0 to total).
            total: Total progress value.
            category: Optional category name for multi-phase progress.
        """
        self.logger.set_progress(current, total, category)

    def set_metrics(self, value: dict[str, Any], category: str) -> None:
        """Set metrics for a category.

        Args:
            value: Dictionary of metric values.
            category: Non-empty category name.
        """
        self.logger.set_metrics(value, category)

    def log_message(self, message: str, context: str = 'info') -> None:
        """Log a user-facing message.

        Args:
            message: Message content.
            context: Message context/level ('info', 'warning', 'danger', 'success').
        """
        self.logger.log('message', {'context': context, 'content': message})

    def log_dev_event(self, message: str, data: dict[str, Any] | None = None) -> None:
        """Log a development/debug event.

        For plugin developers to log custom events during execution.
        Not shown to end users by default.

        Args:
            message: Event message.
            data: Optional additional data.
        """
        self.logger.log('dev_event', {'message': message, 'data': data})

    def end_log(self) -> None:
        """Signal that plugin execution is complete."""
        self.log_message('Plugin run is complete.')


__all__ = ['PluginEnvironment', 'RuntimeContext']
