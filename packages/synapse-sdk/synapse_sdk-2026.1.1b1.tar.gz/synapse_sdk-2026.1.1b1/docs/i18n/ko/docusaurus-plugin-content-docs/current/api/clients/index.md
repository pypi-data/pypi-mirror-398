---
id: index
title: 클라이언트 API
sidebar_position: 1
---

# 클라이언트 API

Synapse SDK는 다양한 백엔드 서비스 및 시스템과 상호 작용하기 위한 포괄적인 클라이언트 라이브러리를 제공합니다. 이 섹션에서는 사용 가능한 모든 클라이언트 API와 사용법을 문서화합니다.

## 개요

클라이언트 API는 여러 카테고리로 구성됩니다:

### 핵심 클라이언트

- **[BackendClient](./backend.md)** - Synapse 백엔드 작업을 위한 메인 클라이언트
- **[BaseClient](./base.md)** - 공통 기능을 가진 기본 클라이언트
- **[AgentClient](./agent.md)** - 에이전트별 작업
- **[RayClient](./ray.md)** - Ray 분산 컴퓨팅 통합

### 백엔드 클라이언트 믹스인

BackendClient는 집중된 기능을 제공하는 여러 전문화된 믹스인으로 구성됩니다:

- **[AnnotationClientMixin](./annotation-mixin.md)** - 태스크 및 어노테이션 관리
- **[CoreClientMixin](./core-mixin.md)** - 핵심 파일 업로드 작업
- **[DataCollectionClientMixin](./data-collection-mixin.md)** - 데이터 수집 및 파일 관리
- **[HITLClientMixin](./hitl-mixin.md)** - Human-in-the-loop 워크플로
- **[IntegrationClientMixin](./integration-mixin.md)** - 플러그인 및 작업 관리
- **[MLClientMixin](./ml-mixin.md)** - 머신러닝 작업

## 빠른 시작

### 기본 백엔드 클라이언트 사용법

```python
from synapse_sdk.clients.backend import BackendClient

# 클라이언트 초기화
client = BackendClient(
    base_url="https://api.synapse.sh",
    api_token="your-api-token"
)

# 어노테이션 작업 사용
tasks = client.list_tasks(params={'project': 123})

# 데이터 컬렉션 작업 사용
collections = client.list_data_collection()

# ML 작업 사용
models = client.list_models(params={'project': 123})
```

### 환경 구성

```python
import os

# 환경 변수 설정
os.environ['SYNAPSE_API_TOKEN'] = "your-api-token"
os.environ['SYNAPSE_AGENT_TOKEN'] = "your-agent-token"

# 클라이언트가 자동으로 환경 변수 사용
client = BackendClient(base_url="https://api.synapse.sh")
```

## 인증

모든 클라이언트는 여러 인증 방법을 지원합니다:

### API 토큰 인증

```python
client = BackendClient(
    base_url="https://api.synapse.sh",
    api_token="your-api-token"
)
```

### 환경 변수 인증

```python
# SYNAPSE_API_TOKEN 환경 변수 설정
client = BackendClient(base_url="https://api.synapse.sh")
```

### 에이전트 토큰 인증 (에이전트용)

```python
client = BackendClient(
    base_url="https://api.synapse.sh",
    agent_token="your-agent-token"
)
```

## 일반적인 패턴

### 오류 처리

```python
from synapse_sdk.clients.exceptions import ClientError

try:
    result = client.get_project(123)
except ClientError as e:
    if e.status_code == 404:
        print("프로젝트를 찾을 수 없음")
    elif e.status_code == 403:
        print("권한이 거부됨")
    else:
        print(f"API 오류: {e}")
```

### 페이지네이션

```python
# 수동 페이지네이션
page1 = client.list_tasks(params={'page': 1, 'page_size': 50})

# 자동 페이지네이션 (권장)
all_tasks = client.list_tasks(list_all=True)
```

### 일괄 작업

```python
# 여러 태스크 생성
tasks_data = [
    {'project': 123, 'data_unit': 789},
    {'project': 123, 'data_unit': 790},
    {'project': 123, 'data_unit': 791}
]
created_tasks = client.create_tasks(tasks_data)

# 여러 할당에 태그 설정
client.set_tags_assignments({
    'assignment_ids': [1, 2, 3],
    'tag_ids': [10, 11]
})
```

### 파일 작업

```python
from pathlib import Path

# 청크 업로드로 대용량 파일 업로드
result = client.create_chunked_upload(Path('/path/to/large_file.zip'))

# 데이터 파일 생성
data_file = client.create_data_file(
    Path('/path/to/data.jpg'),
    use_chunked_upload=True
)
```

## 사용 사례별 클라이언트 기능

### 어노테이션 워크플로

**AnnotationClientMixin** 사용:

- 어노테이션 프로젝트 관리
- 태스크 생성 및 할당
- 어노테이션 데이터 제출
- 태스크 태깅 및 조직

**주요 메서드:**

- `list_tasks()`, `create_tasks()`, `annotate_task_data()`
- `get_project()`, `set_tags_tasks()`

### 데이터 관리

**DataCollectionClientMixin** 사용:

- 데이터 컬렉션 관리
- 파일 및 데이터셋 업로드
- 데이터 유닛 생성
- 일괄 데이터 처리

**주요 메서드:**

- `list_data_collection()`, `get_data_collection()`
- `create_data_file()`, `upload_data_file()`
- `create_data_units()`

### Human-in-the-Loop

**HITLClientMixin** 사용:

- 인간 검토 할당 관리
- 품질 관리 워크플로
- 할당 배포
- 성능 분석

**주요 메서드:**

- `list_assignments()`, `get_assignment()`
- `set_tags_assignments()`

### 시스템 통합

**IntegrationClientMixin** 사용:

- 플러그인 개발 및 관리
- 작업 실행 및 모니터링
- 스토리지 구성
- 에이전트 상태 모니터링

**주요 메서드:**

- `create_plugin()`, `run_plugin()`
- `list_jobs()`, `update_job()`
- `create_storage()`, `health_check_agent()`

### 머신러닝

**MLClientMixin** 사용:

- 모델 관리 및 배포
- 그라운드 트루스 데이터 작업
- 모델 평가 워크플로
- 훈련 데이터 준비

**주요 메서드:**

- `create_model()`, `list_models()`
- `list_ground_truth_events()`, `get_ground_truth_version()`

### 핵심 작업

**CoreClientMixin** 사용:

- 대용량 파일 업로드
- 청크 업로드 작업
- 파일 무결성 검증

**주요 메서드:**

- `create_chunked_upload()`

## 완전한 워크플로 예제

### 엔드투엔드 데이터 처리

```python
def complete_data_workflow():
    client = BackendClient(
        base_url="https://api.synapse.sh",
        api_token="your-token"
    )

    # 1. 데이터 수집
    collection = client.get_data_collection(123)
    data_file = client.create_data_file(Path('/data/image.jpg'))

    # 2. 태스크 생성
    tasks = client.create_tasks([
        {'project': 123, 'data_unit': data_file['data_unit_id']}
    ])

    # 3. 할당 관리
    assignments = client.list_assignments(params={'project': 123})

    # 4. 모델 작업
    models = client.list_models(params={'project': 123})

    return {
        'data_file': data_file,
        'tasks': tasks,
        'assignments': assignments,
        'models': models
    }
```

### 플러그인 개발 및 배포

```python
def plugin_deployment_workflow():
    client = BackendClient(
        base_url="https://api.synapse.sh",
        api_token="your-token"
    )

    # 1. 플러그인 생성
    plugin = client.create_plugin({
        'name': 'My Plugin',
        'description': '사용자 정의 처리 플러그인'
    })

    # 2. 릴리스 생성
    with open('plugin.zip', 'rb') as f:
        release = client.create_plugin_release({
            'plugin': plugin['id'],
            'version': '1.0.0',
            'file': f
        })

    # 3. 플러그인 실행
    job = client.run_plugin(plugin['id'], {
        'parameters': {'threshold': 0.8}
    })

    # 4. 실행 모니터링
    job_status = client.get_job(job['job_id'])

    return {
        'plugin': plugin,
        'release': release,
        'job': job_status
    }
```

## 모범 사례

### 성능 최적화

- 완전한 데이터셋에 대해 `list_all=True` 사용하여 자동으로 페이지네이션 처리
- 50MB보다 큰 파일에 청크 업로드 사용
- 중요한 작업에 재시도 로직 구현
- 가능한 경우 일괄 작업 사용

### 오류 처리

- 항상 try-catch 블록으로 API 호출 감싸기
- 특정 오류 코드 확인 (404, 403, 429, 500)
- 요청 제한에 지수 백오프 구현
- 충분한 컨텍스트로 오류 로깅

### 리소스 관리

- 파일 핸들 즉시 닫기
- 파일 작업에 컨텍스트 매니저 사용
- 대용량 업로드 시 메모리 사용량 모니터링
- 임시 리소스 정리

### 보안

- API 토큰을 안전하게 저장 (환경 변수)
- HTTPS 엔드포인트만 사용
- 파일 경로 및 입력 검증
- 적절한 액세스 제어 구현

## 마이그레이션 가이드

이전 SDK 버전에서 마이그레이션할 때:

1. **임포트 업데이트**: 새로운 믹스인 구조로 인해 임포트 업데이트가 필요할 수 있음
2. **메서드 시그니처 확인**: 일부 메서드의 매개변수가 업데이트되었을 수 있음
3. **오류 처리**: 오류 유형 및 상태 코드가 변경되었을 수 있음
4. **구성**: 인증 방법이 개선되었을 수 있음

## 문제 해결

### 일반적인 문제

**인증 오류 (401/403)**

- API 토큰이 올바르고 만료되지 않았는지 확인
- 요청된 작업에 대한 토큰 권한 확인
- 올바른 기본 URL 확인

**요청 제한 (429)**

- 지수 백오프 구현
- 요청 빈도 감소
- 가능한 경우 일괄 작업 사용

**파일 업로드 실패**

- 파일 크기 제한 확인
- 파일 권한 확인
- 대용량 파일에 청크 업로드 사용
- 네트워크 연결 확인

**연결 시간 초과**

- 시간 초과 설정 증가
- 네트워크 안정성 확인
- 서버 가용성 확인

## 지원

추가 지원이 필요한 경우:

- [문제 해결 가이드](../../troubleshooting.md) 확인
- [예제](../../examples/index.md) 검토
- [FAQ](../../faq.md) 참조