---
id: integration-mixin
title: IntegrationClientMixin
sidebar_position: 15
---

# IntegrationClientMixin

Synapse 백엔드를 위한 플러그인 관리, 작업 실행, 시스템 통합 작업을 제공합니다.

## 개요

`IntegrationClientMixin`은 플러그인, 작업, 에이전트, 스토리지 관리와 관련된 모든 작업을 처리합니다. 이 믹스인은 `BackendClient`에 자동으로 포함되며 시스템 통합 및 자동화 워크플로를 위한 메서드를 제공합니다.

## 에이전트 작업

### `health_check_agent(token)`

에이전트의 상태를 확인합니다.

```python
# 에이전트 상태 확인
status = client.health_check_agent('agent-token-123')
print(f"에이전트 상태: {status}")

# 에이전트 연결 확인
try:
    health = client.health_check_agent('my-agent-token')
    print("에이전트가 정상이고 연결됨")
except ClientError as e:
    print(f"에이전트 상태 확인 실패: {e}")
```

**매개변수:**

- `token` (str): 에이전트 인증 토큰

**반환값:**

- `dict`: 에이전트 상태 및 연결 정보

## 플러그인 관리

### `get_plugin(pk)`

특정 플러그인에 대한 상세 정보를 가져옵니다.

```python
plugin = client.get_plugin(123)
print(f"플러그인: {plugin['name']}")
print(f"버전: {plugin['version']}")
print(f"설명: {plugin['description']}")
print(f"작성자: {plugin['author']}")
```

**매개변수:**

- `pk` (int): 플러그인 ID

**반환값:**

- `dict`: 메타데이터 및 구성을 포함한 완전한 플러그인 정보

### `create_plugin(data)`

시스템에 새로운 플러그인을 생성합니다.

```python
plugin_data = {
    'name': 'My Custom Plugin',
    'description': '사용자 정의 데이터 처리를 위한 플러그인',
    'version': '1.0.0',
    'author': 'Your Name',
    'category': 'data_processing',
    'configuration': {
        'parameters': {
            'threshold': {'type': 'float', 'default': 0.5},
            'max_items': {'type': 'int', 'default': 100}
        }
    }
}

new_plugin = client.create_plugin(plugin_data)
print(f"ID {new_plugin['id']}로 플러그인 생성됨")
```

**매개변수:**

- `data` (dict): 플러그인 구성 및 메타데이터

**플러그인 데이터 구조:**

- `name` (str, 필수): 플러그인 이름
- `description` (str): 플러그인 설명
- `version` (str): 플러그인 버전
- `author` (str): 플러그인 작성자
- `category` (str): 플러그인 카테고리
- `configuration` (dict): 플러그인 구성 스키마

**반환값:**

- `dict`: 생성된 ID가 포함된 생성된 플러그인

### `update_plugin(pk, data)`

기존 플러그인을 업데이트합니다.

```python
# 플러그인 설명 및 버전 업데이트
updated_data = {
    'description': '업데이트된 플러그인 설명',
    'version': '1.1.0',
    'configuration': {
        'parameters': {
            'threshold': {'type': 'float', 'default': 0.7},
            'max_items': {'type': 'int', 'default': 200},
            'new_param': {'type': 'string', 'default': 'default_value'}
        }
    }
}

updated_plugin = client.update_plugin(123, updated_data)
```

**매개변수:**

- `pk` (int): 플러그인 ID
- `data` (dict): 업데이트된 플러그인 데이터

**반환값:**

- `dict`: 업데이트된 플러그인 정보

### `run_plugin(pk, data)`

지정된 매개변수로 플러그인을 실행합니다.

```python
# 매개변수와 함께 플러그인 실행
execution_data = {
    'parameters': {
        'threshold': 0.8,
        'max_items': 150,
        'input_path': '/data/input/',
        'output_path': '/data/output/'
    },
    'context': {
        'project_id': 123,
        'user_id': 456,
        'execution_mode': 'batch'
    }
}

result = client.run_plugin(123, execution_data)
print(f"플러그인 실행 시작됨: {result['job_id']}")
```

**매개변수:**

- `pk` (int): 플러그인 ID
- `data` (dict): 실행 매개변수 및 컨텍스트

**실행 데이터 구조:**

- `parameters` (dict): 플러그인별 매개변수
- `context` (dict): 실행 컨텍스트 정보

**반환값:**

- `dict`: 작업 정보가 포함된 실행 결과

## 플러그인 릴리스 관리

### `get_plugin_release(pk, params=None)`

특정 플러그인 릴리스에 대한 정보를 가져옵니다.

```python
# 릴리스 정보 가져오기
release = client.get_plugin_release(456)
print(f"플러그인 {release['plugin']}의 릴리스 {release['version']}")

# 확장된 플러그인 정보와 함께 릴리스 가져오기
release = client.get_plugin_release(456, params={'expand': 'plugin'})
```

**매개변수:**

- `pk` (int): 플러그인 릴리스 ID
- `params` (dict, 선택사항): 쿼리 매개변수

**반환값:**

- `dict`: 플러그인 릴리스 정보

### `create_plugin_release(data)`

파일 업로드와 함께 새로운 플러그인 릴리스를 생성합니다.

```python
# 플러그인 릴리스 생성
release_data = {
    'plugin': 123,
    'version': '2.0.0',
    'changelog': '새로운 기능 및 버그 수정 추가',
    'is_stable': True,
    'file': open('/path/to/plugin_v2.zip', 'rb')
}

new_release = client.create_plugin_release(release_data)
print(f"릴리스 생성됨: {new_release['id']}")
```

**매개변수:**

- `data` (dict): 파일을 포함한 릴리스 데이터

**릴리스 데이터 구조:**

- `plugin` (int, 필수): 플러그인 ID
- `version` (str, 필수): 릴리스 버전
- `changelog` (str): 릴리스 노트
- `is_stable` (bool): 안정 릴리스 여부
- `file` (file object, 필수): 플러그인 패키지 파일

**반환값:**

- `dict`: 생성된 플러그인 릴리스 정보

## 작업 관리

### `get_job(pk, params=None)`

작업에 대한 상세 정보를 가져옵니다.

```python
# 기본 작업 정보 가져오기
job = client.get_job(789)
print(f"작업 {job['id']}: {job['status']}")

# 로그와 함께 작업 가져오기
job = client.get_job(789, params={'expand': 'logs'})
print(f"작업 로그: {job['logs']}")
```

**매개변수:**

- `pk` (int): 작업 ID
- `params` (dict, 선택사항): 쿼리 매개변수

**일반적인 params:**

- `expand`: 추가 데이터 포함 (`logs`, `metrics`, `result`)

**반환값:**

- `dict`: 완전한 작업 정보

### `list_jobs(params=None)`

필터링 옵션과 함께 작업을 나열합니다.

```python
# 모든 작업 나열
jobs = client.list_jobs()

# 상태별 작업 나열
running_jobs = client.list_jobs(params={'status': 'running'})

# 특정 플러그인의 작업 나열
plugin_jobs = client.list_jobs(params={'plugin': 123})

# 최근 작업 나열
from datetime import datetime, timedelta
recent_date = (datetime.now() - timedelta(days=7)).isoformat()
recent_jobs = client.list_jobs(params={'created_after': recent_date})
```

**매개변수:**

- `params` (dict, 선택사항): 필터링 매개변수

**일반적인 필터링 params:**

- `status`: 작업 상태로 필터링 (`queued`, `running`, `completed`, `failed`)
- `plugin`: 플러그인 ID로 필터링
- `created_after`: 생성 날짜로 필터링
- `user`: 사용자 ID로 필터링

**반환값:**

- `tuple`: (jobs_list, total_count)

### `update_job(pk, data)`

작업 상태 또는 메타데이터를 업데이트합니다.

```python
# 작업 상태 업데이트
client.update_job(789, {'status': 'completed'})

# 결과 데이터와 함께 작업 업데이트
client.update_job(789, {
    'status': 'completed',
    'result': {
        'output_files': ['file1.txt', 'file2.txt'],
        'metrics': {'accuracy': 0.95, 'processing_time': 120}
    }
})

# 작업 진행률 업데이트
client.update_job(789, {
    'progress': 75,
    'status': 'running',
    'metadata': {'current_step': 'processing_images'}
})
```

**매개변수:**

- `pk` (int): 작업 ID
- `data` (dict): 업데이트 데이터

**업데이트 가능한 필드:**

- `status`: 작업 상태
- `progress`: 진행률 백분율 (0-100)
- `result`: 작업 결과 데이터
- `metadata`: 추가 작업 메타데이터

**반환값:**

- `dict`: 업데이트된 작업 정보

### `list_job_console_logs(pk)`

특정 작업의 콘솔 로그를 가져옵니다.

```python
# 작업 콘솔 로그 가져오기
logs = client.list_job_console_logs(789)
for log_entry in logs:
    print(f"[{log_entry['timestamp']}] {log_entry['level']}: {log_entry['message']}")
```

**매개변수:**

- `pk` (int): 작업 ID

**반환값:**

- `list`: 타임스탬프와 레벨이 포함된 콘솔 로그 항목

## 스토리지 관리

### `list_storages()`

사용 가능한 모든 스토리지 구성을 나열합니다.

```python
storages = client.list_storages()
for storage in storages:
    print(f"스토리지: {storage['name']} ({storage['provider']})")
```

**반환값:**

- `list`: 사용 가능한 스토리지 구성

### `get_storage(pk)`

특정 스토리지에 대한 상세 정보를 가져옵니다.

```python
storage = client.get_storage(123)
print(f"스토리지: {storage['name']}")
print(f"제공업체: {storage['provider']}")
print(f"구성: {storage['configuration']}")
```

**매개변수:**

- `pk` (int): 스토리지 ID

**반환값:**

- `dict`: 완전한 스토리지 구성

### `create_storage(data)`

새로운 스토리지 구성을 생성합니다.

```python
# Amazon S3 스토리지 생성
s3_storage = client.create_storage({
    'name': 'My S3 Storage',
    'provider': 'amazon_s3',
    'category': 'external',
    'configuration': {
        'bucket_name': 'my-bucket',
        'region': 'us-west-2',
        'access_key_id': 'YOUR_ACCESS_KEY',
        'secret_access_key': 'YOUR_SECRET_KEY'
    }
})

# 로컬 파일 시스템 스토리지 생성
local_storage = client.create_storage({
    'name': 'Local Storage',
    'provider': 'file_system',
    'category': 'internal',
    'configuration': {
        'base_path': '/data/storage',
        'permissions': '755'
    }
})
```

**매개변수:**

- `data` (dict): 스토리지 구성

**스토리지 데이터 구조:**

- `name` (str, 필수): 스토리지 이름
- `provider` (str, 필수): 스토리지 제공업체 유형
- `category` (str): 스토리지 카테고리 (`internal`, `external`)
- `configuration` (dict): 제공업체별 구성

**지원되는 제공업체:**

- `amazon_s3`: Amazon S3
- `azure`: Azure Blob Storage
- `gcp`: Google Cloud Storage
- `file_system`: 로컬 파일 시스템
- `ftp`, `sftp`: FTP 프로토콜
- `minio`: MinIO 스토리지

**반환값:**

- `dict`: 생성된 스토리지 구성

## 오류 처리

```python
from synapse_sdk.clients.exceptions import ClientError

def robust_plugin_execution(plugin_id, parameters, max_retries=3):
    """오류 처리 및 재시도가 있는 플러그인 실행."""
    for attempt in range(max_retries):
        try:
            result = client.run_plugin(plugin_id, {
                'parameters': parameters,
                'context': {'retry_attempt': attempt}
            })
            return result
        except ClientError as e:
            if e.status_code == 404:
                print(f"플러그인 {plugin_id}을 찾을 수 없음")
                break
            elif e.status_code == 400:
                print(f"잘못된 매개변수: {e.response}")
                break
            elif e.status_code >= 500:
                print(f"서버 오류 (시도 {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 지수 백오프
            else:
                print(f"예상치 못한 오류: {e}")
                break

    return None
```

## 참고

- [BackendClient](./backend.md) - 메인 백엔드 클라이언트
- [AnnotationClientMixin](./annotation-mixin.md) - 태스크 및 어노테이션 작업
- [MLClientMixin](./ml-mixin.md) - 머신러닝 작업
