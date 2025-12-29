---
sidebar_label: actions
title: synapse_sdk.plugins.actions
---

Category-specific action base classes.

Provides specialized base classes for common action types:
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

For step-based workflow infrastructure, use the pipelines module:
    from synapse_sdk.plugins.pipelines.steps import BaseStep, StepRegistry, Orchestrator

