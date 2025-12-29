"""Integration test for pipeline execution.

Run with: uv run python tests/integration/test_pipeline_execution.py
"""

import time

from synapse_sdk.plugins.executors.ray import RayPipelineExecutor
from synapse_sdk.plugins.pipelines import ActionPipeline, RunStatus
from synapse_sdk.plugins.testing import (
    ConvertAction,
    DownloadAction,
    TrainAction,
)


def test_local_execution():
    """Test local pipeline execution (no Ray)."""
    print('\n=== Testing Local Execution ===')

    from synapse_sdk.loggers import ConsoleLogger
    from synapse_sdk.plugins.context import PluginEnvironment, RuntimeContext

    pipeline = ActionPipeline([DownloadAction, ConvertAction, TrainAction])

    ctx = RuntimeContext(
        logger=ConsoleLogger(),
        env=PluginEnvironment(),
    )

    result = pipeline.execute({'dataset_id': 123, 'epochs': 10}, ctx)
    print(f'Result: {result}')
    print('Local execution: OK')


def test_remote_execution():
    """Test remote pipeline execution with Ray."""
    print('\n=== Testing Remote Execution ===')

    # Create pipeline
    pipeline = ActionPipeline([DownloadAction, ConvertAction, TrainAction])

    # Create executor connecting to remote Synapse agent
    # Ray client port is typically 10001
    executor = RayPipelineExecutor(
        ray_address='ray://10.0.0.4:10001',  # Synapse agent Ray cluster
        pipeline_service_url='http://localhost:8100',  # Local SDK access
        actor_pipeline_service_url='http://100.111.105.44:8100',  # Actor access via Tailscale
        include_sdk=True,  # Bundle SDK for remote cluster
    )

    try:
        # Submit pipeline
        print('Submitting pipeline...')
        run_id = pipeline.submit({'dataset_id': 456, 'epochs': 5}, executor)
        print(f'Run ID: {run_id}')

        # Poll for progress
        print('Polling progress...')
        for i in range(30):
            progress = executor.get_progress(run_id)
            print(f'  Status: {progress.status}, Action: {progress.current_action}')

            if progress.status in (RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED):
                break
            time.sleep(2)

        # Get result
        if progress.status == RunStatus.COMPLETED:
            result = executor.get_result(run_id)
            print(f'Result: {result}')
            print('Remote execution: OK')
        else:
            print(f'Pipeline failed: {progress.error}')

    finally:
        executor.close()


def test_streaming_progress():
    """Test SSE progress streaming."""
    print('\n=== Testing Progress Streaming ===')

    from synapse_sdk.plugins.pipelines import display_progress

    pipeline = ActionPipeline([DownloadAction, ConvertAction, TrainAction])

    executor = RayPipelineExecutor(
        ray_address='ray://10.0.0.4:10001',
        pipeline_service_url='http://localhost:8100',
        actor_pipeline_service_url='http://100.111.105.44:8100',
        include_sdk=True,
    )

    try:
        run_id = pipeline.submit({'dataset_id': 789, 'epochs': 3}, executor)
        print(f'Run ID: {run_id}')

        # Stream with Rich display
        final = display_progress(executor.stream_progress(run_id))
        print(f'Final status: {final.status}')

    finally:
        executor.close()


if __name__ == '__main__':
    # Test 1: Local execution (no Ray needed)
    test_local_execution()

    # Test 2: Remote execution
    test_remote_execution()

    # Test 3: Streaming progress
    test_streaming_progress()

    print('\n=== All tests completed ===')
