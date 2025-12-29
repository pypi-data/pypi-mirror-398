"""Pipeline patterns for Synapse SDK.

This module provides various pipeline execution patterns:
- ActionPipeline: Chain actions with input/output schema validation
- PipelineContext: Shared working directory for pipeline actions
- Progress models: Track pipeline and action progress
- steps: Sequential step-based workflows with rollback support (for internal use)

Example:
    >>> from synapse_sdk.plugins.pipelines import ActionPipeline, PipelineContext
    >>>
    >>> # Unix pipe style: Download | Convert | Train
    >>> pipeline = ActionPipeline([
    ...     DownloadDatasetAction,
    ...     ConvertDatasetAction,
    ...     TrainAction,
    ... ])
    >>>
    >>> result = pipeline.execute(params, ctx)
"""

from synapse_sdk.plugins.pipelines.action_pipeline import (
    ActionPipeline,
    SchemaIncompatibleError,
)
from synapse_sdk.plugins.pipelines.context import PipelineContext
from synapse_sdk.plugins.pipelines.display import (
    display_progress,
    display_progress_async,
    print_progress_summary,
)
from synapse_sdk.plugins.pipelines.models import (
    ActionProgress,
    ActionStatus,
    Checkpoint,
    LogEntry,
    LogLevel,
    PipelineProgress,
    RunStatus,
)
from synapse_sdk.plugins.pipelines.steps import (
    BaseStep,
    BaseStepContext,
    LoggingStep,
    Orchestrator,
    StepRegistry,
    StepResult,
    TimingStep,
    ValidationStep,
)

__all__ = [
    # Action Pipeline (recommended)
    'ActionPipeline',
    'SchemaIncompatibleError',
    # Pipeline Context
    'PipelineContext',
    # Display Utilities
    'display_progress',
    'display_progress_async',
    'print_progress_summary',
    # Progress Models
    'ActionProgress',
    'ActionStatus',
    'Checkpoint',
    'LogEntry',
    'LogLevel',
    'PipelineProgress',
    'RunStatus',
    # Steps - Core (internal)
    'BaseStep',
    'BaseStepContext',
    'Orchestrator',
    'StepRegistry',
    'StepResult',
    # Steps - Utilities
    'LoggingStep',
    'TimingStep',
    'ValidationStep',
]
