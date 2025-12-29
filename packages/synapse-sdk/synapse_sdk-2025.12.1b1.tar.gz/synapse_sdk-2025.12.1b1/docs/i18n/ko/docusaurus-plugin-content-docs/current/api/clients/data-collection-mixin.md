---
id: data-collection-mixin
title: DataCollectionClientMixin
sidebar_position: 13
---

# DataCollectionClientMixin

Synapse 백엔드를 위한 데이터 수집 및 파일 관리 작업을 제공합니다.

## 개요

`DataCollectionClientMixin`은 데이터 컬렉션, 파일 업로드, 데이터 유닛, 일괄 처리와 관련된 모든 작업을 처리합니다. 이 믹스인은 `BackendClient`에 자동으로 포함되며 대규모 데이터 작업을 관리하기 위한 메서드를 제공합니다.

## 데이터 컬렉션 작업

### `list_data_collection()`

사용 가능한 모든 데이터 컬렉션 목록을 가져옵니다.

```python
collections = client.list_data_collection()
for collection in collections:
    print(f"컬렉션: {collection['name']} (ID: {collection['id']})")
```

**반환값:**

- `list`: 데이터 컬렉션 객체의 목록

### `get_data_collection(data_collection_id)`

특정 데이터 컬렉션에 대한 상세 정보를 가져옵니다.

```python
collection = client.get_data_collection(123)
print(f"컬렉션: {collection['name']}")
print(f"설명: {collection['description']}")

# 파일 사양 접근
file_specs = collection['file_specifications']
for spec in file_specs:
    print(f"파일 유형: {spec['name']}, 필수: {spec['is_required']}")
```

**매개변수:**

- `data_collection_id` (int): 데이터 컬렉션 ID

**반환값:**

- `dict`: 파일 사양을 포함한 상세 컬렉션 정보

**컬렉션 구조:**

- `id`: 컬렉션 ID
- `name`: 컬렉션 이름
- `description`: 컬렉션 설명
- `file_specifications`: 필수 파일 유형 및 형식 목록
- `project`: 연관된 프로젝트 ID
- `created_at`: 생성 타임스탬프

## 파일 작업

### `create_data_file(file_path, use_chunked_upload=False)`

백엔드에 데이터 파일을 생성하고 업로드합니다.

```python
from pathlib import Path

# 작은 파일을 위한 일반 업로드
data_file = client.create_data_file(Path('/path/to/image.jpg'))
print(f"업로드된 파일 ID: {data_file['id']}")

# 대용량 파일을 위한 청크 업로드 (50MB 이상 권장)
large_file = client.create_data_file(
    Path('/path/to/large_dataset.zip'),
    use_chunked_upload=True
)
print(f"대용량 파일 업로드됨: {large_file['id']}")
```

**매개변수:**

- `file_path` (Path): 업로드할 파일을 가리키는 Path 객체
- `use_chunked_upload` (bool): 대용량 파일을 위한 청크 업로드 활성화

**반환값:**

- `dict` 또는 `str`: 파일 ID와 메타데이터가 포함된 파일 업로드 응답

**청크 업로드를 사용해야 하는 경우:**

- 50MB보다 큰 파일
- 불안정한 네트워크 연결
- 업로드 진행률 추적이 필요한 경우
- 더 나은 오류 복구를 위해

### `upload_data_file(organized_file, collection_id, use_chunked_upload=False)`

정리된 파일 데이터를 특정 컬렉션에 업로드합니다.

```python
# 파일 데이터 정리
organized_file = {
    'files': {
        'image': Path('/path/to/image.jpg'),
        'annotation': Path('/path/to/annotation.json'),
        'metadata': Path('/path/to/metadata.xml')
    },
    'meta': {
        'origin_file_stem': 'sample_001',
        'origin_file_extension': '.jpg',
        'created_at': '2023-10-01T12:00:00Z',
        'batch_id': 'batch_001'
    }
}

# 컬렉션에 업로드
result = client.upload_data_file(
    organized_file=organized_file,
    collection_id=123,
    use_chunked_upload=False
)
```

**매개변수:**

- `organized_file` (dict): 파일과 메타데이터가 포함된 구조화된 파일 데이터
- `collection_id` (int): 대상 데이터 컬렉션 ID
- `use_chunked_upload` (bool): 청크 업로드 활성화

**정리된 파일 구조:**

- `files` (dict): 파일 유형을 파일 경로에 매핑하는 딕셔너리
- `meta` (dict): 파일 그룹과 연관된 메타데이터

**반환값:**

- `dict`: 파일 참조와 ID가 포함된 업로드 결과

### `create_data_units(uploaded_files)`

이전에 업로드된 파일에서 데이터 유닛을 생성합니다.

```python
# 업로드된 파일들
uploaded_files = [
    {
        'id': 1,
        'file': {'image': 'file_id_123', 'annotation': 'file_id_124'},
        'meta': {'batch': 'batch_001'}
    },
    {
        'id': 2,
        'file': {'image': 'file_id_125', 'annotation': 'file_id_126'},
        'meta': {'batch': 'batch_001'}
    }
]

# 데이터 유닛 생성
data_units = client.create_data_units(uploaded_files)
print(f"{len(data_units)}개의 데이터 유닛 생성됨")
```

**매개변수:**

- `uploaded_files` (list): 업로드된 파일 구조의 목록

**반환값:**

- `list`: ID와 메타데이터가 포함된 생성된 데이터 유닛

## 일괄 처리

믹스인은 대규모 작업을 위한 효율적인 일괄 처리를 지원합니다:

```python
from multiprocessing import Pool
from pathlib import Path

# 예제: 여러 파일 일괄 업로드
file_paths = [
    Path('/data/batch1/file1.jpg'),
    Path('/data/batch1/file2.jpg'),
    Path('/data/batch1/file3.jpg'),
    # ... 더 많은 파일
]

# 파일을 배치로 처리
batch_size = 10
for i in range(0, len(file_paths), batch_size):
    batch = file_paths[i:i+batch_size]

    # 배치 업로드
    uploaded_files = []
    for file_path in batch:
        result = client.create_data_file(file_path)
        uploaded_files.append({
            'id': len(uploaded_files) + 1,
            'file': {'image': result['id']},
            'meta': {'batch': f'batch_{i//batch_size}'}
        })

    # 배치용 데이터 유닛 생성
    data_units = client.create_data_units(uploaded_files)
    print(f"배치 {i//batch_size} 처리됨: {len(data_units)}개의 데이터 유닛")
```

## 진행률 추적

대용량 업로드의 경우 진행률을 추적할 수 있습니다:

```python
import os
from tqdm import tqdm

def upload_with_progress(file_paths, collection_id):
    """진행률 추적과 함께 파일 업로드."""
    uploaded_files = []

    with tqdm(total=len(file_paths), desc="파일 업로드 중") as pbar:
        for file_path in file_paths:
            try:
                # 업로드 방법을 결정하기 위해 파일 크기 확인
                file_size = os.path.getsize(file_path)
                use_chunked = file_size > 50 * 1024 * 1024  # 50MB

                # 파일 업로드
                result = client.create_data_file(
                    file_path,
                    use_chunked_upload=use_chunked
                )

                # 컬렉션용 정리
                organized_file = {
                    'files': {'primary': file_path},
                    'meta': {
                        'origin_file_stem': file_path.stem,
                        'origin_file_extension': file_path.suffix,
                        'file_size': file_size
                    }
                }

                upload_result = client.upload_data_file(
                    organized_file,
                    collection_id,
                    use_chunked_upload=use_chunked
                )

                uploaded_files.append(upload_result)
                pbar.update(1)

            except Exception as e:
                print(f"{file_path} 업로드 실패: {e}")
                pbar.update(1)
                continue

    return uploaded_files

# 사용법
file_paths = [Path(f'/data/file_{i}.jpg') for i in range(100)]
results = upload_with_progress(file_paths, collection_id=123)
```

## 데이터 검증

### 파일 사양 검증

```python
def validate_files_against_collection(file_paths, collection_id):
    """컬렉션 사양에 대해 파일을 검증."""
    collection = client.get_data_collection(collection_id)
    file_specs = collection['file_specifications']

    # 사양 조회 생성
    required_types = {spec['name'] for spec in file_specs if spec['is_required']}
    optional_types = {spec['name'] for spec in file_specs if not spec['is_required']}

    # 파일 정리 검증
    organized_files = []
    for file_path in file_paths:
        # 경로 또는 메타데이터에서 파일 유형 추출
        file_type = extract_file_type(file_path)  # 사용자 정의 함수

        if file_type in required_types or file_type in optional_types:
            organized_files.append({
                'path': file_path,
                'type': file_type,
                'valid': True
            })
        else:
            print(f"경고: {file_path}에 대한 알 수 없는 파일 유형 '{file_type}'")
            organized_files.append({
                'path': file_path,
                'type': file_type,
                'valid': False
            })

    return organized_files

def extract_file_type(file_path):
    """경로에서 파일 유형 추출 - 명명 규칙에 따라 구현."""
    # 예제 구현
    if 'image' in str(file_path):
        return 'image'
    elif 'annotation' in str(file_path):
        return 'annotation'
    elif 'metadata' in str(file_path):
        return 'metadata'
    else:
        return 'unknown'
```

## 오류 처리 및 재시도 로직

```python
import time
from synapse_sdk.clients.exceptions import ClientError

def robust_upload(file_path, max_retries=3):
    """안정성을 위한 재시도 로직이 있는 업로드."""
    for attempt in range(max_retries):
        try:
            result = client.create_data_file(file_path, use_chunked_upload=True)
            return result
        except ClientError as e:
            if e.status_code == 413:  # 파일이 너무 큼
                print(f"파일 {file_path}이 너무 큼, 청크 업로드 시도")
                try:
                    return client.create_data_file(file_path, use_chunked_upload=True)
                except Exception as retry_e:
                    print(f"청크 업로드 실패: {retry_e}")
                    if attempt == max_retries - 1:
                        raise
            elif e.status_code == 429:  # 요청 제한
                wait_time = 2 ** attempt  # 지수 백오프
                print(f"요청 제한됨, {wait_time}초 대기 중...")
                time.sleep(wait_time)
            else:
                print(f"업로드 실패 (시도 {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    raise
        except Exception as e:
            print(f"예상치 못한 오류 (시도 {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(1)  # 재시도 전 잠시 대기
```

## 참고

- [BackendClient](./backend.md) - 메인 백엔드 클라이언트
- [CoreClientMixin](./core-mixin.md) - 핵심 파일 작업
- [AnnotationClientMixin](./annotation-mixin.md) - 태스크 및 어노테이션 관리
