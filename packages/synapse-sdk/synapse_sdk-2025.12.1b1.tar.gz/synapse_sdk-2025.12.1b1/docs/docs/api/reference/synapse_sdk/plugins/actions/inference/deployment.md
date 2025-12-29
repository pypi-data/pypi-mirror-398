---
sidebar_label: deployment
title: synapse_sdk.plugins.actions.inference.deployment
---

Deployment action base class for Ray Serve deployments.

## DeploymentProgressCategories Objects

```python
class DeploymentProgressCategories()
```

Standard progress category names for deployment workflows.

Use these constants with set_progress() to track deployment phases:
- INITIALIZE: Ray cluster initialization
- DEPLOY: Deploying to Ray Serve
- REGISTER: Registering with backend

**Example**:

  >>> self.set_progress(1, 3, self.progress.INITIALIZE)
  >>> self.set_progress(2, 3, self.progress.DEPLOY)

## BaseDeploymentAction Objects

```python
class BaseDeploymentAction()
```

Base class for Ray Serve deployment actions.

Provides helper methods for deploying inference endpoints to Ray Serve.
Handles Ray initialization, deployment creation, and backend registration.

Supports two execution modes:
1. Simple execute: Override execute() directly for simple deployments
2. Step-based: Override setup_steps() to register workflow steps

**Attributes**:

- `progress` - Standard progress category names.
- `entrypoint` - The serve deployment class to deploy (set in subclass).
  
  Example (simple execute):
  >>> class MyDeploymentAction(BaseDeploymentAction[MyParams]):
  ...     action_name = 'deployment'
  ...     category = 'neural_net'
  ...     params_model = MyParams
  ...     entrypoint = MyServeDeployment
  ...
  ...     def execute(self) -> dict[str, Any]:
  ...         self.ray_init()
  ...         self.set_progress(1, 3, self.progress.INITIALIZE)
  ...         self.deploy()
  ...         self.set_progress(2, 3, self.progress.DEPLOY)
  ...         app_id = self.register_serve_application()
  ...         self.set_progress(3, 3, self.progress.REGISTER)
  ...         return \{'serve_application': app_id\}
  
  Example (step-based):
  >>> class MyDeploymentAction(BaseDeploymentAction[MyParams]):
  ...     entrypoint = MyServeDeployment
  ...
  ...     def setup_steps(self, registry: StepRegistry[DeploymentContext]) -> None:
  ...         registry.register(InitializeRayStep())
  ...         registry.register(DeployStep())
  ...         registry.register(RegisterStep())

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

#### agent\_client

```python
@property
def agent_client() -> AgentClient
```

Agent client from context.

**Returns**:

  AgentClient instance for Ray operations.
  

**Raises**:

- `RuntimeError` - If no agent_client in context.

#### setup\_steps

```python
def setup_steps(registry: StepRegistry[DeploymentContext]) -> None
```

Register workflow steps for step-based execution.

Override this method to register custom steps for deployment workflow.
If steps are registered, step-based execution takes precedence.

**Arguments**:

- `registry` - StepRegistry to register steps with.
  

**Example**:

  >>> def setup_steps(self, registry: StepRegistry[DeploymentContext]) -> None:
  ...     registry.register(InitializeRayStep())
  ...     registry.register(DeployStep())
  ...     registry.register(RegisterStep())

#### create\_context

```python
def create_context() -> DeploymentContext
```

Create deployment context for step-based workflow.

Override to customize context creation or add additional state.

**Returns**:

  DeploymentContext instance with params and runtime context.

#### run

```python
def run() -> Any
```

Run the action, using steps if registered.

This method is called by executors. It checks if steps are
registered and uses step-based execution if so.

**Returns**:

  Action result (dict or any return type).

#### get\_serve\_app\_name

```python
def get_serve_app_name() -> str
```

Get the name for the Ray Serve application.

Default uses plugin release code from SYNAPSE_PLUGIN_RELEASE_CODE env var.
Override for custom naming.

**Returns**:

  Serve application name.

#### get\_route\_prefix

```python
def get_route_prefix() -> str
```

Get the route prefix for the deployment.

Default uses plugin release checksum from SYNAPSE_PLUGIN_RELEASE_CHECKSUM env var.
Override for custom routing.

**Returns**:

  Route prefix string (e.g., '/abc123').

#### get\_ray\_actor\_options

```python
def get_ray_actor_options() -> dict[str, Any]
```

Get Ray actor options for the deployment.

Default extracts num_cpus and num_gpus from params.
Override for custom resource allocation.

**Returns**:

  Dict with Ray actor options (num_cpus, num_gpus, etc.).

#### get\_runtime\_env

```python
def get_runtime_env() -> dict[str, Any]
```

Get Ray runtime environment.

Override to customize the runtime environment for deployments.

**Returns**:

  Dict with runtime environment configuration.

#### ray\_init

```python
def ray_init(**kwargs: Any) -> None
```

Initialize Ray cluster connection.

Call this before deploying to ensure Ray is connected.

**Arguments**:

- `**kwargs` - Additional arguments for ray.init().

#### deploy

```python
def deploy() -> None
```

Deploy the inference endpoint to Ray Serve.

Uses the entrypoint class and current configuration to create
a Ray Serve deployment.

**Raises**:

- `RuntimeError` - If entrypoint is not set.
- `ImportError` - If Ray Serve is not installed.

#### register\_serve\_application

```python
def register_serve_application() -> int | None
```

Register the serve application with the backend.

Creates a serve application record in the backend for tracking.

**Returns**:

  Serve application ID if created, None otherwise.

