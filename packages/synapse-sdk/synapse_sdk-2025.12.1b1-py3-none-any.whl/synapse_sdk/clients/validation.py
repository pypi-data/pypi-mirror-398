"""Shared validation mixin for HTTP clients.

This module provides a mixin class with Pydantic validation methods
that can be used by both sync and async HTTP clients.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pydantic import BaseModel


class ValidationMixin:
    """Mixin providing Pydantic validation methods for HTTP clients.

    This mixin provides shared validation functionality for both
    BaseClient and AsyncBaseClient, reducing code duplication.
    """

    def _validate_response(self, response: Any, model: type[BaseModel]) -> Any:
        """Validate response against a Pydantic model.

        Args:
            response: The response data to validate.
            model: The Pydantic model to validate against.

        Returns:
            The original response if validation passes.

        Raises:
            TypeError: If the model is not a Pydantic model.
            ValidationError: If the response doesn't match the model.
        """
        if not hasattr(model, 'model_validate'):
            raise TypeError(f'{model.__name__} is not a Pydantic model')
        model.model_validate(response)
        return response

    def _validate_request(self, data: dict, model: type[BaseModel]) -> dict:
        """Validate request data against a Pydantic model.

        Args:
            data: The request data to validate.
            model: The Pydantic model to validate against.

        Returns:
            A dictionary with validated data, excluding None values.

        Raises:
            TypeError: If the model is not a Pydantic model.
            ValidationError: If the data doesn't match the model.
        """
        if not hasattr(model, 'model_validate'):
            raise TypeError(f'{model.__name__} is not a Pydantic model')
        instance = model.model_validate(data)
        return {k: v for k, v in instance.model_dump().items() if v is not None}
