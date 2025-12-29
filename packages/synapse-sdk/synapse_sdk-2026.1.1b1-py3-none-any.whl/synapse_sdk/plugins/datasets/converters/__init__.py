"""Dataset format converters.

Structure:
- base.py: BaseConverter, FromDMConverter, ToDMConverter
- yolo/: YOLO format converters
  - from_dm.py: DM -> YOLO
  - to_dm.py: YOLO -> DM
"""

from synapse_sdk.plugins.datasets.converters.base import (
    BaseConverter,
    DatasetFormat,
    FromDMConverter,
    ToDMConverter,
)
from synapse_sdk.plugins.datasets.converters.yolo import (
    FromDMToYOLOConverter,
    YOLOToDMConverter,
)


def get_converter(
    source: DatasetFormat | str,
    target: DatasetFormat | str,
    **kwargs,
) -> BaseConverter:
    """Get converter for source -> target format conversion.

    Args:
        source: Source dataset format.
        target: Target dataset format.
        **kwargs: Additional arguments passed to converter constructor.

    Returns:
        Converter instance.

    Raises:
        ValueError: If no converter exists for the format pair.

    Example:
        >>> converter = get_converter('dm_v2', 'yolo', is_categorized=True)
        >>> converter.convert()
        >>> converter.save_to_folder('/output')
    """
    source = DatasetFormat(source)
    target = DatasetFormat(target)

    # Map format pairs to converter classes
    converters: dict[tuple[DatasetFormat, DatasetFormat], type[BaseConverter]] = {
        # DM -> YOLO
        (DatasetFormat.DM_V1, DatasetFormat.YOLO): FromDMToYOLOConverter,
        (DatasetFormat.DM_V2, DatasetFormat.YOLO): FromDMToYOLOConverter,
        # YOLO -> DM
        (DatasetFormat.YOLO, DatasetFormat.DM_V1): YOLOToDMConverter,
        (DatasetFormat.YOLO, DatasetFormat.DM_V2): YOLOToDMConverter,
    }

    converter_cls = converters.get((source, target))
    if converter_cls is None:
        raise ValueError(f'No converter available for {source} -> {target}')

    return converter_cls(**kwargs)


__all__ = [
    # Base classes
    'BaseConverter',
    'DatasetFormat',
    'FromDMConverter',
    'ToDMConverter',
    # YOLO converters
    'FromDMToYOLOConverter',
    'YOLOToDMConverter',
    # Factory
    'get_converter',
]
