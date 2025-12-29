---
id: migration
title: 마이그레이션 가이드 (v1에서 v2로)
sidebar_position: 4
---

# 마이그레이션 가이드 (v1에서 v2로)

이 가이드는 synapse-sdk v1과 v2 사이의 변경 사항을 다루며, 코드 업데이트가 필요한 주요 변경 사항과 새로운 기능을 포함합니다.

## 주요 변경 사항 (Breaking Changes)

v1에서 마이그레이션할 때 **코드 업데이트가 필요한** 변경 사항:

| v1 | v2 | 마이그레이션 방법 |
|----|----|-----------------|
| `get_action_class(category, action)` | `get_action_method(config, action)` | category 문자열 대신 config dict 전달 |
| `action_class.method` | `get_action_method(config, action)` | method가 이제 클래스 속성이 아닌 config에서 읽힘 |
| `@register_action` 데코레이터 | 제거됨 | `config.yaml`에 정의하거나 `PluginDiscovery.from_module()` 사용 |
| `_REGISTERED_ACTIONS` 전역 변수 | 제거됨 | 액션 조회에 `PluginDiscovery` 사용 |
| `get_storage('s3://...')` URL 문자열 | Dict 전용 config | `get_storage({'provider': 's3', 'configuration': {...}})` 사용 |
| `from ... import FileSystemStorage` | `from ... import LocalStorage` | 클래스 이름 변경 |
| `from ... import GCPStorage` | `from ... import GCSStorage` | 클래스 이름 변경 |
| `BaseStorage` ABC 상속 | `StorageProtocol` 구현 | 상속 대신 구조적 타이핑(duck typing) 사용 |

## 하위 호환 변경 사항

이 변경 사항들은 **하위 호환됨** - 기존 코드가 계속 작동합니다:

| 기능 | 참고 |
|-----|------|
| Provider 별칭 `file_system` | 계속 작동, `LocalStorage`로 매핑 |
| Provider 별칭 `gcp`, `gs` | 계속 작동, `GCSStorage`로 매핑 |
| `get_plugin_actions()` | 동일한 API |
| `read_requirements()` | 동일한 API |
| `get_pathlib()` | 동일한 API |
| `get_path_file_count()` | 동일한 API |
| `get_path_total_size()` | 동일한 API |

---

## Plugin Utils

### 이전 (synapse-sdk v1)

```python
from synapse_sdk.plugins.utils import get_action_class, get_plugin_actions, read_requirements

# 액션 클래스를 로드하여 run method 가져오기
action_method = get_action_class(config['category'], action).method
```

### 신규 (synapse-sdk v2)

```python
from synapse_sdk.plugins.utils import get_action_method, get_plugin_actions, read_requirements

# config에서 직접 run method 가져오기 (클래스 로딩 불필요)
action_method = get_action_method(config, action)
```

---

## Plugin Types

### 이전

```python
from synapse_sdk.plugins.enums import PluginCategory
from synapse_sdk.plugins.base import RunMethod
```

### 신규

```python
from synapse_sdk.plugins.enums import PluginCategory, RunMethod
```

---

## Plugin Discovery

**새 기능** - config 파일이나 Python 모듈에서 액션 검색:

```python
from synapse_sdk.plugins.discovery import PluginDiscovery

# config.yaml에서
discovery = PluginDiscovery.from_path('/path/to/plugin')
discovery.list_actions()  # ['train', 'inference', 'export']

# Python 모듈에서 (@action 데코레이터와 BaseAction 서브클래스 자동 검색)
import plugin
discovery = PluginDiscovery.from_module(plugin)
```

---

## Storage Utils

### 이전 (synapse-sdk v1)

```python
from synapse_sdk.utils.storage import get_storage, get_pathlib

# URL 문자열 또는 dict config
storage = get_storage('s3://bucket?access_key=KEY&secret_key=SECRET')
# 또는 dict config
storage = get_storage({'provider': 'file_system', 'configuration': {'location': '/data'}})
```

### 신규 (synapse-sdk v2)

```python
from synapse_sdk.utils.storage import get_storage, get_pathlib

# Dict 전용 config (URL 문자열 파싱 제거됨)
storage = get_storage({'provider': 'local', 'configuration': {'location': '/data'}})

# S3 예시
storage = get_storage({
    'provider': 's3',
    'configuration': {
        'bucket_name': 'my-bucket',
        'access_key': 'AKIAIOSFODNN7EXAMPLE',
        'secret_key': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
        'region_name': 'us-east-1',
    }
})
```

### Provider 이름 변경

- `file_system` -> `local` (별칭 `file_system`은 계속 작동)
- `FileSystemStorage` -> `LocalStorage`
- `GCPStorage` -> `GCSStorage`

---

## v2의 새 기능

| 기능 | 설명 |
|-----|------|
| `PluginDiscovery` | config 파일이나 Python 모듈에서 액션 검색 |
| `PluginDiscovery.from_module()` | `@action` 데코레이터와 `BaseAction` 서브클래스 자동 검색 |
| `StorageProtocol` | 커스텀 스토리지 구현을 위한 Protocol 기반 인터페이스 |
| `HTTPStorage` provider | HTTP 파일 서버용 새 provider |
| Plugin Upload 유틸리티 | `archive_and_upload()`, `build_and_upload()`, `download_and_upload()` |
| 파일 유틸리티 | `calculate_checksum()`, `create_archive()`, `create_archive_from_git()` |
| `AsyncAgentClient` | WebSocket/HTTP 스트리밍을 지원하는 비동기 클라이언트 |
| `tail_job_logs()` | 프로토콜 자동 선택으로 job 로그 스트리밍 |

---

## 참고 문서

- [설치](./installation.md) - 스토리지 extras를 포함한 설치 옵션
- [Storage Providers](./features/utils/storage.md) - 상세 스토리지 설정
- [AgentClient](./api/clients/agent.md) - 동기/비동기 클라이언트 사용법
- [RayClient](./api/clients/ray.md) - Job 로그 스트리밍
