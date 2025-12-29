"""Inference action base class with optional step support."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar

from pydantic import BaseModel

from synapse_sdk.plugins.action import BaseAction
from synapse_sdk.plugins.actions.inference.context import InferenceContext
from synapse_sdk.plugins.enums import PluginCategory
from synapse_sdk.plugins.pipelines.steps import Orchestrator, StepRegistry
from synapse_sdk.utils.file.archive import extract_archive

P = TypeVar('P', bound=BaseModel)

if TYPE_CHECKING:
    from synapse_sdk.clients.backend import BackendClient


class InferenceProgressCategories:
    """Standard progress category names for inference workflows.

    Use these constants with set_progress() to track inference phases:
        - MODEL_LOAD: Model loading and initialization
        - INFERENCE: Running inference on inputs
        - POSTPROCESS: Post-processing results

    Example:
        >>> self.set_progress(1, 3, self.progress.MODEL_LOAD)
        >>> self.set_progress(2, 3, self.progress.INFERENCE)
    """

    MODEL_LOAD: str = 'model_load'
    INFERENCE: str = 'inference'
    POSTPROCESS: str = 'postprocess'


class BaseInferenceAction(BaseAction[P]):
    """Base class for inference actions.

    Provides helper methods for model loading and inference workflows.
    Supports both REST API-based inference (via Ray Serve) and batch
    inference with step-based workflows.

    Supports two execution modes:
    1. Simple execute: Override execute() directly for simple workflows
    2. Step-based: Override setup_steps() to register workflow steps

    If setup_steps() registers any steps, the step-based workflow
    takes precedence and execute() is not called directly.

    Attributes:
        category: Plugin category (defaults to NEURAL_NET).
        progress: Standard progress category names.

    Example (simple execute):
        >>> class MyInferenceAction(BaseInferenceAction[MyParams]):
        ...     action_name = 'inference'
        ...     params_model = MyParams
        ...
        ...     def execute(self) -> dict[str, Any]:
        ...         model = self.load_model(self.params.model_id)
        ...         self.set_progress(1, 3, self.progress.MODEL_LOAD)
        ...         results = self.infer(model, self.params.inputs)
        ...         self.set_progress(2, 3, self.progress.INFERENCE)
        ...         return {'results': results}

    Example (step-based):
        >>> class MyInferenceAction(BaseInferenceAction[MyParams]):
        ...     def setup_steps(self, registry: StepRegistry[InferenceContext]) -> None:
        ...         registry.register(LoadModelStep())
        ...         registry.register(InferenceStep())
        ...         registry.register(PostProcessStep())
    """

    category = PluginCategory.NEURAL_NET
    progress = InferenceProgressCategories()

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
                'No client in context. Either provide a client via RuntimeContext '
                'or override the helper methods (load_model, get_model).'
            )
        return self.ctx.client

    def setup_steps(self, registry: StepRegistry[InferenceContext]) -> None:
        """Register workflow steps for step-based execution.

        Override this method to register custom steps for your inference workflow.
        If steps are registered, step-based execution takes precedence.

        Args:
            registry: StepRegistry to register steps with.

        Example:
            >>> def setup_steps(self, registry: StepRegistry[InferenceContext]) -> None:
            ...     registry.register(LoadModelStep())
            ...     registry.register(InferenceStep())
            ...     registry.register(PostProcessStep())
        """
        pass  # Default: no steps, uses simple execute()

    def create_context(self) -> InferenceContext:
        """Create inference context for step-based workflow.

        Override to customize context creation or add additional state.

        Returns:
            InferenceContext instance with params and runtime context.
        """
        params_dict = self.params.model_dump() if hasattr(self.params, 'model_dump') else dict(self.params)
        return InferenceContext(
            runtime_ctx=self.ctx,
            params=params_dict,
            model_id=params_dict.get('model_id'),
        )

    def run(self) -> Any:
        """Run the action, using steps if registered.

        This method is called by executors. It checks if steps are
        registered and uses step-based execution if so.

        Returns:
            Action result (dict or any return type).
        """
        # Check if steps are registered
        registry: StepRegistry[InferenceContext] = StepRegistry()
        self.setup_steps(registry)

        if registry:
            # Step-based execution
            context = self.create_context()
            orchestrator: Orchestrator[InferenceContext] = Orchestrator(
                registry=registry,
                context=context,
                progress_callback=lambda curr, total: self.set_progress(curr, total),
            )
            result = orchestrator.execute()

            # Add context data to result
            result['processed_count'] = context.processed_count
            if context.results:
                result['results'] = context.results

            return result

        # Simple execute mode
        return self.execute()

    def get_model(self, model_id: int) -> dict[str, Any]:
        """Retrieve model metadata by ID.

        Args:
            model_id: Model identifier.

        Returns:
            Model metadata dictionary including file URL.

        Raises:
            RuntimeError: If no client in context.

        Example:
            >>> model = self.get_model(123)
            >>> print(model['name'], model['file'])
        """
        return self.client.get_model(model_id)

    def download_model(
        self,
        model_id: int,
        output_dir: str | Path | None = None,
    ) -> Path:
        """Download and extract model artifacts.

        Fetches model metadata, downloads the model archive, and extracts
        it to the specified directory (or a temp directory if not specified).

        Args:
            model_id: Model identifier.
            output_dir: Directory to extract model to. If None, uses tempdir.

        Returns:
            Path to extracted model directory.

        Raises:
            RuntimeError: If no client in context.
            ValueError: If model has no file URL.

        Example:
            >>> model_path = self.download_model(123)
            >>> # Load model from model_path
        """
        model = self.get_model(model_id)

        if not model.get('file'):
            raise ValueError(f'Model {model_id} has no file URL')

        # Determine output directory
        if output_dir is None:
            output_dir = Path(tempfile.mkdtemp(prefix='synapse_model_'))
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

        # Download and extract
        from synapse_sdk.utils.file.download import download_file

        archive_path = output_dir / 'model.zip'
        download_file(model['file'], archive_path)
        extract_archive(archive_path, output_dir)

        # Remove archive after extraction
        archive_path.unlink(missing_ok=True)

        return output_dir

    def load_model(self, model_id: int) -> dict[str, Any]:
        """Load model for inference.

        Downloads model artifacts and returns model info with local path.
        Override this method for custom model loading (e.g., loading into
        specific framework like PyTorch, TensorFlow).

        Args:
            model_id: Model identifier.

        Returns:
            Model metadata dict with 'path' key for local artifacts.

        Example:
            >>> model_info = self.load_model(123)
            >>> model_path = model_info['path']
            >>> # Load your model framework here:
            >>> # model = torch.load(model_path / 'model.pt')
        """
        model = self.get_model(model_id)
        model_path = self.download_model(model_id)
        model['path'] = str(model_path)
        return model

    def infer(
        self,
        model: Any,
        inputs: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Run inference on inputs.

        Override this method to implement your inference logic.
        This is called by execute() in simple mode.

        Args:
            model: Loaded model (framework-specific).
            inputs: List of input dictionaries.

        Returns:
            List of result dictionaries.

        Raises:
            NotImplementedError: Must be overridden by subclass.

        Example:
            >>> def infer(self, model, inputs):
            ...     results = []
            ...     for inp in inputs:
            ...         prediction = model.predict(inp['image'])
            ...         results.append({'prediction': prediction})
            ...     return results
        """
        raise NotImplementedError(
            'Override infer() to implement inference logic. Example: return model.predict(inputs)'
        )
