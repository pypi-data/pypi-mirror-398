---
id: network
title: Network Utilities
sidebar_position: 4
---

# Network Utilities

스트리밍 구성, 입력 유효성 검사, URL 처리를 위한 유틸리티.

## 개요

`synapse_sdk.utils.network` 모듈은 Ray 클라이언트 mixin에서 사용하는 스트리밍 작업 및 입력 유효성 검사를 위한 필수 유틸리티를 제공합니다.

## StreamLimits

메모리 고갈을 방지하기 위한 스트리밍 리소스 제한 구성.

### 생성자

```python
from synapse_sdk.utils.network import StreamLimits

limits = StreamLimits(
    max_messages=10_000,
    max_lines=50_000,
    max_bytes=50 * 1024 * 1024,  # 50MB
    max_message_size=10_240,     # 10KB
    queue_size=1_000
)
```

### 매개변수

| 매개변수 | 타입 | 기본값 | 설명 |
|---------|------|-------|------|
| `max_messages` | int | 10,000 | 종료 전 최대 WebSocket 메시지 수 |
| `max_lines` | int | 50,000 | HTTP 스트리밍 최대 라인 수 |
| `max_bytes` | int | 50MB | 수신할 최대 총 바이트 |
| `max_message_size` | int | 10KB | 메시지당 최대 크기 (초과 시 건너뜀) |
| `queue_size` | int | 1,000 | 비동기 작업용 내부 큐 크기 |

### 클라이언트와 함께 사용

```python
from synapse_sdk.clients.agent import AgentClient
from synapse_sdk.utils.network import StreamLimits

client = AgentClient(base_url, agent_token)

# 사용자 정의 제한 구성
client.stream_limits = StreamLimits(
    max_messages=50_000,
    max_lines=100_000,
    max_bytes=200 * 1024 * 1024  # 200MB
)

# 사용자 정의 제한으로 스트리밍
for line in client.tail_job_logs('job-123'):
    print(line)
```

---

## 유효성 검사 함수

### validate_resource_id()

주입 공격을 방지하기 위해 리소스 식별자를 유효성 검사합니다.

```python
from synapse_sdk.utils.network import validate_resource_id

# 유효한 사용
job_id = validate_resource_id('raysubmit_abc123', 'job')
node_id = validate_resource_id('node_abc_123', 'node')

# 잘못된 사용은 ClientError (400) 발생
try:
    validate_resource_id('', 'job')  # 비어있음
except ClientError as e:
    print(e)  # "job ID cannot be empty"

try:
    validate_resource_id('job/../malicious', 'job')  # 잘못된 문자
except ClientError as e:
    print(e)  # "Invalid job ID format"
```

**유효성 검사 규칙:**

- 비어있으면 안됨
- 영숫자, 하이픈 (`-`), 밑줄 (`_`)만 허용
- 최대 길이: 100자
- 패턴: `^[a-zA-Z0-9\-_]+$`

**매개변수:**

| 매개변수 | 타입 | 설명 |
|---------|------|------|
| `resource_id` | Any | 유효성 검사할 ID (문자열로 변환됨) |
| `resource_name` | str | 오류 메시지용 이름 (기본값: `'resource'`) |

**반환:** `str` - 유효성 검사된 리소스 ID

**예외:** 유효성 검사 실패 시 `ClientError` (400)

---

### validate_timeout()

경계 확인을 통한 타임아웃 값 유효성 검사.

```python
from synapse_sdk.utils.network import validate_timeout

# 유효한 타임아웃
timeout = validate_timeout(30)      # 30초 -> 30.0
timeout = validate_timeout(10.5)    # 10.5초 -> 10.5

# 잘못된 타임아웃은 ClientError (400) 발생
try:
    validate_timeout(-1)  # 음수
except ClientError as e:
    print(e)  # "Timeout must be a positive number"

try:
    validate_timeout(500)  # 최대값 초과 (기본값 300)
except ClientError as e:
    print(e)  # "Timeout cannot exceed 300 seconds"
```

**매개변수:**

| 매개변수 | 타입 | 기본값 | 설명 |
|---------|------|-------|------|
| `timeout` | int/float | - | 초 단위 타임아웃 값 |
| `max_timeout` | float | 300.0 | 허용되는 최대 타임아웃 |

**반환:** `float` - 유효성 검사된 타임아웃 값

**예외:** 유효하지 않으면 `ClientError` (400)

---

## URL 유틸리티

### http_to_websocket_url()

HTTP/HTTPS URL을 WebSocket URL로 변환합니다.

```python
from synapse_sdk.utils.network import http_to_websocket_url

# HTTP -> WS
ws_url = http_to_websocket_url("http://localhost:8000/ws/")
# 결과: "ws://localhost:8000/ws/"

# HTTPS -> WSS
wss_url = http_to_websocket_url("https://api.example.com/stream/")
# 결과: "wss://api.example.com/stream/"

# 이미 WebSocket인 경우 (변경 없이 반환)
url = http_to_websocket_url("wss://api.example.com/")
# 결과: "wss://api.example.com/"
```

**매개변수:**

| 매개변수 | 타입 | 설명 |
|---------|------|------|
| `url` | str | HTTP, HTTPS, WS, 또는 WSS URL |

**반환:** `str` - WebSocket URL (ws:// 또는 wss://)

**예외:** URL scheme이 유효하지 않으면 `ClientError` (400)

---

## 오류 유틸리티

### sanitize_error_message()

정보 유출을 방지하기 위해 오류 메시지를 정제합니다.

```python
from synapse_sdk.utils.network import sanitize_error_message

# 인용된 문자열 삭제
clean = sanitize_error_message('Failed with token="secret123"', 'connection')
# 결과: 'connection: Failed with token="[REDACTED]"'

# 긴 메시지 자르기 (200자 제한)
clean = sanitize_error_message('Very long error...' * 50, 'error')
# 결과: 'error: Very long error...' (잘림)
```

**매개변수:**

| 매개변수 | 타입 | 설명 |
|---------|------|------|
| `error_msg` | str | 원본 오류 메시지 |
| `context` | str | 선택적 컨텍스트 접두사 |

**반환:** `str` - 정제된 오류 메시지

---

## 전체 예제

```python
from synapse_sdk.utils.network import (
    StreamLimits,
    validate_resource_id,
    validate_timeout,
    http_to_websocket_url,
    sanitize_error_message,
)
from synapse_sdk.clients.exceptions import ClientError

def stream_job_logs(client, job_id: str, timeout: float = 30.0):
    """적절한 유효성 검사로 job 로그 스트리밍."""
    # 입력 유효성 검사
    validated_id = validate_resource_id(job_id, 'job')
    validated_timeout = validate_timeout(timeout)

    # 이 작업에 대한 제한 구성
    client.stream_limits = StreamLimits(max_lines=10_000)

    try:
        for line in client.tail_job_logs(validated_id, validated_timeout):
            yield line
    except ClientError as e:
        clean_msg = sanitize_error_message(str(e), f'job {job_id}')
        raise ClientError(e.status_code, clean_msg)

# 사용법
for line in stream_job_logs(client, 'raysubmit_abc123', 60.0):
    print(line)
```

---

## 오류 코드

| 코드 | 원인 |
|-----|------|
| 400 | 잘못된 리소스 ID, 타임아웃, 또는 URL 형식 |
| 429 | 스트림 제한 초과 |

---

## 참고 문서

- [RayClient](../../api/clients/ray.md) - 스트리밍에 이 유틸리티 사용
- [AgentClient](../../api/clients/agent.md) - StreamLimits 지원 클라이언트
- [Storage](./storage.md) - Storage provider 유틸리티
