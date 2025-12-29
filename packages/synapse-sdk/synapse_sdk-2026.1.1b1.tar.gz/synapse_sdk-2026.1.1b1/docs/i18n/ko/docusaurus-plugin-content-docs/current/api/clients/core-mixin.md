---
id: core-mixin
title: CoreClientMixin
sidebar_position: 12
---

# CoreClientMixin

Synapse 백엔드를 위한 핵심 파일 업로드 및 기본 작업을 제공합니다.

## 개요

`CoreClientMixin`은 핵심 시스템 작업, 특히 대용량 파일을 위한 청크 업로드를 포함한 파일 업로드 기능을 처리합니다. 이 믹스인은 `BackendClient`에 자동으로 포함되며 다른 믹스인에서 사용하는 필수 기능을 제공합니다.

## 파일 업로드 작업

### `create_chunked_upload(file_path)`

최적의 성능과 안정성을 위해 청크 업로드를 사용하여 대용량 파일을 업로드합니다.

```python
from pathlib import Path

# 대용량 파일 업로드
file_path = Path('/path/to/large_dataset.zip')
result = client.create_chunked_upload(file_path)
print(f"업로드 완료: {result}")
print(f"파일 ID: {result['id']}")
```

**매개변수:**

- `file_path` (str | Path): 업로드할 파일의 경로

**반환값:**

- `dict`: 파일 ID와 메타데이터가 포함된 업로드 결과

**기능:**

- **50MB 청크**: 성능을 위한 최적 청크 크기 사용
- **MD5 무결성**: 자동 체크섬 검증
- **재개 기능**: 중단된 업로드 재개 가능
- **진행률 추적**: 업로드 진행률 모니터링 지원
- **오류 복구**: 실패한 청크에 대한 자동 재시도

### 업로드 프로세스 세부사항

청크 업로드 프로세스는 다음과 같이 작동합니다:

1. **파일 분석**: 파일 크기 및 MD5 해시 계산
2. **청크 생성**: 파일을 50MB 청크로 분할
3. **순차 업로드**: 청크를 하나씩 업로드
4. **무결성 검사**: MD5로 각 청크 검증
5. **조립**: 서버에서 청크를 최종 파일로 조립
6. **검증**: 완성된 파일의 최종 무결성 검사

```python
import hashlib
import os
from pathlib import Path

def upload_with_progress(file_path):
    """자세한 진행률 추적과 함께 파일 업로드."""

    file_path = Path(file_path)

    # 파일 정보 가져오기
    file_size = os.path.getsize(file_path)
    print(f"업로드 중인 파일: {file_path.name}")
    print(f"파일 크기: {file_size / (1024*1024):.2f} MB")

    # MD5 계산 (클라이언트에서 자동으로 수행됨)
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)

    print(f"MD5 체크섬: {hash_md5.hexdigest()}")

    # 청크 업로드로 업로드
    try:
        result = client.create_chunked_upload(file_path)
        print("업로드 성공!")
        return result
    except Exception as e:
        print(f"업로드 실패: {e}")
        raise

# 사용법
upload_result = upload_with_progress('/path/to/large_file.zip')
```

## 고급 업로드 시나리오

### 일괄 파일 업로드

```python
def batch_chunked_upload(file_paths, max_concurrent=3):
    """동시성 제어와 함께 여러 대용량 파일 업로드."""
    import concurrent.futures
    import threading

    upload_results = []
    failed_uploads = []

    def upload_single_file(file_path):
        try:
            print(f"업로드 시작: {file_path}")
            result = client.create_chunked_upload(file_path)
            print(f"업로드 완료: {file_path}")
            return {'file_path': file_path, 'result': result, 'status': 'success'}
        except Exception as e:
            print(f"업로드 실패: {file_path} - {e}")
            return {'file_path': file_path, 'error': str(e), 'status': 'failed'}

    # 동시 업로드를 위해 ThreadPoolExecutor 사용
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent) as executor:
        future_to_file = {
            executor.submit(upload_single_file, file_path): file_path
            for file_path in file_paths
        }

        for future in concurrent.futures.as_completed(future_to_file):
            result = future.result()

            if result['status'] == 'success':
                upload_results.append(result)
            else:
                failed_uploads.append(result)

    return {
        'successful': upload_results,
        'failed': failed_uploads,
        'total': len(file_paths)
    }

# 여러 파일 업로드
file_list = [
    Path('/data/file1.zip'),
    Path('/data/file2.zip'),
    Path('/data/file3.zip')
]

batch_results = batch_chunked_upload(file_list, max_concurrent=2)
print(f"성공한 업로드: {len(batch_results['successful'])}")
print(f"실패한 업로드: {len(batch_results['failed'])}")
```

### 재시도 로직이 있는 업로드

```python
import time
from synapse_sdk.clients.exceptions import ClientError

def robust_chunked_upload(file_path, max_retries=3, retry_delay=5):
    """향상된 안정성을 위한 재시도 로직이 있는 업로드."""

    for attempt in range(max_retries):
        try:
            result = client.create_chunked_upload(file_path)
            print(f"{attempt + 1}번째 시도에서 업로드 성공")
            return result

        except ClientError as e:
            if e.status_code == 413:  # 파일이 너무 큼
                print(f"파일 {file_path}이 업로드하기에 너무 큽니다")
                raise
            elif e.status_code == 507:  # 저장 공간 부족
                print("서버 저장 공간이 가득 참")
                raise
            elif e.status_code >= 500:  # 서버 오류
                if attempt < max_retries - 1:
                    print(f"{attempt + 1}번째 시도에서 서버 오류, {retry_delay}초 후 재시도...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 지수 백오프
                else:
                    print(f"{max_retries}번의 시도 후 업로드 실패")
                    raise
            else:
                print(f"오류로 업로드 실패: {e}")
                raise

        except OSError as e:
            print(f"파일 시스템 오류: {e}")
            raise

        except Exception as e:
            if attempt < max_retries - 1:
                print(f"{attempt + 1}번째 시도에서 예상치 못한 오류: {e}")
                time.sleep(retry_delay)
            else:
                print(f"{max_retries}번의 시도 후 오류로 업로드 실패: {e}")
                raise

# 안정적인 업로드 사용
try:
    result = robust_chunked_upload('/path/to/file.zip')
    print(f"파일이 성공적으로 업로드됨: {result['id']}")
except Exception as e:
    print(f"최종 업로드 실패: {e}")
```

### 업로드 진행률 모니터링

```python
import os
from tqdm import tqdm

class ProgressTracker:
    """파일 업로드를 위한 간단한 진행률 추적기."""

    def __init__(self, total_size):
        self.total_size = total_size
        self.uploaded_size = 0
        self.progress_bar = tqdm(total=total_size, unit='B', unit_scale=True, desc="업로드 중")

    def update(self, chunk_size):
        self.uploaded_size += chunk_size
        self.progress_bar.update(chunk_size)

        if self.uploaded_size >= self.total_size:
            self.progress_bar.close()

    def get_progress_percentage(self):
        return (self.uploaded_size / self.total_size) * 100 if self.total_size > 0 else 0

def upload_with_progress_bar(file_path):
    """시각적 진행률 바와 함께 파일 업로드."""

    file_path = Path(file_path)
    file_size = os.path.getsize(file_path)

    # 진행률 추적기 생성
    tracker = ProgressTracker(file_size)

    try:
        # 참고: 실제 청크 업로드는 청크 수준 진행률을 노출하지 않음
        # 이것은 진행률을 추적할 수 있는 방법에 대한 개념적 예제
        print(f"{file_path.name} 업로드 시작 ({file_size / (1024*1024):.2f} MB)")

        result = client.create_chunked_upload(file_path)

        # 진행률 완료 시뮬레이션
        tracker.update(file_size)
        print(f"업로드 완료: {result['id']}")

        return result

    except Exception as e:
        tracker.progress_bar.close()
        print(f"업로드 실패: {e}")
        raise

# 사용법
upload_result = upload_with_progress_bar('/path/to/large_file.zip')
```

## 파일 검증

### 업로드 전 검증

```python
def validate_file_for_upload(file_path, max_size_gb=10):
    """업로드를 시도하기 전에 파일을 검증."""

    file_path = Path(file_path)

    # 파일 존재 확인
    if not file_path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없음: {file_path}")

    # 파일인지 확인 (디렉토리가 아닌)
    if not file_path.is_file():
        raise ValueError(f"경로가 파일이 아님: {file_path}")

    # 파일 크기 확인
    file_size = os.path.getsize(file_path)
    max_size_bytes = max_size_gb * 1024 * 1024 * 1024

    if file_size > max_size_bytes:
        raise ValueError(f"파일이 너무 큼: {file_size / (1024**3):.2f} GB (최대: {max_size_gb} GB)")

    # 파일 권한 확인
    if not os.access(file_path, os.R_OK):
        raise PermissionError(f"파일을 읽을 수 없음: {file_path}")

    # 기본 파일 무결성 검사
    try:
        with open(file_path, 'rb') as f:
            f.read(1024)  # 첫 1KB 읽기 시도
    except Exception as e:
        raise ValueError(f"파일이 손상된 것으로 보임: {e}")

    return {
        'valid': True,
        'file_size': file_size,
        'file_path': str(file_path)
    }

def safe_chunked_upload(file_path):
    """사전 검증과 함께 업로드."""

    try:
        # 먼저 파일 검증
        validation = validate_file_for_upload(file_path)
        print(f"파일 검증 통과: {validation['file_size'] / (1024*1024):.2f} MB")

        # 업로드 진행
        result = client.create_chunked_upload(file_path)
        print(f"업로드 성공: {result['id']}")

        return result

    except (FileNotFoundError, ValueError, PermissionError) as e:
        print(f"검증 실패: {e}")
        return None
    except Exception as e:
        print(f"업로드 실패: {e}")
        return None

# 사용법
upload_result = safe_chunked_upload('/path/to/file.zip')
```

## 성능 최적화

### 최적화된 업로드 전략

```python
def optimized_upload_strategy(file_path):
    """파일 특성에 따른 최적 업로드 전략 선택."""

    file_path = Path(file_path)
    file_size = os.path.getsize(file_path)

    # 임계값 (바이트 단위)
    SMALL_FILE_THRESHOLD = 10 * 1024 * 1024  # 10MB
    LARGE_FILE_THRESHOLD = 100 * 1024 * 1024  # 100MB

    if file_size < SMALL_FILE_THRESHOLD:
        print(f"작은 파일 ({file_size / (1024*1024):.2f} MB) - 일반 업로드 사용")
        # 작은 파일의 경우 다른 업로드 방법을 사용할 수 있음
        # CoreClientMixin은 청크 업로드만 제공하므로 이것은 개념적임
        return client.create_chunked_upload(file_path)

    elif file_size < LARGE_FILE_THRESHOLD:
        print(f"중간 파일 ({file_size / (1024*1024):.2f} MB) - 청크 업로드 사용")
        return client.create_chunked_upload(file_path)

    else:
        print(f"대용량 파일 ({file_size / (1024*1024):.2f} MB) - 최적화된 청크 업로드 사용")
        # 매우 큰 파일의 경우 추가 최적화를 원할 수 있음
        return robust_chunked_upload(file_path, max_retries=5)

# 사용법
result = optimized_upload_strategy('/path/to/any_size_file.zip')
```

## 오류 처리

```python
from synapse_sdk.clients.exceptions import ClientError

def handle_upload_errors():
    """업로드를 위한 포괄적인 오류 처리."""

    try:
        result = client.create_chunked_upload('/path/to/file.zip')
        return result

    except FileNotFoundError:
        print("오류: 파일을 찾을 수 없음")
        return None

    except PermissionError:
        print("오류: 권한이 거부됨 - 파일 권한을 확인하세요")
        return None

    except ClientError as e:
        if e.status_code == 413:
            print("오류: 업로드하기에 파일이 너무 큼")
        elif e.status_code == 507:
            print("오류: 서버 저장 공간이 가득 �참")
        elif e.status_code == 429:
            print("오류: 요청 제한 - 너무 많은 요청")
        elif e.status_code >= 500:
            print(f"오류: 서버 오류 ({e.status_code})")
        else:
            print(f"오류: 클라이언트 오류 ({e.status_code}): {e}")
        return None

    except OSError as e:
        print(f"오류: 운영 체제 오류: {e}")
        return None

    except MemoryError:
        print("오류: 업로드를 위한 메모리 부족")
        return None

    except Exception as e:
        print(f"오류: 예상치 못한 오류: {e}")
        return None

# 오류 처리 사용
upload_result = handle_upload_errors()
if upload_result:
    print(f"업로드 성공: {upload_result['id']}")
else:
    print("업로드 실패")
```

## 참고

- [BackendClient](./backend.md) - 메인 백엔드 클라이언트
- [DataCollectionClientMixin](./data-collection-mixin.md) - 청크 업로드를 사용하는 데이터 수집 작업
- [MLClientMixin](./ml-mixin.md) - 청크 업로드를 사용하는 ML 모델 업로드
