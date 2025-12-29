---
id: models
title: 플러그인 모델
sidebar_position: 1
---

# 플러그인 모델

플러그인 시스템의 핵심 데이터 모델 및 구조입니다.

## PluginRelease

플러그인의 특정 버전을 나타냅니다.

```python
from synapse_sdk.plugins.models import PluginRelease

release = PluginRelease(plugin_path="./my-plugin")
```

### 속성

- `plugin`: 플러그인 코드 식별자
- `version`: 플러그인 버전
- `code`: 플러그인과 버전이 결합된 문자열
- `category`: 플러그인 카테고리
- `name`: 사람이 읽을 수 있는 플러그인 이름
- `actions`: 사용 가능한 플러그인 액션

## PluginAction

플러그인 액션 실행 요청을 나타냅니다.

```python
from synapse_sdk.plugins.models import PluginAction

action = PluginAction(
    plugin="my-plugin",
    version="1.0.0",
    action="process",
    params={"input": "data"}
)
```

## Run

플러그인 액션의 실행 컨텍스트입니다.

```python
def start(self):
    # 메시지 로깅
    self.run.log("Processing started")

    # 진행률 업데이트
    self.run.set_progress(0.5)

    # 메트릭 설정
    self.run.set_metrics({"processed": 100})
```

### 개발 로깅

`Run` 클래스는 `log_dev_event()` 메서드와 `DevLog` 모델을 통해 플러그인 개발자를 위한 특수 로깅 시스템을 포함합니다.

#### DevLog 모델

개발 이벤트 로깅을 위한 구조화된 모델:

```python
from synapse_sdk.shared.enums import Context

class DevLog(BaseModel):
    event_type: str          # 이벤트 카테고리 ('{action_name}_dev_log' 형태로 자동 생성)
    message: str             # 설명 메시지
    data: dict | None        # 선택적 추가 데이터
    level: Context           # 이벤트 심각도 수준
    created: str             # ISO 타임스탬프
```

#### log_dev_event 메서드

디버깅 및 모니터링을 위한 커스텀 개발 이벤트 로깅:

```python
def start(self):
    # 기본 이벤트 로깅 (event_type은 '{action_name}_dev_log' 형태로 자동 설정)
    self.run.log_dev_event('데이터 검증 완료', {'records_count': 100})

    # 성능 추적
    self.run.log_dev_event('처리 시간 기록', {'duration_ms': 1500})

    # 경고 레벨의 디버그
    self.run.log_dev_event('변수 상태 체크포인트',
                          {'variable_x': 42}, level=Context.WARNING)

    # 데이터 없는 간단한 이벤트
    self.run.log_dev_event('플러그인 초기화 완료')
```

**매개변수:**

- `message` (str): 사람이 읽을 수 있는 설명
- `data` (dict, 선택사항): 추가 컨텍스트 데이터
- `level` (Context, 선택사항): 이벤트 심각도 (기본값: Context.INFO)

**참고:** `event_type`은 `{action_name}_dev_log` 형태로 자동 생성되며 플러그인 개발자가 수정할 수 없습니다.

**사용 사례:**

- **디버깅**: 변수 상태 및 실행 흐름 추적
- **성능**: 처리 시간 및 리소스 사용량 기록
- **검증**: 데이터 검증 결과 로깅
- **오류 추적**: 상세한 오류 정보 캡처
- **진행 상황 모니터링**: 장기 실행 작업의 중간 상태 기록
