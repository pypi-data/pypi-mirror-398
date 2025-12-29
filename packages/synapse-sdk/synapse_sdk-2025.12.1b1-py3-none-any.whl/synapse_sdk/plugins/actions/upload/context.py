"""Upload context for sharing state between workflow steps."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from synapse_sdk.plugins.pipelines.steps import BaseStepContext

if TYPE_CHECKING:
    from synapse_sdk.clients.backend import BackendClient


@dataclass
class UploadContext(BaseStepContext):
    """Shared context passed between upload workflow steps.

    Extends BaseStepContext with upload-specific state fields.
    Carries parameters and accumulated state as the workflow
    progresses through steps.

    Attributes:
        params: Upload parameters (from action params).
        storage: Storage configuration (populated by init step).
        pathlib_cwd: Working directory path (populated by init step).
        organized_files: Files organized for upload (populated by organize step).
        uploaded_files: Successfully uploaded files (populated by upload step).
        data_units: Created data units (populated by generate step).

    Example:
        >>> context = UploadContext(
        ...     runtime_ctx=runtime_ctx,
        ...     params={'storage': 1, 'path': '/data'},
        ... )
        >>> # Steps populate state as they execute
        >>> context.organized_files.append({'path': 'file1.jpg'})
    """

    # Upload parameters
    params: dict[str, Any] = field(default_factory=dict)

    # Processing state (populated by steps)
    storage: Any | None = None
    pathlib_cwd: Any | None = None
    organized_files: list[dict[str, Any]] = field(default_factory=list)
    uploaded_files: list[dict[str, Any]] = field(default_factory=list)
    data_units: list[dict[str, Any]] = field(default_factory=list)

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
