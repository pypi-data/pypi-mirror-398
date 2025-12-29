"""Dataset actions for download and conversion workflows.

Provides a single DatasetAction that can perform either download or convert
operations based on the operation parameter. This allows for flexible
pipeline composition.

Example:
    >>> from synapse_sdk.plugins.pipelines import ActionPipeline
    >>> from synapse_sdk.plugins.actions.dataset import DatasetAction
    >>>
    >>> # Create a download -> convert pipeline
    >>> pipeline = ActionPipeline([
    ...     DatasetAction,  # operation='download'
    ...     DatasetAction,  # operation='convert', uses path from download
    ...     TrainAction,
    ... ])
    >>>
    >>> result = pipeline.execute({
    ...     'operation': 'download',
    ...     'dataset_id': 123,
    ...     'target_format': 'yolo',  # for convert step
    ... }, ctx)
"""

from synapse_sdk.plugins.actions.dataset.action import (
    DatasetAction,
    DatasetOperation,
    DatasetParams,
    DatasetResult,
)

__all__ = [
    'DatasetAction',
    'DatasetOperation',
    'DatasetParams',
    'DatasetResult',
]
