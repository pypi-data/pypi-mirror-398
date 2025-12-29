---
sidebar_label: action
title: synapse_sdk.plugins.actions.train.action
---

Train action base class with optional step support.

## TrainProgressCategories Objects

```python
class TrainProgressCategories()
```

Standard progress category names for training workflows.

Use these constants with set_progress() to track multi-phase training:
- DATASET: Data loading and preprocessing
- TRAIN: Model training iterations
- MODEL_UPLOAD: Final model upload to backend

**Example**:

  >>> self.set_progress(1, 10, TrainProgressCategories.DATASET)
  >>> self.set_progress(50, 100, TrainProgressCategories.TRAIN)

## BaseTrainAction Objects

```python
class BaseTrainAction()
```

Base class for training actions.

Provides helper methods for common training workflows:
dataset fetching, model creation, and progress tracking.

Supports two execution modes:
1. Simple execute: Override execute() directly for simple workflows
2. Step-based: Override setup_steps() to register workflow steps

If setup_steps() registers any steps, the step-based workflow
takes precedence and execute() is not called directly.

**Attributes**:

- `progress` - Standard progress category names.
  
  Example (simple execute):
  >>> class MyTrainAction(BaseTrainAction[MyParams]):
  ...     action_name = 'train'
  ...     category = 'neural_net'
  ...     params_model = MyParams
  ...
  ...     def execute(self) -> dict[str, Any]:
  ...         dataset = self.get_dataset()
  ...         self.set_progress(1, 3, self.progress.DATASET)
  ...         model_path = self._train(dataset)
  ...         self.set_progress(2, 3, self.progress.TRAIN)
  ...         model = self.create_model(model_path)
  ...         self.set_progress(3, 3, self.progress.MODEL_UPLOAD)
  ...         return \{'model_id': model['id']\}
  
  Example (step-based):
  >>> class MyTrainAction(BaseTrainAction[MyParams]):
  ...     def setup_steps(self, registry: StepRegistry[TrainContext]) -> None:
  ...         registry.register(LoadDatasetStep())
  ...         registry.register(TrainStep())
  ...         registry.register(UploadModelStep())

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
def setup_steps(registry: StepRegistry[TrainContext]) -> None
```

Register workflow steps for step-based execution.

Override this method to register custom steps for your training workflow.
If steps are registered, step-based execution takes precedence.

**Arguments**:

- `registry` - StepRegistry to register steps with.
  

**Example**:

  >>> def setup_steps(self, registry: StepRegistry[TrainContext]) -> None:
  ...     registry.register(LoadDatasetStep())
  ...     registry.register(TrainStep())
  ...     registry.register(UploadModelStep())

#### create\_context

```python
def create_context() -> TrainContext
```

Create training context for step-based workflow.

Override to customize context creation or add additional state.

**Returns**:

  TrainContext instance with params and runtime context.

#### run

```python
def run() -> Any
```

Run the action, using steps if registered.

This method is called by executors. It checks if steps are
registered and uses step-based execution if so.

**Returns**:

  Action result (dict or any return type).

#### get\_dataset

```python
def get_dataset() -> dict[str, Any]
```

Fetch training dataset from backend.

Default implementation uses params.dataset_id to fetch
via client.get_data_collection(). Override for custom behavior.

**Returns**:

  Dataset metadata dictionary.
  

**Raises**:

- `ValueError` - If params.dataset_id is not set.
- `RuntimeError` - If no client in context.
  

**Example**:

  >>> # Override for S3:
  >>> def get_dataset(self) -> dict[str, Any]:
  ...     return download_from_s3(self.params.s3_path)

#### create\_model

```python
def create_model(path: str, **kwargs: Any) -> dict[str, Any]
```

Upload trained model to backend.

Default implementation uploads via client.create_model().
Override for custom behavior (e.g., MLflow, S3).

**Arguments**:

- `path` - Local path to model artifacts.
- `**kwargs` - Additional fields for model creation.
  

**Returns**:

  Created model metadata dictionary.
  

**Raises**:

- `RuntimeError` - If no client in context.
  

**Example**:

  >>> model = self.create_model('./model', name='my-model')

#### get\_model

```python
def get_model(model_id: int) -> dict[str, Any]
```

Retrieve existing model by ID.

**Arguments**:

- `model_id` - Model identifier.
  

**Returns**:

  Model metadata dictionary.
  

**Raises**:

- `RuntimeError` - If no client in context.

