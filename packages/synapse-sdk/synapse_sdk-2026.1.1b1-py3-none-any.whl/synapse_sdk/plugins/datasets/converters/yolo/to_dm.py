"""Convert YOLO format to Datamaker format.

Supports:
- DMv1 and DMv2 output schemas
- Bounding box, polygon (segmentation), and keypoint annotations
- Categorized (train/valid/test splits) and non-categorized datasets
- Single file conversion mode
"""

from __future__ import annotations

from pathlib import Path
from typing import IO, Any

import yaml

from synapse_sdk.plugins.datasets.converters.base import DatasetFormat, ToDMConverter
from synapse_sdk.plugins.datasets.formats.dm import DMVersion


class YOLOToDMConverter(ToDMConverter):
    """Convert YOLO dataset format to Datamaker format.

    Supports bounding boxes, polygons (YOLO segmentation), and keypoints.
    Outputs either DMv1 or DMv2 schema.

    Example:
        >>> # Directory conversion
        >>> converter = YOLOToDMConverter(
        ...     root_dir='/data/yolo_dataset',
        ...     is_categorized=True,
        ...     dm_version=DMVersion.V2,
        ... )
        >>> converter.convert()
        >>> converter.save_to_folder('/data/dm_output')

        >>> # Single file conversion
        >>> converter = YOLOToDMConverter(
        ...     is_single_conversion=True,
        ...     class_names=['person', 'car'],
        ... )
        >>> result = converter.convert_single_file(label_lines, image_file)
    """

    source_format = DatasetFormat.YOLO

    def __init__(
        self,
        root_dir: str | Path | None = None,
        is_categorized: bool = False,
        is_single_conversion: bool = False,
        dm_version: DMVersion = DMVersion.V2,
        class_names: list[str] | None = None,
    ) -> None:
        """Initialize converter.

        Args:
            root_dir: Root directory containing YOLO data.
            is_categorized: Whether dataset has train/valid/test splits.
            is_single_conversion: Whether converting single files only.
            dm_version: Target Datamaker schema version (V1 or V2).
            class_names: Class names. If not provided, loaded from dataset.yaml.
        """
        super().__init__(root_dir, is_categorized, is_single_conversion, dm_version)
        self.class_names = class_names or []

        # Load class names from dataset.yaml if not provided and not single conversion
        if not class_names and not is_single_conversion and root_dir:
            self._load_class_names()

    def _load_class_names(self) -> None:
        """Load class names from dataset.yaml."""
        yaml_path = self.root_dir / 'dataset.yaml'
        if yaml_path.exists():
            with open(yaml_path, encoding='utf-8') as f:
                config = yaml.safe_load(f)
                self.class_names = config.get('names', [])
        else:
            # Try classes.txt as fallback
            classes_path = self.root_dir / 'classes.txt'
            if classes_path.exists():
                self.class_names = [line.strip() for line in classes_path.read_text().splitlines() if line.strip()]

        if not self.class_names:
            raise FileNotFoundError(
                f'No dataset.yaml or classes.txt found in {self.root_dir}. Provide class_names parameter.'
            )

    def _find_image_dir(self, split_dir: Path) -> Path | None:
        """Find the images directory within a split."""
        for candidate in ['images', 'img', 'imgs']:
            candidate_path = split_dir / candidate
            if candidate_path.is_dir():
                return candidate_path
        return None

    def _parse_yolo_line(
        self,
        line: str,
        img_width: int,
        img_height: int,
    ) -> dict[str, Any] | None:
        """Parse a single YOLO label line.

        Detects format based on number of values:
        - 5 values: bounding box (class cx cy w h)
        - Even values > 5: polygon/segmentation (class x1 y1 x2 y2 ...)
        - 5 + 3*n values: keypoints (class cx cy w h x1 y1 v1 x2 y2 v2 ...)

        Args:
            line: YOLO label line.
            img_width: Image width in pixels.
            img_height: Image height in pixels.

        Returns:
            Parsed annotation dict or None if invalid.
        """
        parts = line.strip().split()
        if len(parts) < 5:
            return None

        class_idx = int(parts[0])
        class_name = self.class_names[class_idx] if class_idx < len(self.class_names) else f'class_{class_idx}'

        num_coords = len(parts) - 1

        # Check if polygon: more than 4 values and even number of coordinates
        if num_coords > 4 and num_coords % 2 == 0:
            # Polygon format: class_id x1 y1 x2 y2 x3 y3 ...
            coords = []
            for i in range(1, len(parts), 2):
                x_norm = float(parts[i])
                y_norm = float(parts[i + 1])
                x_abs = x_norm * img_width
                y_abs = y_norm * img_height
                coords.append([x_abs, y_abs])

            return {
                'type': 'polygon',
                'classification': class_name,
                'data': coords,
            }

        # Check if keypoints: 4 bbox values + 3*n keypoint values
        if num_coords > 4 and (num_coords - 4) % 3 == 0:
            # Keypoint format: class cx cy w h x1 y1 v1 x2 y2 v2 ...
            cx, cy, w, h = map(float, parts[1:5])

            # Denormalize bounding box
            abs_w = w * img_width
            abs_h = h * img_height
            left = (cx - w / 2) * img_width
            top = (cy - h / 2) * img_height

            # Parse keypoints
            keypoints = []
            for i in range(5, len(parts), 3):
                xk = float(parts[i]) * img_width
                yk = float(parts[i + 1]) * img_height
                vk = int(parts[i + 2])
                keypoints.append([xk, yk, vk])

            return {
                'type': 'keypoint',
                'classification': class_name,
                'data': keypoints,
                'bounding_box': [left, top, abs_w, abs_h],
            }

        # Standard bounding box: 5 values
        if num_coords == 4:
            cx, cy, w, h = map(float, parts[1:5])

            # Denormalize: YOLO (cx, cy, w, h) -> (left, top, w, h)
            abs_w = w * img_width
            abs_h = h * img_height
            left = (cx - w / 2) * img_width
            top = (cy - h / 2) * img_height

            return {
                'type': 'bounding_box',
                'classification': class_name,
                'data': [left, top, abs_w, abs_h],
            }

        return None

    def _convert_yolo_split_to_dm(self, split_dir: Path) -> dict[str, tuple[dict, Path]]:
        """Convert a YOLO split directory to DM format.

        Args:
            split_dir: Directory containing images/ and labels/.

        Returns:
            Dict mapping image filename to (dm_json, image_path).
        """
        images_dir = self._find_image_dir(split_dir)
        if not images_dir:
            raise FileNotFoundError(f"No images directory found in {split_dir}. Expected 'images', 'img', or 'imgs'.")

        labels_dir = split_dir / 'labels'
        if not labels_dir.is_dir():
            raise FileNotFoundError(f"No 'labels' directory found in {split_dir}.")

        result: dict[str, tuple[dict, Path]] = {}

        for label_file in labels_dir.glob('*.txt'):
            base = label_file.stem

            # Find corresponding image
            img_path = self.find_image_for_label(base, images_dir)
            if not img_path:
                print(f'[WARNING] Image not found for {label_file.name}, skipping.')
                continue

            img_width, img_height = self.get_image_size(img_path)

            # Parse label file
            label_lines = [line.strip() for line in label_file.read_text().splitlines() if line.strip()]

            # Build DM annotation structure
            dm_json = self._build_dm_json(label_lines, img_width, img_height)
            result[img_path.name] = (dm_json, img_path)

        return result

    def _build_dm_json(
        self,
        label_lines: list[str],
        img_width: int,
        img_height: int,
    ) -> dict[str, Any]:
        """Build DM JSON from YOLO label lines.

        Args:
            label_lines: List of YOLO label lines.
            img_width: Image width.
            img_height: Image height.

        Returns:
            DM format JSON dict.
        """
        if self.dm_version == DMVersion.V2:
            return self._build_dm_v2_json(label_lines, img_width, img_height)
        return self._build_dm_v1_json(label_lines, img_width, img_height)

    def _build_dm_v2_json(
        self,
        label_lines: list[str],
        img_width: int,
        img_height: int,
    ) -> dict[str, Any]:
        """Build DMv2 JSON from YOLO label lines."""
        dm_img: dict[str, list] = {
            'bounding_box': [],
            'polygon': [],
            'keypoint': [],
            'polyline': [],
            'relation': [],
            'group': [],
        }

        for line in label_lines:
            ann = self._parse_yolo_line(line, img_width, img_height)
            if not ann:
                continue

            ann_type = ann['type']
            base_ann = {
                'id': self._generate_unique_id(),
                'classification': ann['classification'],
                'attrs': [],
                'data': ann['data'],
            }

            if ann_type == 'bounding_box':
                dm_img['bounding_box'].append(base_ann)
            elif ann_type == 'polygon':
                dm_img['polygon'].append(base_ann)
            elif ann_type == 'keypoint':
                base_ann['bounding_box'] = ann['bounding_box']
                dm_img['keypoint'].append(base_ann)

        return {
            'classification': {'bounding_box': self.class_names},
            'images': [dm_img],
        }

    def _build_dm_v1_json(
        self,
        label_lines: list[str],
        img_width: int,
        img_height: int,
    ) -> dict[str, Any]:
        """Build DMv1 JSON from YOLO label lines."""
        annotations = []

        for line in label_lines:
            ann = self._parse_yolo_line(line, img_width, img_height)
            if not ann:
                continue

            base_ann = {
                'id': self._generate_unique_id(),
                'tool': ann['type'] if ann['type'] != 'bounding_box' else 'boundingBox',
                'isLocked': False,
                'isVisible': True,
                'classification': {'class': ann['classification']},
                'data': ann['data'],
            }

            if ann['type'] == 'keypoint':
                base_ann['bounding_box'] = ann['bounding_box']

            annotations.append(base_ann)

        return {'annotations': {'image': annotations}}

    def convert(self) -> dict[str, dict] | dict[str, tuple]:
        """Convert YOLO dataset to DM format.

        Returns:
            If categorized: dict mapping split names to image dicts.
            If not categorized: dict mapping image filename to (dm_json, path).
        """
        if self.is_categorized:
            splits = self._validate_splits(['train', 'valid'], ['test'])
            result = {}
            for split, split_dir in splits.items():
                result[split] = self._convert_yolo_split_to_dm(split_dir)
            self.converted_data = result
        else:
            # For non-categorized YOLO, expect images/ and labels/ in root
            result = self._convert_yolo_split_to_dm(self.root_dir)
            self.converted_data = result

        return self.converted_data

    def convert_single_file(
        self,
        data: list[str],
        original_file: IO,
        class_names: list[str] | None = None,
    ) -> dict[str, Any]:
        """Convert a single YOLO label and image to DM format.

        Args:
            data: List of YOLO label lines (from .txt file).
            original_file: Image file object.
            class_names: Optional class names override.

        Returns:
            Dictionary with dm_json, image_path, image_name.
        """
        if not self.is_single_conversion:
            raise RuntimeError('convert_single_file only available when is_single_conversion=True')

        if class_names:
            self.class_names = class_names

        if not self.class_names:
            raise ValueError('class_names must be provided for single file conversion')

        img_path = getattr(original_file, 'name', None)
        if not img_path:
            raise ValueError('original_file must have a "name" attribute.')

        img_width, img_height = self.get_image_size(original_file)

        # Parse label lines
        label_lines = [line.strip() for line in data if line.strip()]
        dm_json = self._build_dm_json(label_lines, img_width, img_height)

        return {
            'dm_json': dm_json,
            'image_path': img_path,
            'image_name': Path(img_path).name,
        }


__all__ = ['YOLOToDMConverter']
