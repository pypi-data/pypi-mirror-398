---
id: agent
title: AgentClient
sidebar_position: 2
---

# AgentClient

에이전트 작업, job 관리, 분산 실행을 위한 클라이언트.

## 개요

`AgentClient`는 플러그인 실행, Ray job 관리, 실시간 로그 스트리밍을 포함한 에이전트 작업에 대한 접근을 제공합니다. 동기(`AgentClient`) 및 비동기(`AsyncAgentClient`) 버전 모두 사용 가능합니다.

## 설치

```bash
pip install synapse-sdk
```

WebSocket 스트리밍 지원:

```bash
pip install synapse-sdk websocket-client  # 동기 클라이언트
pip install synapse-sdk websockets        # 비동기 클라이언트
```

---

## AgentClient (동기)

### 생성자

```python
AgentClient(
    base_url: str,
    agent_token: str,
    *,
    user_token: str = None,
    tenant: str = None,
    timeout: dict = None
)
```

### 매개변수

- `base_url` (str): 에이전트 서버 URL (예: `"https://agent.example.com"`)
- `agent_token` (str): 에이전트 인증 토큰
- `user_token` (str, optional): 사용자 범위 작업을 위한 사용자 인증 토큰
- `tenant` (str, optional): 멀티테넌트 배포를 위한 테넌트 식별자
- `timeout` (dict, optional): 연결 및 읽기 타임아웃 설정

### 사용법

```python
from synapse_sdk.clients.agent import AgentClient

client = AgentClient(
    base_url="https://agent.example.com",
    agent_token="your-agent-token"
)

# 헬스 체크
status = client.health_check()
print(f"Agent status: {status}")

# Ray job 목록
jobs = client.list_jobs()

# job 로그 스트리밍
for line in client.tail_job_logs('raysubmit_abc123'):
    print(line)
```

---

## AsyncAgentClient (비동기)

### 생성자

```python
AsyncAgentClient(
    base_url: str,
    agent_token: str,
    *,
    user_token: str = None,
    tenant: str = None,
    timeout: dict = None
)
```

### Context Manager 사용

```python
from synapse_sdk.clients.agent import AsyncAgentClient

async with AsyncAgentClient(
    base_url="https://agent.example.com",
    agent_token="your-agent-token"
) as client:
    # 헬스 체크
    status = await client.health_check()

    # Ray job 목록
    jobs = await client.list_jobs()

    # 비동기 job 로그 스트리밍
    async for line in client.tail_job_logs('raysubmit_abc123'):
        print(line)
```

### Context Manager 없이 사용

```python
client = AsyncAgentClient(base_url, agent_token)
try:
    jobs = await client.list_jobs()
finally:
    await client.close()
```

---

## 로그 스트리밍

두 클라이언트 모두 WebSocket 또는 HTTP 프로토콜을 통한 실시간 로그 스트리밍을 지원합니다.

### 통합 메서드

```python
# 동기
for line in client.tail_job_logs('job-id', protocol='auto'):
    print(line)

# 비동기
async for line in client.tail_job_logs('job-id', protocol='auto'):
    print(line)
```

### 프로토콜 옵션

- `'auto'` (기본값): WebSocket 먼저 시도, 연결 실패 시 HTTP로 대체
- `'websocket'`: WebSocket만 사용 (가장 낮은 지연시간)
- `'http'`: HTTP chunked 스트리밍만 사용 (호환성 높음)

### 스트림 제한

스트리밍 작업에 대한 리소스 제한 설정:

```python
from synapse_sdk.utils.network import StreamLimits

client.stream_limits = StreamLimits(
    max_messages=10_000,    # 최대 WebSocket 메시지 수
    max_lines=50_000,       # 최대 HTTP 라인 수
    max_bytes=50*1024*1024, # 총 50MB
    max_message_size=10_240 # 메시지당 10KB
)
```

상세 스트리밍 메서드 문서는 [RayClient](./ray.md)를 참조하세요.

---

## Ray 작업

AgentClient는 mixin을 통해 모든 Ray 클러스터 관리 메서드를 포함합니다:

### Job 작업

```python
# 모든 job 목록
jobs = client.list_jobs()

# job 상세 정보
job = client.get_job('raysubmit_abc123')

# job 로그 가져오기 (스트리밍 아님)
logs = client.get_job_logs('raysubmit_abc123')

# 실행 중인 job 중지
result = client.stop_job('raysubmit_abc123')
```

### Node 작업

```python
# 클러스터 노드 목록
nodes = client.list_nodes()

# 노드 상세 정보
node = client.get_node('node-abc123')
```

### Task 작업

```python
# 모든 task 목록
tasks = client.list_tasks()

# task 상세 정보
task = client.get_task('task-xyz789')
```

### Ray Serve 작업

```python
# serve application 목록
apps = client.list_serve_applications()

# application 상세 정보
app = client.get_serve_application('my-app')

# application 삭제
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
        print("잘못된 job ID 또는 매개변수")
    elif e.status_code == 404:
        print("Job을 찾을 수 없음")
    elif e.status_code == 503:
        print("에이전트 연결 실패")
    else:
        print(f"오류: {e}")
```

### 일반적인 오류 코드

| 코드 | 의미 |
|-----|------|
| 400 | 잘못된 매개변수 (job ID, timeout, protocol) |
| 404 | 리소스를 찾을 수 없음 |
| 408 | 연결 또는 읽기 타임아웃 |
| 429 | 스트림 제한 초과 |
| 500 | 내부 오류 또는 라이브러리 없음 |
| 503 | 에이전트 연결 실패 |

---

## 참고 문서

- [RayClient](./ray.md) - 상세 Ray 스트리밍 메서드
- [BackendClient](./backend.md) - Backend 작업
- [BaseClient](./base.md) - 기본 클라이언트 구현
- [Network Utilities](../../features/utils/network.md) - StreamLimits 및 유효성 검사
