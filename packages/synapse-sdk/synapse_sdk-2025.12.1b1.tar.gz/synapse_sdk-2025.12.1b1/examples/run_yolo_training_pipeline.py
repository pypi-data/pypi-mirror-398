"""YOLO training pipeline.

Chains plugin actions: DownloadAction -> ConvertAction -> TrainAction

Usage:
    python run_yolo_training_pipeline.py \
        --dataset-id 2914 \
        --checkpoint-id 34 \
        --epochs 10

Environment variables:
    YOLO_PLUGIN_PATH: Path to synapse-yolo11-plugin directory
    RAY_ADDRESS: Ray cluster address (default: ray://10.0.0.4:10001)
    PIPELINE_SERVICE_URL: Dev-api URL (default: http://localhost:8100)
    ACTOR_PIPELINE_SERVICE_URL: Actor-accessible dev-api URL (default: http://localhost:8100)
"""

from __future__ import annotations

import argparse
import json
import os
import sys

# Add plugin path (from env or default relative path)
_default_plugin = os.path.join(os.path.dirname(__file__), '..', '..', 'synapse-yolo11-plugin')
plugin_path = os.environ.get('YOLO_PLUGIN_PATH', _default_plugin)
if plugin_path not in sys.path:
    sys.path.insert(0, plugin_path)

from plugin.convert import ConvertAction  # noqa: E402
from plugin.download import DownloadAction  # noqa: E402
from plugin.train import TrainAction  # noqa: E402

from synapse_sdk.plugins.executors.ray import RayPipelineExecutor  # noqa: E402
from synapse_sdk.plugins.pipelines import ActionPipeline, display_progress  # noqa: E402


def run_pipeline(params: dict) -> dict:
    """Execute the YOLO training pipeline.

    Args:
        params: Pipeline parameters including dataset_id, checkpoint, epochs, etc.

    Returns:
        TrainResult with weights_path and metrics.

    Raises:
        RuntimeError: If any pipeline action fails.
    """
    ray_address = os.environ.get('RAY_ADDRESS', 'ray://10.0.0.4:10001')
    pipeline_service_url = os.environ.get('PIPELINE_SERVICE_URL', 'http://localhost:8100')

    # actor_pipeline_service_url 시냅스 백엔드에서 파이프라인 모델 구현 전 까지 임시로 사용하는 API
    actor_pipeline_service_url = os.environ.get('ACTOR_PIPELINE_SERVICE_URL', 'http://10.0.0.4:8100')

    plugin_working_dir = os.environ.get('YOLO_PLUGIN_PATH', plugin_path)

    pipeline = ActionPipeline([DownloadAction, ConvertAction, TrainAction])

    executor = RayPipelineExecutor(
        ray_address=ray_address,
        pipeline_service_url=pipeline_service_url,
        actor_pipeline_service_url=actor_pipeline_service_url,
        working_dir=plugin_working_dir,
        include_sdk=True,
    )

    try:
        print(f'Submitting pipeline to {ray_address}...')
        run_id = pipeline.submit(params, executor)
        print(f'Run ID: {run_id}')

        final_progress = display_progress(executor.stream_progress(run_id))

        if final_progress.status.value == 'completed':
            return executor.get_result(run_id)
        else:
            raise RuntimeError(f'Pipeline failed: {final_progress.error}')

    finally:
        executor.close()


def main():
    parser = argparse.ArgumentParser(description='Run YOLO training pipeline')
    parser.add_argument('--dataset-id', type=int, required=True, help='Dataset ID to download')
    parser.add_argument('--checkpoint-id', type=int, required=True, help='Checkpoint ID to use')
    parser.add_argument('--splits', type=str, default=None, help='JSON splits config')
    parser.add_argument('--epochs', type=int, default=100, help='Training epochs')
    args = parser.parse_args()

    params = {
        'dataset_id': args.dataset_id,
        'checkpoint': args.checkpoint_id,
        'splits': json.loads(args.splits) if args.splits else None,
        'epochs': args.epochs,
    }

    result = run_pipeline(params)

    print('\nPipeline completed!')
    print(f'Weights: {result.weights_path}')
    print(f'mAP50: {result.final_mAP50}')


if __name__ == '__main__':
    main()
