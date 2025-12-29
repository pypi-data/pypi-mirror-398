"""Plugin discovery and introspection."""

from __future__ import annotations

import importlib
import inspect
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Any, Callable

from pydantic import BaseModel

from synapse_sdk.plugins.config import ActionConfig, PluginConfig
from synapse_sdk.plugins.enums import PluginCategory, RunMethod
from synapse_sdk.plugins.errors import ActionNotFoundError
from synapse_sdk.plugins.utils import pydantic_to_ui_schema

if TYPE_CHECKING:
    from synapse_sdk.plugins.action import BaseAction


class PluginDiscovery:
    """Plugin discovery and introspection.

    Provides methods to discover actions from configuration files or Python modules.
    Supports both class-based (BaseAction subclasses) and function-based (@action decorator)
    action definitions.

    Example from config:
        >>> discovery = PluginDiscovery.from_path('/path/to/plugin')
        >>> discovery.list_actions()
        ['train', 'inference', 'export']
        >>> action_cls = discovery.get_action_class('train')

    Example from module:
        >>> import my_plugin
        >>> discovery = PluginDiscovery.from_module(my_plugin)
        >>> discovery.list_actions()
        ['train', 'export']
    """

    def __init__(self, config: PluginConfig) -> None:
        """Initialize discovery with a plugin configuration.

        Args:
            config: Validated PluginConfig instance
        """
        self.config = config
        self._action_cache: dict[str, type[BaseAction] | Callable] = {}

    @classmethod
    def from_path(cls, path: Path | str) -> PluginDiscovery:
        """Load plugin from config.yaml path.

        Args:
            path: Path to config.yaml file or directory containing it

        Returns:
            PluginDiscovery instance

        Raises:
            FileNotFoundError: If config.yaml doesn't exist
            ValueError: If config.yaml is invalid
        """
        import yaml

        path = Path(path)
        if path.is_dir():
            path = path / 'config.yaml'

        if not path.exists():
            raise FileNotFoundError(f'Config file not found: {path}')

        with path.open() as f:
            data = yaml.safe_load(f)

        # Convert actions dict to ActionConfig objects if needed
        if 'actions' in data and isinstance(data['actions'], dict):
            actions = {}
            for action_name, action_data in data['actions'].items():
                if isinstance(action_data, dict):
                    action_data.setdefault('name', action_name)
                    actions[action_name] = ActionConfig(**action_data)
                elif isinstance(action_data, ActionConfig):
                    actions[action_name] = action_data
            data['actions'] = actions

        config = PluginConfig(**data)
        return cls(config)

    @classmethod
    def from_module(
        cls,
        module: ModuleType,
        *,
        name: str | None = None,
        category: PluginCategory = PluginCategory.CUSTOM,
    ) -> PluginDiscovery:
        """Discover plugin from Python module by introspection.

        Scans module for:
        - Functions decorated with @action
        - Classes that subclass BaseAction

        Args:
            module: Python module to introspect
            name: Plugin name (defaults to module name)
            category: Plugin category

        Returns:
            PluginDiscovery instance with discovered actions
        """
        from synapse_sdk.plugins.action import BaseAction

        actions: dict[str, ActionConfig] = {}

        for attr_name in dir(module):
            if attr_name.startswith('_'):
                continue

            obj = getattr(module, attr_name)

            # Check for @action decorated functions
            if callable(obj) and hasattr(obj, '_is_action') and obj._is_action:
                action_name = getattr(obj, '_action_name', attr_name)
                actions[action_name] = ActionConfig(
                    name=action_name,
                    description=getattr(obj, '_action_description', ''),
                    entrypoint=f'{module.__name__}:{attr_name}',
                    method=RunMethod.TASK,
                    params_schema=getattr(obj, '_action_params', None),
                )

            # Check for BaseAction subclasses
            elif (
                inspect.isclass(obj)
                and issubclass(obj, BaseAction)
                and obj is not BaseAction
                and hasattr(obj, 'action_name')
            ):
                action_name = obj.action_name
                actions[action_name] = ActionConfig(
                    name=action_name,
                    description=getattr(obj, 'description', ''),
                    entrypoint=f'{module.__name__}:{attr_name}',
                    method=getattr(obj, 'method', RunMethod.TASK),
                    params_schema=getattr(obj, 'params_model', None),
                )

        module_name = name or getattr(module, '__name__', 'unknown')
        config = PluginConfig(
            name=module_name,
            code=module_name.replace('.', '-'),
            category=category,
            actions=actions,
        )
        return cls(config)

    def list_actions(self) -> list[str]:
        """Get available action names.

        Returns:
            List of action names
        """
        return list(self.config.actions.keys())

    def get_action_config(self, name: str) -> ActionConfig:
        """Get configuration for a specific action.

        Args:
            name: Action name

        Returns:
            ActionConfig instance

        Raises:
            ActionNotFoundError: If action doesn't exist
        """
        if name not in self.config.actions:
            raise ActionNotFoundError(
                f"Action '{name}' not found",
                details={'available': self.list_actions()},
            )
        return self.config.actions[name]

    def get_action_method(self, name: str) -> RunMethod:
        """Get execution method for an action.

        Args:
            name: Action name

        Returns:
            RunMethod enum value
        """
        return self.get_action_config(name).method

    def get_action_class(self, name: str) -> type[BaseAction] | Callable:
        """Load action class/function from entrypoint.

        Injects action_name and category from config if not defined on the class.
        This allows plugin developers to write minimal action classes without
        redundant metadata when using config.yaml-based discovery.

        Args:
            name: Action name

        Returns:
            Action class (BaseAction subclass) or decorated function

        Raises:
            ActionNotFoundError: If action doesn't exist or has no entrypoint
        """
        if name in self._action_cache:
            return self._action_cache[name]

        action_config = self.get_action_config(name)
        entrypoint = action_config.entrypoint

        if not entrypoint:
            raise ActionNotFoundError(
                f"Action '{name}' has no entrypoint defined",
                details={'action': name},
            )

        action_cls = _load_entrypoint(entrypoint)

        # Inject action_name from config key if not defined on class
        if not getattr(action_cls, 'action_name', None):
            action_cls.action_name = name

        # Inject category from plugin config if not defined on class
        if not getattr(action_cls, 'category', None):
            action_cls.category = str(self.config.category)

        self._action_cache[name] = action_cls
        return action_cls

    def has_action(self, name: str) -> bool:
        """Check if an action exists.

        Args:
            name: Action name

        Returns:
            True if action exists, False otherwise
        """
        return name in self.config.actions

    def get_action_entrypoint(self, name: str) -> str:
        """Get action entrypoint string without loading the class.

        Useful for remote execution where the class shouldn't be imported locally.

        Args:
            name: Action name

        Returns:
            Entrypoint string (e.g., 'plugin.train.TrainAction')

        Raises:
            ActionNotFoundError: If action doesn't exist or has no entrypoint
        """
        action_config = self.get_action_config(name)
        entrypoint = action_config.entrypoint

        if not entrypoint:
            raise ActionNotFoundError(
                f"Action '{name}' has no entrypoint defined",
                details={'action': name},
            )

        # Normalize entrypoint format: 'module:Class' -> 'module.Class'
        if ':' in entrypoint:
            module_path, class_name = entrypoint.rsplit(':', 1)
            return f'{module_path}.{class_name}'
        return entrypoint

    def get_action_params_model(self, name: str) -> type[BaseModel] | None:
        """Get the params model for an action.

        Args:
            name: Action name

        Returns:
            Pydantic model class for parameters, or None if not defined
        """
        action_config = self.get_action_config(name)

        # First check if params_schema is set on ActionConfig
        if action_config.params_schema:
            return action_config.params_schema

        # Otherwise try to load from action class
        try:
            action_cls = self.get_action_class(name)
            return getattr(action_cls, 'params_model', None)
        except Exception:
            return None

    def get_action_ui_schema(self, name: str) -> list[dict[str, Any]]:
        """Get UI schema for an action's parameters.

        Auto-generates FormKit-compatible UI schema from the action's params_model.

        Args:
            name: Action name

        Returns:
            List of FormKit schema items, or empty list if no params_model

        Example:
            >>> discovery = PluginDiscovery.from_path('/path/to/plugin')
            >>> schema = discovery.get_action_ui_schema('train')
            >>> schema
            [{'$formkit': 'number', 'name': 'epochs', 'label': 'Epochs', ...}]
        """
        params_model = self.get_action_params_model(name)
        if params_model is None:
            return []
        return pydantic_to_ui_schema(params_model)

    def get_action_result_model(self, name: str) -> type[BaseModel] | None:
        """Get the result model for an action.

        Returns the Pydantic model class used for output validation.
        Returns None if no result model is defined (NoResult sentinel).

        Args:
            name: Action name

        Returns:
            Pydantic model class for result validation, or None if not defined

        Example:
            >>> discovery = PluginDiscovery.from_path('/path/to/plugin')
            >>> result_model = discovery.get_action_result_model('train')
            >>> if result_model:
            ...     print(result_model.model_json_schema())
        """
        from synapse_sdk.plugins.action import NoResult

        try:
            action_cls = self.get_action_class(name)
            result_model = getattr(action_cls, 'result_model', NoResult)
            if result_model is NoResult:
                return None
            return result_model
        except Exception:
            return None

    def get_action_result_ui_schema(self, name: str) -> list[dict[str, Any]]:
        """Get UI schema for an action's result type.

        Auto-generates FormKit-compatible UI schema from the action's result_model.
        Useful for displaying expected output format in UIs.

        Args:
            name: Action name

        Returns:
            List of FormKit schema items, or empty list if no result_model

        Example:
            >>> discovery = PluginDiscovery.from_path('/path/to/plugin')
            >>> schema = discovery.get_action_result_ui_schema('train')
            >>> schema
            [{'$formkit': 'text', 'name': 'weights_path', 'label': 'Weights Path', ...}]
        """
        result_model = self.get_action_result_model(name)
        if result_model is None:
            return []
        return pydantic_to_ui_schema(result_model)

    def get_action_input_type(self, name: str) -> str | None:
        """Get the semantic input type for an action.

        Extracts the input_type from the action class's DataType declaration.

        Args:
            name: Action name

        Returns:
            Input type name string, or None if not defined

        Example:
            >>> discovery = PluginDiscovery.from_path('/path/to/plugin')
            >>> discovery.get_action_input_type('train')
            'yolo_dataset'
        """
        try:
            action_cls = self.get_action_class(name)
            input_type = getattr(action_cls, 'input_type', None)
            if input_type is not None and hasattr(input_type, 'name'):
                return input_type.name
            return None
        except Exception:
            return None

    def get_action_output_type(self, name: str) -> str | None:
        """Get the semantic output type for an action.

        Extracts the output_type from the action class's DataType declaration.

        Args:
            name: Action name

        Returns:
            Output type name string, or None if not defined

        Example:
            >>> discovery = PluginDiscovery.from_path('/path/to/plugin')
            >>> discovery.get_action_output_type('train')
            'model_weights'
        """
        try:
            action_cls = self.get_action_class(name)
            output_type = getattr(action_cls, 'output_type', None)
            if output_type is not None and hasattr(output_type, 'name'):
                return output_type.name
            return None
        except Exception:
            return None

    def to_config_dict(self, *, include_ui_schemas: bool = True) -> dict[str, Any]:
        """Export plugin configuration as a dictionary.

        Generates a config dict compatible with the backend API format,
        with optional auto-generation of UI schemas from params_model.

        Args:
            include_ui_schemas: If True, auto-generate train_ui_schemas
                from each action's params_model

        Returns:
            Config dictionary ready for serialization or API submission

        Example:
            >>> discovery = PluginDiscovery.from_module(my_plugin)
            >>> config = discovery.to_config_dict()
            >>> # config['actions']['train']['hyperparameters']['train_ui_schemas']
            >>> # is auto-populated from TrainParams model
        """
        config_dict: dict[str, Any] = {
            'name': self.config.name,
            'code': self.config.code,
            'version': self.config.version,
            'category': str(self.config.category.value),
            'description': self.config.description,
            'readme': self.config.readme,
        }

        # Add optional fields
        if self.config.data_type:
            config_dict['data_type'] = str(self.config.data_type.value)
        if self.config.tasks:
            config_dict['tasks'] = self.config.tasks

        # Build actions dict
        actions_dict: dict[str, Any] = {}
        for action_name, action_config in self.config.actions.items():
            action_dict: dict[str, Any] = {
                'entrypoint': action_config.entrypoint,
                'method': str(action_config.method.value),
            }

            if action_config.description:
                action_dict['description'] = action_config.description

            # Add semantic types (extracted from action class)
            input_type = self.get_action_input_type(action_name)
            output_type = self.get_action_output_type(action_name)
            if input_type:
                action_dict['input_type'] = input_type
            if output_type:
                action_dict['output_type'] = output_type

            # Auto-generate UI schemas from params_model
            if include_ui_schemas:
                ui_schema = self.get_action_ui_schema(action_name)
                if ui_schema:
                    action_dict['hyperparameters'] = {
                        'train_ui_schemas': ui_schema,
                    }

                # Add result schema if defined
                result_schema = self.get_action_result_ui_schema(action_name)
                if result_schema:
                    action_dict['result_schema'] = result_schema

            actions_dict[action_name] = action_dict

        config_dict['actions'] = actions_dict
        return config_dict

    def to_yaml(self, *, include_ui_schemas: bool = True) -> str:
        """Export plugin configuration as YAML string.

        Args:
            include_ui_schemas: If True, auto-generate train_ui_schemas

        Returns:
            YAML-formatted configuration string
        """
        import yaml

        config_dict = self.to_config_dict(include_ui_schemas=include_ui_schemas)
        return yaml.dump(config_dict, default_flow_style=False, allow_unicode=True, sort_keys=False)

    def sync_config_file(self, config_path: Path | str) -> dict[str, str]:
        """Sync actions and types from code to config.yaml.

        Discovers actions from plugin source files and updates config.yaml:
        - Adds new actions found in code but not in config
        - Updates entrypoints if they changed
        - Updates input_type/output_type from code

        This should be called during plugin publish to ensure config.yaml
        reflects the code-defined actions and types.

        Args:
            config_path: Path to config.yaml file

        Returns:
            Dict of action_name -> changes made (for logging)

        Example:
            >>> discovery = PluginDiscovery.from_path('/path/to/plugin')
            >>> changes = discovery.sync_config_file('/path/to/plugin/config.yaml')
            >>> print(changes)
            {'train': 'added (entrypoint=plugin.train.TrainAction, input_type=yolo_dataset)'}
        """
        import yaml

        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f'Config file not found: {config_path}')

        plugin_dir = config_path.parent

        # Read existing config
        with config_path.open() as f:
            config_data = yaml.safe_load(f)

        if config_data is None:
            config_data = {}

        changes: dict[str, str] = {}

        # Ensure actions dict exists
        if 'actions' not in config_data:
            config_data['actions'] = {}

        # Discover actions from source files
        discovered = self.discover_actions(plugin_dir)

        # Process discovered actions
        for action_name, action_info in discovered.items():
            entrypoint = action_info['entrypoint']
            input_type = action_info['input_type']
            output_type = action_info['output_type']

            if action_name not in config_data['actions']:
                # New action - add it
                action_data: dict[str, Any] = {'entrypoint': entrypoint}
                if input_type:
                    action_data['input_type'] = input_type
                if output_type:
                    action_data['output_type'] = output_type

                config_data['actions'][action_name] = action_data

                parts = [f'entrypoint={entrypoint}']
                if input_type:
                    parts.append(f'input_type={input_type}')
                if output_type:
                    parts.append(f'output_type={output_type}')
                changes[action_name] = f'added ({", ".join(parts)})'
            else:
                # Existing action - update fields if changed
                action_data = config_data['actions'][action_name]
                if not isinstance(action_data, dict):
                    action_data = {'entrypoint': action_data}
                    config_data['actions'][action_name] = action_data

                updates = []

                # Update entrypoint if changed
                if action_data.get('entrypoint') != entrypoint:
                    action_data['entrypoint'] = entrypoint
                    updates.append(f'entrypoint={entrypoint}')

                # Update types if changed
                if input_type and action_data.get('input_type') != input_type:
                    action_data['input_type'] = input_type
                    updates.append(f'input_type={input_type}')
                if output_type and action_data.get('output_type') != output_type:
                    action_data['output_type'] = output_type
                    updates.append(f'output_type={output_type}')

                if updates:
                    changes[action_name] = ', '.join(updates)

        # Write back to file
        with config_path.open('w') as f:
            yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        return changes

    @staticmethod
    def discover_actions(plugin_dir: Path | str) -> dict[str, dict[str, Any]]:
        """Discover BaseAction subclasses from plugin source files.

        Scans Python files in the plugin directory for classes that inherit
        from BaseAction and extracts their metadata.

        Args:
            plugin_dir: Path to the plugin directory

        Returns:
            Dict mapping action_name -> {entrypoint, input_type, output_type}

        Example:
            >>> actions = PluginDiscovery.discover_actions('/path/to/plugin')
            >>> actions
            {'train': {'entrypoint': 'plugin.train.TrainAction', 'input_type': 'yolo_dataset', ...}}
        """
        import ast
        import sys

        from synapse_sdk.plugins.action import BaseAction

        plugin_dir = Path(plugin_dir)
        if not plugin_dir.is_dir():
            raise ValueError(f'Plugin directory not found: {plugin_dir}')

        discovered: dict[str, dict[str, Any]] = {}

        # Add plugin directory to sys.path for imports
        plugin_dir_str = str(plugin_dir)
        path_added = False
        if plugin_dir_str not in sys.path:
            sys.path.insert(0, plugin_dir_str)
            path_added = True

        try:
            # Find all Python files (excluding __pycache__, tests, etc.)
            py_files = list(plugin_dir.rglob('*.py'))
            py_files = [
                f
                for f in py_files
                if '__pycache__' not in str(f) and not f.name.startswith('test_') and f.name != 'conftest.py'
            ]

            for py_file in py_files:
                # Get module path relative to plugin directory
                rel_path = py_file.relative_to(plugin_dir)
                module_parts = list(rel_path.with_suffix('').parts)

                # Skip __init__.py files for module path
                if module_parts[-1] == '__init__':
                    module_parts = module_parts[:-1]
                    if not module_parts:
                        continue

                module_name = '.'.join(module_parts)

                # First, use AST to find potential BaseAction subclasses
                # This avoids importing modules that would fail
                try:
                    with py_file.open() as f:
                        tree = ast.parse(f.read(), filename=str(py_file))
                except SyntaxError:
                    continue

                # Look for class definitions that might be actions
                potential_classes = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # Check if it has BaseAction or similar in bases
                        for base in node.bases:
                            base_name = ''
                            if isinstance(base, ast.Name):
                                base_name = base.id
                            elif isinstance(base, ast.Attribute):
                                base_name = base.attr
                            elif isinstance(base, ast.Subscript):
                                # Handle Generic[T] style: BaseAction[Params]
                                if isinstance(base.value, ast.Name):
                                    base_name = base.value.id
                                elif isinstance(base.value, ast.Attribute):
                                    base_name = base.value.attr

                            if 'Action' in base_name or 'Base' in base_name:
                                potential_classes.append(node.name)
                                break

                if not potential_classes:
                    continue

                # Now import the module and check actual inheritance
                try:
                    module = importlib.import_module(module_name)
                except Exception:
                    continue

                for class_name in potential_classes:
                    try:
                        cls = getattr(module, class_name, None)
                        if cls is None:
                            continue

                        # Check if it's a proper BaseAction subclass
                        if not (
                            inspect.isclass(cls)
                            and issubclass(cls, BaseAction)
                            and cls is not BaseAction
                            and not inspect.isabstract(cls)
                        ):
                            continue

                        # Extract action name
                        # Priority: action_name attr > derived from class name
                        action_name = getattr(cls, 'action_name', None)
                        if not action_name:
                            # Derive from class name: TrainAction -> train
                            action_name = class_name
                            if action_name.endswith('Action'):
                                action_name = action_name[:-6]
                            action_name = action_name.lower()

                        # Build entrypoint
                        entrypoint = f'{module_name}.{class_name}'

                        # Extract types
                        input_type = None
                        output_type = None
                        type_cls = getattr(cls, 'input_type', None)
                        if type_cls is not None and hasattr(type_cls, 'name'):
                            input_type = type_cls.name
                        type_cls = getattr(cls, 'output_type', None)
                        if type_cls is not None and hasattr(type_cls, 'name'):
                            output_type = type_cls.name

                        discovered[action_name] = {
                            'entrypoint': entrypoint,
                            'input_type': input_type,
                            'output_type': output_type,
                        }

                    except Exception:
                        continue

        finally:
            # Clean up sys.path
            if path_added and plugin_dir_str in sys.path:
                sys.path.remove(plugin_dir_str)

        return discovered


def _load_entrypoint(entrypoint: str) -> type[BaseAction] | Callable:
    """Load class/function from entrypoint string.

    Supports both colon and dot notation:
    - Colon notation: 'module.path:ClassName' (preferred)
    - Dot notation: 'module.path.ClassName' (common in config.yaml)

    Args:
        entrypoint: Entrypoint string like 'module.path:ClassName' or 'module.path.ClassName'

    Returns:
        Loaded class or function

    Raises:
        ValueError: If entrypoint format is invalid
        ModuleNotFoundError: If module doesn't exist
        AttributeError: If attribute doesn't exist in module
    """
    if ':' in entrypoint:
        # Colon notation: 'module.path:ClassName'
        module_path, attr_name = entrypoint.rsplit(':', 1)
    else:
        # Dot notation: 'module.path.ClassName' -> module='module.path', attr='ClassName'
        module_path, attr_name = entrypoint.rsplit('.', 1)

    module = importlib.import_module(module_path)
    return getattr(module, attr_name)


__all__ = ['PluginDiscovery']
