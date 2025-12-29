---
sidebar_label: validation
title: synapse_sdk.plugins.pipelines.steps.utils.validation
---

Validation step for checking context state.

## ValidationStep Objects

```python
class ValidationStep()
```

Validates context state before proceeding.

Takes a validator function that checks context and returns
(is_valid, error_message). Fails the step if validation fails.

**Example**:

  >>> def check_data(ctx: MyContext) -> tuple[bool, str | None]:
  ...     if not ctx.data:
  ...         return False, 'No data loaded'
  ...     return True, None
  >>>
  >>> registry.register(ValidationStep(check_data, name='validate_data'))

#### name

```python
@property
def name() -> str
```

Return step name.

#### progress\_weight

```python
@property
def progress_weight() -> float
```

Return progress weight.

#### execute

```python
def execute(context: C) -> StepResult
```

Execute validation.

**Arguments**:

- `context` - Shared context to validate.
  

**Returns**:

  StepResult with success=False if validation fails.

