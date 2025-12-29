---
sidebar_label: action
title: synapse_sdk.plugins.actions.upload.action
---

Upload action base class with workflow step support.

## UploadProgressCategories Objects

```python
class UploadProgressCategories()
```

Standard progress category names for upload workflows.

Use these constants with set_progress() to track upload phases:
- INITIALIZE: Storage and path setup
- VALIDATE: File validation
- UPLOAD: File upload to storage
- CLEANUP: Post-upload cleanup

**Example**:

  >>> self.set_progress(1, 4, self.progress.INITIALIZE)

## BaseUploadAction Objects

```python
class BaseUploadAction()
```

Base class for upload actions with workflow step support.

Provides a full step-based workflow system:
- Override setup_steps() to register custom steps
- Steps execute in order with automatic rollback on failure
- Progress tracked across all steps based on weights

**Attributes**:

- `progress` - Standard progress category names.
  

**Example**:

  >>> class MyUploadAction(BaseUploadAction[MyParams]):
  ...     action_name = 'upload'
  ...     category = 'data_upload'
  ...     params_model = MyParams
  ...
  ...     def setup_steps(self, registry: StepRegistry) -> None:
  ...         registry.register(InitializeStep())
  ...         registry.register(ValidateStep())
  ...         registry.register(UploadFilesStep())
  ...         registry.register(CleanupStep())
  >>>
  >>> # Steps are executed in order with automatic rollback on failure
  >>> # Progress is tracked based on step weights

#### client

```python
@property
def client() -> BackendClient
```

Backend client from context.

**Returns**:

  BackendClient instance.
  

**Raises**:

- `RuntimeError` - If no client in context.

#### setup\_steps

```python
def setup_steps(registry: StepRegistry[UploadContext]) -> None
```

Register workflow steps.

Override this method to register custom steps for your upload workflow.
Steps are executed in registration order.

**Arguments**:

- `registry` - StepRegistry to register steps with.
  

**Example**:

  >>> def setup_steps(self, registry: StepRegistry[UploadContext]) -> None:
  ...     registry.register(InitializeStep())
  ...     registry.register(ValidateStep())
  ...     registry.register(UploadFilesStep())

#### create\_context

```python
def create_context() -> UploadContext
```

Create upload context for the workflow.

Override to customize context creation or add additional state.

**Returns**:

  UploadContext instance with params and runtime context.

#### execute

```python
def execute() -> dict[str, Any]
```

Execute the upload workflow.

Creates registry, registers steps via setup_steps(), creates context,
and runs the orchestrator.

**Returns**:

  Dict with success status and workflow results.
  

**Raises**:

- `RuntimeError` - If no steps registered or a step fails.

