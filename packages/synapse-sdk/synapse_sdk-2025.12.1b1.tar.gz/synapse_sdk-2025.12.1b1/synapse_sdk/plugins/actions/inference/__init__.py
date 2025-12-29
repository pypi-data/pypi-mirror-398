"""Inference action module with Ray Serve integration.

This module provides base classes for inference and deployment actions:

- **BaseInferenceAction**: For batch inference or REST API inference
- **BaseDeploymentAction**: For deploying models to Ray Serve
- **BaseServeDeployment**: Ray Serve deployment class for model serving
- **InferenceContext**: Step-based workflow context for inference
- **DeploymentContext**: Step-based workflow context for deployment

Example (Simple Inference):
    >>> from synapse_sdk.plugins.actions.inference import BaseInferenceAction
    >>>
    >>> class MyInferenceAction(BaseInferenceAction[MyParams]):
    ...     action_name = 'inference'
    ...     category = 'neural_net'
    ...     params_model = MyParams
    ...
    ...     def execute(self) -> dict:
    ...         model_info = self.load_model(self.params.model_id)
    ...         results = self.infer(model_info, self.params.inputs)
    ...         return {'results': results}

Example (Ray Serve Deployment):
    >>> from synapse_sdk.plugins.actions.inference import (
    ...     BaseDeploymentAction,
    ...     BaseServeDeployment,
    ... )
    >>>
    >>> class MyServeDeployment(BaseServeDeployment):
    ...     async def _get_model(self, model_info: dict) -> Any:
    ...         import torch
    ...         return torch.load(model_info['path'] / 'model.pt')
    ...
    ...     async def infer(self, inputs: list[dict]) -> list[dict]:
    ...         model = await self.get_model()
    ...         return [{'pred': model(inp)} for inp in inputs]
    >>>
    >>> class MyDeploymentAction(BaseDeploymentAction[MyParams]):
    ...     action_name = 'deployment'
    ...     category = 'neural_net'
    ...     params_model = MyParams
    ...     entrypoint = MyServeDeployment
    ...
    ...     def execute(self) -> dict:
    ...         self.ray_init()
    ...         self.deploy()
    ...         app_id = self.register_serve_application()
    ...         return {'serve_application': app_id}
"""

from __future__ import annotations

from synapse_sdk.plugins.actions.inference.action import (
    BaseInferenceAction,
    InferenceProgressCategories,
)
from synapse_sdk.plugins.actions.inference.context import (
    DeploymentContext,
    InferenceContext,
)
from synapse_sdk.plugins.actions.inference.deployment import (
    BaseDeploymentAction,
    DeploymentProgressCategories,
)
from synapse_sdk.plugins.actions.inference.serve import (
    BaseServeDeployment,
    create_serve_multiplexed_model_id,
)

__all__ = [
    # Actions
    'BaseInferenceAction',
    'BaseDeploymentAction',
    # Serve
    'BaseServeDeployment',
    'create_serve_multiplexed_model_id',
    # Contexts
    'InferenceContext',
    'DeploymentContext',
    # Progress Categories
    'InferenceProgressCategories',
    'DeploymentProgressCategories',
]
