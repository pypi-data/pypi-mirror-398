---
sidebar_label: orchestrator
title: synapse_sdk.plugins.pipelines.steps.orchestrator
---

Orchestrator for executing workflow steps with rollback support.

## Orchestrator Objects

```python
class Orchestrator()
```

Executes workflow steps with progress tracking and rollback.

Type parameter C is the context type shared between steps.
Runs steps in order, tracking progress based on step weights.
On failure, automatically rolls back executed steps in reverse order.

**Attributes**:

- `registry` - StepRegistry containing ordered steps.
- `context` - Shared context for step communication.
- `progress_callback` - Optional callback for progress updates.
  

**Example**:

  >>> registry = StepRegistry[MyContext]()
  >>> registry.register(InitStep())
  >>> registry.register(ProcessStep())
  >>> context = MyContext(runtime_ctx=runtime_ctx)
  >>> orchestrator = Orchestrator(registry, context)
  >>> result = orchestrator.execute()

#### execute

```python
def execute() -> dict[str, Any]
```

Execute all steps in order with rollback on failure.

**Returns**:

  Dict with success status and step count.
  

**Raises**:

- `RuntimeError` - If any step fails (after rollback).

