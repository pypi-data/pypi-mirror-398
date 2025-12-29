"""Inference context for step-based workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from synapse_sdk.plugins.pipelines.steps import BaseStepContext


@dataclass
class InferenceContext(BaseStepContext):
    """Context for inference action step-based workflows.

    Extends BaseStepContext with inference-specific state including
    model information, request/response tracking, and batch processing.

    Attributes:
        params: Action parameters dict.
        model_id: ID of the model being used for inference.
        model: Loaded model information from backend.
        model_path: Local path to downloaded/extracted model.
        requests: Input requests to process.
        results: Inference results.
        batch_size: Batch size for processing.
        processed_count: Number of processed items.

    Example:
        >>> context = InferenceContext(
        ...     runtime_ctx=self.ctx,
        ...     params={'model_id': 123},
        ...     model_id=123,
        ... )
        >>> context.results.append({'prediction': 0.95})
    """

    params: dict[str, Any] = field(default_factory=dict)
    model_id: int | None = None
    model: dict[str, Any] | None = None
    model_path: str | None = None
    requests: list[dict[str, Any]] = field(default_factory=list)
    results: list[dict[str, Any]] = field(default_factory=list)
    batch_size: int = 1
    processed_count: int = 0


@dataclass
class DeploymentContext(BaseStepContext):
    """Context for deployment action step-based workflows.

    Extends BaseStepContext with deployment-specific state including
    model information, serve application configuration, and deployment status.

    Attributes:
        params: Action parameters dict.
        model_id: ID of the model to deploy.
        model: Model information from backend.
        model_path: Local path to model artifacts.
        serve_app_name: Name of the Ray Serve application.
        serve_app_id: ID of the created serve application.
        route_prefix: URL route prefix for the deployment.
        ray_actor_options: Ray actor configuration options.
        deployed: Whether deployment succeeded.

    Example:
        >>> context = DeploymentContext(
        ...     runtime_ctx=self.ctx,
        ...     params={'model_id': 123},
        ...     serve_app_name='my-model-v1',
        ... )
    """

    params: dict[str, Any] = field(default_factory=dict)
    model_id: int | None = None
    model: dict[str, Any] | None = None
    model_path: str | None = None
    serve_app_name: str | None = None
    serve_app_id: int | None = None
    route_prefix: str | None = None
    ray_actor_options: dict[str, Any] = field(default_factory=dict)
    deployed: bool = False
