"""Base converter classes for dataset format conversions.

Provides:
- BaseConverter: Shared logic for all converters
- FromDMConverter: Base for DM -> external format conversions
- ToDMConverter: Base for external format -> DM conversions
"""

from __future__ import annotations

import json
import shutil
import uuid
from abc import ABC, abstractmethod
from enum import StrEnum
from pathlib import Path
from typing import IO, Any

from synapse_sdk.plugins.datasets.formats.dm import DMVersion


class DatasetFormat(StrEnum):
    """Supported dataset formats."""

    DM_V1 = 'dm_v1'
    DM_V2 = 'dm_v2'
    YOLO = 'yolo'
    COCO = 'coco'
    PASCAL = 'pascal'

    @classmethod
    def from_dm_version(cls, version: DMVersion) -> DatasetFormat:
        """Get DatasetFormat from DMVersion."""
        if version == DMVersion.V1:
            return cls.DM_V1
        return cls.DM_V2


class BaseConverter(ABC):
    """Base class for shared logic between converters.

    Attributes:
        root_dir: Root directory containing source data.
        is_categorized: Whether dataset has train/valid/test splits.
        is_single_conversion: Whether converting single files (not directories).
        converted_data: Holds converted data after calling convert().

    Example:
        >>> converter = MyConverter(root_dir='/data/source', is_categorized=True)
        >>> converter.convert()
        >>> converter.save_to_folder('/data/output')
    """

    IMG_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp', '.webp']

    def __init__(
        self,
        root_dir: str | Path | None = None,
        is_categorized: bool = False,
        is_single_conversion: bool = False,
    ) -> None:
        """Initialize converter.

        Args:
            root_dir: Root directory containing data.
            is_categorized: Whether to handle train/valid/test splits.
            is_single_conversion: Whether converting single files only.

        Raises:
            ValueError: If root_dir not specified for directory conversion.
        """
        self.root_dir = Path(root_dir) if root_dir else None
        self.is_categorized = is_categorized
        self.is_single_conversion = is_single_conversion
        self.converted_data: Any = None

        if not is_single_conversion and not root_dir:
            raise ValueError('root_dir must be specified for directory conversion')

    @staticmethod
    def ensure_dir(path: Path | str) -> Path:
        """Ensure directory exists, creating if necessary."""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def get_image_size(image_path: Path | str | IO) -> tuple[int, int]:
        """Get image dimensions (width, height)."""
        from PIL import Image

        with Image.open(image_path) as img:
            return img.size

    def find_image_for_label(
        self,
        label_stem: str,
        image_dir: Path,
    ) -> Path | None:
        """Find image file matching a label file stem."""
        for ext in self.IMG_EXTENSIONS:
            img_path = image_dir / f'{label_stem}{ext}'
            if img_path.exists():
                return img_path
        return None

    def _validate_required_dirs(self, dirs: dict[str, Path]) -> None:
        """Validate that all required directories exist."""
        for name, path in dirs.items():
            if not path.exists():
                raise FileNotFoundError(f'Required directory "{name}" does not exist: {path}')

    def _validate_optional_dirs(self, dirs: dict[str, Path]) -> dict[str, Path]:
        """Validate optional directories, return those that exist."""
        existing = {}
        for name, path in dirs.items():
            if path.exists():
                existing[name] = path
        return existing

    def _validate_splits(
        self,
        required_splits: list[str],
        optional_splits: list[str] | None = None,
    ) -> dict[str, Path]:
        """Validate required and optional splits in the dataset.

        Args:
            required_splits: Splits that must exist (e.g., ['train', 'valid']).
            optional_splits: Splits that may exist (e.g., ['test']).

        Returns:
            Dictionary mapping split names to their paths.

        Raises:
            FileNotFoundError: If required split is missing.
        """
        if self.root_dir is None:
            raise ValueError('root_dir must be set')

        splits: dict[str, Path] = {}
        optional_splits = optional_splits or []

        if self.is_categorized:
            required_dirs = {split: self.root_dir / split for split in required_splits}
            self._validate_required_dirs(required_dirs)
            splits.update(required_dirs)

            optional_dirs = {split: self.root_dir / split for split in optional_splits}
            splits.update(self._validate_optional_dirs(optional_dirs))
        else:
            # Non-categorized: expect json/ and original_files/ in root
            required_dirs = {
                'json': self.root_dir / 'json',
                'original_files': self.root_dir / 'original_files',
            }
            self._validate_required_dirs(required_dirs)
            splits['root'] = self.root_dir

        return splits

    def _set_directories(self, split: str | None = None) -> None:
        """Set json_dir and original_file_dir based on split."""
        if self.root_dir is None:
            raise ValueError('root_dir must be set')

        if split:
            split_dir = self.root_dir / split
            self.json_dir = split_dir / 'json'
            self.original_file_dir = split_dir / 'original_files'
        else:
            self.json_dir = self.root_dir / 'json'
            self.original_file_dir = self.root_dir / 'original_files'

    @staticmethod
    def _generate_unique_id() -> str:
        """Generate a unique 10-character ID."""
        return uuid.uuid4().hex[:10]

    @abstractmethod
    def convert(self) -> Any:
        """Convert data (in-memory). Must be implemented by subclasses."""
        ...

    @abstractmethod
    def save_to_folder(self, output_dir: str | Path) -> None:
        """Save converted data to folder. Must be implemented by subclasses."""
        ...

    def convert_single_file(
        self,
        data: Any,
        original_file: IO,
        **kwargs: Any,
    ) -> Any:
        """Convert a single data object and corresponding original file.

        Only available when is_single_conversion=True.

        Args:
            data: The data object to convert.
            original_file: File object for the corresponding original file.
            **kwargs: Additional converter-specific parameters.

        Returns:
            Converted data in target format.

        Raises:
            RuntimeError: If not in single conversion mode.
            NotImplementedError: If subclass doesn't implement this.
        """
        if not self.is_single_conversion:
            raise RuntimeError('convert_single_file only available when is_single_conversion=True')
        raise NotImplementedError('Subclasses must implement convert_single_file')


class FromDMConverter(BaseConverter):
    """Base class for converting from Datamaker format to external formats.

    Subclasses convert DM (v1 or v2) -> YOLO, COCO, PASCAL, etc.

    Expected source structure:
    - Categorized: root_dir/{train,valid,test}/json/*.json + original_files/*
    - Non-categorized: root_dir/json/*.json + original_files/*

    Example:
        >>> converter = FromDMToYOLOConverter(
        ...     root_dir='/data/dm_dataset',
        ...     is_categorized=True,
        ...     dm_version=DMVersion.V2,
        ... )
        >>> result = converter.convert()
        >>> converter.save_to_folder('/data/yolo_output')
    """

    source_format: DatasetFormat = DatasetFormat.DM_V2
    target_format: DatasetFormat

    def __init__(
        self,
        root_dir: str | Path | None = None,
        is_categorized: bool = False,
        is_single_conversion: bool = False,
        dm_version: DMVersion = DMVersion.V2,
    ) -> None:
        """Initialize FromDMConverter.

        Args:
            root_dir: Root directory containing DM data.
            is_categorized: Whether dataset has train/valid/test splits.
            is_single_conversion: Whether converting single files only.
            dm_version: Datamaker schema version (V1 or V2).
        """
        super().__init__(root_dir, is_categorized, is_single_conversion)
        self.dm_version = dm_version
        self.source_format = DatasetFormat.from_dm_version(dm_version)
        self.class_names: list[str] = []
        self.class_map: dict[str, int] | None = None

    def save_to_folder(self, output_dir: str | Path) -> None:
        """Save converted data to folder.

        Subclasses should override to implement format-specific saving.
        """
        output_dir = Path(output_dir)
        self.ensure_dir(output_dir)
        if self.converted_data is None:
            self.converted_data = self.convert()


class ToDMConverter(BaseConverter):
    """Base class for converting external formats to Datamaker format.

    Subclasses convert YOLO, COCO, PASCAL -> DM (v1 or v2).

    Output structure:
    - Categorized: output_dir/{train,valid,test}/json/*.json + original_files/*
    - Non-categorized: output_dir/json/*.json + original_files/*

    Example:
        >>> converter = YOLOToDMConverter(
        ...     root_dir='/data/yolo_dataset',
        ...     is_categorized=True,
        ...     dm_version=DMVersion.V2,
        ... )
        >>> result = converter.convert()
        >>> converter.save_to_folder('/data/dm_output')
    """

    source_format: DatasetFormat
    target_format: DatasetFormat = DatasetFormat.DM_V2

    def __init__(
        self,
        root_dir: str | Path | None = None,
        is_categorized: bool = False,
        is_single_conversion: bool = False,
        dm_version: DMVersion = DMVersion.V2,
    ) -> None:
        """Initialize ToDMConverter.

        Args:
            root_dir: Root directory containing source data.
            is_categorized: Whether dataset has train/valid/test splits.
            is_single_conversion: Whether converting single files only.
            dm_version: Target Datamaker schema version (V1 or V2).
        """
        super().__init__(root_dir, is_categorized, is_single_conversion)
        self.dm_version = dm_version
        self.target_format = DatasetFormat.from_dm_version(dm_version)

    def save_to_folder(self, output_dir: str | Path) -> None:
        """Save converted DM data to folder."""
        output_dir = Path(output_dir)
        self.ensure_dir(output_dir)

        if self.converted_data is None:
            self.converted_data = self.convert()

        if self.is_categorized:
            for split, img_dict in self.converted_data.items():
                split_dir = output_dir / split
                json_dir = self.ensure_dir(split_dir / 'json')
                original_file_dir = self.ensure_dir(split_dir / 'original_files')

                for img_filename, (dm_json, img_src_path) in img_dict.items():
                    json_filename = Path(img_filename).stem + '.json'
                    (json_dir / json_filename).write_text(json.dumps(dm_json, indent=2, ensure_ascii=False))
                    if img_src_path and Path(img_src_path).exists():
                        shutil.copy(img_src_path, original_file_dir / img_filename)
        else:
            json_dir = self.ensure_dir(output_dir / 'json')
            original_file_dir = self.ensure_dir(output_dir / 'original_files')

            for img_filename, (dm_json, img_src_path) in self.converted_data.items():
                json_filename = Path(img_filename).stem + '.json'
                (json_dir / json_filename).write_text(json.dumps(dm_json, indent=2, ensure_ascii=False))
                if img_src_path and Path(img_src_path).exists():
                    shutil.copy(img_src_path, original_file_dir / img_filename)


__all__ = [
    'BaseConverter',
    'DatasetFormat',
    'FromDMConverter',
    'ToDMConverter',
]
