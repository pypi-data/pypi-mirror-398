"""Pipeline execution context for shared working directory."""

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class PipelineContext:
    """Shared context for all actions in a pipeline execution.

    Provides a consistent working directory structure that persists
    across all actions in the pipeline. Each pipeline run gets a unique
    directory under the base path.

    Attributes:
        pipeline_id: Unique identifier for this pipeline run.
        run_id: Unique identifier for this specific execution.
        base_path: Base directory for all pipeline working directories.
        metadata: Optional metadata for the pipeline.

    Example:
        >>> ctx = PipelineContext(pipeline_id="my-pipeline")
        >>> ctx.work_dir
        PosixPath('/tmp/synapse_pipelines/my-pipeline/abc123')
        >>> ctx.datasets_dir
        PosixPath('/tmp/synapse_pipelines/my-pipeline/abc123/datasets')
    """

    pipeline_id: str
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    base_path: Path = field(default_factory=lambda: Path('/tmp/synapse_pipelines'))
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Ensure base path is a Path object and create work directory."""
        if isinstance(self.base_path, str):
            self.base_path = Path(self.base_path)
        # Create work directory on initialization
        self.work_dir.mkdir(parents=True, exist_ok=True)

    @property
    def work_dir(self) -> Path:
        """Get the working directory for this pipeline run."""
        return self.base_path / self.pipeline_id / self.run_id

    @property
    def datasets_dir(self) -> Path:
        """Get the datasets directory (for downloaded/converted data)."""
        path = self.work_dir / 'datasets'
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def models_dir(self) -> Path:
        """Get the models directory (for trained models/weights)."""
        path = self.work_dir / 'models'
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def artifacts_dir(self) -> Path:
        """Get the artifacts directory (for outputs, exports, etc.)."""
        path = self.work_dir / 'artifacts'
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def logs_dir(self) -> Path:
        """Get the logs directory."""
        path = self.work_dir / 'logs'
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def checkpoints_dir(self) -> Path:
        """Get the checkpoints directory for pipeline resume."""
        path = self.work_dir / 'checkpoints'
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_action_dir(self, action_name: str) -> Path:
        """Get a dedicated directory for a specific action.

        Args:
            action_name: Name of the action.

        Returns:
            Path to the action's dedicated directory.
        """
        path = self.work_dir / 'actions' / action_name
        path.mkdir(parents=True, exist_ok=True)
        return path

    def cleanup(self) -> None:
        """Remove all files in the working directory.

        Use with caution - this deletes all pipeline artifacts.
        """
        import shutil

        if self.work_dir.exists():
            shutil.rmtree(self.work_dir)


__all__ = ['PipelineContext']
