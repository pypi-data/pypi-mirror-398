"""Train context for sharing state between workflow steps."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from synapse_sdk.plugins.pipelines.steps import BaseStepContext

if TYPE_CHECKING:
    from synapse_sdk.clients.backend import BackendClient


@dataclass
class TrainContext(BaseStepContext):
    """Shared context passed between training workflow steps.

    Extends BaseStepContext with training-specific state fields.
    Carries parameters and accumulated state as the workflow
    progresses through steps.

    Attributes:
        params: Training parameters (from action params).
        dataset: Loaded dataset (populated by dataset step).
        model_path: Path to trained model (populated by training step).
        model: Created model metadata (populated by upload step).

    Example:
        >>> context = TrainContext(
        ...     runtime_ctx=runtime_ctx,
        ...     params={'dataset_id': 1, 'epochs': 10},
        ... )
        >>> # Steps populate state as they execute
        >>> context.dataset = loaded_dataset
    """

    # Training parameters
    params: dict[str, Any] = field(default_factory=dict)

    # Processing state (populated by steps)
    dataset: Any | None = None
    model_path: str | None = None
    model: dict[str, Any] | None = None

    @property
    def client(self) -> BackendClient:
        """Backend client from runtime context.

        Returns:
            BackendClient instance.

        Raises:
            RuntimeError: If no client in runtime context.
        """
        if self.runtime_ctx.client is None:
            raise RuntimeError('No client in runtime context')
        return self.runtime_ctx.client
