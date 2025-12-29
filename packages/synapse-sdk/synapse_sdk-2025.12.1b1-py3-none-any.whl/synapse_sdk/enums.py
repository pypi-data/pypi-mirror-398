from __future__ import annotations

from typing import Any

from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

from synapse_sdk.utils.file import download_file, get_temp_path


class FileField(str):
    """Pydantic field type that automatically downloads files from URLs.

    When used as a type annotation in a Pydantic model, URLs are automatically
    downloaded during validation and replaced with local file paths.

    The downloaded files are cached in /tmp/datamaker/media/ using a hash of
    the URL as the filename, preventing redundant downloads.

    Examples:
        >>> from pydantic import BaseModel
        >>> from synapse_sdk.enums import FileField
        >>>
        >>> class InferenceParams(BaseModel):
        ...     input_file: FileField
        ...     config_file: FileField | None = None
        >>>
        >>> # URL is automatically downloaded during validation
        >>> params = InferenceParams(input_file="https://example.com/image.jpg")
        >>> params.input_file  # "/tmp/datamaker/media/abc123def.jpg"

    Note:
        - Downloads happen synchronously during validation
        - Files are cached by URL hash (same URL = same local path)
        - The field value becomes a string path to the local file
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        return core_schema.with_info_before_validator_function(
            cls._validate,
            core_schema.str_schema(),
        )

    @classmethod
    def _validate(cls, value: Any, info: core_schema.ValidationInfo) -> str:
        """Download the file from URL and return local path.

        Args:
            value: The URL string to download from.
            info: Pydantic validation context (unused but required by protocol).

        Returns:
            String path to the downloaded local file.

        Raises:
            requests.HTTPError: If download fails.
            ValueError: If value is not a valid URL string.
        """
        if not isinstance(value, str):
            raise ValueError(f'FileField expects a URL string, got {type(value).__name__}')

        if not value:
            raise ValueError('FileField URL cannot be empty')

        path_download = get_temp_path('media')
        path_download.mkdir(parents=True, exist_ok=True)

        return str(download_file(value, path_download))


__all__ = ['FileField']
