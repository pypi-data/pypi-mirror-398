"""Dataset action with download and convert operations.

A single action class that handles both dataset download and format conversion,
selected via the operation parameter. Designed for pipeline composition.
"""

from __future__ import annotations

import json
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from synapse_sdk.plugins.action import BaseAction
from synapse_sdk.plugins.datasets.converters import DatasetFormat, get_converter
from synapse_sdk.plugins.datasets.formats.dm import DMVersion
from synapse_sdk.plugins.enums import PluginCategory
from synapse_sdk.plugins.types import YOLODataset

if TYPE_CHECKING:
    from synapse_sdk.clients.backend import BackendClient


class DatasetOperation(StrEnum):
    """Dataset operation types."""

    DOWNLOAD = 'download'
    CONVERT = 'convert'


class DatasetParams(BaseModel):
    """Parameters for DatasetAction.

    The operation field determines which operation to perform:
    - download: Downloads dataset from backend
    - convert: Converts dataset from one format to another

    Attributes:
        operation: Which operation to perform.
        dataset_id: Data collection ID (for download).
        splits: Split definitions for categorized download.
        path: Source dataset path (for convert, or set by download).
        source_format: Source format (for convert).
        target_format: Target format (for convert).
        dm_version: Datamaker version (for convert from DM).
        output_dir: Output directory (optional for both).
        is_categorized: Whether dataset has train/valid/test splits.
    """

    operation: DatasetOperation = DatasetOperation.DOWNLOAD

    # Download params
    dataset_id: int | None = Field(default=None, description='Data collection ID')
    splits: dict[str, dict[str, Any]] | None = Field(
        default=None,
        description='Split definitions: {"train": {...filters}, "valid": {...}}',
    )

    # Convert params
    path: Path | str | None = Field(default=None, description='Dataset path')
    source_format: str = Field(default='dm_v2', description='Source format')
    target_format: str = Field(default='yolo', description='Target format')
    dm_version: str = Field(default='v2', description='Datamaker version')

    # Shared params
    output_dir: Path | str | None = Field(default=None, description='Output directory')
    is_categorized: bool = Field(default=False, description='Has splits')


class DatasetResult(BaseModel):
    """Result from DatasetAction.

    Contains paths and metadata about the processed dataset.

    Attributes:
        path: Path to dataset directory.
        format: Dataset format (e.g., 'dm_v2', 'yolo').
        is_categorized: Whether dataset has splits.
        config_path: Path to config file (e.g., dataset.yaml for YOLO).
        count: Number of items processed.
        source_path: Original source path (for convert).
    """

    path: Path
    format: str
    is_categorized: bool = False
    config_path: Path | None = None
    count: int | None = None
    source_path: Path | None = None

    class Config:
        arbitrary_types_allowed = True


class DatasetAction(BaseAction[DatasetParams]):
    """Dataset action with download and convert operations.

    A unified action for dataset operations that can be used in pipelines.
    The operation is determined by the params.operation field.

    Type declarations:
        - input_type: None (accepts initial params)
        - output_type: Dynamic based on operation and target_format
          - download: 'dm_dataset'
          - convert to yolo: 'yolo_dataset'
          - convert to coco: 'coco_dataset'

    For download:
        - Requires: dataset_id
        - Optional: splits, output_dir
        - Returns: path, format='dm_v2', is_categorized, count

    For convert:
        - Requires: path, target_format
        - Optional: source_format, dm_version, output_dir
        - Returns: path, format, config_path, source_path

    Example:
        >>> # Standalone usage
        >>> action = DatasetAction(
        ...     DatasetParams(operation='download', dataset_id=123),
        ...     ctx,
        ... )
        >>> result = action.execute()
        >>>
        >>> # Pipeline usage
        >>> pipeline = ActionPipeline([DatasetAction, DatasetAction, TrainAction])
        >>> result = pipeline.execute({
        ...     'operation': 'download',
        ...     'dataset_id': 123,
        ...     'target_format': 'yolo',  # Used by second DatasetAction
        ... }, ctx)
    """

    category = PluginCategory.NEURAL_NET

    # Input type is flexible (accepts various initial params)
    input_type = None
    # Output type: use YOLODataset for convert (most common), DMv2Dataset for download
    # For precise typing, use separate DownloadAction/ConvertAction classes
    output_type = YOLODataset  # Default assumes convert to YOLO

    result_model = DatasetResult

    @property
    def client(self) -> BackendClient:
        """Backend client from context."""
        if self.ctx.client is None:
            raise RuntimeError('No backend client in context')
        return self.ctx.client

    def execute(self) -> DatasetResult:
        """Execute the dataset operation based on params.operation."""
        if self.params.operation == DatasetOperation.DOWNLOAD:
            return self.download()
        elif self.params.operation == DatasetOperation.CONVERT:
            return self.convert()
        else:
            raise ValueError(f'Unknown operation: {self.params.operation}')

    def download(self) -> DatasetResult:
        """Download dataset from backend.

        Downloads data units from a data collection and saves them
        locally in Datamaker format (json/ + original_files/).

        Returns:
            DatasetResult with path, format, count.

        Raises:
            ValueError: If dataset_id not provided.
        """
        from synapse_sdk.utils.file import get_temp_path

        if self.params.dataset_id is None:
            raise ValueError('dataset_id is required for download operation')

        dataset_id = self.params.dataset_id
        splits = self.params.splits
        is_categorized = splits is not None and len(splits) > 0

        # Determine output directory
        output_dir = Path(self.params.output_dir) if self.params.output_dir else get_temp_path(f'datasets/{dataset_id}')
        output_dir = Path(output_dir)

        # Report initial progress
        self.set_progress(0, 100, 'init')

        # Get collection info
        collection = self.client.get_data_collection(dataset_id)
        self.log(
            'download_start',
            {
                'dataset_id': dataset_id,
                'collection_name': collection.get('name'),
                'is_categorized': is_categorized,
            },
        )

        # Report collection fetched
        self.set_progress(1, 100, 'init')

        total_downloaded = 0

        if is_categorized and splits:
            # Download each split separately
            for split_name, filters in splits.items():
                split_dir = output_dir / split_name
                count = self._download_split(
                    dataset_id=dataset_id,
                    output_dir=split_dir,
                    filters=filters or {},
                )
                total_downloaded += count
                self.log(
                    'split_downloaded',
                    {
                        'split': split_name,
                        'count': count,
                    },
                )
        else:
            # Download all data units
            total_downloaded = self._download_split(
                dataset_id=dataset_id,
                output_dir=output_dir,
                filters={},
            )

        self.log(
            'download_complete',
            {
                'path': str(output_dir),
                'total_units': total_downloaded,
            },
        )

        return DatasetResult(
            path=output_dir,
            format='dm_v2',
            is_categorized=is_categorized,
            count=total_downloaded,
        )

    def _download_split(
        self,
        dataset_id: int,
        output_dir: Path,
        filters: dict[str, Any],
        max_workers: int = 10,
    ) -> int:
        """Download a single split of the dataset."""
        # Create output directories
        json_dir = output_dir / 'json'
        files_dir = output_dir / 'original_files'
        json_dir.mkdir(parents=True, exist_ok=True)
        files_dir.mkdir(parents=True, exist_ok=True)

        # Report fetching data units
        self.set_progress(2, 100, 'fetch')

        # List data units
        params = {'data_collection': dataset_id, **filters}
        data_units_gen, total_count = self.client.list_data_units(
            params=params,
            list_all=True,
        )

        # Report data units fetched
        self.set_progress(5, 100, 'fetch')
        self.log('data_units_listed', {'total_count': total_count})

        downloaded = 0

        def download_unit(unit: dict) -> bool:
            """Download a single data unit."""
            try:
                unit_id = unit.get('id') or unit.get('data_unit_id')
                files = unit.get('files', {})

                # Build DM v2 JSON structure
                dm_json = self._build_dm_json(unit)

                # Determine base name from first file or unit ID
                base_name = None
                for file_info in files.values():
                    if isinstance(file_info, dict):
                        file_path = file_info.get('path') or file_info.get('url', '')
                    else:
                        file_path = str(file_info)
                    if file_path:
                        base_name = Path(file_path).stem
                        break

                if not base_name:
                    base_name = str(unit_id)

                # Save JSON
                json_path = json_dir / f'{base_name}.json'
                json_path.write_text(json.dumps(dm_json, indent=2, ensure_ascii=False))

                # Copy/download files
                for file_name, file_info in files.items():
                    if isinstance(file_info, dict):
                        file_path = file_info.get('path')
                    else:
                        file_path = str(file_info)

                    if file_path and Path(file_path).exists():
                        dest = files_dir / Path(file_path).name
                        if not dest.exists():
                            shutil.copy(file_path, dest)

                return True
            except Exception as e:
                self.log('download_unit_error', {'unit_id': unit_id, 'error': str(e)})
                return False

        # Process units with thread pool
        # Note: data_units_gen is a lazy generator that fetches pages from API
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            units_fetched = 0

            # Submit downloads as we iterate (reports fetch progress)
            for unit in data_units_gen:
                futures.append(executor.submit(download_unit, unit))
                units_fetched += 1
                # Report fetch progress (5-50% range)
                fetch_progress = 5 + (units_fetched / total_count) * 45
                if units_fetched % 10 == 0 or units_fetched == total_count:
                    self.set_progress(int(fetch_progress), 100, 'fetch')

            # Process completed downloads (50-100% range)
            for i, future in enumerate(as_completed(futures)):
                if future.result():
                    downloaded += 1
                # Report download progress (50-100% range)
                download_progress = 50 + ((i + 1) / total_count) * 50
                self.set_progress(int(download_progress), 100, 'download')

        return downloaded

    def _build_dm_json(self, unit: dict) -> dict[str, Any]:
        """Build Datamaker v2 JSON from a data unit."""
        annotations = unit.get('annotations', {})

        dm_image: dict[str, list] = {
            'bounding_box': [],
            'polygon': [],
            'polyline': [],
            'keypoint': [],
            'relation': [],
            'group': [],
        }

        if isinstance(annotations, dict):
            for key in dm_image.keys():
                if key in annotations:
                    dm_image[key] = annotations[key]

        # Build classification map from annotations
        classifications: dict[str, set[str]] = {}
        for ann_type, anns in dm_image.items():
            if anns:
                classifications[ann_type] = set()
                for ann in anns:
                    if 'classification' in ann:
                        classifications[ann_type].add(ann['classification'])

        return {
            'classification': {k: sorted(v) for k, v in classifications.items() if v},
            'images': [dm_image],
        }

    def convert(self) -> DatasetResult:
        """Convert dataset from one format to another.

        Converts the dataset at params.path to params.target_format.

        Returns:
            DatasetResult with converted path, format, config_path.

        Raises:
            ValueError: If path not provided.
        """
        if self.params.path is None:
            raise ValueError('path is required for convert operation')

        source_path = Path(self.params.path)
        if not source_path.exists():
            raise FileNotFoundError(f'Dataset path does not exist: {source_path}')

        # Parse formats
        target_format = DatasetFormat(self.params.target_format)
        dm_version = DMVersion.V1 if self.params.dm_version == 'v1' else DMVersion.V2

        # Determine source format
        source_format_str = self.params.source_format
        if source_format_str in ('dm_v1', 'dm_v2', 'dm'):
            src_format = DatasetFormat.DM_V1 if dm_version == DMVersion.V1 else DatasetFormat.DM_V2
        else:
            src_format = DatasetFormat(source_format_str)

        # Determine output directory
        if self.params.output_dir:
            output_dir = Path(self.params.output_dir)
        else:
            output_dir = source_path.parent / f'{source_path.name}_{target_format.value}'

        self.log(
            'convert_start',
            {
                'source_path': str(source_path),
                'source_format': src_format.value,
                'target_format': target_format.value,
                'is_categorized': self.params.is_categorized,
            },
        )

        # Get converter and run conversion
        converter = get_converter(
            source=src_format,
            target=target_format,
            root_dir=source_path,
            is_categorized=self.params.is_categorized,
            dm_version=dm_version,
        )

        converter.convert()
        converter.save_to_folder(output_dir)

        # Determine config path
        config_path = None
        if target_format == DatasetFormat.YOLO:
            config_path = output_dir / 'dataset.yaml'
            if not config_path.exists():
                config_path = None

        self.log(
            'convert_complete',
            {
                'output_path': str(output_dir),
                'config_path': str(config_path) if config_path else None,
            },
        )

        return DatasetResult(
            path=output_dir,
            format=target_format.value,
            is_categorized=self.params.is_categorized,
            config_path=config_path,
            source_path=source_path,
        )


__all__ = ['DatasetAction', 'DatasetOperation', 'DatasetParams', 'DatasetResult']
