"""Convert Datamaker format to YOLO format.

Supports:
- DMv1 and DMv2 schemas
- Bounding box, polygon, and keypoint annotations
- Categorized (train/valid/test splits) and non-categorized datasets
- Single file conversion mode
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import IO, Any

from synapse_sdk.plugins.datasets.converters.base import DatasetFormat, FromDMConverter
from synapse_sdk.plugins.datasets.formats.dm import DMVersion


class FromDMToYOLOConverter(FromDMConverter):
    """Convert Datamaker dataset format to YOLO format.

    Supports bounding boxes, polygons (native YOLO segmentation format),
    and keypoints. Works with both DMv1 and DMv2 schemas.

    Example:
        >>> # Directory conversion
        >>> converter = FromDMToYOLOConverter(
        ...     root_dir='/data/dm_dataset',
        ...     is_categorized=True,
        ...     dm_version=DMVersion.V2,
        ... )
        >>> converter.convert()
        >>> converter.save_to_folder('/data/yolo_output')

        >>> # Single file conversion
        >>> converter = FromDMToYOLOConverter(is_single_conversion=True)
        >>> result = converter.convert_single_file(dm_json, image_file)
    """

    target_format = DatasetFormat.YOLO

    def __init__(
        self,
        root_dir: str | Path | None = None,
        is_categorized: bool = False,
        is_single_conversion: bool = False,
        dm_version: DMVersion = DMVersion.V2,
    ) -> None:
        """Initialize converter.

        Args:
            root_dir: Root directory containing DM data.
            is_categorized: Whether dataset has train/valid/test splits.
            is_single_conversion: Whether converting single files only.
            dm_version: Datamaker schema version (V1 or V2).
        """
        super().__init__(root_dir, is_categorized, is_single_conversion, dm_version)
        self.dataset_yaml_content: str = ''

    @staticmethod
    def get_all_classes(list_of_dirs: list[Path], dm_version: DMVersion = DMVersion.V2) -> list[str]:
        """Collect all unique class names from directories.

        Args:
            list_of_dirs: List of directories to scan.
            dm_version: Datamaker schema version.

        Returns:
            Sorted list of unique class names.
        """
        classes: set[str] = set()

        for d in list_of_dirs:
            if not d or not d.is_dir():
                continue

            json_dir = d / 'json' if (d / 'json').is_dir() else d

            for jfile in json_dir.glob('*.json'):
                with open(jfile, encoding='utf-8') as f:
                    data = json.load(f)

                if dm_version == DMVersion.V2:
                    for img_ann in data.get('images', []):
                        for key in ['bounding_box', 'polygon', 'keypoint']:
                            for ann in img_ann.get(key, []):
                                if 'classification' in ann:
                                    classes.add(ann['classification'])
                else:
                    # V1: annotations keyed by asset
                    for anns in data.get('annotations', {}).values():
                        for ann in anns:
                            classification = ann.get('classification', {})
                            if isinstance(classification, dict):
                                for val in classification.values():
                                    if isinstance(val, str):
                                        classes.add(val)

        return sorted(classes)

    @staticmethod
    def polygon_to_yolo_string(polygon: list, width: int, height: int) -> str:
        """Convert polygon points to normalized YOLO segmentation format.

        YOLO segmentation format: x1 y1 x2 y2 x3 y3 ... (normalized 0-1)

        Args:
            polygon: List of [x, y] points.
            width: Image width in pixels.
            height: Image height in pixels.

        Returns:
            Space-separated normalized coordinate string.
        """
        if not polygon:
            return ''

        coords = []
        for point in polygon:
            x, y = point[0], point[1]
            x_norm = x / width
            y_norm = y / height
            coords.extend([f'{x_norm:.6f}', f'{y_norm:.6f}'])

        return ' '.join(coords)

    @staticmethod
    def keypoints_to_yolo_string(keypoints: list, width: int, height: int) -> str:
        """Convert keypoints to normalized YOLO keypoint format.

        YOLO keypoint format: x1 y1 v1 x2 y2 v2 ... (normalized, v=visibility)

        Args:
            keypoints: List of [x, y, visibility] points.
            width: Image width in pixels.
            height: Image height in pixels.

        Returns:
            Space-separated normalized coordinate string with visibility.
        """
        kp_strs = []
        for kp in keypoints:
            x, y = kp[0], kp[1]
            v = kp[2] if len(kp) > 2 else 2  # Default visible
            x_norm = x / width
            y_norm = y / height
            kp_strs.extend([f'{x_norm:.6f}', f'{y_norm:.6f}', str(int(v))])
        return ' '.join(kp_strs)

    def _convert_split_dir(self, split_dir: Path, split_name: str) -> list[dict[str, Any]]:
        """Convert one split folder to YOLO format."""
        if self.class_map is None:
            raise ValueError('class_map not initialized. Call convert() first.')

        json_dir = split_dir / 'json'
        img_dir = split_dir / 'original_files'
        entries = []

        for jfile in json_dir.glob('*.json'):
            base = jfile.stem

            # Find corresponding image
            img_path = self.find_image_for_label(base, img_dir)
            if not img_path:
                print(f'[{split_name}] Image for {base} not found, skipping.')
                continue

            width, height = self.get_image_size(img_path)

            with open(jfile, encoding='utf-8') as f:
                data = json.load(f)

            label_lines = self._convert_dm_json_to_yolo_lines(data, width, height)

            entries.append({
                'img_path': img_path,
                'img_name': img_path.name,
                'label_name': f'{base}.txt',
                'label_lines': label_lines,
            })

        return entries

    def _convert_root_dir(self) -> list[dict[str, Any]]:
        """Convert non-categorized dataset to YOLO format."""
        return self._convert_split_dir(self.root_dir, 'root')

    def _convert_dm_json_to_yolo_lines(
        self,
        data: dict[str, Any],
        width: int,
        height: int,
    ) -> list[str]:
        """Convert DM JSON data to YOLO label lines."""
        label_lines = []

        if self.dm_version == DMVersion.V2:
            if 'images' in data and data['images']:
                img_ann = data['images'][0]
                label_lines.extend(self._convert_v2_annotations(img_ann, width, height))
        else:
            # V1: annotations keyed by asset
            for anns in data.get('annotations', {}).values():
                label_lines.extend(self._convert_v1_annotations(anns, width, height))

        return label_lines

    def _convert_v2_annotations(
        self,
        img_ann: dict[str, Any],
        width: int,
        height: int,
    ) -> list[str]:
        """Convert DMv2 image annotations to YOLO lines."""
        lines = []

        # Bounding boxes
        for box in img_ann.get('bounding_box', []):
            classification = box.get('classification')
            if classification not in self.class_map:
                continue

            cidx = self.class_map[classification]
            x, y, w, h = box['data']

            # Convert to YOLO format: center_x, center_y, width, height (normalized)
            cx = (x + w / 2) / width
            cy = (y + h / 2) / height
            nw = w / width
            nh = h / height

            lines.append(f'{cidx} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}')

        # Polygons (YOLO segmentation format)
        for poly in img_ann.get('polygon', []):
            classification = poly.get('classification')
            if classification not in self.class_map:
                continue

            cidx = self.class_map[classification]
            poly_str = self.polygon_to_yolo_string(poly['data'], width, height)
            if poly_str:
                lines.append(f'{cidx} {poly_str}')

        # Keypoints
        for kp in img_ann.get('keypoint', []):
            classification = kp.get('classification')
            if classification not in self.class_map:
                continue

            cidx = self.class_map[classification]

            # Get bounding box for keypoint (required for YOLO pose)
            if 'bounding_box' in kp:
                bbox = kp['bounding_box']
                if isinstance(bbox, dict):
                    x, y, w, h = bbox['x'], bbox['y'], bbox['width'], bbox['height']
                else:
                    x, y, w, h = bbox
                cx = (x + w / 2) / width
                cy = (y + h / 2) / height
                nw = w / width
                nh = h / height
            else:
                # Fallback to full image
                cx, cy, nw, nh = 0.5, 0.5, 1.0, 1.0

            kp_str = self.keypoints_to_yolo_string(kp['data'], width, height)
            lines.append(f'{cidx} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f} {kp_str}')

        return lines

    def _convert_v1_annotations(
        self,
        annotations: list[dict[str, Any]],
        width: int,
        height: int,
    ) -> list[str]:
        """Convert DMv1 annotations to YOLO lines."""
        lines = []

        for ann in annotations:
            tool = ann.get('tool', '')

            # Get class name from classification
            class_name = None
            classification = ann.get('classification', {})
            if isinstance(classification, dict):
                class_name = classification.get('class') or classification.get('label')
                if not class_name:
                    for val in classification.values():
                        if isinstance(val, str):
                            class_name = val
                            break

            if not class_name or class_name not in self.class_map:
                continue

            cidx = self.class_map[class_name]
            data = ann.get('data') or ann.get('points')
            if not data:
                continue

            if tool in ('boundingBox', 'bounding_box'):
                if isinstance(data, dict):
                    x, y, w, h = data['x'], data['y'], data['width'], data['height']
                else:
                    x, y, w, h = data

                cx = (x + w / 2) / width
                cy = (y + h / 2) / height
                nw = w / width
                nh = h / height
                lines.append(f'{cidx} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}')

            elif tool == 'polygon':
                poly_str = self.polygon_to_yolo_string(data, width, height)
                if poly_str:
                    lines.append(f'{cidx} {poly_str}')

            elif tool == 'keypoint':
                bbox = ann.get('bounding_box')
                if bbox:
                    if isinstance(bbox, dict):
                        x, y, w, h = bbox['x'], bbox['y'], bbox['width'], bbox['height']
                    else:
                        x, y, w, h = bbox
                    cx = (x + w / 2) / width
                    cy = (y + h / 2) / height
                    nw = w / width
                    nh = h / height
                else:
                    cx, cy, nw, nh = 0.5, 0.5, 1.0, 1.0

                kp_str = self.keypoints_to_yolo_string(data, width, height)
                lines.append(f'{cidx} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f} {kp_str}')

        return lines

    def convert(self) -> dict[str, list[dict[str, Any]]] | list[dict[str, Any]]:
        """Convert DM format to YOLO format.

        Returns:
            If categorized: dict mapping split names to list of entries.
            If not categorized: list of entries.
            Each entry contains img_path, img_name, label_name, label_lines.
        """
        yaml_lines = [f'path: {self.root_dir}']

        if self.is_categorized:
            splits = self._validate_splits(['train', 'valid'], ['test'])
            self.class_names = self.get_all_classes(list(splits.values()), self.dm_version)
            self.class_map = {name: idx for idx, name in enumerate(self.class_names)}

            result = {}
            for split, split_dir in splits.items():
                result[split] = self._convert_split_dir(split_dir, split)
            self.converted_data = result

            yaml_lines.append('train: train/images')
            yaml_lines.append('val: valid/images')
            if 'test' in splits:
                yaml_lines.append('test: test/images')
        else:
            self._validate_splits([], [])
            self.class_names = self.get_all_classes([self.root_dir], self.dm_version)
            self.class_map = {name: idx for idx, name in enumerate(self.class_names)}

            result = self._convert_root_dir()
            self.converted_data = result

            yaml_lines.append('train: images')
            yaml_lines.append('val: images')

        yaml_lines.extend(['', f'nc: {len(self.class_names)}', f'names: {self.class_names}', ''])
        self.dataset_yaml_content = '\n'.join(yaml_lines)

        return self.converted_data

    def save_to_folder(self, output_dir: str | Path | None = None) -> None:
        """Save converted YOLO data to folder.

        Args:
            output_dir: Output directory. Defaults to root_dir.
        """
        output_dir = Path(output_dir) if output_dir else self.root_dir
        self.ensure_dir(output_dir)

        if self.converted_data is None:
            self.converted_data = self.convert()

        if self.is_categorized:
            for split, entries in self.converted_data.items():
                split_imgs = self.ensure_dir(output_dir / split / 'images')
                split_labels = self.ensure_dir(output_dir / split / 'labels')

                for entry in entries:
                    shutil.copy(entry['img_path'], split_imgs / entry['img_name'])
                    (split_labels / entry['label_name']).write_text('\n'.join(entry['label_lines']))
        else:
            imgs_dir = self.ensure_dir(output_dir / 'images')
            labels_dir = self.ensure_dir(output_dir / 'labels')

            for entry in self.converted_data:
                shutil.copy(entry['img_path'], imgs_dir / entry['img_name'])
                (labels_dir / entry['label_name']).write_text('\n'.join(entry['label_lines']))

        # Write dataset.yaml and classes.txt
        (output_dir / 'dataset.yaml').write_text(self.dataset_yaml_content)
        (output_dir / 'classes.txt').write_text('\n'.join(self.class_names) + '\n')

    def convert_single_file(
        self,
        data: dict[str, Any],
        original_file: IO,
        class_names: list[str] | None = None,
    ) -> dict[str, Any]:
        """Convert a single DM JSON and image to YOLO format.

        Args:
            data: DM format JSON data.
            original_file: Image file object.
            class_names: Optional class names. If not provided, extracted from data.

        Returns:
            Dictionary with label_lines, class_names, class_map.
        """
        if not self.is_single_conversion:
            raise RuntimeError('convert_single_file only available when is_single_conversion=True')

        # Extract class names if not provided
        if class_names is None:
            class_names = []
            classes: set[str] = set()

            if self.dm_version == DMVersion.V2:
                for img_ann in data.get('images', []):
                    for key in ['bounding_box', 'polygon', 'keypoint']:
                        for ann in img_ann.get(key, []):
                            if 'classification' in ann:
                                classes.add(ann['classification'])
            else:
                for anns in data.get('annotations', {}).values():
                    for ann in anns:
                        classification = ann.get('classification', {})
                        if isinstance(classification, dict):
                            for val in classification.values():
                                if isinstance(val, str):
                                    classes.add(val)

            class_names = sorted(classes)

        self.class_names = class_names
        self.class_map = {name: idx for idx, name in enumerate(class_names)}

        width, height = self.get_image_size(original_file)
        label_lines = self._convert_dm_json_to_yolo_lines(data, width, height)

        return {
            'label_lines': label_lines,
            'class_names': class_names,
            'class_map': self.class_map,
        }


__all__ = ['FromDMToYOLOConverter']
