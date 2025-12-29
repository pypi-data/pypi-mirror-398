---
id: gradio-playground
title: Synapse Playground (Container)
sidebar_position: 2
---

# Synapse Playground

Synapse Playground는 사용자가 플러그인의 기능을 웹 브라우저에서 직접 테스트하고 체험할 수 있는 대화형 UI 환경입니다. 이 시스템은 플러그인을 Gradio 애플리케이션을 호스팅하는 격리된 Docker 컨테이너로 실행하며, Agent의 컨테이너 API를 통해 관리됩니다.

## 개요

### Synapse Playground란?

Synapse Playground는 플러그인을 설치하거나 별도의 환경 설정 없이도 웹 기반 Gradio 인터페이스를 통해 플러그인 기능과 상호작용할 수 있게 해줍니다. SDK는 `ContainerClientMixin`을 제공하여 Agent와 통신하고, Agent는 모든 Docker 컨테이너 라이프사이클 관리를 담당합니다.

### 주요 특징

- **Agent 관리 컨테이너**: Agent가 Docker 컨테이너 생성, 모니터링, 정리를 담당
- **자동 재시작**: 동일한 플러그인과 모델을 가진 기존 컨테이너는 새로 생성하지 않고 재시작
- **동적 포트 할당**: 자동 포트 할당으로 동시 실행 컨테이너 간 충돌 방지
- **플러그인 아카이브 업로드**: 로컬 플러그인 아카이브 직접 업로드 지원
- **컨테이너 추적**: 데이터베이스 기반 컨테이너 상태 추적으로 안정성 확보

## 아키텍처

### 시스템 구성 요소

```
SDK (ContainerClientMixin)
    |
    | HTTP API 호출
    v
Agent (Container ViewSet)
    |
    | Docker SDK
    v
Docker Engine
    |
    v
Plugin Container (Gradio App, 7860 포트)
```

| 구성 요소 | 역할 | 설명 |
|-----------|------|------|
| **SDK ContainerClientMixin** | 클라이언트 인터페이스 | Agent의 컨테이너 API와 상호작용하는 Python 메서드 제공 |
| **Agent Container ViewSet** | 컨테이너 관리 | Docker 작업 처리: 빌드, 실행, 중지, 제거 |
| **Docker Engine** | 런타임 | 호스트에서 격리된 컨테이너 실행 |
| **Plugin Container** | Gradio 호스트 | 플러그인의 Gradio 인터페이스를 7860 포트에서 실행 |

### 컨테이너 라이프사이클

1. **생성 요청**: SDK가 Agent에 컨테이너 생성 요청 전송
2. **중복 확인**: Agent가 동일한 `plugin_release` + `model`을 가진 컨테이너 존재 여부 확인
3. **재시작 또는 빌드**: 존재하면 재시작, 아니면 플러그인으로 새 이미지 빌드
4. **포트 할당**: Agent가 7860-8860 범위에서 사용 가능한 포트 탐색
5. **컨테이너 실행**: 포트 매핑과 환경 변수와 함께 Docker 컨테이너 시작
6. **엔드포인트 반환**: Agent가 SDK에 Gradio 엔드포인트 URL 반환

## SDK 사용법

### ContainerClientMixin

`ContainerClientMixin`은 `AgentClient`에 포함되어 있으며 컨테이너 관리 메서드를 제공합니다.

```python
from synapse_sdk.clients.agent import AgentClient

client = AgentClient(host="http://agent-url:8000", token="your-token")
```

### 컨테이너 생성

#### Plugin Release 문자열 사용

```python
response = client.create_container(
    plugin_release="my-plugin@1.0.0",
    model=123,  # 선택사항: 컨테이너를 모델과 연결
    params={"input_size": 512},  # PLUGIN_PARAMS 환경 변수로 플러그인에 전달
    envs={"CUDA_VISIBLE_DEVICES": "0"},  # 추가 환경 변수
    labels=["gradio", "production"],  # 필터링용 컨테이너 레이블
    metadata={"created_by": "admin"}  # 저장할 메타데이터
)

# 응답
{
    'id': 'abc123def456...',
    'status': 'running',
    'name': 'quirky_einstein',
    'image': 'synapse-plugin-my-plugin-1.0.0',
    'endpoint': 'http://10.0.22.1:7860'
}
```

#### PluginRelease 객체 사용

```python
from synapse_sdk.plugins.models import PluginRelease

# 액션 정의가 포함된 config를 가진 PluginRelease
plugin_release = PluginRelease(config={
    'code': 'my-plugin',
    'version': '1.0.0',
    'actions': {
        'gradio': {'entrypoint': 'plugin.gradio_interface.app'}
    }
})

response = client.create_container(
    plugin_release=plugin_release,
    params={"batch_size": 32}
)
```

#### 플러그인 아카이브 업로드

```python
# 로컬 플러그인 아카이브를 업로드하고 컨테이너 생성
response = client.create_container(
    plugin_release="my-plugin@1.0.0",
    plugin_file="/path/to/plugin-release.zip"
)
```

### 컨테이너 재시작 동작

동일한 `plugin_release`와 `model`을 가진 컨테이너가 이미 존재하면, Agent는 새로 생성하지 않고 재시작합니다:

```python
# 첫 번째 호출 - 새 컨테이너 생성
response1 = client.create_container("my-plugin@1.0.0", model=123)
# {'id': 'abc...', 'status': 'running', 'endpoint': 'http://host:7860'}

# 동일한 plugin_release + model로 두 번째 호출 - 기존 컨테이너 재시작
response2 = client.create_container("my-plugin@1.0.0", model=123)
# {'id': 'abc...', 'status': 'running', 'endpoint': 'http://host:7860', 'restarted': True}
```

### 컨테이너 목록 조회

```python
# 모든 컨테이너 목록
result = client.list_containers()
# {'results': [...], 'count': 5}

# 상태로 필터링
result = client.list_containers(params={"status": "running"})

# 페이지네이션 처리하여 모든 컨테이너 가져오기
containers, count = client.list_containers(list_all=True)
for container in containers:
    print(f"{container['name']}: {container['status']}")
```

### 컨테이너 상세 정보 조회

```python
container = client.get_container("abc123def456")
# {
#     'id': 'abc123def456...',
#     'name': 'quirky_einstein',
#     'status': 'running',
#     'image': 'synapse-plugin-my-plugin-1.0.0',
#     'attrs': {...}  # 전체 Docker 컨테이너 속성
# }
```

### 컨테이너 삭제

```python
client.delete_container("abc123def456")
# 컨테이너를 중지하고 제거
```

### 헬스 체크

```python
# Docker 소켓 접근 가능 여부 확인
health = client.health_check()
```

## Agent 측 구현

### Agent의 컨테이너 처리 방식

Agent의 `ContainerViewSet`은 전체 Docker 라이프사이클을 관리합니다:

1. **이미지 빌드**: Dockerfile 생성, 플러그인 파일 복사, requirements 설치
2. **포트 관리**: 데이터베이스와 실행 중인 컨테이너를 스캔하여 사용 가능한 포트 탐색
3. **컨테이너 추적**: 상태 관리를 위해 데이터베이스에 컨테이너 메타데이터 저장
4. **재시작 로직**: 새 컨테이너 생성 전 기존 컨테이너 존재 여부 확인

### 컨테이너 데이터베이스 모델

Agent는 다음 필드로 컨테이너를 추적합니다:

| 필드 | 설명 |
|------|------|
| `container_id` | Docker 컨테이너 ID |
| `plugin_release` | 플러그인 식별자 (예: "my-plugin@1.0.0") |
| `model` | 연결된 모델 ID (nullable) |
| `host_port` | 할당된 호스트 포트 |
| `status` | 컨테이너 상태 |
| `created_at` / `updated_at` | 타임스탬프 |

### 고유 제약 조건

컨테이너는 `(plugin_release, model)` 조합으로 고유하게 식별되며, 이를 통해 새로 생성하지 않고 재시작하는 동작이 가능합니다.

## 플러그인 요구사항

### Playground용 플러그인 구조

플러그인은 Gradio 인터페이스 파일을 포함해야 합니다:

```
my-plugin/
├── config.yaml
├── plugin/
│   ├── __init__.py
│   ├── gradio_interface.py    # 필수: Gradio 앱 정의
│   └── ...
└── requirements.txt           # 의존성 (gradio는 자동 포함)
```

### gradio_interface.py 예제

```python
import gradio as gr

def predict(image):
    # 추론 로직
    result = model.predict(image)
    return result

demo = gr.Interface(
    fn=predict,
    inputs=gr.Image(type="pil"),
    outputs=gr.Label(),
    title="My Plugin Playground"
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
```

### Gradio 액션이 포함된 config.yaml

```yaml
code: my-plugin
name: My Plugin
version: 1.0.0
category: neural_net

actions:
  gradio:
    entrypoint: plugin.gradio_interface.app
    method: job
```

## 환경 변수

컨테이너는 다음 환경 변수를 받습니다:

| 변수 | 설명 |
|------|------|
| `PLUGIN_PARAMS` | `create_container()`에서 전달된 JSON 인코딩 params |
| 사용자 정의 `envs` | `create_container()`에 전달된 추가 변수 |

Gradio 앱에서 접근:

```python
import os
import json

params = json.loads(os.environ.get('PLUGIN_PARAMS', '{}'))
input_size = params.get('input_size', 512)
```

## Docker 요구사항

### 호스트 요구사항

- Agent 호스트에서 Docker Engine 실행 중
- `/var/run/docker.sock` 마운트 (컨테이너화된 Agent의 경우)
- 포트 범위 7860-8860 사용 가능

### 베이스 이미지

Agent는 설정 가능한 베이스 이미지를 사용합니다:

```python
base_image = config.GRADIO_CONTAINER_BASE_IMAGE
```

### 생성되는 Dockerfile

Agent는 각 플러그인에 대해 Dockerfile을 생성합니다:

```dockerfile
FROM {base_image}

COPY . .
RUN pip install --no-cache-dir -r requirements.txt
```

## API 레퍼런스

### create_container()

```python
def create_container(
    plugin_release: Optional[Union[str, PluginRelease]] = None,
    *,
    model: Optional[int] = None,
    params: Optional[Dict[str, Any]] = None,
    envs: Optional[Dict[str, str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    labels: Optional[Iterable[str]] = None,
    plugin_file: Optional[Union[str, Path]] = None,
) -> dict
```

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| `plugin_release` | str 또는 PluginRelease | 플러그인 식별자: `"code@version"` 문자열 또는 PluginRelease 객체 |
| `model` | int | 컨테이너 고유성을 위한 선택적 모델 ID |
| `params` | dict | `PLUGIN_PARAMS` 환경 변수로 전달되는 파라미터 |
| `envs` | dict | 추가 환경 변수 |
| `metadata` | dict | 컨테이너 레코드와 함께 저장되는 메타데이터 |
| `labels` | list[str] | 표시/필터링용 컨테이너 레이블 |
| `plugin_file` | str 또는 Path | 업로드할 로컬 플러그인 아카이브 |

**반환값**: `id`, `status`, `name`, `image`, `endpoint`, 그리고 선택적으로 `restarted`를 포함하는 컨테이너 정보 dict

**예외**:
- `ValueError`: `plugin_release`와 `plugin_file` 모두 제공되지 않음
- `TypeError`: 잘못된 `plugin_release` 타입
- `FileNotFoundError`: `plugin_file` 경로가 존재하지 않음

### list_containers()

```python
def list_containers(
    params: Optional[Dict[str, Any]] = None,
    *,
    list_all: bool = False
) -> Union[dict, tuple]
```

### get_container()

```python
def get_container(container_id: Union[int, str]) -> dict
```

### delete_container()

```python
def delete_container(container_id: Union[int, str]) -> None
```

### health_check()

```python
def health_check() -> dict
```

## 관련 문서

- [플러그인 시스템 개요](../../plugins.md)
- [Agent 클라이언트 API](../../../api/clients/agent.md)
