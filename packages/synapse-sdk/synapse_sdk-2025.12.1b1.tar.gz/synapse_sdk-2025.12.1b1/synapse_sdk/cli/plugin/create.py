"""Plugin creation command."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import questionary
import yaml
from jinja2 import Environment, FileSystemLoader
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from synapse_sdk.plugins.enums import (
    AnnotationCategory,
    AnnotationType,
    DataType,
    PluginCategory,
    SmartToolType,
)
from synapse_sdk.plugins.templates import TEMPLATES_DIR

# Category descriptions for interactive prompts
CATEGORY_DESCRIPTIONS = {
    PluginCategory.NEURAL_NET: 'Train and deploy ML models',
    PluginCategory.SMART_TOOL: 'Interactive annotation helpers',
    PluginCategory.EXPORT: 'Data format conversion',
    PluginCategory.UPLOAD: 'External data import',
    PluginCategory.DATA_VALIDATION: 'Pre-annotation data checks',
    PluginCategory.PRE_ANNOTATION: 'Auto-generate initial annotations',
    PluginCategory.POST_ANNOTATION: 'Process annotations after labeling',
    PluginCategory.CUSTOM: 'Custom plugin type',
}

# Tasks by data type
TASKS_BY_DATA_TYPE = {
    DataType.IMAGE: [
        'object_detection',
        'classification',
        'segmentation',
        'keypoint',
    ],
    DataType.TEXT: [
        'classification',
        'ner',
        'qa',
    ],
    DataType.VIDEO: [
        'object_tracking',
        'action_recognition',
        'segmentation',
    ],
    DataType.AUDIO: [
        'classification',
        'transcription',
    ],
    DataType.PCD: [
        'object_detection',
        'segmentation',
    ],
}


@dataclass
class PluginSpec:
    """Specification for a plugin to create."""

    name: str
    code: str
    version: str
    category: PluginCategory
    description: str

    # Category-specific fields
    data_type: DataType | None = None
    tasks: list[str] = field(default_factory=list)
    annotation_category: AnnotationCategory | None = None
    annotation_type: AnnotationType | None = None
    smart_tool_type: SmartToolType | None = None
    supported_data_types: list[DataType] = field(default_factory=list)

    @property
    def directory_name(self) -> str:
        """Get the directory name for the plugin."""
        return f'synapse-{self.code}-plugin'

    def to_template_context(self) -> dict[str, Any]:
        """Convert to template context dictionary."""
        return {
            'name': self.name,
            'code': self.code,
            'version': self.version,
            'category': self.category.value,
            'description': self.description,
            'data_type': self.data_type.value if self.data_type else None,
            'tasks': [f'{self.data_type.value}.{t}' for t in self.tasks] if self.data_type and self.tasks else [],
            'annotation_category': self.annotation_category.value if self.annotation_category else None,
            'annotation_type': self.annotation_type.value if self.annotation_type else None,
            'smart_tool_type': self.smart_tool_type.value if self.smart_tool_type else None,
            'supported_data_types': [dt.value for dt in self.supported_data_types],
        }


def slugify(text: str) -> str:
    """Convert text to slug format.

    Args:
        text: Text to slugify.

    Returns:
        Slugified text (lowercase, hyphens instead of spaces).
    """
    # Convert to lowercase and replace spaces/underscores with hyphens
    slug = text.lower().strip()
    slug = re.sub(r'[\s_]+', '-', slug)
    # Remove non-alphanumeric characters except hyphens
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    # Remove consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    return slug


def validate_code(code: str) -> bool | str:
    """Validate plugin code format.

    Args:
        code: Plugin code to validate.

    Returns:
        True if valid, error message otherwise.
    """
    if not code:
        return 'Code cannot be empty'
    if not re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$', code):
        return 'Code must be lowercase letters, numbers, and hyphens (no leading/trailing hyphens)'
    return True


def prompt_category() -> PluginCategory:
    """Prompt user to select a plugin category.

    Returns:
        Selected plugin category.
    """
    choices = [
        questionary.Choice(
            title=f'{cat.value.replace("_", " ").title():20} {CATEGORY_DESCRIPTIONS[cat]}',
            value=cat,
        )
        for cat in PluginCategory
    ]

    return questionary.select(
        'Select plugin category:',
        choices=choices,
    ).ask()


def prompt_basic_info(category: PluginCategory) -> tuple[str, str, str, str]:
    """Prompt user for basic plugin information.

    Args:
        category: Selected plugin category.

    Returns:
        Tuple of (name, code, version, description).
    """
    name = questionary.text(
        'Plugin name:',
        validate=lambda x: len(x) > 0 or 'Name cannot be empty',
    ).ask()

    default_code = slugify(name)
    code = questionary.text(
        'Plugin code:',
        default=default_code,
        validate=validate_code,
    ).ask()

    version = questionary.text(
        'Version:',
        default='0.1.0',
    ).ask()

    default_description = f'{name} plugin'
    description = questionary.text(
        'Description:',
        default=default_description,
    ).ask()

    return name, code, version, description


def prompt_neural_net_options() -> tuple[DataType | None, list[str]]:
    """Prompt user for neural net specific options.

    Returns:
        Tuple of (data_type, tasks).
    """
    data_type_choices = [questionary.Choice(title=dt.value, value=dt) for dt in DataType]
    data_type = questionary.select(
        'Data type:',
        choices=data_type_choices,
    ).ask()

    available_tasks = TASKS_BY_DATA_TYPE.get(data_type, [])
    if available_tasks:
        tasks = questionary.checkbox(
            'Tasks (select with space, confirm with enter):',
            choices=available_tasks,
        ).ask()
    else:
        tasks = []

    return data_type, tasks


def prompt_smart_tool_options() -> tuple[AnnotationCategory, AnnotationType, SmartToolType]:
    """Prompt user for smart tool specific options.

    Returns:
        Tuple of (annotation_category, annotation_type, smart_tool_type).
    """
    annotation_category = questionary.select(
        'Annotation category:',
        choices=[ac.value for ac in AnnotationCategory],
    ).ask()

    annotation_type = questionary.select(
        'Annotation type:',
        choices=[at.value for at in AnnotationType],
    ).ask()

    smart_tool_type = questionary.select(
        'Smart tool type:',
        choices=[
            questionary.Choice(title='Interactive - User triggers predictions', value=SmartToolType.INTERACTIVE),
            questionary.Choice(title='Automatic - Runs on all data', value=SmartToolType.AUTOMATIC),
            questionary.Choice(title='Semi-automatic - Suggests, user confirms', value=SmartToolType.SEMI_AUTOMATIC),
        ],
    ).ask()

    return (
        AnnotationCategory(annotation_category),
        AnnotationType(annotation_type),
        smart_tool_type,
    )


def prompt_upload_options() -> list[DataType]:
    """Prompt user for upload specific options.

    Returns:
        List of supported data types.
    """
    choices = [questionary.Choice(title=dt.value, value=dt) for dt in DataType]
    return questionary.checkbox(
        'Supported data types (select with space):',
        choices=choices,
    ).ask()


def collect_plugin_spec(
    *,
    name: str | None = None,
    code: str | None = None,
    category: str | None = None,
    interactive: bool = True,
) -> PluginSpec | None:
    """Collect plugin specification from user.

    Args:
        name: Plugin name (skip prompt if provided).
        code: Plugin code (skip prompt if provided).
        category: Plugin category (skip prompt if provided).
        interactive: Whether to prompt for input.

    Returns:
        PluginSpec if successful, None if user cancelled.
    """
    # Get category
    if category:
        selected_category = PluginCategory(category)
    elif interactive:
        selected_category = prompt_category()
        if not selected_category:
            return None
    else:
        selected_category = PluginCategory.CUSTOM

    # Get basic info
    if name and code:
        plugin_name = name
        plugin_code = code
        version = '0.1.0'
        description = f'{name} plugin'
    elif interactive:
        result = prompt_basic_info(selected_category)
        if not all(result):
            return None
        plugin_name, plugin_code, version, description = result
    else:
        raise ValueError('name and code are required in non-interactive mode')

    # Create base spec
    spec = PluginSpec(
        name=plugin_name,
        code=plugin_code,
        version=version,
        category=selected_category,
        description=description,
    )

    # Category-specific prompts
    if interactive:
        if selected_category == PluginCategory.NEURAL_NET:
            data_type, tasks = prompt_neural_net_options()
            if data_type:
                spec.data_type = data_type
                spec.tasks = tasks or []

        elif selected_category == PluginCategory.SMART_TOOL:
            result = prompt_smart_tool_options()
            if all(result):
                spec.annotation_category, spec.annotation_type, spec.smart_tool_type = result

        elif selected_category == PluginCategory.UPLOAD:
            supported = prompt_upload_options()
            if supported:
                spec.supported_data_types = supported

    return spec


def display_preview(spec: PluginSpec, console: Console) -> None:
    """Display a preview of the plugin to be created.

    Args:
        spec: Plugin specification.
        console: Rich console for output.
    """
    # Create tree view of files
    tree = Tree(f'[bold]{spec.directory_name}/[/bold]')
    tree.add('[dim]config.yaml[/dim]         Plugin configuration')
    tree.add('[dim]README.md[/dim]           Documentation')
    tree.add('[dim]requirements.txt[/dim]   Dependencies')
    tree.add('[dim]pyproject.toml[/dim]     Project metadata')
    tree.add('[dim].gitignore[/dim]          Git ignore rules')
    tree.add('[dim].synapseignore[/dim]     Publish ignore rules')

    plugin_branch = tree.add('[dim]plugin/[/dim]             Action implementations')

    # Add category-specific files
    category = spec.category.value
    if category == 'neural_net':
        plugin_branch.add('[dim]train.py[/dim]')
        plugin_branch.add('[dim]inference.py[/dim]')
    elif category == 'smart_tool':
        plugin_branch.add('[dim]auto_label.py[/dim]')
    elif category == 'export':
        plugin_branch.add('[dim]export.py[/dim]')
    elif category == 'upload':
        plugin_branch.add('[dim]upload.py[/dim]')
    elif category == 'data_validation':
        plugin_branch.add('[dim]validate.py[/dim]')
    elif category == 'pre_annotation':
        plugin_branch.add('[dim]pre_annotate.py[/dim]')
    elif category == 'post_annotation':
        plugin_branch.add('[dim]post_annotate.py[/dim]')
    else:
        plugin_branch.add('[dim]main.py[/dim]')

    # Create info table
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column('Key', style='dim')
    table.add_column('Value')
    table.add_row('Name', spec.name)
    table.add_row('Code', spec.code)
    table.add_row('Version', spec.version)
    table.add_row('Category', spec.category.value.replace('_', ' ').title())

    if spec.data_type:
        table.add_row('Data Type', spec.data_type.value)
    if spec.tasks:
        table.add_row('Tasks', ', '.join(spec.tasks))
    if spec.annotation_type:
        table.add_row('Annotation Type', spec.annotation_type.value)
    if spec.smart_tool_type:
        table.add_row('Tool Type', spec.smart_tool_type.value)
    if spec.supported_data_types:
        table.add_row('Supported Types', ', '.join(dt.value for dt in spec.supported_data_types))

    console.print()
    console.print(Panel(table, title='Plugin Info', border_style='blue'))
    console.print()
    console.print(Panel(tree, title='Files to Create', border_style='green'))
    console.print()


def render_template(template_path: Path, context: dict[str, Any]) -> str:
    """Render a Jinja2 template.

    Args:
        template_path: Path to template file.
        context: Template context.

    Returns:
        Rendered template content.
    """
    env = Environment(
        loader=FileSystemLoader(template_path.parent),
        keep_trailing_newline=True,
    )
    template = env.get_template(template_path.name)
    return template.render(**context)


def create_plugin(spec: PluginSpec, output_dir: Path, console: Console) -> Path:
    """Create a plugin from specification.

    Args:
        spec: Plugin specification.
        output_dir: Directory to create plugin in.
        console: Rich console for output.

    Returns:
        Path to created plugin directory.
    """
    plugin_dir = output_dir / spec.directory_name
    context = spec.to_template_context()
    category = spec.category.value

    # Create plugin directory
    plugin_dir.mkdir(parents=True, exist_ok=True)
    (plugin_dir / 'plugin').mkdir(exist_ok=True)

    # Render base templates
    base_dir = TEMPLATES_DIR / 'base'
    for template_file in base_dir.glob('*.j2'):
        output_name = template_file.stem  # Remove .j2
        content = render_template(template_file, context)
        (plugin_dir / output_name).write_text(content)

    # Render base plugin/__init__.py
    init_template = base_dir / 'plugin' / '__init__.py.j2'
    if init_template.exists():
        content = render_template(init_template, context)
        (plugin_dir / 'plugin' / '__init__.py').write_text(content)

    # Render category-specific templates
    category_dir = TEMPLATES_DIR / category
    if category_dir.exists():
        # Merge category config with base config
        category_config_template = category_dir / 'config.yaml.j2'
        if category_config_template.exists():
            base_config_path = plugin_dir / 'config.yaml'
            base_config = yaml.safe_load(base_config_path.read_text())
            category_config_content = render_template(category_config_template, context)
            category_config = yaml.safe_load(category_config_content)
            base_config.update(category_config)
            base_config_path.write_text(yaml.dump(base_config, sort_keys=False, default_flow_style=False))

        # Copy category-specific plugin files
        category_plugin_dir = category_dir / 'plugin'
        if category_plugin_dir.exists():
            for template_file in category_plugin_dir.glob('*.j2'):
                output_name = template_file.stem
                content = render_template(template_file, context)
                (plugin_dir / 'plugin' / output_name).write_text(content)

    console.print(f'[green]Created plugin at[/green] {plugin_dir}')
    return plugin_dir


@dataclass
class CreateResult:
    """Result of plugin creation."""

    plugin_dir: Path
    spec: PluginSpec


def create_plugin_interactive(
    *,
    output_dir: Path | None = None,
    name: str | None = None,
    code: str | None = None,
    category: str | None = None,
    console: Console,
    yes: bool = False,
) -> CreateResult | None:
    """Create a plugin interactively.

    Args:
        output_dir: Directory to create plugin in. Defaults to current directory.
        name: Plugin name (skip prompt if provided).
        code: Plugin code (skip prompt if provided).
        category: Plugin category (skip prompt if provided).
        console: Rich console for output.
        yes: Skip confirmation prompt.

    Returns:
        CreateResult if successful, None if cancelled.
    """
    output_dir = output_dir or Path.cwd()

    # Collect spec
    spec = collect_plugin_spec(
        name=name,
        code=code,
        category=category,
        interactive=True,
    )

    if not spec:
        return None

    # Check if directory already exists
    plugin_dir = output_dir / spec.directory_name
    if plugin_dir.exists():
        console.print(f'[red]Directory already exists:[/red] {plugin_dir}')
        if not yes:
            overwrite = questionary.confirm(
                'Overwrite existing directory?',
                default=False,
            ).ask()
            if not overwrite:
                return None
        shutil.rmtree(plugin_dir)

    # Show preview
    display_preview(spec, console)

    # Confirm
    if not yes:
        confirmed = questionary.confirm(
            'Create plugin?',
            default=True,
        ).ask()
        if not confirmed:
            console.print('[yellow]Cancelled[/yellow]')
            return None

    # Create plugin
    plugin_dir = create_plugin(spec, output_dir, console)

    return CreateResult(plugin_dir=plugin_dir, spec=spec)


__all__ = [
    'PluginSpec',
    'CreateResult',
    'create_plugin',
    'create_plugin_interactive',
    'collect_plugin_spec',
    'display_preview',
    'slugify',
    'validate_code',
]
