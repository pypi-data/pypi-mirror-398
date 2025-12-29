"""Plugin CLI commands."""

from synapse_sdk.cli.plugin.create import (
    CreateResult,
    PluginSpec,
    create_plugin,
    create_plugin_interactive,
)
from synapse_sdk.cli.plugin.job import (
    display_job,
    get_job,
    get_job_logs,
    tail_job_logs,
)
from synapse_sdk.cli.plugin.publish import (
    PublishResult,
    create_plugin_archive,
    display_files_preview,
    find_config_file,
    load_synapseignore,
    publish_plugin,
)
from synapse_sdk.cli.plugin.run import (
    RunResult,
    resolve_plugin_code,
    run_plugin,
)
from synapse_sdk.cli.plugin.test import (
    TestResult,
    test_plugin,
)

__all__ = [
    # Create
    'CreateResult',
    'PluginSpec',
    'create_plugin',
    'create_plugin_interactive',
    # Job
    'display_job',
    'get_job',
    'get_job_logs',
    'tail_job_logs',
    # Publish
    'PublishResult',
    'create_plugin_archive',
    'display_files_preview',
    'find_config_file',
    'load_synapseignore',
    'publish_plugin',
    # Run
    'RunResult',
    'resolve_plugin_code',
    'run_plugin',
    # Test
    'TestResult',
    'test_plugin',
]
