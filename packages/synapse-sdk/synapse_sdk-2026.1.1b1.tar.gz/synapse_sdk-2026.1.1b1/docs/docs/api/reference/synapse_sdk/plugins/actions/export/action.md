---
sidebar_label: action
title: synapse_sdk.plugins.actions.export.action
---

Export action base class with optional step support.

## ExportProgressCategories Objects

```python
class ExportProgressCategories()
```

Standard progress category names for export workflows.

Use these constants with set_progress() to track export phases:
- DATASET_CONVERSION: Data conversion and file generation

**Example**:

  >>> self.set_progress(50, 100, self.progress.DATASET_CONVERSION)

## BaseExportAction Objects

```python
class BaseExportAction()
```

Base class for export actions.

Provides helper methods for export workflows.
Override get_filtered_results() for your specific target type.

Supports two execution modes:
1. Simple execute: Override execute() directly for simple workflows
2. Step-based: Override setup_steps() to register workflow steps

If setup_steps() registers any steps, the step-based workflow
takes precedence and execute() is not called directly.

**Attributes**:

- `progress` - Standard progress category names.
  
  Example (simple execute):
  >>> class MyExportAction(BaseExportAction[MyParams]):
  ...     action_name = 'export'
  ...     category = 'data_export'
  ...     params_model = MyParams
  ...
  ...     def get_filtered_results(self, filters: dict) -> tuple[Any, int]:
  ...         return self.client.get_assignments(filters)
  ...
  ...     def execute(self) -> dict[str, Any]:
  ...         results, count = self.get_filtered_results(self.params.filter)
  ...         self.set_progress(0, count, self.progress.DATASET_CONVERSION)
  ...         for i, item in enumerate(results, 1):
  ...             # Process and export item
  ...             self.set_progress(i, count, self.progress.DATASET_CONVERSION)
  ...         return \{'exported': count\}
  
  Example (step-based):
  >>> class MyExportAction(BaseExportAction[MyParams]):
  ...     def setup_steps(self, registry: StepRegistry[ExportContext]) -> None:
  ...         registry.register(FetchResultsStep())
  ...         registry.register(ProcessStep())
  ...         registry.register(FinalizeStep())

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
def setup_steps(registry: StepRegistry[ExportContext]) -> None
```

Register workflow steps for step-based execution.

Override this method to register custom steps for your export workflow.
If steps are registered, step-based execution takes precedence.

**Arguments**:

- `registry` - StepRegistry to register steps with.
  

**Example**:

  >>> def setup_steps(self, registry: StepRegistry[ExportContext]) -> None:
  ...     registry.register(FetchResultsStep())
  ...     registry.register(ProcessStep())
  ...     registry.register(FinalizeStep())

#### create\_context

```python
def create_context() -> ExportContext
```

Create export context for step-based workflow.

Override to customize context creation or add additional state.

**Returns**:

  ExportContext instance with params and runtime context.

#### run

```python
def run() -> Any
```

Run the action, using steps if registered.

This method is called by executors. It checks if steps are
registered and uses step-based execution if so.

**Returns**:

  Action result (dict or any return type).

#### get\_filtered\_results

```python
def get_filtered_results(filters: dict[str, Any]) -> tuple[Any, int]
```

Fetch filtered results for export.

Override this method for your specific target type
(assignments, ground_truth, tasks, or custom).

**Arguments**:

- `filters` - Filter criteria dict.
  

**Returns**:

  Tuple of (results_iterator, total_count).
  

**Raises**:

- `NotImplementedError` - Must be overridden by subclass.
  

**Example**:

  >>> # Override for assignments:
  >>> def get_filtered_results(self, filters: dict) -> tuple[Any, int]:
  ...     return self.client.get_assignments(filters)
  >>>
  >>> # Override for ground truth:
  >>> def get_filtered_results(self, filters: dict) -> tuple[Any, int]:
  ...     return self.client.get_ground_truth(filters)

