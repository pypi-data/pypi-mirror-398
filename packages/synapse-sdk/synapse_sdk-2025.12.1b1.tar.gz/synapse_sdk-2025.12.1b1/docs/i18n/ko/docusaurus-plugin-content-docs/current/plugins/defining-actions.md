---
id: defining-actions
title: 액션 정의하기
sidebar_position: 2
---

# 액션 정의하기

액션은 Synapse 플러그인의 핵심 구성 요소입니다. SDK v2는 두 가지 방식으로 액션을 정의할 수 있습니다:

1. **함수 기반** - `@action` 데코레이터 사용 (더 간단함)
2. **클래스 기반** - `BaseAction` 또는 카테고리별 베이스 클래스 사용 (더 많은 기능)

## 함수 기반 액션

간단한 stateless 액션에는 `@action` 데코레이터를 사용하세요:

```python
from pydantic import BaseModel, Field
from synapse_sdk.plugins.decorators import action


class TrainParams(BaseModel):
    epochs: int = Field(default=50, ge=1, le=1000)
    batch_size: int = Field(default=8, ge=1, le=512)
    learning_rate: float = Field(default=0.001)


@action('train', params=TrainParams)
def train(params: TrainParams, ctx):
    """모델 학습."""
    for epoch in range(params.epochs):
        ctx.set_progress(epoch + 1, params.epochs, 'train')
        # 학습 로직

    return {'status': 'completed', 'epochs': params.epochs}
```

### 데코레이터 문법

```python
@action(name, description, params)
```

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `name` | `str` | 아니오 | 액션 이름. 기본값은 함수 이름. |
| `description` | `str` | 아니오 | 사람이 읽을 수 있는 설명. |
| `params` | `type[BaseModel]` | 아니오 | 파라미터 검증용 Pydantic 모델. |

**문법 변형:**

```python
# 위치 인자로 name 전달
@action('train', params=TrainParams)
def train(params, ctx): ...

# 키워드만 사용 - name은 함수 이름으로 기본 설정
@action(params=TrainParams)
def train(params, ctx): ...  # name은 'train'이 됨

# 모든 키워드 인자 사용
@action(name='train', description='모델 학습', params=TrainParams)
def train(params, ctx): ...

# 최소 형태 - params 검증 없음
@action('inference')
def inference(params, ctx): ...
```

### 함수 시그니처

```python
def action_function(params: ParamsModel, ctx: RuntimeContext) -> Any:
    ...
```

| 인자 | 타입 | 설명 |
|------|------|------|
| `params` | Pydantic 모델 인스턴스 | 검증된 파라미터 |
| `ctx` | `RuntimeContext` | 로깅, 환경, 클라이언트가 포함된 런타임 컨텍스트 |

## 클래스 기반 액션

헬퍼 메소드가 있는 복잡한 워크플로우에는 클래스 기반 액션을 사용하세요:

```python
from pydantic import BaseModel, Field
from synapse_sdk.plugins.actions.train import BaseTrainAction


class TrainParams(BaseModel):
    epochs: int = Field(default=50, ge=1, le=1000)
    batch_size: int = Field(default=8, ge=1, le=512)
    learning_rate: float = Field(default=0.001)


class YoloTrainAction(BaseTrainAction[TrainParams]):
    params_model = TrainParams

    def execute(self):
        # self.params로 파라미터 접근
        # self.ctx로 컨텍스트 접근

        dataset = self.get_dataset()  # BaseTrainAction의 헬퍼

        for epoch in range(self.params.epochs):
            self.set_progress(epoch + 1, self.params.epochs, 'train')
            # 학습 로직

        self.create_model('/path/to/model.pt')
        return {'status': 'completed'}
```

### 최소 클래스 정의

config.yaml 기반 디스커버리를 사용할 때는 `params_model`과 `execute()`만 필요합니다:

```python
class YoloTrainAction(BaseTrainAction[TrainParams]):
    params_model = TrainParams  # 필수

    def execute(self):  # 필수
        return {'status': 'done'}
```

SDK가 디스커버리 과정에서 config.yaml에서 `action_name`과 `category`를 주입합니다.

### 선택적 클래스 속성

config.yaml 값을 오버라이드하려면 명시적으로 메타데이터를 설정할 수 있습니다:

```python
class YoloTrainAction(BaseTrainAction[TrainParams]):
    action_name = 'train'      # 선택 - config 키에서 주입됨
    category = 'neural_net'    # 선택 - 플러그인 category에서 주입됨
    params_model = TrainParams

    def execute(self):
        return {'status': 'done'}
```

### 사용 가능한 베이스 클래스

| 베이스 클래스 | 카테고리 | 헬퍼 메소드 |
|--------------|----------|------------|
| `BaseAction` | 일반 | `set_progress()`, `set_metrics()`, `log()` |
| `BaseTrainAction` | `neural_net` | `get_dataset()`, `create_model()`, `get_model()` |
| `BaseExportAction` | `export` | `get_filtered_results()` |
| `BaseUploadAction` | `upload` | 롤백이 있는 단계 기반 워크플로우 |
| `BaseInferenceAction` | `neural_net` | 모델 로딩 헬퍼 |

## RuntimeContext

함수 기반과 클래스 기반 액션 모두 `RuntimeContext`를 받습니다:

```python
@dataclass
class RuntimeContext:
    logger: BaseLogger
    env: PluginEnvironment
    job_id: str | None
    client: BackendClient | None
    agent_client: AgentClient | None
    checkpoint: dict[str, Any] | None  # 사전학습 모델 정보
```

### 사용 가능한 메소드

```python
# 진행률 추적
ctx.set_progress(current=50, total=100, category='train')

# 메트릭
ctx.set_metrics({'loss': 0.1, 'accuracy': 0.95}, category='training')

# 로깅
ctx.log('event_name', {'key': 'value'})
ctx.log_message('사용자에게 보이는 메시지', context='info')
ctx.log_dev_event('디버그 메시지', data={'debug': True})

# 환경변수
value = ctx.env.get('MY_VAR', default='fallback')

# 백엔드 클라이언트 (사용 가능한 경우)
dataset = ctx.client.get_data_collection(dataset_id)

# 체크포인트 (사전학습 모델)
model_path = ctx.checkpoint.get('path', 'default.pt') if ctx.checkpoint else 'default.pt'
```

## 디스커버리 모드

### 1. 모듈 디스커버리 (@action 사용)

config.yaml 엔트리포인트 불필요 - SDK가 모듈을 분석합니다:

```python
# plugin/train.py
@action('train', params=TrainParams)
def train(params, ctx):
    ...
```

```python
from synapse_sdk.plugins.discovery import PluginDiscovery
import plugin.train as train_module

discovery = PluginDiscovery.from_module(train_module)
discovery.list_actions()  # ['train'] - 자동 발견
```

### 2. Config 디스커버리 (엔트리포인트 사용)

config.yaml에 엔트리포인트 지정:

```yaml
# config.yaml
name: yolov8
code: yolov8
category: neural_net

actions:
  train:
    entrypoint: plugin.train.YoloTrainAction
    method: job
  inference:
    entrypoint: plugin.inference.infer  # 함수도 가능
    method: task
```

```python
discovery = PluginDiscovery.from_path('/path/to/plugin')
discovery.list_actions()  # ['train', 'inference']
```

## 액션 실행

### run_plugin 사용

```python
from synapse_sdk.plugins.runner import run_plugin

# 모듈 경로에서 자동 디스커버리
result = run_plugin('plugin.train', 'train', {'epochs': 10})

# config.yaml 경로에서 자동 디스커버리
result = run_plugin('/path/to/plugin', 'train', {'epochs': 10})

# 실행 모드
result = run_plugin('plugin', 'train', params, mode='local')  # 현재 프로세스
result = run_plugin('plugin', 'train', params, mode='task')   # Ray Actor
job_id = run_plugin('plugin', 'train', params, mode='job')    # Ray Job (비동기)
```

## 모범 사례

### 1. 간단한 액션에는 함수 기반 사용

```python
@action('healthcheck')
def healthcheck(params, ctx):
    return {'status': 'ok'}
```

### 2. 복잡한 워크플로우에는 클래스 기반 사용

```python
class TrainAction(BaseTrainAction[TrainParams]):
    params_model = TrainParams

    def execute(self):
        dataset = self.get_dataset()       # 내장 헬퍼
        model_path = self._train(dataset)  # 커스텀 메소드
        self.create_model(model_path)      # 내장 헬퍼
        return {'status': 'done'}

    def _train(self, dataset):
        # 커스텀 학습 로직
        pass
```

### 3. Config를 진실의 원천으로

```python
# 최소 형태 - SDK가 config.yaml에서 action_name/category 주입
class TrainAction(BaseTrainAction[TrainParams]):
    params_model = TrainParams

    def execute(self):
        return {}
```

### 4. 사전학습 모델에는 Checkpoint 사용

```python
def execute(self):
    checkpoint = self.ctx.checkpoint or {}
    model_path = checkpoint.get('path', 'yolov8n.pt')
    category = checkpoint.get('category', 'base')  # 'base' 또는 fine-tuned

    model = load_model(model_path)
    ...
```

### 5. 의미 있는 진행률 리포트

```python
def execute(self):
    total_epochs = self.params.epochs

    for epoch in range(total_epochs):
        self.set_progress(epoch + 1, total_epochs, 'train')
        # 에폭 학습

    self.set_progress(100, 100, 'model_upload')
    self.create_model(model_path)
```
