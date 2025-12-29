"""Deployment action base class for Ray Serve deployments."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

from pydantic import BaseModel

from synapse_sdk.plugins.action import BaseAction
from synapse_sdk.plugins.actions.inference.context import DeploymentContext
from synapse_sdk.plugins.pipelines.steps import Orchestrator, StepRegistry

P = TypeVar('P', bound=BaseModel)

if TYPE_CHECKING:
    from synapse_sdk.clients.agent import AgentClient
    from synapse_sdk.clients.backend import BackendClient


class DeploymentProgressCategories:
    """Standard progress category names for deployment workflows.

    Use these constants with set_progress() to track deployment phases:
        - INITIALIZE: Ray cluster initialization
        - DEPLOY: Deploying to Ray Serve
        - REGISTER: Registering with backend

    Example:
        >>> self.set_progress(1, 3, self.progress.INITIALIZE)
        >>> self.set_progress(2, 3, self.progress.DEPLOY)
    """

    INITIALIZE: str = 'initialize'
    DEPLOY: str = 'deploy'
    REGISTER: str = 'register'


class BaseDeploymentAction(BaseAction[P]):
    """Base class for Ray Serve deployment actions.

    Provides helper methods for deploying inference endpoints to Ray Serve.
    Handles Ray initialization, deployment creation, and backend registration.

    Supports two execution modes:
    1. Simple execute: Override execute() directly for simple deployments
    2. Step-based: Override setup_steps() to register workflow steps

    Attributes:
        progress: Standard progress category names.
        entrypoint: The serve deployment class to deploy (set in subclass).

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
        ...         return {'serve_application': app_id}

    Example (step-based):
        >>> class MyDeploymentAction(BaseDeploymentAction[MyParams]):
        ...     entrypoint = MyServeDeployment
        ...
        ...     def setup_steps(self, registry: StepRegistry[DeploymentContext]) -> None:
        ...         registry.register(InitializeRayStep())
        ...         registry.register(DeployStep())
        ...         registry.register(RegisterStep())
    """

    progress = DeploymentProgressCategories()

    # Override in subclass with your serve deployment class
    entrypoint: type | None = None

    @property
    def client(self) -> BackendClient:
        """Backend client from context.

        Returns:
            BackendClient instance.

        Raises:
            RuntimeError: If no client in context.
        """
        if self.ctx.client is None:
            raise RuntimeError('No client in context. Provide a client via RuntimeContext.')
        return self.ctx.client

    @property
    def agent_client(self) -> AgentClient:
        """Agent client from context.

        Returns:
            AgentClient instance for Ray operations.

        Raises:
            RuntimeError: If no agent_client in context.
        """
        if self.ctx.agent_client is None:
            raise RuntimeError('No agent_client in context. Provide an agent_client via RuntimeContext.')
        return self.ctx.agent_client

    def setup_steps(self, registry: StepRegistry[DeploymentContext]) -> None:
        """Register workflow steps for step-based execution.

        Override this method to register custom steps for deployment workflow.
        If steps are registered, step-based execution takes precedence.

        Args:
            registry: StepRegistry to register steps with.

        Example:
            >>> def setup_steps(self, registry: StepRegistry[DeploymentContext]) -> None:
            ...     registry.register(InitializeRayStep())
            ...     registry.register(DeployStep())
            ...     registry.register(RegisterStep())
        """
        pass  # Default: no steps, uses simple execute()

    def create_context(self) -> DeploymentContext:
        """Create deployment context for step-based workflow.

        Override to customize context creation or add additional state.

        Returns:
            DeploymentContext instance with params and runtime context.
        """
        params_dict = self.params.model_dump() if hasattr(self.params, 'model_dump') else dict(self.params)
        return DeploymentContext(
            runtime_ctx=self.ctx,
            params=params_dict,
            model_id=params_dict.get('model_id'),
            serve_app_name=self.get_serve_app_name(),
            route_prefix=self.get_route_prefix(),
            ray_actor_options=self.get_ray_actor_options(),
        )

    def run(self) -> Any:
        """Run the action, using steps if registered.

        This method is called by executors. It checks if steps are
        registered and uses step-based execution if so.

        Returns:
            Action result (dict or any return type).
        """
        # Check if steps are registered
        registry: StepRegistry[DeploymentContext] = StepRegistry()
        self.setup_steps(registry)

        if registry:
            # Step-based execution
            context = self.create_context()
            orchestrator: Orchestrator[DeploymentContext] = Orchestrator(
                registry=registry,
                context=context,
                progress_callback=lambda curr, total: self.set_progress(curr, total),
            )
            result = orchestrator.execute()

            # Add context data to result
            if context.serve_app_id:
                result['serve_application'] = context.serve_app_id
            result['deployed'] = context.deployed

            return result

        # Simple execute mode
        return self.execute()

    def get_serve_app_name(self) -> str:
        """Get the name for the Ray Serve application.

        Default uses plugin release code from SYNAPSE_PLUGIN_RELEASE_CODE env var.
        Override for custom naming.

        Returns:
            Serve application name.
        """
        return self.ctx.env.get_str('SYNAPSE_PLUGIN_RELEASE_CODE', 'synapse-serve-app') or 'synapse-serve-app'

    def get_route_prefix(self) -> str:
        """Get the route prefix for the deployment.

        Default uses plugin release checksum from SYNAPSE_PLUGIN_RELEASE_CHECKSUM env var.
        Override for custom routing.

        Returns:
            Route prefix string (e.g., '/abc123').
        """
        checksum = self.ctx.env.get_str('SYNAPSE_PLUGIN_RELEASE_CHECKSUM', 'default') or 'default'
        return f'/{checksum}'

    def get_ray_actor_options(self) -> dict[str, Any]:
        """Get Ray actor options for the deployment.

        Default extracts num_cpus and num_gpus from params.
        Override for custom resource allocation.

        Returns:
            Dict with Ray actor options (num_cpus, num_gpus, etc.).
        """
        options: dict[str, Any] = {
            'runtime_env': self.get_runtime_env(),
        }

        params_dict = self.params.model_dump() if hasattr(self.params, 'model_dump') else dict(self.params)

        for option in ['num_cpus', 'num_gpus', 'memory']:
            if value := params_dict.get(option):
                options[option] = value

        return options

    def get_runtime_env(self) -> dict[str, Any]:
        """Get Ray runtime environment.

        Override to customize the runtime environment for deployments.

        Returns:
            Dict with runtime environment configuration.
        """
        return {}

    def ray_init(self, **kwargs: Any) -> None:
        """Initialize Ray cluster connection.

        Call this before deploying to ensure Ray is connected.

        Args:
            **kwargs: Additional arguments for ray.init().
        """
        try:
            import ray
        except ImportError:
            raise ImportError("Ray is required for deployment actions. Install with: pip install 'synapse-sdk[ray]'")

        if not ray.is_initialized():
            ray.init(**kwargs)

    def deploy(self) -> None:
        """Deploy the inference endpoint to Ray Serve.

        Uses the entrypoint class and current configuration to create
        a Ray Serve deployment.

        Raises:
            RuntimeError: If entrypoint is not set.
            ImportError: If Ray Serve is not installed.
        """
        if self.entrypoint is None:
            raise RuntimeError(
                'entrypoint must be set to a serve deployment class. Example: entrypoint = MyServeDeployment'
            )

        try:
            from ray import serve
        except ImportError:
            raise ImportError(
                "Ray Serve is required for deployment actions. Install with: pip install 'synapse-sdk[ray]'"
            )

        # Get deployment configuration
        app_name = self.get_serve_app_name()
        route_prefix = self.get_route_prefix()
        ray_actor_options = self.get_ray_actor_options()

        # Delete existing deployment if present
        try:
            serve.delete(app_name)
        except Exception:
            pass  # Ignore if not exists

        # Get backend URL for the deployment
        backend_url = self.ctx.env.get_str('SYNAPSE_PLUGIN_RUN_HOST', '') or ''

        # Create and deploy
        # The entrypoint should be a class that implements BaseServeDeployment
        deployment = serve.deployment(ray_actor_options=ray_actor_options)(self.entrypoint).bind(backend_url)

        serve.run(
            deployment,
            name=app_name,
            route_prefix=route_prefix,
        )

    def register_serve_application(self) -> int | None:
        """Register the serve application with the backend.

        Creates a serve application record in the backend for tracking.

        Returns:
            Serve application ID if created, None otherwise.
        """
        job_id = self.ctx.job_id
        if not job_id:
            return None

        app_name = self.get_serve_app_name()

        # Get serve application status from Ray
        try:
            serve_app = self.agent_client.get_serve_application(app_name)
        except Exception:
            return None

        # Register with backend
        result = self.client.create_serve_application({
            'job': job_id,
            'status': serve_app.get('status'),
            'data': serve_app,
        })

        return result.get('id')
