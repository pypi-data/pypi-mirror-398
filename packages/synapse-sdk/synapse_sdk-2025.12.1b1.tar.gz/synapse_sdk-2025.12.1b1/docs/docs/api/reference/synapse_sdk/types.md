---
sidebar_label: types
title: synapse_sdk.types
---

## FileField Objects

```python
class FileField(str)
```

Pydantic field type that automatically downloads files from URLs.

When used as a type annotation in a Pydantic model, URLs are automatically
downloaded during validation and replaced with local file paths.

The downloaded files are cached in /tmp/datamaker/media/ using a hash of
the URL as the filename, preventing redundant downloads.

**Examples**:

  >>> from pydantic import BaseModel
  >>> from synapse_sdk.types import FileField
  >>>
  >>> class InferenceParams(BaseModel):
  ...     input_file: FileField
  ...     config_file: FileField | None = None
  >>>
  >>> # URL is automatically downloaded during validation
  >>> params = InferenceParams(input_file="https://example.com/image.jpg")
  >>> params.input_file  # "/tmp/datamaker/media/abc123def.jpg"
  

**Notes**:

  - Downloads happen synchronously during validation
  - Files are cached by URL hash (same URL = same local path)
  - The field value becomes a string path to the local file

