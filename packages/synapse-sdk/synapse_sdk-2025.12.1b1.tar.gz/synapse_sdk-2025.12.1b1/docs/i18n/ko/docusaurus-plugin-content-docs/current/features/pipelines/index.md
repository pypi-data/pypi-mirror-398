---
id: pipelines
title: 파이프라인 패턴
sidebar_position: 3
---

# 파이프라인 패턴

Synapse SDK는 복잡한 워크플로우를 조율하기 위한 강력한 파이프라인 패턴을 제공합니다. 이러한 패턴을 통해 복잡한 작업을 개별적이고 관리 가능한 단계로 분할하고, 내장된 진행 상황 추적, 오류 처리, 자동 롤백 기능을 활용할 수 있습니다.

## 사용 가능한 파이프라인 패턴

### [스텝 오케스트레이션](./step-orchestration.md)

다음 기능을 갖춘 순차적 스텝 기반 워크플로우 시스템:

- **순서화된 스텝 실행** - 의존성에 따라 순차적으로 스텝 실행
- **자동 진행 상황 추적** - 모든 스텝에 걸쳐 가중치 기반 진행률 계산
- **실패 시 롤백** - 스텝 실패 시 자동 정리
- **스텝 조합** - 쉽게 스텝을 결합하고 재정렬
- **유틸리티 래퍼** - 내장된 로깅, 타이밍, 검증 스텝

## 파이프라인 사용 시기

파이프라인 패턴은 다음과 같은 경우에 적합합니다:

| 시나리오 | 예시 |
|----------|------|
| 다단계 워크플로우 | 업로드: 초기화 -> 검증 -> 업로드 -> 정리 |
| 정리가 필요한 작업 | 실패 시 정리가 필요한 파일 처리 |
| 진행 상황 추적 작업 | 학습: 데이터셋(20%) -> 학습(60%) -> 업로드(20%) |
| 조합 가능한 워크플로우 | 액션 간에 공유되는 재사용 가능한 스텝 |

## 빠른 예제

```python
from synapse_sdk.plugins.pipelines.steps import (
    BaseStep, StepResult, StepRegistry, Orchestrator, BaseStepContext
)
from dataclasses import dataclass, field

@dataclass
class MyContext(BaseStepContext):
    """내 워크플로우용 커스텀 컨텍스트."""
    data: list[str] = field(default_factory=list)
    processed_count: int = 0

class LoadDataStep(BaseStep[MyContext]):
    @property
    def name(self) -> str:
        return 'load_data'

    @property
    def progress_weight(self) -> float:
        return 0.2  # 전체 진행률의 20%

    def execute(self, context: MyContext) -> StepResult:
        context.data = ['item1', 'item2', 'item3']
        return StepResult(success=True)

class ProcessDataStep(BaseStep[MyContext]):
    @property
    def name(self) -> str:
        return 'process_data'

    @property
    def progress_weight(self) -> float:
        return 0.7  # 전체 진행률의 70%

    def execute(self, context: MyContext) -> StepResult:
        for item in context.data:
            # 각 항목 처리
            context.processed_count += 1
        return StepResult(success=True)

    def rollback(self, context: MyContext, result: StepResult) -> None:
        # 실패 시 정리
        context.processed_count = 0

class FinalizeStep(BaseStep[MyContext]):
    @property
    def name(self) -> str:
        return 'finalize'

    @property
    def progress_weight(self) -> float:
        return 0.1  # 전체 진행률의 10%

    def execute(self, context: MyContext) -> StepResult:
        return StepResult(
            success=True,
            data={'processed': context.processed_count}
        )

# 워크플로우 실행
registry = StepRegistry[MyContext]()
registry.register(LoadDataStep())
registry.register(ProcessDataStep())
registry.register(FinalizeStep())

context = MyContext(runtime_ctx=runtime_ctx)
orchestrator = Orchestrator(registry, context)
result = orchestrator.execute()
# {'success': True, 'steps_executed': 3, 'steps_total': 3}
```

## 핵심 컴포넌트

| 컴포넌트 | 설명 |
|----------|------|
| `BaseStep[C]` | 워크플로우 스텝을 위한 추상 기본 클래스 |
| `StepResult` | 스텝 실행 결과를 담는 데이터클래스 |
| `StepRegistry[C]` | 순서화된 스텝 목록 관리 |
| `Orchestrator[C]` | 진행 상황 추적 및 롤백과 함께 스텝 실행 |
| `BaseStepContext` | 스텝 간 상태 공유를 위한 기본 컨텍스트 |

## 유틸리티 스텝

| 유틸리티 | 설명 |
|----------|------|
| `LoggingStep` | 시작/종료 로깅으로 스텝을 래핑 |
| `TimingStep` | 스텝 실행 시간 측정 |
| `ValidationStep` | 진행 전 컨텍스트 상태 검증 |

## 액션과의 통합

모든 기본 액션 클래스(Train, Export, Upload)는 선택적으로 스텝 기반 실행을 지원합니다:

```python
from synapse_sdk.plugins import BaseUploadAction
from synapse_sdk.plugins.pipelines.steps import BaseStep, StepRegistry

class MyUploadAction(BaseUploadAction[MyParams]):
    def setup_steps(self, registry: StepRegistry[UploadContext]) -> None:
        registry.register(InitializeStep())
        registry.register(ValidateStep())
        registry.register(UploadFilesStep())
        registry.register(CleanupStep())
```

전체 문서는 [스텝 오케스트레이션](./step-orchestration.md) 가이드를 참조하세요.
