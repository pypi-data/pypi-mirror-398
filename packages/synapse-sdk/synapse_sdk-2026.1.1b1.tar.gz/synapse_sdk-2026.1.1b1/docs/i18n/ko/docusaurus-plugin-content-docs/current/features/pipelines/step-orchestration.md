---
id: step-orchestration
title: 스텝 오케스트레이션
sidebar_position: 1
---

# 스텝 오케스트레이션

스텝 오케스트레이션은 복잡한 작업을 개별적이고 관리 가능한 스텝으로 분할할 수 있는 강력한 워크플로우 패턴입니다. 각 스텝은 고유한 실행 로직, 진행 가중치, 스킵 조건, 롤백 동작을 가질 수 있습니다.

## 스텝 오케스트레이션을 사용하는 이유

### 이점

| 이점 | 설명 |
|------|------|
| **관심사 분리** | 각 스텝이 하나의 특정 작업을 처리하여 코드를 이해하고 유지보수하기 쉬움 |
| **재사용성** | 스텝을 여러 워크플로우와 액션에서 공유 가능 |
| **테스트 용이성** | 개별 스텝을 독립적으로 단위 테스트 가능 |
| **진행 상황 추적** | 가중치 기반 진행률 계산으로 정확한 진행 상황 보고 |
| **오류 복구** | 실패 시 자동 롤백으로 부분 작업 정리 |
| **유연성** | 스텝을 동적으로 삽입, 제거, 재정렬 가능 |
| **관찰 가능성** | 디버깅을 위한 내장 로깅 및 타이밍 유틸리티 |

### 사용 시기

스텝 오케스트레이션은 다음과 같은 경우에 적합합니다:

- **다단계 작업**: 업로드 워크플로우 (초기화 -> 검증 -> 업로드 -> 정리)
- **장시간 실행 작업**: 학습 파이프라인 (데이터 로드 -> 학습 -> 모델 저장)
- **정리가 필요한 작업**: 실패 시 임시 파일 정리가 필요한 파일 처리
- **조합 가능한 워크플로우**: 재사용 가능한 스텝 컴포넌트로 워크플로우 구성

### 사용하지 않을 때

스텝 오케스트레이션은 오버헤드가 있습니다. 간단한 작업의 경우 직접 `execute()`를 사용하세요:

- 단일 단계 작업 (예: 단순 데이터 가져오기)
- 정리가 필요 없는 작업
- 3개 미만의 논리적 단계를 가진 워크플로우

## 핵심 개념

### 스텝

스텝은 워크플로우에서 개별적인 작업 단위입니다. 각 스텝은:

- 식별을 위한 고유한 **name**을 가짐
- 진행률 계산을 위한 **progress weight** (0.0 ~ 1.0) 지정
- 실제 작업을 수행하는 **execute()** 구현
- 선택적으로 **can_skip()**과 **rollback()** 구현 가능

```python
from synapse_sdk.plugins.pipelines.steps import BaseStep, StepResult

class ValidateFilesStep(BaseStep[UploadContext]):
    @property
    def name(self) -> str:
        return 'validate_files'

    @property
    def progress_weight(self) -> float:
        return 0.1  # 전체 워크플로우 진행률의 10%

    def execute(self, context: UploadContext) -> StepResult:
        invalid_files = []
        for file in context.files:
            if not self._is_valid(file):
                invalid_files.append(file)

        if invalid_files:
            return StepResult(
                success=False,
                error=f'유효하지 않은 파일: {invalid_files}'
            )

        return StepResult(success=True, data={'validated': len(context.files)})

    def can_skip(self, context: UploadContext) -> bool:
        # 검증이 명시적으로 비활성화된 경우 스킵
        return context.params.get('skip_validation', False)

    def rollback(self, context: UploadContext, result: StepResult) -> None:
        # 검증에는 롤백할 것이 없음
        pass

    def _is_valid(self, file: dict) -> bool:
        # 검증 로직
        return file.get('size', 0) > 0
```

### StepResult

모든 스텝은 다음을 포함하는 `StepResult`를 반환합니다:

| 필드 | 타입 | 설명 |
|------|------|------|
| `success` | `bool` | 스텝이 성공적으로 완료되었는지 여부 |
| `data` | `dict[str, Any]` | 스텝의 출력 데이터 |
| `error` | `str | None` | 스텝 실패 시 오류 메시지 |
| `rollback_data` | `dict[str, Any]` | 롤백에 필요한 데이터 |
| `skipped` | `bool` | 스텝이 스킵되었는지 여부 |
| `timestamp` | `datetime` | 스텝 완료 시각 |

```python
# 성공 결과
return StepResult(success=True, data={'files_processed': 10})

# 실패 결과
return StepResult(success=False, error='연결 시간 초과')

# 롤백 데이터가 포함된 결과
return StepResult(
    success=True,
    data={'uploaded_ids': [1, 2, 3]},
    rollback_data={'uploaded_ids': [1, 2, 3]}  # 실패 시 정리용
)
```

### 컨텍스트

컨텍스트는 모든 스텝 간에 전달되는 공유 상태 객체입니다:

- 워크플로우별 필드로 `BaseStepContext`를 확장
- 로깅/진행 상황을 위한 `RuntimeContext` 접근 제공
- 스텝 실행에 따라 데이터 축적
- 스텝 결과와 오류 추적

```python
from dataclasses import dataclass, field
from synapse_sdk.plugins.pipelines.steps import BaseStepContext

@dataclass
class UploadContext(BaseStepContext):
    """업로드 워크플로우용 공유 컨텍스트."""
    # 워크플로우 매개변수
    params: dict = field(default_factory=dict)

    # 축적된 상태
    files_to_upload: list[str] = field(default_factory=list)
    uploaded_files: list[dict] = field(default_factory=list)
    total_bytes: int = 0

    # 백엔드 클라이언트 접근
    @property
    def client(self):
        return self.runtime_ctx.client
```

### 레지스트리

`StepRegistry`는 순서화된 스텝 목록을 관리합니다:

```python
from synapse_sdk.plugins.pipelines.steps import StepRegistry

registry = StepRegistry[UploadContext]()

# 순서대로 스텝 등록
registry.register(InitializeStep())
registry.register(ValidateStep())
registry.register(UploadStep())
registry.register(CleanupStep())

# 동적 스텝 조작
registry.insert_before('upload', CompressionStep())  # 업로드 전에 압축 추가
registry.insert_after('validate', SanitizeStep())    # 검증 후에 정제 추가
registry.unregister('cleanup')                        # 정리 스텝 제거

# 스텝 수와 총 가중치 확인
print(f"스텝 수: {len(registry)}")
print(f"총 가중치: {registry.total_weight}")
```

### 오케스트레이터

`Orchestrator`는 스텝을 실행하고 다음을 처리합니다:

- 순차적 스텝 실행
- 가중치 기반 진행 상황 추적
- 실패 시 자동 롤백
- 스킵 조건 평가

```python
from synapse_sdk.plugins.pipelines.steps import Orchestrator

orchestrator = Orchestrator(
    registry=registry,
    context=context,
    progress_callback=lambda current, total: print(f'{current}/{total}%')
)

try:
    result = orchestrator.execute()
    # {'success': True, 'steps_executed': 4, 'steps_total': 4}
except RuntimeError as e:
    # 스텝 실패, 롤백 수행됨
    print(f"워크플로우 실패: {e}")
```

## 진행 상황 추적

진행률은 스텝 가중치를 기반으로 계산됩니다:

```python
class Step1(BaseStep[MyContext]):
    @property
    def progress_weight(self) -> float:
        return 0.2  # 20%

class Step2(BaseStep[MyContext]):
    @property
    def progress_weight(self) -> float:
        return 0.6  # 60%

class Step3(BaseStep[MyContext]):
    @property
    def progress_weight(self) -> float:
        return 0.2  # 20%

# 진행 상황 업데이트:
# Step1 완료 후: 20%
# Step2 완료 후: 80%
# Step3 완료 후: 100%
```

오케스트레이터는 가중치를 정규화하므로, 정확히 1.0이 되지 않아도 됩니다.

## 롤백 동작

스텝이 실패하면 오케스트레이터는:

1. 즉시 실행 중지
2. 이전에 실행된 모든 스텝에 대해 **역순으로** `rollback()` 호출
3. 실패 세부 정보와 함께 `RuntimeError` 발생

```python
class UploadFilesStep(BaseStep[UploadContext]):
    def execute(self, context: UploadContext) -> StepResult:
        uploaded_ids = []
        for file in context.files:
            file_id = self._upload(file)
            uploaded_ids.append(file_id)

        return StepResult(
            success=True,
            rollback_data={'uploaded_ids': uploaded_ids}
        )

    def rollback(self, context: UploadContext, result: StepResult) -> None:
        # 업로드된 파일 정리
        for file_id in result.rollback_data.get('uploaded_ids', []):
            try:
                self._delete(file_id)
            except Exception:
                context.errors.append(f'파일 {file_id} 롤백 실패')
```

## 유틸리티 스텝

SDK는 일반적인 패턴을 위한 유틸리티 스텝 래퍼를 제공합니다:

### LoggingStep

시작/종료 로깅으로 스텝을 래핑합니다:

```python
from synapse_sdk.plugins.pipelines.steps import LoggingStep

# 로깅으로 모든 스텝 래핑
logged_step = LoggingStep(UploadFilesStep())
registry.register(logged_step)

# 로그 출력:
# step_start {'step': 'upload_files'}
# step_end {'step': 'upload_files', 'elapsed': 1.234, 'success': True}
```

### TimingStep

스텝 실행 시간을 측정합니다:

```python
from synapse_sdk.plugins.pipelines.steps import TimingStep

timed_step = TimingStep(ProcessDataStep())
registry.register(timed_step)

# 결과에 시간 포함:
# result.data['duration_seconds'] = 1.234567
```

### ValidationStep

진행 전 컨텍스트 상태를 검증합니다:

```python
from synapse_sdk.plugins.pipelines.steps import ValidationStep

def check_files_exist(context: UploadContext) -> tuple[bool, str | None]:
    if not context.files:
        return False, '업로드할 파일이 없습니다'
    return True, None

registry.register(ValidationStep(
    validator=check_files_exist,
    name='validate_files_exist',
    progress_weight=0.05
))
```

## 액션과의 통합

모든 기본 액션 클래스는 `setup_steps()`를 통해 선택적으로 스텝 기반 실행을 지원합니다:

### Upload 액션

```python
from synapse_sdk.plugins import BaseUploadAction
from synapse_sdk.plugins.actions.upload import UploadContext

class MyUploadAction(BaseUploadAction[UploadParams]):
    def setup_steps(self, registry: StepRegistry[UploadContext]) -> None:
        registry.register(InitStorageStep())
        registry.register(OrganizeFilesStep())
        registry.register(UploadFilesStep())
        registry.register(GenerateMetadataStep())
        registry.register(CleanupStep())
```

### Train 액션

```python
from synapse_sdk.plugins import BaseTrainAction
from synapse_sdk.plugins.actions.train import TrainContext

class MyTrainAction(BaseTrainAction[TrainParams]):
    def setup_steps(self, registry: StepRegistry[TrainContext]) -> None:
        registry.register(LoadDatasetStep())     # 20%
        registry.register(TrainModelStep())       # 60%
        registry.register(UploadModelStep())      # 20%

    # setup_steps()가 오버라이드되지 않거나 스텝을 등록하지 않으면,
    # 액션은 대신 단순 execute() 모드를 사용합니다
```

### Export 액션

```python
from synapse_sdk.plugins import BaseExportAction
from synapse_sdk.plugins.actions.export import ExportContext

class MyExportAction(BaseExportAction[ExportParams]):
    def setup_steps(self, registry: StepRegistry[ExportContext]) -> None:
        registry.register(FetchResultsStep())
        registry.register(ProcessBatchStep())
        registry.register(WriteOutputStep())
```

## 완전한 예제

다음은 파일 업로드 워크플로우의 완전한 예제입니다:

```python
from dataclasses import dataclass, field
from pathlib import Path
from synapse_sdk.plugins import BaseUploadAction
from synapse_sdk.plugins.pipelines.steps import (
    BaseStep, StepResult, StepRegistry, BaseStepContext, LoggingStep
)

# 컨텍스트 정의
@dataclass
class FileUploadContext(BaseStepContext):
    source_path: Path | None = None
    files: list[Path] = field(default_factory=list)
    uploaded_ids: list[int] = field(default_factory=list)

# 스텝 정의
class DiscoverFilesStep(BaseStep[FileUploadContext]):
    @property
    def name(self) -> str:
        return 'discover_files'

    @property
    def progress_weight(self) -> float:
        return 0.1

    def execute(self, context: FileUploadContext) -> StepResult:
        if not context.source_path or not context.source_path.exists():
            return StepResult(success=False, error='소스 경로를 찾을 수 없습니다')

        context.files = list(context.source_path.glob('**/*'))
        context.files = [f for f in context.files if f.is_file()]

        if not context.files:
            return StepResult(success=False, error='파일을 찾을 수 없습니다')

        return StepResult(success=True, data={'file_count': len(context.files)})

class UploadFilesStep(BaseStep[FileUploadContext]):
    @property
    def name(self) -> str:
        return 'upload_files'

    @property
    def progress_weight(self) -> float:
        return 0.8

    def execute(self, context: FileUploadContext) -> StepResult:
        for i, file in enumerate(context.files):
            # 각 파일 업로드
            file_id = context.client.upload_file(file)
            context.uploaded_ids.append(file_id)

            # 스텝 내 진행 상황 업데이트
            progress = (i + 1) / len(context.files)
            context.set_progress(int(progress * 100), 100, 'upload')

        return StepResult(
            success=True,
            rollback_data={'uploaded_ids': context.uploaded_ids.copy()}
        )

    def rollback(self, context: FileUploadContext, result: StepResult) -> None:
        for file_id in result.rollback_data.get('uploaded_ids', []):
            try:
                context.client.delete_file(file_id)
            except Exception:
                context.errors.append(f'파일 {file_id} 삭제 실패')

class FinalizeStep(BaseStep[FileUploadContext]):
    @property
    def name(self) -> str:
        return 'finalize'

    @property
    def progress_weight(self) -> float:
        return 0.1

    def execute(self, context: FileUploadContext) -> StepResult:
        context.log('upload_complete', {
            'file_count': len(context.uploaded_ids),
            'file_ids': context.uploaded_ids
        })
        return StepResult(success=True)

# 액션에서 사용
class FileUploadAction(BaseUploadAction[FileUploadParams]):
    def setup_steps(self, registry: StepRegistry) -> None:
        # 디버깅을 위해 로깅으로 스텝 래핑
        registry.register(LoggingStep(DiscoverFilesStep()))
        registry.register(LoggingStep(UploadFilesStep()))
        registry.register(LoggingStep(FinalizeStep()))

    def create_context(self) -> FileUploadContext:
        return FileUploadContext(
            runtime_ctx=self.ctx,
            source_path=Path(self.params.source_path)
        )
```

## 모범 사례

### 1. 스텝을 집중적으로 유지

각 스텝은 하나의 일을 잘 수행해야 합니다:

```python
# 좋음: 집중된 스텝
class ValidateFilesStep(BaseStep): ...
class CompressFilesStep(BaseStep): ...
class UploadFilesStep(BaseStep): ...

# 나쁨: 모놀리식 스텝
class ProcessEverythingStep(BaseStep): ...  # 검증, 압축, 업로드 모두 수행
```

### 2. 의미 있는 진행 가중치 사용

실제 시간/복잡도를 기반으로 가중치 할당:

```python
# 좋음: 가중치가 실제 시간 분포를 반영
LoadDataStep:    0.1   # 빠른 파일 읽기
TrainModelStep:  0.8   # 긴 학습 루프
SaveModelStep:   0.1   # 빠른 저장

# 나쁨: 동일한 가중치는 현실을 반영하지 않음
LoadDataStep:    0.33
TrainModelStep:  0.33  # 학습이 10배 더 오래 걸림!
SaveModelStep:   0.33
```

### 3. 파괴적 스텝에 대한 롤백 구현

리소스를 생성하는 모든 스텝은 실패 시 정리해야 합니다:

```python
class CreateResourcesStep(BaseStep):
    def execute(self, context) -> StepResult:
        resource_id = create_resource()
        return StepResult(
            success=True,
            rollback_data={'resource_id': resource_id}
        )

    def rollback(self, context, result) -> None:
        resource_id = result.rollback_data.get('resource_id')
        if resource_id:
            delete_resource(resource_id)
```

### 4. 조건부 스텝에 can_skip() 사용

```python
class CompressionStep(BaseStep):
    def can_skip(self, context) -> bool:
        # 파일이 이미 압축된 경우 스킵
        return all(f.suffix == '.gz' for f in context.files)
```

### 5. 중요한 이벤트 로깅

디버깅을 위해 컨텍스트 로깅 사용:

```python
def execute(self, context) -> StepResult:
    context.log('step_progress', {'phase': 'starting', 'item_count': 100})
    # ... 작업 ...
    context.log('step_progress', {'phase': 'complete', 'processed': 100})
    return StepResult(success=True)
```

## API 레퍼런스

### BaseStep[C]

| 메서드/속성 | 설명 |
|-------------|------|
| `name: str` | 고유한 스텝 식별자 (추상 속성) |
| `progress_weight: float` | 상대적 진행 가중치 0.0-1.0 (추상 속성) |
| `execute(context: C) -> StepResult` | 스텝 실행 (추상 메서드) |
| `can_skip(context: C) -> bool` | 스텝 스킵 가능 여부 확인 (기본값: False) |
| `rollback(context: C, result: StepResult) -> None` | 실패 시 정리 (기본값: no-op) |

### StepResult

| 필드 | 타입 | 기본값 |
|------|------|--------|
| `success` | `bool` | `True` |
| `data` | `dict[str, Any]` | `{}` |
| `error` | `str | None` | `None` |
| `rollback_data` | `dict[str, Any]` | `{}` |
| `skipped` | `bool` | `False` |
| `timestamp` | `datetime` | `datetime.now()` |

### StepRegistry[C]

| 메서드 | 설명 |
|--------|------|
| `register(step)` | 워크플로우 끝에 스텝 추가 |
| `unregister(name)` | 이름으로 스텝 제거 |
| `insert_before(name, step)` | 다른 스텝 전에 삽입 |
| `insert_after(name, step)` | 다른 스텝 후에 삽입 |
| `get_steps()` | 순서화된 스텝 목록 반환 |
| `total_weight` | 모든 스텝 가중치의 합 |

### Orchestrator[C]

| 메서드 | 설명 |
|--------|------|
| `__init__(registry, context, progress_callback=None)` | 오케스트레이터 생성 |
| `execute() -> dict` | 롤백과 함께 모든 스텝 실행 |

### BaseStepContext

| 필드/메서드 | 설명 |
|-------------|------|
| `runtime_ctx: RuntimeContext` | 부모 런타임 컨텍스트 |
| `step_results: list[StepResult]` | 실행된 스텝의 결과 |
| `errors: list[str]` | 축적된 오류 메시지 |
| `log(event, data, file=None)` | 런타임 컨텍스트를 통해 로깅 |
| `set_progress(current, total, category=None)` | 진행 상황 업데이트 |
| `set_metrics(value, category)` | 메트릭 설정 |
