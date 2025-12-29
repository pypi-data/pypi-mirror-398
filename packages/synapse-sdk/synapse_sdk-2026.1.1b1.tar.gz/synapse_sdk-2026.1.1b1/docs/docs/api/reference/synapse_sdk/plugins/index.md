---
sidebar_label: plugins
title: synapse_sdk.plugins
---

Plugin architecture for Synapse SDK.

This module provides the core plugin framework including:
- Plugin configuration and discovery
- Action definition (class-based and function-based)
- Execution modes (local, task, job)
- Pipeline patterns (step-based workflows)

**Example**:

  >>> from synapse_sdk.plugins import action, run_plugin
  >>> from pydantic import BaseModel
  >>>
  >>> class TrainParams(BaseModel):
  ...     epochs: int = 10
  >>>
  >>> @action(params=TrainParams)
  ... def train(params: TrainParams, context) -> dict:
  ...     return \{'trained': True\}
  >>>
  >>> # Execute the plugin action
  >>> result = run_plugin('my_plugin', 'train', \{'epochs': 20\})

