---
sidebar_label: upload
title: synapse_sdk.plugins.actions.upload
---

Upload action module with workflow step support.

Provides a full step-based workflow system for upload actions:
- BaseUploadAction: Base class for upload workflows
- UploadContext: Upload-specific context extending BaseStepContext
- UploadProgressCategories: Standard progress category names

For step infrastructure (BaseStep, StepRegistry, Orchestrator),
use the generic pipeline module:
from synapse_sdk.plugins.pipelines.steps import BaseStep, StepRegistry

**Example**:

  >>> from synapse_sdk.plugins.pipelines.steps import BaseStep, StepResult
  >>> from synapse_sdk.plugins.actions.upload import (
  ...     BaseUploadAction,
  ...     UploadContext,
  ... )
  >>>
  >>> class InitStep(BaseStep[UploadContext]):
  ...     @property
  ...     def name(self) -> str:
  ...         return 'initialize'
  ...
  ...     @property
  ...     def progress_weight(self) -> float:
  ...         return 0.1
  ...
  ...     def execute(self, context: UploadContext) -> StepResult:
  ...         # Initialize storage, validate params
  ...         return StepResult(success=True)
  >>>
  >>> class MyUploadAction(BaseUploadAction[MyParams]):
  ...     def setup_steps(self, registry) -> None:
  ...         registry.register(InitStep())

