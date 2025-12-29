"""Base Ray Serve deployment class for inference endpoints."""

from __future__ import annotations

import tempfile
from abc import ABC, abstractmethod
from typing import Any


class BaseServeDeployment(ABC):
    """Base class for Ray Serve inference deployments.

    Provides model loading with multiplexing support. Subclasses implement
    _get_model() to load their specific model format and infer() to run
    inference.

    This class is designed to be used with Ray Serve's @serve.deployment
    decorator and supports model multiplexing via @serve.multiplexed().

    Attributes:
        backend_url: URL of the Synapse backend for model fetching.
        _model_cache: Internal cache for loaded models.

    Example:
        >>> from ray import serve
        >>> from fastapi import FastAPI
        >>>
        >>> app = FastAPI()
        >>>
        >>> @serve.deployment
        >>> @serve.ingress(app)
        >>> class MyInference(BaseServeDeployment):
        ...     async def _get_model(self, model_info: dict) -> Any:
        ...         import torch
        ...         return torch.load(model_info['path'] / 'model.pt')
        ...
        ...     async def infer(self, inputs: list[dict]) -> list[dict]:
        ...         model = await self.get_model()
        ...         return [{'prediction': model(inp)} for inp in inputs]
        >>>
        >>> # Deploy with:
        >>> deployment = MyInference.bind(backend_url='https://api.example.com')
        >>> serve.run(deployment)
    """

    def __init__(self, backend_url: str) -> None:
        """Initialize the serve deployment.

        Args:
            backend_url: URL of the Synapse backend for fetching models.
        """
        self.backend_url = backend_url
        self._model_cache: dict[str, Any] = {}

    async def _load_model_from_token(self, model_token: str) -> Any:
        """Load model from an encoded token.

        Decodes the JWT token containing model info, fetches model from
        backend, downloads and extracts artifacts, then calls _get_model().

        Args:
            model_token: JWT-encoded token with model info.

        Returns:
            Loaded model object (format depends on _get_model implementation).

        Raises:
            ImportError: If jwt or required dependencies not installed.
        """
        try:
            import jwt
        except ImportError:
            raise ImportError('PyJWT is required for model token decoding. Install with: pip install PyJWT')

        # Decode token to get model info
        model_info = jwt.decode(model_token, self.backend_url, algorithms=['HS256'])

        # Create backend client with user credentials
        from synapse_sdk.clients.backend import BackendClient

        client = BackendClient(
            base_url=self.backend_url,
            access_token=model_info['token'],
            tenant=model_info.get('tenant'),
        )

        # Fetch model metadata
        model = client.get_model(int(model_info['model']))

        if not model.get('file'):
            raise ValueError(f'Model {model_info["model"]} has no file URL')

        # Download and extract model
        with tempfile.TemporaryDirectory() as temp_path:
            from pathlib import Path

            from synapse_sdk.utils.file.archive import extract_archive
            from synapse_sdk.utils.file.download import download_file

            archive_path = Path(temp_path) / 'model.zip'
            download_file(model['file'], archive_path)
            extract_archive(archive_path, temp_path)

            model['path'] = Path(temp_path)
            return await self._get_model(model)

    async def get_model(self) -> Any:
        """Get the current model for inference.

        Uses Ray Serve's multiplexing to load the appropriate model
        based on the request's multiplexed model ID header.

        Returns:
            Loaded model object.

        Note:
            This method uses Ray Serve's @serve.multiplexed() decorator
            internally. Ensure requests include the appropriate header.
        """
        # Import here to avoid issues when Ray is not installed
        try:
            from ray import serve
        except ImportError:
            raise ImportError("Ray Serve is required. Install with: pip install 'synapse-sdk[ray]'")

        model_id = serve.get_multiplexed_model_id()
        return await self._load_model_multiplexed(model_id)

    async def _load_model_multiplexed(self, model_id: str) -> Any:
        """Load model with multiplexing support.

        This method is decorated with @serve.multiplexed() to enable
        model multiplexing in Ray Serve deployments.

        Args:
            model_id: The model token/ID from request header.

        Returns:
            Loaded model object.
        """
        # Check cache first
        if model_id in self._model_cache:
            return self._model_cache[model_id]

        # Load and cache
        model = await self._load_model_from_token(model_id)
        self._model_cache[model_id] = model
        return model

    @abstractmethod
    async def _get_model(self, model_info: dict[str, Any]) -> Any:
        """Load model from extracted artifacts.

        Override this method to implement your specific model loading logic.
        Called after model artifacts are downloaded and extracted.

        Args:
            model_info: Model metadata dict with 'path' key for local artifacts.
                       The path is a Path object pointing to extracted directory.

        Returns:
            Loaded model object (framework-specific).

        Example (PyTorch):
            >>> async def _get_model(self, model_info: dict) -> Any:
            ...     import torch
            ...     model_path = model_info['path'] / 'model.pt'
            ...     return torch.load(model_path)

        Example (ONNX):
            >>> async def _get_model(self, model_info: dict) -> Any:
            ...     import onnxruntime as ort
            ...     model_path = model_info['path'] / 'model.onnx'
            ...     return ort.InferenceSession(str(model_path))
        """
        raise NotImplementedError(
            'Override _get_model() to load your model format. '
            'Example: return torch.load(model_info["path"] / "model.pt")'
        )

    @abstractmethod
    async def infer(self, *args: Any, **kwargs: Any) -> Any:
        """Run inference on inputs.

        Override this method to implement your inference logic.
        Use self.get_model() to obtain the loaded model.

        Args:
            *args: Inference inputs (format depends on implementation).
            **kwargs: Additional inference parameters.

        Returns:
            Inference results (format depends on implementation).

        Example:
            >>> async def infer(self, inputs: list[dict]) -> list[dict]:
            ...     model = await self.get_model()
            ...     results = []
            ...     for inp in inputs:
            ...         prediction = model.predict(inp['data'])
            ...         results.append({'prediction': prediction.tolist()})
            ...     return results
        """
        raise NotImplementedError(
            'Override infer() to implement inference logic. Example: return model.predict(inputs)'
        )


def create_serve_multiplexed_model_id(
    model_id: int | str,
    token: str,
    backend_url: str,
    tenant: str | None = None,
) -> str:
    """Create a JWT-encoded model ID for serve multiplexing.

    This helper creates the token that should be passed in the
    'serve_multiplexed_model_id' header for inference requests.

    Args:
        model_id: The model ID to encode.
        token: User access token for authentication.
        backend_url: Backend URL (used as JWT secret).
        tenant: Optional tenant identifier.

    Returns:
        JWT-encoded model token string.

    Example:
        >>> model_token = create_serve_multiplexed_model_id(
        ...     model_id=123,
        ...     token='user_access_token',
        ...     backend_url='https://api.example.com',
        ...     tenant='my-tenant',
        ... )
        >>> # Use in request headers:
        >>> headers = {'serve_multiplexed_model_id': model_token}
    """
    try:
        import jwt
    except ImportError:
        raise ImportError('PyJWT is required for model token encoding. Install with: pip install PyJWT')

    payload: dict[str, Any] = {
        'model': str(model_id),
        'token': token,
    }

    if tenant:
        payload['tenant'] = tenant

    return jwt.encode(payload, backend_url, algorithm='HS256')
