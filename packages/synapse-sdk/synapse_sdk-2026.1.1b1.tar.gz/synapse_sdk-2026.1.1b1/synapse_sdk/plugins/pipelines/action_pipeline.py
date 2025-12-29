"""Action pipeline for chaining plugin actions with schema validation.

Provides a pipeline orchestrator that chains actions together like Unix pipes,
validating that the output schema of each action is compatible with the
input schema of the next action.

Example:
    >>> from synapse_sdk.plugins.pipelines import ActionPipeline
    >>>
    >>> # Define compatible actions
    >>> class DownloadAction(BaseAction[DownloadParams]):
    ...     result_model = DownloadResult
    ...
    >>> class ConvertAction(BaseAction[ConvertParams]):  # ConvertParams compatible with DownloadResult
    ...     result_model = ConvertResult
    ...
    >>> # Create pipeline (validates schema compatibility at creation time)
    >>> pipeline = ActionPipeline([DownloadAction, ConvertAction, TrainAction])
    >>>
    >>> # Execute pipeline (passes results as params)
    >>> result = pipeline.execute(initial_params, ctx)
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from synapse_sdk.plugins.action import BaseAction, NoResult, validate_result
from synapse_sdk.plugins.types import DataType

if TYPE_CHECKING:
    from synapse_sdk.plugins.context import RuntimeContext

_logger = logging.getLogger(__name__)


class SchemaIncompatibleError(Exception):
    """Raised when action schemas are incompatible in a pipeline."""

    pass


class ActionPipeline:
    """Pipeline that chains actions by validating input/output schema compatibility.

    Actions are executed sequentially, with each action's result being merged
    with the initial params to form the next action's params. This allows
    downstream actions to use both the original params and upstream results.

    Schema Compatibility:
        For action A -> action B to be compatible:
        - A.result_model must be defined (not NoResult)
        - All required fields in B.params_model must be satisfiable by either:
          - A.result_model fields, OR
          - Initial params passed to pipeline.execute()

    Example:
        >>> # Unix pipe style: Download | Convert | Train
        >>> pipeline = ActionPipeline([
        ...     DownloadDatasetAction,
        ...     ConvertDatasetAction,
        ...     TrainAction,
        ... ])
        >>>
        >>> result = pipeline.execute(
        ...     params={'dataset_id': 123, 'target_format': 'yolo'},
        ...     ctx=runtime_ctx,
        ... )
    """

    def __init__(
        self,
        actions: list[type[BaseAction]],
        *,
        validate_schemas: bool = True,
        strict: bool = False,
    ) -> None:
        """Initialize pipeline with action sequence.

        Args:
            actions: Ordered list of action classes to execute.
            validate_schemas: If True, validate schema compatibility at init.
            strict: If True, raise on schema mismatch. If False, log warning.

        Raises:
            SchemaIncompatibleError: If strict=True and schemas are incompatible.
            ValueError: If actions list is empty.
        """
        if not actions:
            raise ValueError('Pipeline requires at least one action')

        self._actions = actions
        self._strict = strict

        if validate_schemas:
            self._validate_pipeline()

    def _validate_pipeline(self) -> None:
        """Validate type and schema compatibility between adjacent actions.

        Checks:
        1. Semantic type compatibility (output_type -> input_type)
        2. Field compatibility (result_model fields -> params_model fields)

        Raises:
            SchemaIncompatibleError: If strict mode and types/schemas incompatible.
        """
        for i in range(len(self._actions) - 1):
            source = self._actions[i]
            target = self._actions[i + 1]

            # Check semantic type compatibility
            self._validate_types(source, target)

            # Check schema field compatibility
            self._validate_fields(source, target)

    def _validate_types(
        self,
        source: type[BaseAction],
        target: type[BaseAction],
    ) -> None:
        """Validate semantic type compatibility between actions.

        Types are compatible if:
        - Either is None (skip validation)
        - They are the same DataType class
        - One is a subclass of the other (e.g., YOLODataset is-a Dataset)

        Args:
            source: Source action class.
            target: Target action class.

        Raises:
            SchemaIncompatibleError: If strict mode and types incompatible.
        """
        source_output: type[DataType] | None = getattr(source, 'output_type', None)
        target_input: type[DataType] | None = getattr(target, 'input_type', None)

        # If either is None, skip type validation (rely on schema validation)
        if source_output is None or target_input is None:
            return

        # Check type compatibility using DataType.is_compatible_with
        if not source_output.is_compatible_with(target_input):
            msg = (
                f"Type mismatch: '{source.__name__}' outputs {source_output.name!r} "
                f"but '{target.__name__}' expects {target_input.name!r}."
            )
            if self._strict:
                raise SchemaIncompatibleError(msg)
            _logger.warning(msg)

    def _validate_fields(
        self,
        source: type[BaseAction],
        target: type[BaseAction],
    ) -> None:
        """Validate field compatibility between actions.

        Args:
            source: Source action class.
            target: Target action class.

        Raises:
            SchemaIncompatibleError: If strict mode and fields incompatible.
        """
        # Check if source has result schema
        if source.result_model is NoResult:
            msg = (
                f"Action '{source.__name__}' has no result_model. "
                f"Cannot validate field compatibility with '{target.__name__}'."
            )
            if self._strict:
                raise SchemaIncompatibleError(msg)
            _logger.warning(msg)
            return

        # Check field compatibility
        source_fields = self._get_model_fields(source.result_model)
        target_required = self._get_required_fields(target.params_model)

        missing = target_required - source_fields
        if missing:
            msg = (
                f"Schema mismatch: '{source.__name__}' result missing fields "
                f"required by '{target.__name__}' params: {missing}. "
                f'These must be provided in initial params.'
            )
            if self._strict:
                raise SchemaIncompatibleError(msg)
            _logger.info(msg)

    @staticmethod
    def _get_model_fields(model: type[BaseModel]) -> set[str]:
        """Get all field names from a Pydantic model."""
        if not hasattr(model, 'model_fields'):
            return set()
        return set(model.model_fields.keys())

    @staticmethod
    def _get_required_fields(model: type[BaseModel]) -> set[str]:
        """Get required field names (no default) from a Pydantic model."""
        if not hasattr(model, 'model_fields'):
            return set()
        return {name for name, field in model.model_fields.items() if field.is_required()}

    def execute(
        self,
        params: dict[str, Any] | BaseModel,
        ctx: RuntimeContext,
        *,
        progress_callback: Callable[[int, int, str], None] | None = None,
    ) -> Any:
        """Execute the pipeline, chaining action results as params.

        Args:
            params: Initial parameters (dict or Pydantic model).
            ctx: Runtime context for all actions.
            progress_callback: Optional callback(current, total, action_name).

        Returns:
            Result from the final action in the pipeline.

        Raises:
            RuntimeError: If any action fails.
        """
        # Convert Pydantic model to dict if needed
        if isinstance(params, BaseModel):
            accumulated_params = params.model_dump()
        else:
            accumulated_params = dict(params)

        total_actions = len(self._actions)
        final_result = None

        for i, action_cls in enumerate(self._actions):
            action_name = action_cls.action_name or action_cls.__name__

            # Report progress
            if progress_callback:
                progress_callback(i, total_actions, action_name)

            # Validate params against action's params_model
            try:
                validated_params = action_cls.params_model.model_validate(accumulated_params)
            except Exception as e:
                raise RuntimeError(f"Failed to validate params for action '{action_name}': {e}") from e

            # Create and execute action
            action = action_cls(validated_params, ctx)

            try:
                if hasattr(action, 'run'):
                    result = action.run()
                else:
                    result = action.execute()
            except Exception as e:
                raise RuntimeError(f"Action '{action_name}' failed: {e}") from e

            # Validate result
            result = validate_result(result, action_cls.result_model, _logger)

            # Merge result into accumulated params for next action
            if isinstance(result, BaseModel):
                result_dict = result.model_dump()
            elif isinstance(result, dict):
                result_dict = result
            else:
                result_dict = {}

            accumulated_params.update(result_dict)
            final_result = result

        # Final progress
        if progress_callback:
            progress_callback(total_actions, total_actions, 'complete')

        return final_result

    def validate_initial_params(
        self,
        params: dict[str, Any] | BaseModel,
    ) -> list[str]:
        """Check if initial params satisfy all required fields across pipeline.

        Args:
            params: Initial parameters to validate.

        Returns:
            List of missing required fields (empty if all satisfied).
        """
        if isinstance(params, BaseModel):
            provided = set(params.model_dump().keys())
        else:
            provided = set(params.keys())

        missing = []
        accumulated = provided.copy()

        for i, action_cls in enumerate(self._actions):
            required = self._get_required_fields(action_cls.params_model)
            action_missing = required - accumulated

            if action_missing:
                missing.extend(f'{action_cls.__name__}.{field}' for field in action_missing)

            # Add result fields to accumulated
            if action_cls.result_model is not NoResult:
                accumulated.update(self._get_model_fields(action_cls.result_model))

        return missing

    def submit(
        self,
        params: dict[str, Any] | BaseModel,
        executor: Any,
        *,
        name: str | None = None,
        resume_from: str | None = None,
    ) -> str:
        """Submit the pipeline for remote execution (non-blocking).

        This method submits the pipeline to a remote executor for asynchronous
        execution. Use wait() or executor.get_progress() to monitor progress.

        Args:
            params: Initial parameters for the pipeline.
            executor: Pipeline executor (e.g., RayPipelineExecutor).
            name: Optional pipeline name for tracking.
            resume_from: Run ID to resume from. If provided, the pipeline will
                skip completed actions and restore accumulated params from the
                latest checkpoint of that run.

        Returns:
            Run ID for tracking the execution.

        Example:
            >>> from synapse_sdk.plugins.executors.ray import RayPipelineExecutor
            >>>
            >>> executor = RayPipelineExecutor(
            ...     ray_address='auto',
            ...     pipeline_service_url='http://localhost:8100',
            ... )
            >>> run_id = pipeline.submit(params, executor)
            >>> progress = executor.get_progress(run_id)
            >>> result = pipeline.wait(run_id, executor)
            >>>
            >>> # Resume from a failed run
            >>> new_run_id = pipeline.submit(params, executor, resume_from=run_id)
        """
        from synapse_sdk.plugins.executors.ray.pipeline import PipelineDefinition

        # Convert Pydantic model to dict if needed
        if isinstance(params, BaseModel):
            params_dict = params.model_dump()
        else:
            params_dict = dict(params)

        # Create pipeline definition
        pipeline_name = name or self.__repr__()
        pipeline_def = PipelineDefinition(
            name=pipeline_name,
            actions=self._actions,
        )

        # Submit to executor
        return executor.submit(pipeline_def, params_dict, resume_from=resume_from)

    def wait(
        self,
        run_id: str,
        executor: Any,
        *,
        timeout_seconds: float = 3600,
        poll_interval: float = 5.0,
    ) -> Any:
        """Wait for a submitted pipeline to complete.

        Args:
            run_id: Run ID from submit().
            executor: The same executor used for submit().
            timeout_seconds: Maximum time to wait.
            poll_interval: Seconds between progress polls.

        Returns:
            Final pipeline result.

        Raises:
            ExecutionError: If pipeline fails or times out.

        Example:
            >>> run_id = pipeline.submit(params, executor)
            >>> # ... do other work ...
            >>> result = pipeline.wait(run_id, executor)
        """
        executor.wait(run_id, timeout_seconds, poll_interval)
        return executor.get_result(run_id)

    @property
    def actions(self) -> list[type[BaseAction]]:
        """Get list of action classes in the pipeline."""
        return self._actions.copy()

    def __len__(self) -> int:
        return len(self._actions)

    def __repr__(self) -> str:
        action_names = ' | '.join(a.__name__ for a in self._actions)
        return f'ActionPipeline({action_names})'


__all__ = ['ActionPipeline', 'SchemaIncompatibleError']
