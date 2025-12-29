"""Tests for synapse_sdk.clients.validation module."""

from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError as PydanticValidationError

from synapse_sdk.clients.validation import ValidationMixin

# -----------------------------------------------------------------------------
# Test Models
# -----------------------------------------------------------------------------


class SimpleModel(BaseModel):
    """Simple model for testing."""

    id: int
    name: str


class ModelWithOptional(BaseModel):
    """Model with optional fields."""

    id: int
    name: str
    description: str | None = None
    active: bool | None = None


class NestedModel(BaseModel):
    """Model with nested structure."""

    data: SimpleModel
    count: int


class NotAPydanticModel:
    """A class that is not a Pydantic model."""

    def __init__(self, value: str):
        self.value = value


# -----------------------------------------------------------------------------
# ValidationMixin Tests
# -----------------------------------------------------------------------------


class TestValidationMixin:
    """Tests for ValidationMixin class."""

    @pytest.fixture
    def mixin(self):
        """Create a ValidationMixin instance."""
        return ValidationMixin()

    # -------------------------------------------------------------------------
    # _validate_response Tests
    # -------------------------------------------------------------------------

    def test_validate_response_valid_dict(self, mixin):
        """Valid dict passes validation and returns original."""
        response = {'id': 1, 'name': 'Test'}
        result = mixin._validate_response(response, SimpleModel)
        assert result == response
        assert result is response  # Same object returned

    def test_validate_response_returns_original(self, mixin):
        """Returns original response, not model instance."""
        response = {'id': 1, 'name': 'Test', 'extra_field': 'ignored'}
        result = mixin._validate_response(response, SimpleModel)
        # Result should be the original dict, not a model
        assert isinstance(result, dict)
        assert result == response

    def test_validate_response_invalid_missing_field(self, mixin):
        """Missing required field raises PydanticValidationError."""
        response = {'id': 1}  # Missing 'name'
        with pytest.raises(PydanticValidationError):
            mixin._validate_response(response, SimpleModel)

    def test_validate_response_invalid_wrong_type(self, mixin):
        """Wrong type raises PydanticValidationError."""
        response = {'id': 'not_an_int', 'name': 'Test'}
        with pytest.raises(PydanticValidationError):
            mixin._validate_response(response, SimpleModel)

    def test_validate_response_non_pydantic_model(self, mixin):
        """Non-Pydantic model raises TypeError."""
        response = {'id': 1, 'name': 'Test'}
        with pytest.raises(TypeError) as exc_info:
            mixin._validate_response(response, NotAPydanticModel)
        assert 'NotAPydanticModel' in str(exc_info.value)
        assert 'not a Pydantic model' in str(exc_info.value)

    def test_validate_response_nested_model(self, mixin):
        """Validates nested model structures."""
        response = {'data': {'id': 1, 'name': 'Test'}, 'count': 5}
        result = mixin._validate_response(response, NestedModel)
        assert result == response

    def test_validate_response_nested_model_invalid(self, mixin):
        """Invalid nested structure raises PydanticValidationError."""
        response = {'data': {'id': 1}, 'count': 5}  # Missing 'name' in nested
        with pytest.raises(PydanticValidationError):
            mixin._validate_response(response, NestedModel)

    # -------------------------------------------------------------------------
    # _validate_request Tests
    # -------------------------------------------------------------------------

    def test_validate_request_valid_data(self, mixin):
        """Valid data passes validation and returns dict."""
        data = {'id': 1, 'name': 'Test'}
        result = mixin._validate_request(data, SimpleModel)
        assert result == {'id': 1, 'name': 'Test'}

    def test_validate_request_filters_none_values(self, mixin):
        """None values are filtered from result."""
        data = {'id': 1, 'name': 'Test', 'description': None, 'active': None}
        result = mixin._validate_request(data, ModelWithOptional)
        assert result == {'id': 1, 'name': 'Test'}
        assert 'description' not in result
        assert 'active' not in result

    def test_validate_request_keeps_non_none_values(self, mixin):
        """Non-None values are preserved."""
        data = {'id': 1, 'name': 'Test', 'description': 'A description', 'active': True}
        result = mixin._validate_request(data, ModelWithOptional)
        assert result == {
            'id': 1,
            'name': 'Test',
            'description': 'A description',
            'active': True,
        }

    def test_validate_request_invalid_missing_field(self, mixin):
        """Missing required field raises PydanticValidationError."""
        data = {'id': 1}  # Missing 'name'
        with pytest.raises(PydanticValidationError):
            mixin._validate_request(data, SimpleModel)

    def test_validate_request_invalid_wrong_type(self, mixin):
        """Wrong type raises PydanticValidationError."""
        data = {'id': 'not_an_int', 'name': 'Test'}
        with pytest.raises(PydanticValidationError):
            mixin._validate_request(data, SimpleModel)

    def test_validate_request_non_pydantic_model(self, mixin):
        """Non-Pydantic model raises TypeError."""
        data = {'id': 1, 'name': 'Test'}
        with pytest.raises(TypeError) as exc_info:
            mixin._validate_request(data, NotAPydanticModel)
        assert 'NotAPydanticModel' in str(exc_info.value)
        assert 'not a Pydantic model' in str(exc_info.value)

    def test_validate_request_empty_dict(self, mixin):
        """Empty dict fails for required fields."""
        data = {}
        with pytest.raises(PydanticValidationError):
            mixin._validate_request(data, SimpleModel)

    def test_validate_request_extra_fields_ignored(self, mixin):
        """Extra fields are passed through model but excluded if None after dump."""
        data = {'id': 1, 'name': 'Test', 'unknown_field': 'ignored'}
        result = mixin._validate_request(data, SimpleModel)
        # Extra fields should be ignored by Pydantic
        assert result == {'id': 1, 'name': 'Test'}

    def test_validate_request_false_value_preserved(self, mixin):
        """False boolean values are preserved (not filtered as None)."""
        data = {'id': 1, 'name': 'Test', 'active': False}
        result = mixin._validate_request(data, ModelWithOptional)
        assert result['active'] is False

    def test_validate_request_zero_value_preserved(self, mixin):
        """Zero values are preserved (not filtered as None)."""

        class ModelWithZeroable(BaseModel):
            id: int
            count: int | None = None

        data = {'id': 1, 'count': 0}
        result = mixin._validate_request(data, ModelWithZeroable)
        assert result['count'] == 0

    def test_validate_request_empty_string_preserved(self, mixin):
        """Empty string values are preserved (not filtered as None)."""

        class ModelWithEmptyString(BaseModel):
            id: int
            name: str | None = None

        data = {'id': 1, 'name': ''}
        result = mixin._validate_request(data, ModelWithEmptyString)
        assert result['name'] == ''
