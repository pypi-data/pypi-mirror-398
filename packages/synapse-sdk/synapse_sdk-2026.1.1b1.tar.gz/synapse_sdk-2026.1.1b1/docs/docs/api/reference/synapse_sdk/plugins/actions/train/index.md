---
sidebar_label: train
title: synapse_sdk.plugins.actions.train
---

Train action module with optional workflow step support.

Provides the training action base class:
    - BaseTrainAction: Base class for training workflows
    - TrainContext: Training-specific context extending BaseStepContext
    - TrainProgressCategories: Standard progress category names

For step infrastructure (BaseStep, StepRegistry, Orchestrator),
use the generic pipeline module:
    from synapse_sdk.plugins.pipelines.steps import BaseStep, StepRegistry

Example (simple execute):
    >>> class MyTrainAction(BaseTrainAction[MyParams]):
    ...     def execute(self) -> dict[str, Any]:
    ...         dataset = self.get_dataset()
    ...         # ... train model ...
    ...         return \{'model_id': model['id']\}

Example (step-based):
    >>> from synapse_sdk.plugins.pipelines.steps import BaseStep, StepResult
    >>>
    >>> class LoadDatasetStep(BaseStep[TrainContext]):
    ...     @property
    ...     def name(self) -> str:
    ...         return 'load_dataset'
    ...
    ...     @property
    ...     def progress_weight(self) -> float:
    ...         return 0.2
    ...
    ...     def execute(self, context: TrainContext) -> StepResult:
    ...         context.dataset = load_data(context.params['dataset_id'])
    ...         return StepResult(success=True)
    >>>
    >>> class MyTrainAction(BaseTrainAction[MyParams]):
    ...     def setup_steps(self, registry) -> None:
    ...         registry.register(LoadDatasetStep())
    ...         registry.register(TrainStep())
    ...         registry.register(UploadModelStep())

