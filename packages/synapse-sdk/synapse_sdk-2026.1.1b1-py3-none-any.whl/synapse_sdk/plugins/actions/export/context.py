"""Export context for sharing state between workflow steps."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from synapse_sdk.plugins.pipelines.steps import BaseStepContext

if TYPE_CHECKING:
    from synapse_sdk.clients.backend import BackendClient


@dataclass
class ExportContext(BaseStepContext):
    """Shared context passed between export workflow steps.

    Extends BaseStepContext with export-specific state fields.
    Carries parameters and accumulated state as the workflow
    progresses through steps.

    Attributes:
        params: Export parameters (from action params).
        results: Fetched results to export (populated by fetch step).
        total_count: Total number of items to export.
        exported_count: Number of items successfully exported.
        output_path: Path to export output file/directory.

    Example:
        >>> context = ExportContext(
        ...     runtime_ctx=runtime_ctx,
        ...     params={'format': 'coco', 'filter': {}},
        ... )
        >>> # Steps populate state as they execute
        >>> context.results = fetched_data
    """

    # Export parameters
    params: dict[str, Any] = field(default_factory=dict)

    # Processing state (populated by steps)
    results: Any | None = None
    total_count: int = 0
    exported_count: int = 0
    output_path: str | None = None

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
