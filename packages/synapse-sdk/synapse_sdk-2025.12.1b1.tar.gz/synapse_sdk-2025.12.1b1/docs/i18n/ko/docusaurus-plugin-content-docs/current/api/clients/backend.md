---
id: backend
title: BackendClient
sidebar_position: 10
---

# BackendClient

Synapse 백엔드 API와 상호작용하기 위한 메인 클라이언트입니다.

## 개요

`BackendClient`는 데이터 관리, 플러그인 실행, 어노테이션, 머신러닝 워크플로를 포함한 모든 백엔드 작업에 대한 포괄적인 액세스를 제공합니다. 여러 전문화된 믹스인의 기능을 통합합니다:

- **AnnotationClientMixin**: 작업 및 어노테이션 관리
- **CoreClientMixin**: 파일 업로드 및 핵심 작업
- **DataCollectionClientMixin**: 데이터 수집 및 파일 관리
- **HITLClientMixin**: Human-in-the-loop 할당 작업
- **IntegrationClientMixin**: 플러그인 및 작업 관리
- **MLClientMixin**: 머신러닝 모델 및 정답 데이터 작업

## 생성자

```python
BackendClient(
    base_url: str,
    api_token: str = None,
    agent_token: str = None,
    timeout: dict = None
)
```

### 매개변수

- **base_url** (`str`): Synapse 백엔드 API의 기본 URL
- **api_token** (`str`, 선택사항): API 인증 토큰. `SYNAPSE_API_TOKEN` 환경변수로도 설정 가능
- **agent_token** (`str`, 선택사항): 에이전트 인증 토큰. `SYNAPSE_AGENT_TOKEN` 환경변수로도 설정 가능
- **timeout** (`dict`, 선택사항): 사용자 정의 타임아웃 설정. 기본값은 `{'connect': 5, 'read': 30}`

### 예제

```python
from synapse_sdk.clients.backend import BackendClient

# 토큰을 명시적으로 지정하여 클라이언트 생성
client = BackendClient(
    base_url="https://api.synapse.sh",
    api_token="your-api-token"
)

# 또는 환경변수 사용
import os
os.environ['SYNAPSE_API_TOKEN'] = "your-api-token"
client = BackendClient(base_url="https://api.synapse.sh")
```

## API 메서드

### 어노테이션 작업

#### `get_project(pk)`

ID로 프로젝트 상세정보를 가져옵니다.

```python
project = client.get_project(123)
```

#### `get_task(pk, params)`

선택적 매개변수와 함께 작업 상세정보를 가져옵니다.

```python
task = client.get_task(456, params={'expand': 'data_unit'})
```

#### `annotate_task_data(pk, data)`

작업에 대한 어노테이션 데이터를 제출합니다.

```python
result = client.annotate_task_data(456, {
    'annotations': [
        {'type': 'bbox', 'coordinates': [10, 10, 100, 100]}
    ]
})
```

#### `list_tasks(params=None, url_conversion=None, list_all=False)`

필터링 및 페이지네이션과 함께 작업 목록을 가져옵니다.

```python
# 프로젝트의 작업 가져오기
tasks = client.list_tasks(params={'project': 123})

# 모든 작업 가져오기 (페이지네이션 자동 처리)
all_tasks = client.list_tasks(list_all=True)
```

#### `create_tasks(data)`

새로운 작업를 생성합니다.

```python
new_tasks = client.create_tasks([
    {'project': 123, 'data_unit': 789},
    {'project': 123, 'data_unit': 790}
])
```

#### `set_tags_tasks(data, params=None)`

여러 작업에 태그를 설정합니다.

```python
client.set_tags_tasks({
    'task_ids': [456, 457],
    'tag_ids': [1, 2, 3]
})
```

### 핵심 작업

#### `create_chunked_upload(file_path)`

최적 성능을 위해 청크 업로드를 사용하여 대용량 파일을 업로드합니다.

```python
from pathlib import Path

result = client.create_chunked_upload(Path('/path/to/large_file.zip'))
print(f"업로드 완료: {result}")
```

**기능:**

- 최적 성능을 위한 50MB 청크 사용
- 자동 재시도 및 재개 기능
- MD5 무결성 검증
- 진행률 추적 지원

### 데이터 수집 작업

#### `list_data_collection()`

사용 가능한 모든 데이터 컬렉션을 나열합니다.

```python
collections = client.list_data_collection()
```

#### `get_data_collection(data_collection_id)`

특정 데이터 컬렉션에 대한 상세 정보를 가져옵니다.

```python
collection = client.get_data_collection(123)
file_specs = collection['file_specifications']
```

#### `create_data_file(file_path, use_chunked_upload=False)`

백엔드에 데이터 파일을 생성하고 업로드합니다.

```python
from pathlib import Path

# 일반 업로드
data_file = client.create_data_file(Path('/path/to/file.jpg'))

# 대용량 파일을 위한 청크 업로드
large_file = client.create_data_file(
    Path('/path/to/large_file.zip'),
    use_chunked_upload=True
)
```

#### `upload_data_file(organized_file, collection_id, use_chunked_upload=False)`

정리된 파일 데이터를 컬렉션에 업로드합니다.

```python
result = client.upload_data_file(
    organized_file={'files': {...}, 'meta': {...}},
    collection_id=123,
    use_chunked_upload=False
)
```

#### `create_data_units(uploaded_files)`

업로드된 파일에서 데이터 유닛을 생성합니다.

```python
data_units = client.create_data_units([
    {'id': 1, 'file': {...}},
    {'id': 2, 'file': {...}}
])
```

### HITL (Human-in-the-Loop) 작업

#### `get_assignment(pk)`

ID로 할당 상세정보를 가져옵니다.

```python
assignment = client.get_assignment(789)
```

#### `list_assignments(params=None, url_conversion=None, list_all=False)`

필터링 옵션과 함께 할당 목록을 가져옵니다.

```python
# 프로젝트의 할당 가져오기
assignments = client.list_assignments(params={'project': 123})

# 모든 할당 가져오기
all_assignments = client.list_assignments(list_all=True)
```

#### `set_tags_assignments(data, params=None)`

여러 할당에 태그를 설정합니다.

```python
client.set_tags_assignments({
    'assignment_ids': [789, 790],
    'tag_ids': [1, 2]
})
```

### 통합 작업

#### `health_check_agent(token)`

에이전트 상태를 확인합니다.

```python
status = client.health_check_agent('agent-token-123')
```

#### `get_plugin(pk)` / `create_plugin(data)` / `update_plugin(pk, data)`

플러그인을 관리합니다.

```python
# 플러그인 가져오기
plugin = client.get_plugin(123)

# 플러그인 생성
new_plugin = client.create_plugin({
    'name': 'My Plugin',
    'description': 'Plugin description'
})

# 플러그인 업데이트
updated = client.update_plugin(123, {'description': 'Updated description'})
```

#### `run_plugin(pk, data)`

제공된 데이터로 플러그인을 실행합니다.

```python
result = client.run_plugin(123, {
    'parameters': {'input': 'value'},
    'context': {...}
})
```

#### 플러그인 릴리스 관리

```python
# 플러그인 릴리스 생성
release = client.create_plugin_release({
    'plugin': 123,
    'version': '1.0.0',
    'file': open('/path/to/plugin.zip', 'rb')
})

# 릴리스 상세정보 가져오기
release_info = client.get_plugin_release(456)
```

#### 작업 관리

```python
# 작업 목록
jobs = client.list_jobs(params={'status': 'running'})

# 작업 상세정보 가져오기
job = client.get_job(789, params={'expand': 'logs'})

# 작업 상태 업데이트
client.update_job(789, {'status': 'completed'})

# 작업 콘솔 로그 가져오기
logs = client.list_job_console_logs(789)
```

#### 스토리지 작업

```python
# 스토리지 목록
storages = client.list_storages()

# 스토리지 상세정보 가져오기
storage = client.get_storage(123)

# 스토리지 생성
new_storage = client.create_storage({
    'name': 'My Storage',
    'provider': 'amazon_s3',
    'configuration': {...}
})
```

### 머신러닝 작업

#### `list_models(params=None)` / `get_model(pk, params=None, url_conversion=None)`

ML 모델을 관리합니다.

```python
# 모델 목록
models = client.list_models(params={'project': 123})

# 모델 상세정보 가져오기
model = client.get_model(456, params={'expand': 'metrics'})
```

#### `create_model(data)`

파일 업로드와 함께 새로운 ML 모델을 생성합니다.

```python
new_model = client.create_model({
    'name': 'My Model',
    'project': 123,
    'file': '/path/to/model.pkl'
})
```

#### 정답 데이터 작업

```python
# 정답 이벤트 목록
events = client.list_ground_truth_events(
    params={'ground_truth_dataset_versions': [123]},
    list_all=True
)

# 정답 버전 가져오기
version = client.get_ground_truth_version(123)
```

## 스토리지 모델

백엔드 클라이언트는 스토리지 작업을 위한 사전 정의된 모델을 포함합니다:

### StorageCategory

- `INTERNAL`: 내부 스토리지 시스템
- `EXTERNAL`: 외부 스토리지 제공업체

### StorageProvider

- `AMAZON_S3`: Amazon S3
- `AZURE`: Microsoft Azure Blob Storage
- `DIGITAL_OCEAN`: DigitalOcean Spaces
- `FILE_SYSTEM`: 로컬 파일 시스템
- `FTP` / `SFTP`: FTP 프로토콜
- `MINIO`: MinIO 스토리지
- `GCP`: Google Cloud Storage

## 오류 처리

모든 API 메서드는 다양한 오류 조건에 대해 `ClientError` 예외를 발생시킬 수 있습니다:

```python
from synapse_sdk.clients.exceptions import ClientError

try:
    project = client.get_project(999)
except ClientError as e:
    print(f"API 오류: {e}")
    print(f"상태 코드: {e.status_code}")
    print(f"응답: {e.response}")
```

## 페이지네이션

`list_all=True`를 지원하는 메서드는 자동으로 페이지네이션을 처리합니다:

```python
# 수동 페이지네이션
tasks_page1 = client.list_tasks(params={'page': 1, 'page_size': 100})

# 자동 페이지네이션 (권장)
all_tasks = client.list_tasks(list_all=True)
```

## URL 변환

일부 메서드는 파일 필드에 대한 URL 변환을 지원합니다:

```python
# 사용자 정의 URL 변환
tasks = client.list_tasks(
    url_conversion={'files': lambda url: f"https://cdn.example.com{url}"}
)
```

## 참고

- [AgentClient](./agent.md) - 에이전트별 작업용
- [BaseClient](./base.md) - 기본 클라이언트 구현
