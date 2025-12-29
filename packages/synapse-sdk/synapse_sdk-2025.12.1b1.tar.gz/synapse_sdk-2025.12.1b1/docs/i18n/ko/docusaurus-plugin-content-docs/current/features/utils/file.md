---
id: file
title: 파일 유틸리티
sidebar_position: 1
---

# 파일 유틸리티

더 나은 유지보수성과 기능성을 위해 모듈형 구조로 구성된 포괄적인 파일 작업 및 처리 유틸리티입니다.

## 모듈 개요

파일 유틸리티는 다양한 작업을 위한 전문화된 모듈로 구성된 모듈형 구조로 리팩토링되었습니다:

- **`synapse_sdk.utils.file.archive`** - ZIP 아카이브 생성 및 추출
- **`synapse_sdk.utils.file.checksum`** - 파일 해시 계산 및 검증
- **`synapse_sdk.utils.file.chunking`** - 메모리 효율적인 청크 단위 파일 읽기
- **`synapse_sdk.utils.file.download`** - 비동기 지원을 포함한 파일 다운로드 유틸리티
- **`synapse_sdk.utils.file.encoding`** - Base64 인코딩 및 파일 형식 처리
- **`synapse_sdk.utils.file.io`** - JSON/YAML 파일용 일반 I/O 작업
- **`synapse_sdk.utils.file.video`** - 비디오 트랜스코딩 및 형식 변환

### 하위 호환성

모든 함수는 메인 모듈 임포트를 통해 여전히 액세스할 수 있습니다:

```python
# 두 방법 모두 동일하게 작동합니다
from synapse_sdk.utils.file import read_file_in_chunks, download_file
from synapse_sdk.utils.file.chunking import read_file_in_chunks
from synapse_sdk.utils.file.download import download_file
```

## 아카이브 작업

ZIP 아카이브를 생성하고 추출하는 함수입니다.

```python
from synapse_sdk.utils.file.archive import archive, unarchive

# 아카이브 생성
archive('/path/to/directory', '/path/to/output.zip')

# 아카이브 추출
unarchive('/path/to/archive.zip', '/path/to/extract/directory')
```

## 청크 파일 작업

### read_file_in_chunks

효율적인 메모리 사용을 위해 파일을 청크 단위로 읽습니다. 대용량 파일이나 업로드 또는 해싱을 위해 파일을 청크 단위로 처리할 때 특히 유용합니다.

```python
from synapse_sdk.utils.file.chunking import read_file_in_chunks

# 기본 50MB 청크로 파일 읽기
for chunk in read_file_in_chunks('/path/to/large_file.bin'):
    process_chunk(chunk)

# 사용자 정의 청크 크기로 읽기 (10MB)
for chunk in read_file_in_chunks('/path/to/file.bin', chunk_size=1024*1024*10):
    upload_chunk(chunk)
```

**매개변수:**

- `file_path` (str | Path): 읽을 파일의 경로
- `chunk_size` (int, 선택사항): 각 청크의 바이트 크기. 기본값은 50MB (52,428,800 바이트)

**반환값:**

- 파일 내용 청크를 바이트로 생성하는 제너레이터

**예외:**

- `FileNotFoundError`: 파일이 존재하지 않는 경우
- `PermissionError`: 권한으로 인해 파일을 읽을 수 없는 경우
- `OSError`: 파일 읽기 중 OS 수준 오류가 발생하는 경우

### 사용 사례

**대용량 파일 처리**: 메모리에 맞지 않는 파일을 효율적으로 처리:

```python
import hashlib

def calculate_hash_for_large_file(file_path):
    hash_md5 = hashlib.md5()
    for chunk in read_file_in_chunks(file_path):
        hash_md5.update(chunk)
    return hash_md5.hexdigest()
```

**청크 업로드 통합**: `CoreClientMixin.create_chunked_upload` 메서드와 원활하게 통합:

```python
from synapse_sdk.clients.backend.core import CoreClientMixin

client = CoreClientMixin(base_url='https://api.example.com')
result = client.create_chunked_upload('/path/to/large_file.zip')
```

**모범 사례:**

- 최적의 업로드 성능을 위해 기본 청크 크기(50MB) 사용
- 사용 가능한 메모리와 네트워크 조건에 따라 청크 크기 조정
- 매우 큰 파일(>1GB)의 경우 더 나은 진행률 추적을 위해 작은 청크 사용 고려
- 파일 작업 시 항상 예외 처리

## 체크섬 함수

### calculate_checksum

일반 파일의 체크섬을 계산합니다:

```python
from synapse_sdk.utils.file.checksum import calculate_checksum

checksum = calculate_checksum('/path/to/file.bin')
```

### get_checksum_from_file

Django 의존성 없이 파일형 객체의 체크섬을 계산합니다. 이 함수는 `read()` 메서드가 있는 모든 파일형 객체와 함께 작동하므로 Django의 File 객체, BytesIO, StringIO 및 일반 파일 객체와 호환됩니다.

```python
import hashlib
from io import BytesIO
from synapse_sdk.utils.file.checksum import get_checksum_from_file

# BytesIO를 사용한 기본 사용법 (기본값은 SHA1)
data = BytesIO(b'Hello, world!')
checksum = get_checksum_from_file(data)
print(checksum)  # 16진수 문자열로 된 SHA1 해시

# 다른 해시 알고리즘 사용
checksum_md5 = get_checksum_from_file(data, digest_mod=hashlib.md5)
checksum_sha256 = get_checksum_from_file(data, digest_mod=hashlib.sha256)

# 실제 파일 객체와 함께
with open('/path/to/file.txt', 'rb') as f:
    checksum = get_checksum_from_file(f)
```

**매개변수:**

- `file` (IO[Any]): 청크 단위 읽기를 지원하는 read() 메서드가 있는 파일형 객체
- `digest_mod` (Callable[[], Any], 선택사항): hashlib의 해시 알고리즘. 기본값은 `hashlib.sha1`

**반환값:**

- `str`: 파일 내용의 16진수 다이제스트

**주요 기능:**

- **메모리 효율성**: 대용량 파일 처리를 위해 4KB 청크로 파일 읽기
- **자동 파일 포인터 재설정**: 파일 객체가 시킹을 지원하는 경우 처음으로 재설정
- **텍스트/바이너리 불가지론**: 텍스트(StringIO)와 바이너리(BytesIO) 파일 객체 모두 처리
- **Django 의존성 없음**: Django 없이 작동하면서 Django File 객체와 호환
- **유연한 해시 알고리즘**: 모든 hashlib 알고리즘 지원(SHA1, SHA256, MD5 등)

## 다운로드 함수

동기 및 비동기 지원을 모두 포함한 URL에서 파일을 다운로드하는 유틸리티입니다.

```python
from synapse_sdk.utils.file.download import download_file, adownload_file

# 동기 다운로드
local_path = download_file(url, destination)

# 비동기 다운로드
import asyncio
local_path = await adownload_file(url, destination)

# 여러 파일의 URL을 경로로 변환
from synapse_sdk.utils.file.download import files_url_to_path
paths = files_url_to_path(url_list, destination_directory)
```

## 인코딩 함수

파일용 Base64 인코딩 유틸리티입니다.

```python
from synapse_sdk.utils.file.encoding import convert_file_to_base64

# 파일을 base64로 변환
base64_data = convert_file_to_base64('/path/to/file.jpg')
```

## I/O 함수

구조화된 데이터 파일용 일반 I/O 작업입니다.

```python
from synapse_sdk.utils.file.io import get_dict_from_file, get_temp_path

# JSON 또는 YAML 파일에서 딕셔너리 로드
config = get_dict_from_file('/path/to/config.json')
settings = get_dict_from_file('/path/to/settings.yaml')

# 임시 파일 경로 얻기
temp_path = get_temp_path()
temp_subpath = get_temp_path('subdir/file.tmp')
```

## 비디오 트랜스코딩

형식 변환, 압축 및 최적화를 위해 FFmpeg를 사용하는 고급 비디오 트랜스코딩 기능입니다.

### 요구사항

- **ffmpeg-python**: `pip install ffmpeg-python`
- **FFmpeg**: 시스템에 설치되어 PATH에서 사용 가능해야 함

### 지원되는 비디오 형식

비디오 모듈은 다양한 입력 형식을 지원합니다:
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

### 핵심 함수

#### validate_video_format

파일이 지원되는 비디오 형식인지 확인합니다:

```python
from synapse_sdk.utils.file.video.transcode import validate_video_format

if validate_video_format('video.mp4'):
    print("지원되는 형식")
else:
    print("지원되지 않는 형식")
```

#### get_video_info

비디오 파일에서 메타데이터를 추출합니다:

```python
from synapse_sdk.utils.file.video.transcode import get_video_info

info = get_video_info('input.mp4')
print(f"재생시간: {info['duration']} 초")
print(f"해상도: {info['width']}x{info['height']}")
print(f"비디오 코덱: {info['video_codec']}")
print(f"오디오 코덱: {info['audio_codec']}")
print(f"FPS: {info['fps']}")
```

#### transcode_video

광범위한 구성 옵션을 가진 주요 트랜스코딩 함수:

```python
from synapse_sdk.utils.file.video.transcode import transcode_video, TranscodeConfig
from pathlib import Path

# 기본 설정으로 기본 트랜스코딩
output_path = transcode_video('input.avi', 'output.mp4')

# 사용자 정의 구성
config = TranscodeConfig(
    vcodec='libx264',     # 비디오 코덱
    preset='fast',        # 인코딩 속도 vs 품질
    crf=20,              # 품질 (낮을수록 품질 향상)
    acodec='aac',        # 오디오 코덱
    audio_bitrate='128k', # 오디오 비트레이트
    resolution='1920x1080', # 출력 해상도
    fps=30,              # 프레임 레이트
    start_time=10.0,     # 10초부터 시작
    duration=60.0        # 60초만 처리
)

output_path = transcode_video('input.mkv', 'output.mp4', config)
```

#### TranscodeConfig 옵션

```python
@dataclass
class TranscodeConfig:
    vcodec: str = 'libx264'           # 비디오 코덱 (libx264, libx265 등)
    preset: str = 'medium'            # 인코딩 프리셋 (fast, medium, slow)
    crf: int = 28                     # 품질 팩터 (0-51, 낮을수록 품질 향상)
    acodec: str = 'aac'              # 오디오 코덱 (aac, opus 등)
    audio_bitrate: str = '128k'       # 오디오 비트레이트
    movflags: str = '+faststart'      # MP4 최적화 플래그
    resolution: Optional[str] = None  # 출력 해상도 (예: '1920x1080')
    fps: Optional[int] = None         # 출력 프레임 레이트
    start_time: Optional[float] = None # 시작 시간(초)
    duration: Optional[float] = None   # 처리할 재생시간(초)
```

#### 진행률 콜백 지원

콜백 함수로 트랜스코딩 진행률을 모니터링합니다:

```python
def progress_callback(progress_percent):
    print(f"진행률: {progress_percent:.1f}%")

output_path = transcode_video(
    'input.mp4',
    'output.mp4',
    progress_callback=progress_callback
)
```

#### optimize_for_web

사전 정의된 설정으로 빠른 웹 최적화:

```python
from synapse_sdk.utils.file.video.transcode import optimize_for_web

# 빠른 시작으로 웹 스트리밍을 위해 최적화
web_video = optimize_for_web('input.mov', 'web_output.mp4')
```

이 함수는 최적화된 설정을 사용합니다:
- 빠른 인코딩 프리셋
- 웹 친화적 압축 (CRF 23)
- 스트리밍용 빠른 시작 플래그
- 더 나은 웹 호환성을 위한 프래그먼트 키프레임

### 오류 처리

비디오 모듈은 특정 예외를 제공합니다:

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
    print("입력 형식이 지원되지 않음")
except FFmpegNotFoundError:
    print("FFmpeg가 설치되지 않음")
except TranscodingFailedError as e:
    print(f"트랜스코딩 실패: {e}")
```

### 고급 사용 예제

**배치 처리**:

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
            print(f"처리됨: {video_file.name}")
        except VideoTranscodeError as e:
            print(f"{video_file.name} 처리 실패: {e}")
```

**품질 최적화**:

```python
# 보관용 고품질
archive_config = TranscodeConfig(
    preset='slow',
    crf=18,
    audio_bitrate='256k'
)

# 모바일용 작은 크기
mobile_config = TranscodeConfig(
    preset='fast',
    crf=28,
    resolution='1280x720',
    audio_bitrate='96k'
)

# 다른 구성 적용
archive_output = transcode_video(input_file, 'archive.mp4', archive_config)
mobile_output = transcode_video(input_file, 'mobile.mp4', mobile_config)
```

**비디오 클리핑**:

```python
# 1분부터 시작하여 30초 클립 추출
clip_config = TranscodeConfig(
    start_time=60.0,    # 1분에서 시작
    duration=30.0,      # 30초 추출
    crf=20             # 고품질
)

clip = transcode_video('long_video.mp4', 'clip.mp4', clip_config)
```