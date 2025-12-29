"""Upload action base class with workflow step support."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

from pydantic import BaseModel

from synapse_sdk.plugins.action import BaseAction
from synapse_sdk.plugins.actions.upload.context import UploadContext
from synapse_sdk.plugins.enums import PluginCategory
from synapse_sdk.plugins.pipelines.steps import Orchestrator, StepRegistry

P = TypeVar('P', bound=BaseModel)

if TYPE_CHECKING:
    from synapse_sdk.clients.backend import BackendClient


class UploadProgressCategories:
    """Standard progress category names for upload workflows.

    Use these constants with set_progress() to track upload phases:
        - INITIALIZE: Storage and path setup
        - VALIDATE: File validation
        - UPLOAD: File upload to storage
        - CLEANUP: Post-upload cleanup

    Example:
        >>> self.set_progress(1, 4, self.progress.INITIALIZE)
    """

    INITIALIZE: str = 'initialize'
    VALIDATE: str = 'validate'
    UPLOAD: str = 'upload'
    CLEANUP: str = 'cleanup'


class BaseUploadAction(BaseAction[P]):
    """Base class for upload actions with workflow step support.

    Provides a full step-based workflow system:
    - Override setup_steps() to register custom steps
    - Steps execute in order with automatic rollback on failure
    - Progress tracked across all steps based on weights

    Attributes:
        category: Plugin category (defaults to UPLOAD).
        progress: Standard progress category names.

    Example:
        >>> class MyUploadAction(BaseUploadAction[MyParams]):
        ...     action_name = 'upload'
        ...     params_model = MyParams
        ...
        ...     def setup_steps(self, registry: StepRegistry) -> None:
        ...         registry.register(InitializeStep())
        ...         registry.register(ValidateStep())
        ...         registry.register(UploadFilesStep())
        ...         registry.register(CleanupStep())
        >>>
        >>> # Steps are executed in order with automatic rollback on failure
        >>> # Progress is tracked based on step weights
    """

    category = PluginCategory.UPLOAD
    progress = UploadProgressCategories()

    @property
    def client(self) -> BackendClient:
        """Backend client from context.

        Returns:
            BackendClient instance.

        Raises:
            RuntimeError: If no client in context.
        """
        if self.ctx.client is None:
            raise RuntimeError('No client in context. Provide a client via RuntimeContext.')
        return self.ctx.client

    def setup_steps(self, registry: StepRegistry[UploadContext]) -> None:
        """Register workflow steps.

        Override this method to register custom steps for your upload workflow.
        Steps are executed in registration order.

        Args:
            registry: StepRegistry to register steps with.

        Example:
            >>> def setup_steps(self, registry: StepRegistry[UploadContext]) -> None:
            ...     registry.register(InitializeStep())
            ...     registry.register(ValidateStep())
            ...     registry.register(UploadFilesStep())
        """
        pass  # Subclasses override to add steps

    def create_context(self) -> UploadContext:
        """Create upload context for the workflow.

        Override to customize context creation or add additional state.

        Returns:
            UploadContext instance with params and runtime context.
        """
        params_dict = self.params.model_dump() if hasattr(self.params, 'model_dump') else dict(self.params)
        return UploadContext(
            params=params_dict,
            runtime_ctx=self.ctx,
        )

    def execute(self) -> dict[str, Any]:
        """Execute the upload workflow.

        Creates registry, registers steps via setup_steps(), creates context,
        and runs the orchestrator.

        Returns:
            Dict with success status and workflow results.

        Raises:
            RuntimeError: If no steps registered or a step fails.
        """
        # Setup
        registry: StepRegistry[UploadContext] = StepRegistry()
        self.setup_steps(registry)

        if not registry:
            raise RuntimeError('No steps registered. Override setup_steps() to register workflow steps.')

        # Create context and orchestrator
        context = self.create_context()
        orchestrator: Orchestrator[UploadContext] = Orchestrator(
            registry=registry,
            context=context,
            progress_callback=lambda curr, total: self.set_progress(curr, total),
        )

        # Execute workflow
        result = orchestrator.execute()

        # Add upload-specific result data
        result['uploaded_files'] = len(context.uploaded_files)
        result['data_units'] = len(context.data_units)

        return result
