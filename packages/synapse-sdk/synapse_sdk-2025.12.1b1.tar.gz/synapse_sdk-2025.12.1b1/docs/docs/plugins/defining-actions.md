---
id: defining-actions
title: Defining Actions
sidebar_position: 2
---

# Defining Actions

Actions are the core building blocks of Synapse plugins. SDK v2 provides two ways to define actions:

1. **Function-based** using the `@action` decorator (simpler)
2. **Class-based** using `BaseAction` or category-specific base classes (more features)

## Function-Based Actions

Use the `@action` decorator for simple, stateless actions:

```python
from pydantic import BaseModel, Field
from synapse_sdk.plugins.decorators import action


class TrainParams(BaseModel):
    epochs: int = Field(default=50, ge=1, le=1000)
    batch_size: int = Field(default=8, ge=1, le=512)
    learning_rate: float = Field(default=0.001)


@action('train', params=TrainParams)
def train(params: TrainParams, ctx):
    """Train a model."""
    for epoch in range(params.epochs):
        ctx.set_progress(epoch + 1, params.epochs, 'train')
        # Training logic here

    return {'status': 'completed', 'epochs': params.epochs}
```

### Decorator Syntax

```python
@action(name, description, params)
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | `str` | No | Action name. Defaults to function name. |
| `description` | `str` | No | Human-readable description. |
| `params` | `type[BaseModel]` | No | Pydantic model for parameter validation. |

**Syntax variations:**

```python
# Positional name
@action('train', params=TrainParams)
def train(params, ctx): ...

# Keyword only - name defaults to function name
@action(params=TrainParams)
def train(params, ctx): ...  # name will be 'train'

# All keyword arguments
@action(name='train', description='Train a model', params=TrainParams)
def train(params, ctx): ...

# Minimal - no params validation
@action('inference')
def inference(params, ctx): ...
```

### Function Signature

```python
def action_function(params: ParamsModel, ctx: RuntimeContext) -> Any:
    ...
```

| Argument | Type | Description |
|----------|------|-------------|
| `params` | Pydantic model instance | Validated parameters |
| `ctx` | `RuntimeContext` | Runtime context with logging, env, client |

## Class-Based Actions

Use class-based actions for complex workflows with helper methods:

```python
from pydantic import BaseModel, Field
from synapse_sdk.plugins.actions.train import BaseTrainAction


class TrainParams(BaseModel):
    epochs: int = Field(default=50, ge=1, le=1000)
    batch_size: int = Field(default=8, ge=1, le=512)
    learning_rate: float = Field(default=0.001)


class YoloTrainAction(BaseTrainAction[TrainParams]):
    params_model = TrainParams

    def execute(self):
        # Access params via self.params
        # Access context via self.ctx

        dataset = self.get_dataset()  # Helper from BaseTrainAction

        for epoch in range(self.params.epochs):
            self.set_progress(epoch + 1, self.params.epochs, 'train')
            # Training logic

        self.create_model('/path/to/model.pt')
        return {'status': 'completed'}
```

### Minimal Class Definition

When using config.yaml-based discovery, you only need `params_model` and `execute()`:

```python
class YoloTrainAction(BaseTrainAction[TrainParams]):
    params_model = TrainParams  # Required

    def execute(self):  # Required
        return {'status': 'done'}
```

The SDK injects `action_name` and `category` from config.yaml during discovery.

### Optional Class Attributes

You can explicitly set metadata to override config.yaml values:

```python
class YoloTrainAction(BaseTrainAction[TrainParams]):
    action_name = 'train'      # Optional - injected from config key
    category = 'neural_net'    # Optional - injected from plugin category
    params_model = TrainParams

    def execute(self):
        return {'status': 'done'}
```

### Available Base Classes

| Base Class | Category | Helper Methods |
|------------|----------|----------------|
| `BaseAction` | Generic | `set_progress()`, `set_metrics()`, `log()` |
| `BaseTrainAction` | `neural_net` | `get_dataset()`, `create_model()`, `get_model()` |
| `BaseExportAction` | `export` | `get_filtered_results()` |
| `BaseUploadAction` | `upload` | Step-based workflow with rollback |
| `BaseInferenceAction` | `neural_net` | Model loading helpers |

## RuntimeContext

Both function-based and class-based actions receive a `RuntimeContext`:

```python
@dataclass
class RuntimeContext:
    logger: BaseLogger
    env: PluginEnvironment
    job_id: str | None
    client: BackendClient | None
    agent_client: AgentClient | None
    checkpoint: dict[str, Any] | None  # Pretrained model info
```

### Available Methods

```python
# Progress tracking
ctx.set_progress(current=50, total=100, category='train')

# Metrics
ctx.set_metrics({'loss': 0.1, 'accuracy': 0.95}, category='training')

# Logging
ctx.log('event_name', {'key': 'value'})
ctx.log_message('User-facing message', context='info')
ctx.log_dev_event('Debug message', data={'debug': True})

# Environment
value = ctx.env.get('MY_VAR', default='fallback')

# Backend client (if available)
dataset = ctx.client.get_data_collection(dataset_id)

# Checkpoint (pretrained model)
model_path = ctx.checkpoint.get('path', 'default.pt') if ctx.checkpoint else 'default.pt'
```

## Discovery Modes

### 1. Module Discovery (with @action)

No config.yaml entrypoint needed - SDK introspects the module:

```python
# plugin/train.py
@action('train', params=TrainParams)
def train(params, ctx):
    ...
```

```python
from synapse_sdk.plugins.discovery import PluginDiscovery
import plugin.train as train_module

discovery = PluginDiscovery.from_module(train_module)
discovery.list_actions()  # ['train'] - auto-discovered
```

### 2. Config Discovery (with entrypoint)

Specify entrypoint in config.yaml:

```yaml
# config.yaml
name: yolov8
code: yolov8
category: neural_net

actions:
  train:
    entrypoint: plugin.train.YoloTrainAction
    method: job
  inference:
    entrypoint: plugin.inference.infer  # Can be function too
    method: task
```

```python
discovery = PluginDiscovery.from_path('/path/to/plugin')
discovery.list_actions()  # ['train', 'inference']
```

## Running Actions

### Via run_plugin

```python
from synapse_sdk.plugins.runner import run_plugin

# Auto-discover from module path
result = run_plugin('plugin.train', 'train', {'epochs': 10})

# Auto-discover from config.yaml path
result = run_plugin('/path/to/plugin', 'train', {'epochs': 10})

# Execution modes
result = run_plugin('plugin', 'train', params, mode='local')  # Current process
result = run_plugin('plugin', 'train', params, mode='task')   # Ray Actor
job_id = run_plugin('plugin', 'train', params, mode='job')    # Ray Job (async)
```

## Best Practices

### 1. Use Function-Based for Simple Actions

```python
@action('healthcheck')
def healthcheck(params, ctx):
    return {'status': 'ok'}
```

### 2. Use Class-Based for Complex Workflows

```python
class TrainAction(BaseTrainAction[TrainParams]):
    params_model = TrainParams

    def execute(self):
        dataset = self.get_dataset()      # Built-in helper
        model_path = self._train(dataset)  # Custom method
        self.create_model(model_path)      # Built-in helper
        return {'status': 'done'}

    def _train(self, dataset):
        # Custom training logic
        pass
```

### 3. Let Config Be the Source of Truth

```python
# Minimal - SDK injects action_name/category from config.yaml
class TrainAction(BaseTrainAction[TrainParams]):
    params_model = TrainParams

    def execute(self):
        return {}
```

### 4. Use Checkpoint for Pretrained Models

```python
def execute(self):
    checkpoint = self.ctx.checkpoint or {}
    model_path = checkpoint.get('path', 'yolov8n.pt')
    category = checkpoint.get('category', 'base')  # 'base' or fine-tuned

    model = load_model(model_path)
    ...
```

### 5. Report Progress Meaningfully

```python
def execute(self):
    total_epochs = self.params.epochs

    for epoch in range(total_epochs):
        self.set_progress(epoch + 1, total_epochs, 'train')
        # Train epoch

    self.set_progress(100, 100, 'model_upload')
    self.create_model(model_path)
```
