"""YOLO format Pydantic models.

Supports standard YOLO detection format with normalized coordinates.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class YOLOAnnotation(BaseModel):
    """Single YOLO annotation line.

    YOLO format uses normalized center coordinates:
    `class_id cx cy w h`

    All coordinates are normalized to [0, 1] range.

    Attributes:
        class_id: Class index (0-based).
        cx: Normalized center x coordinate.
        cy: Normalized center y coordinate.
        w: Normalized width.
        h: Normalized height.
    """

    class_id: int = Field(ge=0)
    cx: float = Field(ge=0, le=1)
    cy: float = Field(ge=0, le=1)
    w: float = Field(ge=0, le=1)
    h: float = Field(ge=0, le=1)

    def to_line(self) -> str:
        """Convert to YOLO label line format.

        Returns:
            String in format: `class_id cx cy w h`
        """
        return f'{self.class_id} {self.cx:.6f} {self.cy:.6f} {self.w:.6f} {self.h:.6f}'

    @classmethod
    def from_line(cls, line: str) -> YOLOAnnotation:
        """Parse from YOLO label line.

        Args:
            line: String in format: `class_id cx cy w h`

        Returns:
            YOLOAnnotation instance.
        """
        parts = line.strip().split()
        return cls(
            class_id=int(parts[0]),
            cx=float(parts[1]),
            cy=float(parts[2]),
            w=float(parts[3]),
            h=float(parts[4]),
        )

    def to_absolute(self, width: int, height: int) -> tuple[float, float, float, float]:
        """Convert to absolute pixel coordinates.

        Args:
            width: Image width in pixels.
            height: Image height in pixels.

        Returns:
            Tuple of (x, y, w, h) in absolute coordinates.
        """
        abs_w = self.w * width
        abs_h = self.h * height
        abs_x = (self.cx * width) - (abs_w / 2)
        abs_y = (self.cy * height) - (abs_h / 2)
        return abs_x, abs_y, abs_w, abs_h

    @classmethod
    def from_absolute(
        cls,
        class_id: int,
        x: float,
        y: float,
        w: float,
        h: float,
        img_width: int,
        img_height: int,
    ) -> YOLOAnnotation:
        """Create from absolute pixel coordinates.

        Args:
            class_id: Class index.
            x: Top-left x coordinate.
            y: Top-left y coordinate.
            w: Box width.
            h: Box height.
            img_width: Image width in pixels.
            img_height: Image height in pixels.

        Returns:
            YOLOAnnotation with normalized coordinates.
        """
        cx = (x + w / 2) / img_width
        cy = (y + h / 2) / img_height
        nw = w / img_width
        nh = h / img_height
        return cls(class_id=class_id, cx=cx, cy=cy, w=nw, h=nh)


class YOLODatasetConfig(BaseModel):
    """YOLO dataset.yaml configuration.

    Standard YOLO dataset configuration file structure.

    Attributes:
        path: Root path to dataset.
        train: Relative path to training images.
        val: Relative path to validation images.
        test: Optional relative path to test images.
        nc: Number of classes.
        names: List of class names.
    """

    path: str = '.'
    train: str = 'train/images'
    val: str = 'valid/images'
    test: str | None = None
    nc: int
    names: list[str]

    def to_yaml(self) -> str:
        """Convert to YAML string.

        Returns:
            YAML-formatted string for dataset.yaml.
        """
        lines = [
            f'path: {self.path}',
            f'train: {self.train}',
            f'val: {self.val}',
        ]
        if self.test:
            lines.append(f'test: {self.test}')
        lines.extend([
            '',
            f'nc: {self.nc}',
            f'names: {self.names}',
            '',
        ])
        return '\n'.join(lines)

    @classmethod
    def from_yaml(cls, yaml_path: Path | str) -> YOLODatasetConfig:
        """Load from YAML file.

        Args:
            yaml_path: Path to dataset.yaml file.

        Returns:
            YOLODatasetConfig instance.
        """
        import yaml

        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        return cls(
            path=data.get('path', '.'),
            train=data.get('train', 'train/images'),
            val=data.get('val', 'valid/images'),
            test=data.get('test'),
            nc=data['nc'],
            names=data['names'],
        )


class YOLOImage(BaseModel):
    """YOLO image with its label file content.

    Represents a single image and its annotations.

    Attributes:
        image_path: Path to the image file.
        annotations: List of YOLO annotations.
    """

    image_path: Path
    annotations: list[YOLOAnnotation] = Field(default_factory=list)

    def to_label_content(self) -> str:
        """Convert annotations to label file content.

        Returns:
            Newline-separated YOLO annotation lines.
        """
        return '\n'.join(ann.to_line() for ann in self.annotations)

    @classmethod
    def from_label_file(cls, image_path: Path, label_path: Path) -> YOLOImage:
        """Load from image and label file pair.

        Args:
            image_path: Path to image file.
            label_path: Path to corresponding label file.

        Returns:
            YOLOImage instance.
        """
        annotations = []
        if label_path.exists():
            for line in label_path.read_text().strip().splitlines():
                if line.strip():
                    annotations.append(YOLOAnnotation.from_line(line))
        return cls(image_path=image_path, annotations=annotations)


class YOLODataset(BaseModel):
    """Full YOLO dataset structure.

    Contains configuration and images for all splits.

    Attributes:
        config: Dataset configuration (dataset.yaml content).
        train_images: Training images with annotations.
        val_images: Validation images with annotations.
        test_images: Test images with annotations (optional).
    """

    config: YOLODatasetConfig
    train_images: list[YOLOImage] = Field(default_factory=list)
    val_images: list[YOLOImage] = Field(default_factory=list)
    test_images: list[YOLOImage] = Field(default_factory=list)


__all__ = [
    'YOLOAnnotation',
    'YOLODataset',
    'YOLODatasetConfig',
    'YOLOImage',
]
