"""Train action base class with optional step support."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar

from pydantic import BaseModel, Field

from synapse_sdk.plugins.action import BaseAction
from synapse_sdk.plugins.actions.train.context import TrainContext
from synapse_sdk.plugins.enums import PluginCategory
from synapse_sdk.plugins.pipelines.steps import Orchestrator, StepRegistry

P = TypeVar('P', bound=BaseModel)

if TYPE_CHECKING:
    from synapse_sdk.clients.backend import BackendClient


class BaseTrainParams(BaseModel):
    """Base parameters for training actions.

    Provides common fields used across training workflows.
    Extend this class to add plugin-specific training parameters.

    Attributes:
        checkpoint: Optional model ID to use as starting checkpoint.

    Example:
        >>> class MyTrainParams(BaseTrainParams):
        ...     epochs: int = 100
        ...     batch_size: int = 32
    """

    checkpoint: int | None = Field(default=None, description='Checkpoint model ID to resume from')


class TrainProgressCategories:
    """Standard progress category names for training workflows.

    Use these constants with set_progress() to track multi-phase training:
        - DATASET: Data loading and preprocessing
        - TRAIN: Model training iterations
        - MODEL_UPLOAD: Final model upload to backend

    Example:
        >>> self.set_progress(1, 10, TrainProgressCategories.DATASET)
        >>> self.set_progress(50, 100, TrainProgressCategories.TRAIN)
    """

    DATASET: str = 'dataset'
    TRAIN: str = 'train'
    MODEL_UPLOAD: str = 'model_upload'


class BaseTrainAction(BaseAction[P]):
    """Base class for training actions.

    Provides helper methods for common training workflows:
    dataset fetching, model creation, and progress tracking.

    Supports two execution modes:
    1. Simple execute: Override execute() directly for simple workflows
    2. Step-based: Override setup_steps() to register workflow steps

    If setup_steps() registers any steps, the step-based workflow
    takes precedence and execute() is not called directly.

    Attributes:
        category: Plugin category (defaults to NEURAL_NET).
        progress: Standard progress category names.

    Example (without result schema):
        >>> class MyTrainAction(BaseTrainAction[MyParams]):
        ...     def execute(self) -> dict[str, Any]:
        ...         return {'weights_path': '/model.pt'}

    Example (with result schema):
        >>> class TrainResult(BaseModel):
        ...     weights_path: str
        ...     final_loss: float
        >>>
        >>> class MyTrainAction(BaseTrainAction[MyParams]):
        ...     result_model = TrainResult
        ...
        ...     def execute(self) -> TrainResult:
        ...         return TrainResult(weights_path='/model.pt', final_loss=0.1)

    Example (step-based):
        >>> class MyTrainAction(BaseTrainAction[MyParams]):
        ...     def setup_steps(self, registry: StepRegistry[TrainContext]) -> None:
        ...         registry.register(LoadDatasetStep())
        ...         registry.register(TrainStep())
        ...         registry.register(UploadModelStep())
    """

    category = PluginCategory.NEURAL_NET
    progress = TrainProgressCategories()

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
                'or override the helper methods (get_dataset, create_model, get_model).'
            )
        return self.ctx.client

    def setup_steps(self, registry: StepRegistry[TrainContext]) -> None:
        """Register workflow steps for step-based execution.

        Override this method to register custom steps for your training workflow.
        If steps are registered, step-based execution takes precedence.

        Args:
            registry: StepRegistry to register steps with.

        Example:
            >>> def setup_steps(self, registry: StepRegistry[TrainContext]) -> None:
            ...     registry.register(LoadDatasetStep())
            ...     registry.register(TrainStep())
            ...     registry.register(UploadModelStep())
        """
        pass  # Default: no steps, uses simple execute()

    def create_context(self) -> TrainContext:
        """Create training context for step-based workflow.

        Override to customize context creation or add additional state.

        Returns:
            TrainContext instance with params and runtime context.
        """
        params_dict = self.params.model_dump() if hasattr(self.params, 'model_dump') else dict(self.params)
        return TrainContext(
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
        registry: StepRegistry[TrainContext] = StepRegistry()
        self.setup_steps(registry)

        if registry:
            # Step-based execution
            context = self.create_context()
            orchestrator: Orchestrator[TrainContext] = Orchestrator(
                registry=registry,
                context=context,
                progress_callback=lambda curr, total: self.set_progress(curr, total),
            )
            result = orchestrator.execute()

            # Add context data to result
            if context.model:
                result['model'] = context.model

            return result

        # Simple execute mode
        return self.execute()

    def get_dataset(self) -> dict[str, Any]:
        """Fetch training dataset from backend.

        Default implementation uses params.dataset_id to fetch
        via client.get_data_collection(). Override for custom behavior.

        Returns:
            Dataset metadata dictionary.

        Raises:
            ValueError: If params.dataset_id is not set.
            RuntimeError: If no client in context.

        Example:
            >>> # Override for S3:
            >>> def get_dataset(self) -> dict[str, Any]:
            ...     return download_from_s3(self.params.s3_path)
        """
        dataset_id = getattr(self.params, 'dataset_id', None)
        if dataset_id is None:
            raise ValueError(
                'params.dataset_id is required for default get_dataset(). '
                'Either set dataset_id in your params model or override get_dataset().'
            )
        return self.client.get_data_collection(dataset_id)

    def create_model(self, path: str, **kwargs: Any) -> dict[str, Any]:
        """Upload trained model to backend.

        Default implementation uploads via client.create_model().
        Override for custom behavior (e.g., MLflow, S3).

        Args:
            path: Local path to model artifacts.
            **kwargs: Additional fields for model creation.

        Returns:
            Created model metadata dictionary.

        Raises:
            RuntimeError: If no client in context.

        Example:
            >>> model = self.create_model('./model', name='my-model')
        """
        return self.client.create_model({
            'file': path,
            **kwargs,
        })

    def get_model(self, model_id: int) -> dict[str, Any]:
        """Retrieve existing model by ID.

        Args:
            model_id: Model identifier.

        Returns:
            Model metadata dictionary.

        Raises:
            RuntimeError: If no client in context.
        """
        return self.client.get_model(model_id)

    def get_checkpoint(self) -> dict[str, Any] | None:
        """Get checkpoint for training, either from context or by fetching from backend.

        This method handles checkpoint resolution in the following order:
        1. If ctx.checkpoint is already set (remote mode), returns it directly
        2. If params has a 'checkpoint' field (model ID), fetches and extracts the model

        The returned checkpoint dict contains:
            - category: 'base' or fine-tuned model category
            - path: Local path to the extracted model files

        Returns:
            Checkpoint dict with 'category' and 'path', or None if no checkpoint.

        Raises:
            RuntimeError: If no client in context and checkpoint ID provided.
            FileNotFoundError: If model file cannot be downloaded/extracted.

        Example:
            >>> checkpoint = self.get_checkpoint()
            >>> if checkpoint:
            ...     model_path = checkpoint['path']
            ...     is_base = checkpoint['category'] == 'base'
        """
        from synapse_sdk.utils.file import extract_archive, get_temp_path

        # If checkpoint is already in context (remote mode), return it
        if self.ctx.checkpoint is not None:
            return self.ctx.checkpoint

        # Check if params has a checkpoint field (model ID)
        checkpoint_id = getattr(self.params, 'checkpoint', None)
        if checkpoint_id is None:
            return None

        # Fetch model from backend
        model = self.get_model(checkpoint_id)

        # The model['file'] is downloaded by the client's url_conversion
        model_file = Path(model['file'])

        # Extract to temp path
        output_path = get_temp_path(f'models/{model_file.stem}')
        if not output_path.exists():
            output_path.mkdir(parents=True, exist_ok=True)
            extract_archive(model_file, output_path)

        # Determine category - base models vs fine-tuned
        category = model.get('category') or 'base'

        return {
            'category': category,
            'path': output_path,
            'id': model.get('id'),
            'name': model.get('name'),
        }
