from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from synapse_sdk.plugins.enums import (
    AnnotationCategory,
    AnnotationType,
    DataType,
    PackageManager,
    PluginCategory,
    RunMethod,
    SmartToolType,
)


class ActionConfig(BaseModel):
    """Configuration for a single plugin action.

    Attributes:
        name: Action name (e.g., 'train', 'infer', 'export').
        description: Human-readable description of the action.
        entrypoint: Module path to action class (e.g., 'my_plugin.actions:TrainAction').
        method: Execution method (job, task, or serve).
        params_schema: Pydantic model class for parameter validation.
        input_type: Semantic input type (e.g., 'yolo_dataset'). Auto-synced from code.
        output_type: Semantic output type (e.g., 'model_weights'). Auto-synced from code.
    """

    name: str
    description: str = ''
    entrypoint: str = ''
    method: RunMethod = RunMethod.TASK
    params_schema: type[BaseModel] | None = None

    # Semantic types for pipeline compatibility (auto-synced from action class)
    input_type: str | None = None
    output_type: str | None = None

    model_config = {'arbitrary_types_allowed': True}


class PluginConfig(BaseModel):
    """Configuration for a plugin.

    Attributes:
        name: Human-readable plugin name.
        code: Unique identifier for the plugin (e.g., 'yolov8').
        version: Semantic version string.
        category: Plugin category for organization.
        description: Human-readable description.
        readme: Path to README file relative to plugin root.
        package_manager: Package manager for dependencies ('pip' or 'uv').
        package_manager_options: Additional options for package manager.
        wheels_dir: Directory containing .whl files for local installation (default: 'wheels').
        env: Environment variables to inject into runtime environment.
        runtime_env: Full Ray runtime_env configuration (merged with auto-generated settings).
        data_type: Primary data type handled by the plugin.
        tasks: List of tasks in format 'data_type.task_name' (e.g., 'image.object_detection').
        supported_data_type: Data types supported by upload plugins.
        annotation_category: Annotation category for smart tools.
        annotation_type: Annotation type for smart tools.
        smart_tool: Smart tool implementation type.
        actions: Dictionary of action name to ActionConfig.
    """

    name: str
    code: str
    version: str = '0.1.0'
    category: PluginCategory = PluginCategory.CUSTOM
    description: str = ''
    readme: str = 'README.md'

    # Package management
    package_manager: PackageManager = PackageManager.PIP
    package_manager_options: list[str] = Field(default_factory=list)
    wheels_dir: str = 'wheels'

    # Runtime environment
    env: dict[str, Any] = Field(default_factory=dict)
    runtime_env: dict[str, Any] = Field(default_factory=dict)

    # Data type configuration
    data_type: DataType | None = None
    tasks: list[str] = Field(default_factory=list)
    supported_data_type: list[DataType] = Field(default_factory=list)

    # Smart tool configuration
    annotation_category: AnnotationCategory | None = None
    annotation_type: AnnotationType | None = None
    smart_tool: SmartToolType | None = None

    # Actions
    actions: dict[str, ActionConfig] = Field(default_factory=dict)


__all__ = ['ActionConfig', 'PluginConfig']
