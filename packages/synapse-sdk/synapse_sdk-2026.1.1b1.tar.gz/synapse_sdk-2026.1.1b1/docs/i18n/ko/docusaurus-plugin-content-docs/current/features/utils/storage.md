---
id: storage
title: Storage Providers
sidebar_position: 2
---

# Storage Providers

dict 기반 구성으로 여러 클라우드 제공자를 지원하는 스토리지 추상화 레이어.

## 설치

```bash
pip install synapse-sdk                    # 로컬 스토리지만
pip install synapse-sdk[storage-s3]        # S3/MinIO 지원
pip install synapse-sdk[storage-gcs]       # Google Cloud Storage
pip install synapse-sdk[storage-sftp]      # SFTP 지원
pip install synapse-sdk[storage-all]       # 모든 제공자
```

---

## 사용 가능한 제공자

| 제공자 | 별칭 | 설명 |
|-------|------|------|
| `local` | `file_system` | 로컬 파일시스템 |
| `s3` | `amazon_s3`, `minio` | S3 호환 스토리지 |
| `gcs` | `gs`, `gcp` | Google Cloud Storage |
| `sftp` | - | SFTP 서버 |
| `http` | `https` | HTTP 파일 서버 (읽기 전용) |

---

## 기본 사용법

```python
from synapse_sdk.utils.storage import (
    get_storage,
    get_pathlib,
    get_path_file_count,
    get_path_total_size,
)

# 스토리지 인스턴스 생성
storage = get_storage({
    'provider': 'local',
    'configuration': {'location': '/data'}
})

# 파일 업로드
from pathlib import Path
url = storage.upload(Path('/tmp/file.txt'), 'uploads/file.txt')

# 존재 여부 확인
exists = storage.exists('uploads/file.txt')

# 경로 탐색을 위한 pathlib 객체 가져오기
path = get_pathlib(config, '/uploads')
for file in path.rglob('*.txt'):
    print(file)

# 통계 가져오기
count = get_path_file_count(config, '/uploads')
size = get_path_total_size(config, '/uploads')
```

---

## 제공자 구성

### 로컬 파일시스템

```python
config = {
    'provider': 'local',  # 또는 'file_system'
    'configuration': {
        'location': '/data'
    }
}
```

### S3 / MinIO

```python
config = {
    'provider': 's3',  # 또는 'amazon_s3', 'minio'
    'configuration': {
        'bucket_name': 'my-bucket',
        'access_key': 'AKIAIOSFODNN7EXAMPLE',
        'secret_key': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
        'region_name': 'us-east-1',
        'endpoint_url': 'http://minio:9000',  # 선택사항, MinIO용
    }
}
```

### Google Cloud Storage

```python
config = {
    'provider': 'gcs',  # 또는 'gs', 'gcp'
    'configuration': {
        'bucket_name': 'my-bucket',
        'credentials': '/path/to/service-account.json',
    }
}
```

### SFTP

```python
config = {
    'provider': 'sftp',
    'configuration': {
        'host': 'sftp.example.com',
        'username': 'user',
        'password': 'secret',  # 또는 private_key 사용
        # 'private_key': '/path/to/id_rsa',
        'root_path': '/data',
    }
}
```

### HTTP (읽기 전용)

```python
config = {
    'provider': 'http',  # 또는 'https'
    'configuration': {
        'base_url': 'https://files.example.com/uploads/',
        'timeout': 60,
    }
}
```

---

## Storage Protocol

모든 스토리지 제공자는 `StorageProtocol`을 구현합니다:

```python
from typing import Protocol
from pathlib import Path

class StorageProtocol(Protocol):
    def upload(self, local_path: Path, remote_path: str) -> str: ...
    def download(self, remote_path: str, local_path: Path) -> Path: ...
    def exists(self, remote_path: str) -> bool: ...
    def delete(self, remote_path: str) -> None: ...
    def list_files(self, prefix: str = '') -> list[str]: ...
```

### 커스텀 스토리지 구현

```python
from synapse_sdk.utils.storage import StorageProtocol
from pathlib import Path

class MyCustomStorage:
    """duck typing으로 StorageProtocol 구현."""

    def upload(self, local_path: Path, remote_path: str) -> str:
        # 업로드 구현
        return f"custom://{remote_path}"

    def download(self, remote_path: str, local_path: Path) -> Path:
        # 다운로드 구현
        return local_path

    def exists(self, remote_path: str) -> bool:
        # 존재 여부 확인
        return True

    def delete(self, remote_path: str) -> None:
        # 삭제 구현
        pass

    def list_files(self, prefix: str = '') -> list[str]:
        # 파일 목록
        return []
```

---

## 유틸리티 함수

### get_storage()

구성에서 스토리지 인스턴스 생성.

```python
from synapse_sdk.utils.storage import get_storage

storage = get_storage({
    'provider': 's3',
    'configuration': {
        'bucket_name': 'my-bucket',
        # ...
    }
})
```

### get_pathlib()

클라우드 스토리지 탐색을 위한 pathlib 유사 객체 가져오기.

```python
from synapse_sdk.utils.storage import get_pathlib

path = get_pathlib(config, '/uploads')

# 파일 반복
for file in path.rglob('*.json'):
    print(file.name)
```

### get_path_file_count()

스토리지 경로의 파일 개수 세기.

```python
from synapse_sdk.utils.storage import get_path_file_count

count = get_path_file_count(config, '/uploads')
print(f"파일 수: {count}")
```

### get_path_total_size()

스토리지 경로의 파일 총 크기 가져오기.

```python
from synapse_sdk.utils.storage import get_path_total_size

size = get_path_total_size(config, '/uploads')
print(f"총 크기: {size} bytes")
```

---

## v1에서 마이그레이션

### 주요 변경 사항

| v1 | v2 |
|----|----|
| `get_storage('s3://bucket?key=value')` | Dict 구성만 사용 |
| `FileSystemStorage` 클래스 | `LocalStorage` 클래스 |
| `GCPStorage` 클래스 | `GCSStorage` 클래스 |
| `BaseStorage` 상속 | `StorageProtocol` 구현 |

### 제공자 별칭 (하위 호환)

| 별칭 | 매핑 |
|-----|------|
| `file_system` | `local` / `LocalStorage` |
| `gcp`, `gs` | `gcs` / `GCSStorage` |
| `amazon_s3`, `minio` | `s3` / `S3Storage` |

---

## 예제

### 파일 업로드

```python
from synapse_sdk.utils.storage import get_storage
from pathlib import Path

storage = get_storage({
    'provider': 's3',
    'configuration': {
        'bucket_name': 'ml-models',
        'access_key': '...',
        'secret_key': '...',
    }
})

# 모델 파일 업로드
model_path = Path('/models/model.pt')
url = storage.upload(model_path, 'models/v1/model.pt')
print(f"업로드됨: {url}")
```

### 다운로드 및 처리

```python
from synapse_sdk.utils.storage import get_storage
from pathlib import Path
import tempfile

storage = get_storage({
    'provider': 'gcs',
    'configuration': {
        'bucket_name': 'datasets',
        'credentials': '/path/to/creds.json',
    }
})

# 임시 파일로 다운로드
with tempfile.NamedTemporaryFile(suffix='.csv') as tmp:
    local_path = storage.download('data/dataset.csv', Path(tmp.name))
    # 파일 처리
    import pandas as pd
    df = pd.read_csv(local_path)
```

### 파일 목록 및 필터링

```python
from synapse_sdk.utils.storage import get_pathlib

path = get_pathlib(config, '/experiments')

# 모든 체크포인트 찾기
checkpoints = list(path.rglob('*.ckpt'))
print(f"{len(checkpoints)}개 체크포인트 발견")

# 패턴으로 필터링
recent = [f for f in checkpoints if 'epoch_10' in f.name]
```

---

## 참고 문서

- [마이그레이션 가이드](../../migration.md) - v1에서 v2로 마이그레이션
- [설치](../../installation.md) - 스토리지 extras 설치
- [Network Utilities](./network.md) - 네트워크 스트리밍 유틸리티
