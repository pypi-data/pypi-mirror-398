---
sidebar_label: registry
title: synapse_sdk.plugins.pipelines.steps.registry
---

Step registry for managing ordered workflow steps.

## StepRegistry Objects

```python
class StepRegistry()
```

Registry for managing ordered workflow steps.

Type parameter C is the context type for steps in this registry.
Maintains an ordered list of steps and provides methods for
registration, removal, and insertion at specific positions.

**Example**:

  >>> registry = StepRegistry[MyContext]()
  >>> registry.register(InitStep())
  >>> registry.register(ProcessStep())
  >>> registry.insert_before('process', ValidateStep())
  >>> for step in registry.get_steps():
  ...     print(step.name)  # init, validate, process

#### register

```python
def register(step: BaseStep[C]) -> None
```

Add step to end of workflow.

**Arguments**:

- `step` - Step instance to register.

#### unregister

```python
def unregister(name: str) -> None
```

Remove step by name.

**Arguments**:

- `name` - Name of step to remove.

#### get\_steps

```python
def get_steps() -> list[BaseStep[C]]
```

Get ordered list of steps.

**Returns**:

  Copy of the step list in execution order.

#### insert\_after

```python
def insert_after(after_name: str, step: BaseStep[C]) -> None
```

Insert step after another step.

**Arguments**:

- `after_name` - Name of existing step to insert after.
- `step` - Step instance to insert.
  

**Raises**:

- `ValueError` - If step with after_name not found.

#### insert\_before

```python
def insert_before(before_name: str, step: BaseStep[C]) -> None
```

Insert step before another step.

**Arguments**:

- `before_name` - Name of existing step to insert before.
- `step` - Step instance to insert.
  

**Raises**:

- `ValueError` - If step with before_name not found.

#### total\_weight

```python
@property
def total_weight() -> float
```

Sum of all step weights.

**Returns**:

  Total progress weight across all registered steps.

