"""Plugin utilities for configuration parsing and action discovery."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, get_args, get_origin

from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from synapse_sdk.plugins.enums import RunMethod
from synapse_sdk.utils.file.requirements import read_requirements

if TYPE_CHECKING:
    from synapse_sdk.plugins.config import PluginConfig


def get_plugin_actions(config: dict | PluginConfig | Path | str) -> list[str]:
    """Extract action names from plugin configuration.

    Args:
        config: Plugin config dict, PluginConfig instance, or path to config.yaml

    Returns:
        List of action names. Returns empty list on error.
    """
    from synapse_sdk.plugins.config import PluginConfig

    if isinstance(config, (str, Path)):
        config = _load_config_from_path(config)
    if isinstance(config, PluginConfig):
        return list(config.actions.keys())
    if isinstance(config, dict):
        return list(config.get('actions', {}).keys())
    return []


def get_action_method(config: dict | PluginConfig, action: str) -> RunMethod:
    """Get the run method for an action from config.

    Args:
        config: Plugin config dict or PluginConfig instance
        action: Action name

    Returns:
        RunMethod enum value. Defaults to TASK if not found.
    """
    from synapse_sdk.plugins.config import PluginConfig

    if isinstance(config, PluginConfig):
        action_config = config.actions.get(action)
        if action_config:
            return action_config.method
    elif isinstance(config, dict):
        actions = config.get('actions', {})
        action_config = actions.get(action, {})
        method = action_config.get('method', 'task')
        return RunMethod(method)
    return RunMethod.TASK


def get_action_config(config: dict | PluginConfig, action: str) -> dict:
    """Get the full configuration for a specific action.

    Args:
        config: Plugin config dict or PluginConfig instance
        action: Action name

    Returns:
        Action configuration dictionary

    Raises:
        KeyError: If action not found
        ValueError: If config type is invalid
    """
    from synapse_sdk.plugins.config import PluginConfig

    if isinstance(config, PluginConfig):
        action_cfg = config.actions.get(action)
        if action_cfg:
            return action_cfg.model_dump()
        raise KeyError(f"Action '{action}' not found. Available: {list(config.actions.keys())}")
    elif isinstance(config, dict):
        actions = config.get('actions', {})
        if action in actions:
            return actions[action]
        raise KeyError(f"Action '{action}' not found. Available: {list(actions.keys())}")
    raise ValueError('Invalid config type')


def _load_config_from_path(path: Path | str) -> dict:
    """Load plugin config from YAML file.

    Args:
        path: Path to config.yaml or directory containing it

    Returns:
        Parsed config dictionary
    """
    import yaml

    path = Path(path)
    if path.is_dir():
        path = path / 'config.yaml'
    with path.open() as f:
        return yaml.safe_load(f)


# =============================================================================
# UI Schema Generation
# =============================================================================


def _type_to_formkit(annotation: type | None) -> str:
    """Convert Python type annotation to FormKit input type.

    Args:
        annotation: Python type annotation (int, float, str, bool, etc.)

    Returns:
        FormKit input type string
    """
    if annotation is None:
        return 'text'

    # Handle Optional types
    origin = get_origin(annotation)
    if origin is type(None):
        return 'text'

    # Unwrap Optional/Union types
    if origin is not None:
        args = get_args(annotation)
        # Filter out NoneType for Optional[X]
        non_none_args = [a for a in args if a is not type(None)]
        if non_none_args:
            annotation = non_none_args[0]

    # Map Python types to FormKit types
    type_map: dict[type, str] = {
        int: 'number',
        float: 'number',
        str: 'text',
        bool: 'checkbox',
        list: 'checkbox',  # Multi-select
    }

    return type_map.get(annotation, 'text')  # type: ignore[arg-type]


def _to_label(name: str) -> str:
    """Convert snake_case field name to Title Case label.

    Args:
        name: Field name in snake_case (e.g., "batch_size")

    Returns:
        Human-readable label (e.g., "Batch Size")

    Example:
        >>> _to_label("batch_size")
        "Batch Size"
        >>> _to_label("learning_rate")
        "Learning Rate"
    """
    return re.sub(r'_', ' ', name).title()


def _extract_constraints(field_info: FieldInfo) -> dict[str, Any]:
    """Extract validation constraints from Pydantic FieldInfo.

    Converts Pydantic constraints (ge, le, gt, lt) to FormKit validation rules.

    Args:
        field_info: Pydantic FieldInfo object

    Returns:
        Dict with min, max, step if applicable
    """
    constraints: dict[str, Any] = {}

    # Extract from metadata (Pydantic v2 style)
    for meta in field_info.metadata:
        meta_type = type(meta).__name__

        if meta_type == 'Ge':  # Greater than or equal
            constraints['min'] = meta.ge
        elif meta_type == 'Le':  # Less than or equal
            constraints['max'] = meta.le
        elif meta_type == 'Gt':  # Greater than (use as min)
            constraints['min'] = meta.gt
        elif meta_type == 'Lt':  # Less than (use as max)
            constraints['max'] = meta.lt
        elif meta_type == 'MultipleOf':  # Step value
            constraints['step'] = meta.multiple_of

    return constraints


def pydantic_to_ui_schema(model: type[BaseModel]) -> list[dict[str, Any]]:
    """Convert a Pydantic model to FormKit UI schema format.

    This generates a UI schema compatible with the legacy config.yaml format,
    suitable for rendering forms in the frontend.

    Args:
        model: Pydantic BaseModel class with field definitions

    Returns:
        List of FormKit schema items, one per field

    Example:
        >>> from pydantic import BaseModel, Field
        >>>
        >>> class TrainParams(BaseModel):
        ...     epochs: int = Field(default=50, ge=1, le=1000)
        ...     batch_size: int = Field(default=8, ge=1, le=512)
        ...     learning_rate: float = Field(default=0.001)
        ...
        >>> schema = pydantic_to_ui_schema(TrainParams)
        >>> schema[0]
        {
            '$formkit': 'number',
            'name': 'epochs',
            'label': 'Epochs',
            'value': 50,
            'placeholder': 50,
            'min': 1,
            'max': 1000,
            'number': True
        }

    Custom UI via json_schema_extra:
        >>> class Params(BaseModel):
        ...     model_size: str = Field(
        ...         default="medium",
        ...         json_schema_extra={
        ...             "formkit": "select",
        ...             "options": ["small", "medium", "large"],
        ...             "help": "Model size selection"
        ...         }
        ...     )
    """
    schema: list[dict[str, Any]] = []

    for name, field_info in model.model_fields.items():
        # Start with basic item structure
        item: dict[str, Any] = {
            '$formkit': _type_to_formkit(field_info.annotation),
            'name': name,
            'label': _to_label(name),
        }

        # Add default value (check for PydanticUndefined)
        if field_info.default is not PydanticUndefined and field_info.default is not None:
            item['value'] = field_info.default
            item['placeholder'] = field_info.default

        # Add description as help text
        if field_info.description:
            item['help'] = field_info.description

        # Check if field is required (no default)
        if field_info.is_required():
            item['required'] = True

        # Add validation constraints
        constraints = _extract_constraints(field_info)
        item.update(constraints)

        # Add number flag for numeric types
        if item['$formkit'] == 'number':
            item['number'] = True

        # Apply custom overrides from json_schema_extra
        if field_info.json_schema_extra:
            extra = field_info.json_schema_extra
            if callable(extra):
                # Handle callable json_schema_extra
                extra_dict: dict[str, Any] = {}
                extra(extra_dict)
                extra = extra_dict

            if isinstance(extra, dict):
                # Override formkit type if specified
                if 'formkit' in extra:
                    item['$formkit'] = extra['formkit']

                # Copy other properties
                for key in ('options', 'help', 'required', 'step', 'min', 'max'):
                    if key in extra:
                        item[key] = extra[key]

        schema.append(item)

    return schema


def get_action_ui_schema(
    model: type[BaseModel],
    action_name: str | None = None,
) -> dict[str, Any]:
    """Get UI schema for an action's parameters.

    Returns the schema in the format expected by the backend API.

    Args:
        model: Pydantic model class for action parameters
        action_name: Optional action name for the response

    Returns:
        Dict with action name and ui_schemas list

    Example:
        >>> schema = get_action_ui_schema(TrainParams, 'train')
        >>> schema
        {
            'action': 'train',
            'ui_schemas': [...]
        }
    """
    return {
        'action': action_name,
        'ui_schemas': pydantic_to_ui_schema(model),
    }


__all__ = [
    'get_plugin_actions',
    'get_action_method',
    'get_action_config',
    'read_requirements',
    # Schema utilities
    'pydantic_to_ui_schema',
    'get_action_ui_schema',
]
