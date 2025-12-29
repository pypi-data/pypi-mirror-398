---
id: utils
title: Plugin Utilities
sidebar_position: 3
---

# Plugin Utilities

플러그인 개발, 구성 관리, 액션 처리를 위한 유틸리티 함수.

## 개요

`synapse_sdk.plugins.utils` 모듈은 플러그인 구성 작업, 액션 관리, 플러그인 메타데이터 처리를 위한 함수 모음을 제공합니다.

---

## 구성 유틸리티

### get_plugin_actions()

플러그인 구성에서 액션 이름 목록 가져오기.

```python
from synapse_sdk.plugins.utils import get_plugin_actions

# Dict에서
config = {'actions': {'train': {...}, 'inference': {...}}}
actions = get_plugin_actions(config=config)
# 반환: ['train', 'inference']

# 플러그인 경로에서
actions = get_plugin_actions(plugin_path="./my-plugin")
```

### get_action_config()

플러그인 내 특정 액션의 구성 가져오기.

```python
from synapse_sdk.plugins.utils import get_action_config

action_config = get_action_config('train', plugin_path="./my-plugin")
# 반환: {'entrypoint': 'plugin.train.TrainAction', 'method': 'job'}
```

---

## 액션 유틸리티

### get_action_method()

액션의 실행 메서드 (job/task/serve_application) 가져오기.

```python
from synapse_sdk.plugins.utils import get_action_method
from synapse_sdk.plugins.enums import RunMethod

method = get_action_method(config, 'train')
if method == RunMethod.JOB:
    # job 레코드 생성, 비동기 실행
    pass
elif method == RunMethod.TASK:
    # Ray task로 실행
    pass
```

**매개변수:**

- `config`: 플러그인 구성 (dict 또는 PluginConfig)
- `action`: 액션 이름

**반환:** `RunMethod` enum 값

---

## run_plugin()

자동 검색으로 플러그인 액션 실행.

```python
from synapse_sdk.plugins.runner import run_plugin

# Python 모듈 경로에서 자동 검색
result = run_plugin('plugins.yolov8', 'train', {'epochs': 10})

# config.yaml 경로에서 자동 검색
result = run_plugin('/path/to/plugin', 'train', {'epochs': 10})

# 실행 모드
result = run_plugin('plugin', 'train', params, mode='local')  # 현재 프로세스 (기본값)
result = run_plugin('plugin', 'train', params, mode='task')   # Ray Actor (빠른 시작)
job_id = run_plugin('plugin', 'train', params, mode='job')    # Ray Job API (비동기)

# 명시적 액션 클래스 (검색 건너뜀)
result = run_plugin('yolov8', 'train', {'epochs': 10}, action_cls=TrainAction)
```

**매개변수:**

- `source`: 플러그인 모듈 경로 또는 파일시스템 경로
- `action`: 실행할 액션 이름
- `params`: 액션에 대한 매개변수 dict
- `mode`: 실행 모드 (`'local'`, `'task'`, `'job'`)
- `action_cls`: 선택적 명시적 액션 클래스 (검색 건너뜀)

**반환:** 액션 결과 또는 job ID (비동기 모드의 경우)

---

## PluginDiscovery

config 파일 또는 Python 모듈에서 포괄적인 플러그인 조회.

### Config 경로에서

```python
from synapse_sdk.plugins.discovery import PluginDiscovery

# config.yaml이 포함된 디렉토리에서 로드
discovery = PluginDiscovery.from_path('/path/to/plugin')

# 사용 가능한 메서드
discovery.list_actions()              # ['train', 'inference', 'export']
discovery.has_action('train')         # True
discovery.get_action_method('train')  # RunMethod.JOB
discovery.get_action_config('train')  # ActionConfig 인스턴스
discovery.get_action_class('train')   # entrypoint에서 클래스 로드
```

### Python 모듈에서

```python
from synapse_sdk.plugins.discovery import PluginDiscovery
import my_plugin

# @action 데코레이터와 BaseAction 서브클래스 자동 검색
discovery = PluginDiscovery.from_module(my_plugin)

# 검색된 액션 목록
for action in discovery.list_actions():
    print(f"Action: {action}")
    print(f"  Method: {discovery.get_action_method(action)}")
```

### 액션 정의

**옵션 1: @action 데코레이터 (Python 모듈에 권장)**

```python
from synapse_sdk.plugins.decorators import action
from pydantic import BaseModel

class TrainParams(BaseModel):
    epochs: int = 10
    batch_size: int = 32

@action(name='train', description='모델 학습', params=TrainParams)
def train(params: TrainParams, ctx):
    return {'accuracy': 0.95}
```

**옵션 2: BaseAction 클래스**

```python
from synapse_sdk.plugins.action import BaseAction
from pydantic import BaseModel

class TrainParams(BaseModel):
    epochs: int = 10

class TrainAction(BaseAction[TrainParams]):
    action_name = 'train'
    params_model = TrainParams

    def execute(self):
        # self.params에 검증된 TrainParams 포함
        # self.ctx에 RuntimeContext 포함
        return {'accuracy': 0.95}
```

**옵션 3: config.yaml (패키지된 플러그인에 권장)**

```yaml
name: YOLOv8 Plugin
code: yolov8
version: 1.0.0
category: neural_net

actions:
  train:
    entrypoint: plugin.train.TrainAction
    method: job
    description: YOLOv8 모델 학습

  infer:
    entrypoint: plugin.inference.InferAction
    method: task
```

---

## 모범 사례

1. **오류 처리**: 유틸리티 호출을 항상 try-catch로 감싸기
2. **구성 유효성 검사**: 사용 전 config 유효성 검사
3. **경로 처리**: 가능한 한 절대 경로 사용
4. **액션 확인**: 인스턴스화 전 액션 가용성 확인
5. **타입 안전성**: 더 나은 IDE 지원을 위해 제공된 타입 힌트 사용
6. **run_plugin 사용**: 실행에 수동 검색보다 `run_plugin()` 선호
7. **PluginDiscovery 사용**: 더 이상 사용되지 않는 전역 레지스트리 대신 조회에 사용

---

## 참고 문서

- [마이그레이션 가이드](../../migration.md) - v1에서 v2로 마이그레이션
- [플러그인 모델](./models.md) - 플러그인 데이터 모델
