---
id: ray
title: RayClientMixin
sidebar_position: 4
---

# RayClientMixin

Ray 클러스터 관리 및 실시간 로그 스트리밍을 위한 Mixin.

## 개요

`RayClientMixin`은 job 관리, 실시간 로그 스트리밍 (WebSocket/HTTP), 노드 모니터링, Ray Serve 애플리케이션 제어를 포함한 Ray 클러스터 작업을 제공합니다. `AgentClient` (동기) 및 `AsyncAgentClient` (비동기) 모두에 포함되어 있습니다.

## 주요 기능

- **Job 관리**: Ray job 목록, 조회, 중지
- **실시간 로그 스트리밍**: 자동 대체 기능이 있는 WebSocket 및 HTTP 기반 로그 테일링
- **노드 모니터링**: 클러스터 노드 모니터링
- **Task 모니터링**: task 실행 추적
- **Ray Serve**: serve 애플리케이션 배포 및 관리
- **리소스 보호**: 메모리 고갈 방지를 위한 StreamLimits

---

## 로그 스트리밍

### tail_job_logs()

자동 프로토콜 선택이 있는 통합 스트리밍 메서드.

```python
def tail_job_logs(
    job_id: str,
    timeout: float = 30.0,
    *,
    protocol: Literal['websocket', 'http', 'auto'] = 'auto'
) -> Generator[str, None, None]
```

**매개변수:**

- `job_id` (str): Ray job ID (예: `'raysubmit_abc123'`)
- `timeout` (float): 연결 타임아웃 초 단위 (기본값: 30)
- `protocol`: 프로토콜 선택:
  - `'auto'` (기본값): WebSocket 먼저 시도, 실패 시 HTTP로 대체
  - `'websocket'`: WebSocket만 사용 (가장 낮은 지연시간)
  - `'http'`: HTTP chunked 스트리밍만 사용 (호환성 높음)

**반환:** 문자열로 된 로그 라인

**예제:**

```python
# 자동 프로토콜 선택 (권장)
for line in client.tail_job_logs('raysubmit_abc123'):
    print(line)

# 명시적 WebSocket
for line in client.tail_job_logs('raysubmit_abc123', protocol='websocket'):
    print(line)

# 명시적 HTTP 스트리밍
for line in client.tail_job_logs('raysubmit_abc123', protocol='http'):
    print(line)

# 사용자 정의 타임아웃으로
for line in client.tail_job_logs('raysubmit_abc123', timeout=60):
    if 'ERROR' in line:
        break
```

### websocket_tail_job_logs()

가장 낮은 지연시간을 위한 직접 WebSocket 스트리밍.

```python
def websocket_tail_job_logs(
    job_id: str,
    timeout: float = 30.0
) -> Generator[str, None, None]
```

**필요:** `websocket-client` 패키지 (동기) 또는 `websockets` 패키지 (비동기)

```python
for line in client.websocket_tail_job_logs('raysubmit_abc123'):
    print(line)
```

### stream_tail_job_logs()

대체용 HTTP chunked transfer 스트리밍.

```python
def stream_tail_job_logs(
    job_id: str,
    timeout: float = 30.0
) -> Generator[str, None, None]
```

```python
for line in client.stream_tail_job_logs('raysubmit_abc123'):
    print(line)
```

---

## 비동기 스트리밍

`AsyncAgentClient`의 경우 모든 스트리밍 메서드가 `AsyncGenerator`를 반환합니다:

```python
from synapse_sdk.clients.agent import AsyncAgentClient

async with AsyncAgentClient(base_url, agent_token) as client:
    # 자동 프로토콜
    async for line in client.tail_job_logs('raysubmit_abc123'):
        print(line)

    # WebSocket
    async for line in client.websocket_tail_job_logs('raysubmit_abc123'):
        print(line)

    # HTTP
    async for line in client.stream_tail_job_logs('raysubmit_abc123'):
        print(line)
```

---

## 스트림 제한

메모리 고갈 방지를 위한 리소스 제한 설정:

```python
from synapse_sdk.utils.network import StreamLimits

# 사용자 정의 제한 설정
client.stream_limits = StreamLimits(
    max_messages=10_000,     # 최대 WebSocket 메시지 수
    max_lines=50_000,        # 최대 HTTP 라인 수
    max_bytes=50*1024*1024,  # 총 50MB
    max_message_size=10_240  # 메시지당 10KB
)
```

제한 초과 시 상태 코드 429와 함께 `ClientError`가 발생합니다.

---

## Job 작업

### list_jobs()

클러스터의 모든 Ray job 목록.

```python
jobs = client.list_jobs()
for job in jobs:
    print(f"Job {job['job_id']}: {job['status']}")
```

### get_job()

특정 job의 상세 정보.

```python
job = client.get_job('raysubmit_abc123')
print(f"Status: {job['status']}")
print(f"Start time: {job['start_time']}")
```

### get_job_logs()

job의 모든 로그 가져오기 (스트리밍 아님).

```python
logs = client.get_job_logs('raysubmit_abc123')
print(logs)
```

### stop_job()

실행 중인 job 중지.

```python
result = client.stop_job('raysubmit_abc123')
print(f"Stopped: {result}")
```

---

## Node 작업

### list_nodes()

Ray 클러스터의 모든 노드 목록.

```python
nodes = client.list_nodes()
for node in nodes:
    print(f"Node {node['node_id']}: {node['state']}")
```

### get_node()

특정 노드의 상세 정보.

```python
node = client.get_node('node-abc123')
print(f"Alive: {node['alive']}")
```

---

## Task 작업

### list_tasks()

클러스터의 모든 task 목록.

```python
tasks = client.list_tasks()
```

### get_task()

특정 task의 상세 정보.

```python
task = client.get_task('task-xyz789')
```

---

## Ray Serve 작업

### list_serve_applications()

모든 Ray Serve 애플리케이션 목록.

```python
apps = client.list_serve_applications()
```

### get_serve_application()

serve 애플리케이션의 상세 정보.

```python
app = client.get_serve_application('my-app')
print(f"Status: {app['status']}")
```

### delete_serve_application()

serve 애플리케이션 삭제.

```python
client.delete_serve_application('my-app')
```

---

## 오류 처리

```python
from synapse_sdk.clients.exceptions import ClientError

try:
    for line in client.tail_job_logs('invalid-job'):
        print(line)
except ClientError as e:
    if e.status_code == 400:
        print("잘못된 job ID 형식")
    elif e.status_code == 429:
        print("스트림 제한 초과")
    elif e.status_code == 500:
        print("WebSocket 라이브러리 미설치")
    elif e.status_code == 503:
        print("연결 실패")
```

### 오류 코드

| 코드 | 의미 |
|-----|------|
| 400 | 잘못된 job ID, 타임아웃, 또는 프로토콜 |
| 404 | 리소스를 찾을 수 없음 |
| 408 | 연결 타임아웃 |
| 429 | 스트림 제한 초과 |
| 500 | 라이브러리 없음 또는 내부 오류 |
| 503 | 연결 실패 또는 종료됨 |

---

## 모범 사례

### 프로토콜 선택

```python
# 자동으로 대체 처리 (프로덕션 권장)
for line in client.tail_job_logs(job_id, protocol='auto'):
    process(line)

# 인터랙티브 모니터링에 WebSocket 사용
for line in client.tail_job_logs(job_id, protocol='websocket'):
    display_realtime(line)

# 프록시/방화벽 호환성을 위해 HTTP 사용
for line in client.tail_job_logs(job_id, protocol='http'):
    log(line)
```

### 오류 복구

```python
import time

def robust_streaming(client, job_id, max_retries=3):
    for attempt in range(max_retries):
        try:
            for line in client.tail_job_logs(job_id):
                yield line
            break
        except ClientError as e:
            if e.status_code == 503 and attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 지수 백오프
                continue
            raise
```

### 스트림 제한 설정

```python
# 대용량 프로덕션 로그
client.stream_limits = StreamLimits(
    max_messages=50_000,
    max_lines=100_000,
    max_bytes=200 * 1024 * 1024  # 200MB
)

# 제한된 개발 환경
client.stream_limits = StreamLimits(
    max_messages=1_000,
    max_lines=5_000,
    max_bytes=10 * 1024 * 1024  # 10MB
)
```

---

## 참고 문서

- [AgentClient](./agent.md) - Ray mixin이 포함된 메인 클라이언트
- [Network Utilities](../../features/utils/network.md) - StreamLimits 및 유효성 검사
- [BaseClient](./base.md) - 기본 클라이언트 구현
