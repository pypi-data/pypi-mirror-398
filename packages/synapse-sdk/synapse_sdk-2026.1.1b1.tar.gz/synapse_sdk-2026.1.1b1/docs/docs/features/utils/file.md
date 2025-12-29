---
id: file
title: File Utilities
sidebar_position: 1
---

# File Utilities

Comprehensive file operations and handling utilities organized in a modular structure for better maintainability and functionality.

## Module Overview

The file utilities have been refactored into a modular structure with specialized modules for different operations:

- **`synapse_sdk.utils.file.archive`** - ZIP archive creation and extraction
- **`synapse_sdk.utils.file.checksum`** - File hash calculations and verification
- **`synapse_sdk.utils.file.chunking`** - Memory-efficient file reading in chunks
- **`synapse_sdk.utils.file.download`** - File downloading utilities with async support
- **`synapse_sdk.utils.file.encoding`** - Base64 encoding and file format handling
- **`synapse_sdk.utils.file.io`** - General I/O operations for JSON/YAML files
- **`synapse_sdk.utils.file.video`** - Video transcoding and format conversion

### Backward Compatibility

All functions remain accessible from the main module import:

```python
# Both approaches work identically
from synapse_sdk.utils.file import read_file_in_chunks, download_file
from synapse_sdk.utils.file.chunking import read_file_in_chunks
from synapse_sdk.utils.file.download import download_file
```

## Archive Operations

Functions for creating and extracting ZIP archives.

```python
from synapse_sdk.utils.file.archive import archive, unarchive

# Create archive
archive('/path/to/directory', '/path/to/output.zip')

# Extract archive
unarchive('/path/to/archive.zip', '/path/to/extract/directory')
```

## Chunked File Operations

### read_file_in_chunks

Read files in chunks for efficient memory usage, particularly useful for large files or when processing files in chunks for uploading or hashing.

```python
from synapse_sdk.utils.file.chunking import read_file_in_chunks

# Read a file in default 50MB chunks
for chunk in read_file_in_chunks('/path/to/large_file.bin'):
    process_chunk(chunk)

# Read with custom chunk size (10MB)
for chunk in read_file_in_chunks('/path/to/file.bin', chunk_size=1024*1024*10):
    upload_chunk(chunk)
```

**Parameters:**

- `file_path` (str | Path): Path to the file to read
- `chunk_size` (int, optional): Size of each chunk in bytes. Defaults to 50MB (52,428,800 bytes)

**Returns:**

- Generator yielding file content chunks as bytes

**Raises:**

- `FileNotFoundError`: If the file doesn't exist
- `PermissionError`: If the file can't be read due to permissions
- `OSError`: If there's an OS-level error reading the file

### Use Cases

**Large File Processing**: Efficiently process files that are too large to fit in memory:

```python
import hashlib

def calculate_hash_for_large_file(file_path):
    hash_md5 = hashlib.md5()
    for chunk in read_file_in_chunks(file_path):
        hash_md5.update(chunk)
    return hash_md5.hexdigest()
```

**Chunked Upload Integration**: The function integrates seamlessly with the `CoreClientMixin.create_chunked_upload` method:

```python
from synapse_sdk.clients.backend.core import CoreClientMixin

client = CoreClientMixin(base_url='https://api.example.com')
result = client.create_chunked_upload('/path/to/large_file.zip')
```

**Best Practices:**

- Use default chunk size (50MB) for optimal upload performance
- Adjust chunk size based on available memory and network conditions
- For very large files (>1GB), consider using smaller chunks for better progress tracking
- Always handle exceptions when working with file operations

## Checksum Functions

### calculate_checksum

Calculate checksum for regular files:

```python
from synapse_sdk.utils.file.checksum import calculate_checksum

checksum = calculate_checksum('/path/to/file.bin')
```

### get_checksum_from_file

Calculate checksum for file-like objects without requiring Django dependencies. This function works with any file-like object that has a `read()` method, making it compatible with Django's File objects, BytesIO, StringIO, and regular file objects.

```python
import hashlib
from io import BytesIO
from synapse_sdk.utils.file.checksum import get_checksum_from_file

# Basic usage with BytesIO (defaults to SHA1)
data = BytesIO(b'Hello, world!')
checksum = get_checksum_from_file(data)
print(checksum)  # SHA1 hash as hexadecimal string

# Using different hash algorithms
checksum_md5 = get_checksum_from_file(data, digest_mod=hashlib.md5)
checksum_sha256 = get_checksum_from_file(data, digest_mod=hashlib.sha256)

# With real file objects
with open('/path/to/file.txt', 'rb') as f:
    checksum = get_checksum_from_file(f)
```

**Parameters:**

- `file` (IO[Any]): File-like object with read() method that supports reading in chunks
- `digest_mod` (Callable[[], Any], optional): Hash algorithm from hashlib. Defaults to `hashlib.sha1`

**Returns:**

- `str`: Hexadecimal digest of the file contents

**Key Features:**

- **Memory Efficient**: Reads files in 4KB chunks to handle large files
- **Automatic File Pointer Reset**: Resets to beginning if the file object supports seeking
- **Text/Binary Agnostic**: Handles both text (StringIO) and binary (BytesIO) file objects
- **No Django Dependency**: Works without Django while being compatible with Django File objects
- **Flexible Hash Algorithms**: Supports any hashlib algorithm (SHA1, SHA256, MD5, etc.)

## Download Functions

Utilities for downloading files from URLs with both synchronous and asynchronous support.

```python
from synapse_sdk.utils.file.download import download_file, adownload_file

# Synchronous download
local_path = download_file(url, destination)

# Asynchronous download
import asyncio
local_path = await adownload_file(url, destination)

# URL to path conversion for multiple files
from synapse_sdk.utils.file.download import files_url_to_path
paths = files_url_to_path(url_list, destination_directory)
```

## Encoding Functions

Base64 encoding utilities for files.

```python
from synapse_sdk.utils.file.encoding import convert_file_to_base64

# Convert file to base64
base64_data = convert_file_to_base64('/path/to/file.jpg')
```

## I/O Functions

General I/O operations for structured data files.

```python
from synapse_sdk.utils.file.io import get_dict_from_file, get_temp_path

# Load dictionary from JSON or YAML file
config = get_dict_from_file('/path/to/config.json')
settings = get_dict_from_file('/path/to/settings.yaml')

# Get temporary file path
temp_path = get_temp_path()
temp_subpath = get_temp_path('subdir/file.tmp')
```

## Video Transcoding

Advanced video transcoding capabilities using FFmpeg for format conversion, compression, and optimization.

### Requirements

- **ffmpeg-python**: `pip install ffmpeg-python`
- **FFmpeg**: Must be installed on the system and available in PATH

### Supported Video Formats

The video module supports a wide range of input formats:
- **MP4** (.mp4, .m4v)
- **AVI** (.avi)
- **MOV** (.mov)
- **MKV** (.mkv)
- **WebM** (.webm)
- **FLV** (.flv)
- **WMV** (.wmv)
- **MPEG** (.mpeg, .mpg)
- **3GP** (.3gp)
- **OGV** (.ogv)

### Core Functions

#### validate_video_format

Check if a file has a supported video format:

```python
from synapse_sdk.utils.file.video.transcode import validate_video_format

if validate_video_format('video.mp4'):
    print("Supported format")
else:
    print("Unsupported format")
```

#### get_video_info

Extract metadata from video files:

```python
from synapse_sdk.utils.file.video.transcode import get_video_info

info = get_video_info('input.mp4')
print(f"Duration: {info['duration']} seconds")
print(f"Resolution: {info['width']}x{info['height']}")
print(f"Video Codec: {info['video_codec']}")
print(f"Audio Codec: {info['audio_codec']}")
print(f"FPS: {info['fps']}")
```

#### transcode_video

Main transcoding function with extensive configuration options:

```python
from synapse_sdk.utils.file.video.transcode import transcode_video, TranscodeConfig
from pathlib import Path

# Basic transcoding with default settings
output_path = transcode_video('input.avi', 'output.mp4')

# Custom configuration
config = TranscodeConfig(
    vcodec='libx264',     # Video codec
    preset='fast',        # Encoding speed vs quality
    crf=20,              # Quality (lower = better quality)
    acodec='aac',        # Audio codec
    audio_bitrate='128k', # Audio bitrate
    resolution='1920x1080', # Output resolution
    fps=30,              # Frame rate
    start_time=10.0,     # Start from 10 seconds
    duration=60.0        # Only process 60 seconds
)

output_path = transcode_video('input.mkv', 'output.mp4', config)
```

#### TranscodeConfig Options

```python
@dataclass
class TranscodeConfig:
    vcodec: str = 'libx264'           # Video codec (libx264, libx265, etc.)
    preset: str = 'medium'            # Encoding preset (fast, medium, slow)
    crf: int = 28                     # Quality factor (0-51, lower = better)
    acodec: str = 'aac'              # Audio codec (aac, opus, etc.)
    audio_bitrate: str = '128k'       # Audio bitrate
    movflags: str = '+faststart'      # MP4 optimization flags
    resolution: Optional[str] = None  # Output resolution (e.g., '1920x1080')
    fps: Optional[int] = None         # Output frame rate
    start_time: Optional[float] = None # Start time in seconds
    duration: Optional[float] = None   # Duration to process in seconds
```

#### Progress Callback Support

Monitor transcoding progress with callback functions:

```python
def progress_callback(progress_percent):
    print(f"Progress: {progress_percent:.1f}%")

output_path = transcode_video(
    'input.mp4',
    'output.mp4',
    progress_callback=progress_callback
)
```

#### optimize_for_web

Quick web optimization with predefined settings:

```python
from synapse_sdk.utils.file.video.transcode import optimize_for_web

# Optimized for web streaming with fast start
web_video = optimize_for_web('input.mov', 'web_output.mp4')
```

This function uses optimized settings:
- Fast encoding preset
- Web-friendly compression (CRF 23)
- Fast start flag for streaming
- Fragment keyframes for better web compatibility

### Error Handling

The video module provides specific exceptions:

```python
from synapse_sdk.utils.file.video.transcode import (
    VideoTranscodeError,
    UnsupportedFormatError,
    FFmpegNotFoundError,
    TranscodingFailedError
)

try:
    transcode_video('input.xyz', 'output.mp4')
except UnsupportedFormatError:
    print("Input format not supported")
except FFmpegNotFoundError:
    print("FFmpeg not installed")
except TranscodingFailedError as e:
    print(f"Transcoding failed: {e}")
```

### Advanced Usage Examples

**Batch Processing**:

```python
import os
from pathlib import Path

input_dir = Path('/path/to/videos')
output_dir = Path('/path/to/output')

for video_file in input_dir.glob('*'):
    if validate_video_format(video_file):
        output_file = output_dir / f"{video_file.stem}.mp4"
        try:
            transcode_video(video_file, output_file)
            print(f"Processed: {video_file.name}")
        except VideoTranscodeError as e:
            print(f"Failed to process {video_file.name}: {e}")
```

**Quality Optimization**:

```python
# High quality for archival
archive_config = TranscodeConfig(
    preset='slow',
    crf=18,
    audio_bitrate='256k'
)

# Small size for mobile
mobile_config = TranscodeConfig(
    preset='fast',
    crf=28,
    resolution='1280x720',
    audio_bitrate='96k'
)

# Apply different configs
archive_output = transcode_video(input_file, 'archive.mp4', archive_config)
mobile_output = transcode_video(input_file, 'mobile.mp4', mobile_config)
```

**Video Clipping**:

```python
# Extract 30-second clip starting from 1 minute
clip_config = TranscodeConfig(
    start_time=60.0,    # Start at 1 minute
    duration=30.0,      # Extract 30 seconds
    crf=20             # High quality
)

clip = transcode_video('long_video.mp4', 'clip.mp4', clip_config)
```