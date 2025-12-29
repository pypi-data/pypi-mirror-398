"""Category-specific action base classes.

Provides specialized base classes for common action types:
    - DatasetAction: Download and convert dataset workflows
    - BaseTrainAction: Training workflows with dataset/model helpers
    - BaseExportAction: Export workflows with filtered results
    - BaseUploadAction: Upload workflows with step-based execution
    - BaseInferenceAction: Inference workflows with model loading
    - BaseDeploymentAction: Ray Serve deployment workflows

Each base class provides:
    - Standard progress category names
    - Helper methods with sensible defaults
    - Override points for custom behavior
    - Optional step-based workflow execution

For pipeline orchestration, use the pipelines module:
    from synapse_sdk.plugins.pipelines import ActionPipeline
"""

from synapse_sdk.plugins.actions.dataset import (
    DatasetAction,
    DatasetOperation,
    DatasetParams,
    DatasetResult,
)
from synapse_sdk.plugins.actions.export import (
    BaseExportAction,
    ExportContext,
    ExportProgressCategories,
)
from synapse_sdk.plugins.actions.inference import (
    BaseDeploymentAction,
    BaseInferenceAction,
    BaseServeDeployment,
    DeploymentContext,
    DeploymentProgressCategories,
    InferenceContext,
    InferenceProgressCategories,
    create_serve_multiplexed_model_id,
)
from synapse_sdk.plugins.actions.train import (
    BaseTrainAction,
    TrainContext,
    TrainProgressCategories,
)
from synapse_sdk.plugins.actions.upload import (
    BaseStep,
    BaseUploadAction,
    Orchestrator,
    StepRegistry,
    StepResult,
    UploadContext,
    UploadProgressCategories,
)

__all__ = [
    # Dataset
    'DatasetAction',
    'DatasetOperation',
    'DatasetParams',
    'DatasetResult',
    # Train
    'BaseTrainAction',
    'TrainContext',
    'TrainProgressCategories',
    # Export
    'BaseExportAction',
    'ExportContext',
    'ExportProgressCategories',
    # Upload
    'BaseUploadAction',
    'UploadContext',
    'UploadProgressCategories',
    # Inference
    'BaseInferenceAction',
    'InferenceContext',
    'InferenceProgressCategories',
    # Deployment
    'BaseDeploymentAction',
    'DeploymentContext',
    'DeploymentProgressCategories',
    # Serve
    'BaseServeDeployment',
    'create_serve_multiplexed_model_id',
    # Step infrastructure (re-exported from pipelines.steps)
    'BaseStep',
    'StepResult',
    'StepRegistry',
    'Orchestrator',
]
