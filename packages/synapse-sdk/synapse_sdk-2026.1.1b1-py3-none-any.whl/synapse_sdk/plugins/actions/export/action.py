"""Export action base class with optional step support."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

from pydantic import BaseModel

from synapse_sdk.plugins.action import BaseAction
from synapse_sdk.plugins.actions.export.context import ExportContext
from synapse_sdk.plugins.enums import PluginCategory
from synapse_sdk.plugins.pipelines.steps import Orchestrator, StepRegistry

P = TypeVar('P', bound=BaseModel)

if TYPE_CHECKING:
    from synapse_sdk.clients.backend import BackendClient


class ExportProgressCategories:
    """Standard progress category names for export workflows.

    Use these constants with set_progress() to track export phases:
        - DATASET_CONVERSION: Data conversion and file generation

    Example:
        >>> self.set_progress(50, 100, self.progress.DATASET_CONVERSION)
    """

    DATASET_CONVERSION: str = 'dataset_conversion'


class BaseExportAction(BaseAction[P]):
    """Base class for export actions.

    Provides helper methods for export workflows.
    Override get_filtered_results() for your specific target type.

    Supports two execution modes:
    1. Simple execute: Override execute() directly for simple workflows
    2. Step-based: Override setup_steps() to register workflow steps

    If setup_steps() registers any steps, the step-based workflow
    takes precedence and execute() is not called directly.

    Attributes:
        category: Plugin category (defaults to EXPORT).
        progress: Standard progress category names.

    Example (simple execute):
        >>> class MyExportAction(BaseExportAction[MyParams]):
        ...     action_name = 'export'
        ...     params_model = MyParams
        ...
        ...     def get_filtered_results(self, filters: dict) -> tuple[Any, int]:
        ...         return self.client.get_assignments(filters)
        ...
        ...     def execute(self) -> dict[str, Any]:
        ...         results, count = self.get_filtered_results(self.params.filter)
        ...         self.set_progress(0, count, self.progress.DATASET_CONVERSION)
        ...         for i, item in enumerate(results, 1):
        ...             # Process and export item
        ...             self.set_progress(i, count, self.progress.DATASET_CONVERSION)
        ...         return {'exported': count}

    Example (step-based):
        >>> class MyExportAction(BaseExportAction[MyParams]):
        ...     def setup_steps(self, registry: StepRegistry[ExportContext]) -> None:
        ...         registry.register(FetchResultsStep())
        ...         registry.register(ProcessStep())
        ...         registry.register(FinalizeStep())
    """

    category = PluginCategory.EXPORT
    progress = ExportProgressCategories()

    @property
    def client(self) -> BackendClient:
        """Backend client from context.

        Returns:
            BackendClient instance.

        Raises:
            RuntimeError: If no client in context.
        """
        if self.ctx.client is None:
            raise RuntimeError(
                'No client in context. Either provide a client via RuntimeContext or override get_filtered_results().'
            )
        return self.ctx.client

    def setup_steps(self, registry: StepRegistry[ExportContext]) -> None:
        """Register workflow steps for step-based execution.

        Override this method to register custom steps for your export workflow.
        If steps are registered, step-based execution takes precedence.

        Args:
            registry: StepRegistry to register steps with.

        Example:
            >>> def setup_steps(self, registry: StepRegistry[ExportContext]) -> None:
            ...     registry.register(FetchResultsStep())
            ...     registry.register(ProcessStep())
            ...     registry.register(FinalizeStep())
        """
        pass  # Default: no steps, uses simple execute()

    def create_context(self) -> ExportContext:
        """Create export context for step-based workflow.

        Override to customize context creation or add additional state.

        Returns:
            ExportContext instance with params and runtime context.
        """
        params_dict = self.params.model_dump() if hasattr(self.params, 'model_dump') else dict(self.params)
        return ExportContext(
            runtime_ctx=self.ctx,
            params=params_dict,
        )

    def run(self) -> Any:
        """Run the action, using steps if registered.

        This method is called by executors. It checks if steps are
        registered and uses step-based execution if so.

        Returns:
            Action result (dict or any return type).
        """
        # Check if steps are registered
        registry: StepRegistry[ExportContext] = StepRegistry()
        self.setup_steps(registry)

        if registry:
            # Step-based execution
            context = self.create_context()
            orchestrator: Orchestrator[ExportContext] = Orchestrator(
                registry=registry,
                context=context,
                progress_callback=lambda curr, total: self.set_progress(curr, total),
            )
            result = orchestrator.execute()

            # Add context data to result
            result['exported_count'] = context.exported_count
            if context.output_path:
                result['output_path'] = context.output_path

            return result

        # Simple execute mode
        return self.execute()

    def get_filtered_results(self, filters: dict[str, Any]) -> tuple[Any, int]:
        """Fetch filtered results for export.

        Override this method for your specific target type
        (assignments, ground_truth, tasks, or custom).

        Args:
            filters: Filter criteria dict.

        Returns:
            Tuple of (results_iterator, total_count).

        Raises:
            NotImplementedError: Must be overridden by subclass.

        Example:
            >>> # Override for assignments:
            >>> def get_filtered_results(self, filters: dict) -> tuple[Any, int]:
            ...     return self.client.get_assignments(filters)
            >>>
            >>> # Override for ground truth:
            >>> def get_filtered_results(self, filters: dict) -> tuple[Any, int]:
            ...     return self.client.get_ground_truth(filters)
        """
        raise NotImplementedError(
            'Override get_filtered_results() for your target type. Example: return self.client.get_assignments(filters)'
        )
