---
sidebar_label: action
title: synapse_sdk.plugins.actions.inference.action
---

Inference action base class with optional step support.

## InferenceProgressCategories Objects

```python
class InferenceProgressCategories()
```

Standard progress category names for inference workflows.

Use these constants with set_progress() to track inference phases:
- MODEL_LOAD: Model loading and initialization
- INFERENCE: Running inference on inputs
- POSTPROCESS: Post-processing results

**Example**:

  >>> self.set_progress(1, 3, self.progress.MODEL_LOAD)
  >>> self.set_progress(2, 3, self.progress.INFERENCE)

## BaseInferenceAction Objects

```python
class BaseInferenceAction()
```

Base class for inference actions.

Provides helper methods for model loading and inference workflows.
Supports both REST API-based inference (via Ray Serve) and batch
inference with step-based workflows.

Supports two execution modes:
1. Simple execute: Override execute() directly for simple workflows
2. Step-based: Override setup_steps() to register workflow steps

If setup_steps() registers any steps, the step-based workflow
takes precedence and execute() is not called directly.

**Attributes**:

- `progress` - Standard progress category names.
  
  Example (simple execute):
  >>> class MyInferenceAction(BaseInferenceAction[MyParams]):
  ...     action_name = 'inference'
  ...     category = 'neural_net'
  ...     params_model = MyParams
  ...
  ...     def execute(self) -> dict[str, Any]:
  ...         model = self.load_model(self.params.model_id)
  ...         self.set_progress(1, 3, self.progress.MODEL_LOAD)
  ...         results = self.infer(model, self.params.inputs)
  ...         self.set_progress(2, 3, self.progress.INFERENCE)
  ...         return \{'results': results\}
  
  Example (step-based):
  >>> class MyInferenceAction(BaseInferenceAction[MyParams]):
  ...     def setup_steps(self, registry: StepRegistry[InferenceContext]) -> None:
  ...         registry.register(LoadModelStep())
  ...         registry.register(InferenceStep())
  ...         registry.register(PostProcessStep())

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
def setup_steps(registry: StepRegistry[InferenceContext]) -> None
```

Register workflow steps for step-based execution.

Override this method to register custom steps for your inference workflow.
If steps are registered, step-based execution takes precedence.

**Arguments**:

- `registry` - StepRegistry to register steps with.
  

**Example**:

  >>> def setup_steps(self, registry: StepRegistry[InferenceContext]) -> None:
  ...     registry.register(LoadModelStep())
  ...     registry.register(InferenceStep())
  ...     registry.register(PostProcessStep())

#### create\_context

```python
def create_context() -> InferenceContext
```

Create inference context for step-based workflow.

Override to customize context creation or add additional state.

**Returns**:

  InferenceContext instance with params and runtime context.

#### run

```python
def run() -> Any
```

Run the action, using steps if registered.

This method is called by executors. It checks if steps are
registered and uses step-based execution if so.

**Returns**:

  Action result (dict or any return type).

#### get\_model

```python
def get_model(model_id: int) -> dict[str, Any]
```

Retrieve model metadata by ID.

**Arguments**:

- `model_id` - Model identifier.
  

**Returns**:

  Model metadata dictionary including file URL.
  

**Raises**:

- `RuntimeError` - If no client in context.
  

**Example**:

  >>> model = self.get_model(123)
  >>> print(model['name'], model['file'])

#### download\_model

```python
def download_model(model_id: int,
                   output_dir: str | Path | None = None) -> Path
```

Download and extract model artifacts.

Fetches model metadata, downloads the model archive, and extracts
it to the specified directory (or a temp directory if not specified).

**Arguments**:

- `model_id` - Model identifier.
- `output_dir` - Directory to extract model to. If None, uses tempdir.
  

**Returns**:

  Path to extracted model directory.
  

**Raises**:

- `RuntimeError` - If no client in context.
- `ValueError` - If model has no file URL.
  

**Example**:

  >>> model_path = self.download_model(123)
  >>> # Load model from model_path

#### load\_model

```python
def load_model(model_id: int) -> dict[str, Any]
```

Load model for inference.

Downloads model artifacts and returns model info with local path.
Override this method for custom model loading (e.g., loading into
specific framework like PyTorch, TensorFlow).

**Arguments**:

- `model_id` - Model identifier.
  

**Returns**:

  Model metadata dict with 'path' key for local artifacts.
  

**Example**:

  >>> model_info = self.load_model(123)
  >>> model_path = model_info['path']
  >>> # Load your model framework here:
  >>> # model = torch.load(model_path / 'model.pt')

#### infer

```python
def infer(model: Any, inputs: list[dict[str, Any]]) -> list[dict[str, Any]]
```

Run inference on inputs.

Override this method to implement your inference logic.
This is called by execute() in simple mode.

**Arguments**:

- `model` - Loaded model (framework-specific).
- `inputs` - List of input dictionaries.
  

**Returns**:

  List of result dictionaries.
  

**Raises**:

- `NotImplementedError` - Must be overridden by subclass.
  

**Example**:

  >>> def infer(self, model, inputs):
  ...     results = []
  ...     for inp in inputs:
  ...         prediction = model.predict(inp['image'])
  ...         results.append(\{'prediction': prediction\})
  ...     return results

