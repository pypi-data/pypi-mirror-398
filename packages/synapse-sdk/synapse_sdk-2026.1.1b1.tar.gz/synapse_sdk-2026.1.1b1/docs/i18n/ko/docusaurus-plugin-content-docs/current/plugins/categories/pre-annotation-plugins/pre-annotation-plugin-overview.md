---
id: pre-annotation-plugin-overview
title: Pre-annotation 플러그인 개요
sidebar_position: 1
---

# Pre-annotation 플러그인 개요

Pre-annotation 플러그인은 Synapse 플랫폼을 위한 자동화된 작업 주석 기능을 제공하며, 파일 기반 및 AI 추론 기반 주석 워크플로우를 포괄적인 검증, 진행 추적 및 오류 처리와 함께 지원합니다.

## 빠른 개요

**카테고리:** Pre-annotation
**사용 가능한 액션:** `to_task`
**실행 방법:** 작업(Job) 기반 실행

## 주요 기능

- **파일 기반 주석 (File-based Annotation)**: 파일 URL의 JSON 데이터를 사용한 자동 작업 주석
- **추론 기반 주석 (Inference-based Annotation)**: 전처리기 플러그인과 모델 추론을 사용한 AI 기반 주석
- **전략 패턴 아키텍처 (Strategy Pattern Architecture)**: 플러그형 검증, 주석, 메트릭 전략
- **워크플로우 오케스트레이션 (Workflow Orchestration)**: 실패 시 자동 롤백을 지원하는 7단계 오케스트레이션 워크플로우
- **진행 추적 (Progress Tracking)**: 실시간 진행 업데이트 및 포괄적인 메트릭
- **유연한 작업 필터링 (Flexible Task Filtering)**: 다양한 기준을 사용한 고급 작업 필터링

## 사용 사례

- 사전 생성된 JSON 파일을 사용한 대량 작업 주석
- 학습된 모델을 사용한 AI 기반 자동 주석
- 사람의 검토 전 작업 사전 라벨링
- 자동 주석을 사용한 데이터셋 준비
- 모델 보조 주석 워크플로우
- 대기 중인 작업의 일괄 처리

## 지원되는 주석 방법

### 파일 기반 주석 (`method: 'file'`)

데이터 유닛 파일 사양에 저장된 JSON 파일에서 주석 데이터를 가져와 작업에 적용합니다.

**사용 시기:**

- 사전 생성된 주석 JSON 파일이 있는 경우
- 주석이 데이터 유닛의 파일로 저장된 경우
- 결정론적이고 재현 가능한 주석이 필요한 경우
- 외부 도구가 주석 파일을 생성한 경우

**요구사항:**

- `target_specification_name`: 주석 JSON을 포함하는 파일 사양 이름
- 작업에 지정된 파일 사양이 포함된 데이터 유닛이 있어야 함
- JSON 파일이 HTTP/HTTPS URL을 통해 접근 가능해야 함

### 추론 기반 주석 (`method: 'inference'`)

전처리기 플러그인을 사용하여 작업 데이터에 대한 모델 추론을 실행하고 자동으로 주석을 생성합니다.

**사용 시기:**

- 자동 주석을 위한 학습된 모델이 있는 경우
- AI 보조 주석이 필요한 경우
- 모델을 통해 이미지/데이터를 처리해야 하는 경우
- 능동 학습(active learning) 워크플로우를 구현하는 경우

**요구사항:**

- `pre_processor`: 배포된 전처리기 플러그인의 ID
- 전처리기가 활성화되어 실행 중이어야 함
- 작업에 주 이미지 또는 호환 가능한 데이터가 있어야 함

## 구성 개요

### 기본 파라미터

```json
{
  "name": "Annotation Job",
  "description": "Annotate pending tasks",
  "project": 123,
  "agent": 1,
  "task_filters": {
    "status": "pending"
  },
  "method": "file"
}
```

### 주요 파라미터

| 파라미터                    | 타입    | 필수   | 설명                                   |
| --------------------------- | ------- | ------ | -------------------------------------- |
| `name`                      | string  | 예     | 액션 이름 (공백 불가)                  |
| `description`               | string  | 아니오 | 액션 설명                              |
| `project`                   | integer | 예     | 프로젝트 ID                            |
| `agent`                     | integer | 예     | 에이전트 ID                            |
| `task_filters`              | object  | 예     | 작업 필터링 기준                       |
| `method`                    | string  | 예     | 주석 방법: `'file'` 또는 `'inference'` |
| `target_specification_name` | string  | 조건부 | 파일 사양 이름 (파일 방법에 필수)      |
| `pre_processor`             | integer | 조건부 | 전처리기 ID (추론 방법에 필수)         |
| `pre_processor_params`      | object  | 아니오 | 전처리기 구성 파라미터                 |

## 빠른 시작

### 파일 기반 주석 예제

```python
from synapse_sdk.plugins.categories.pre_annotation.actions.to_task import ToTaskAction

params = {
    'name': 'File_Annotation_Job',
    'project': 123,
    'agent': 1,
    'task_filters': {
        'status': 'pending',
        'data_collection': 456
    },
    'method': 'file',
    'target_specification_name': 'annotation_data'
}

action = ToTaskAction(run=run_instance, params=params)
result = action.start()
```

### 추론 기반 주석 예제

```python
params = {
    'name': 'AI_Annotation_Job',
    'project': 123,
    'agent': 1,
    'task_filters': {
        'status': 'pending'
    },
    'method': 'inference',
    'pre_processor': 789,
    'pre_processor_params': {
        'confidence_threshold': 0.8
    }
}

action = ToTaskAction(run=run_instance, params=params)
result = action.start()
```

## 워크플로우 단계

to_task 액션은 7단계 오케스트레이션 워크플로우를 통해 실행됩니다:

1. **프로젝트 검증 (Project Validation)** - 프로젝트 존재 및 데이터 컬렉션 확인
2. **작업 검증 (Task Validation)** - 필터와 일치하는 작업 찾기 및 검증
3. **방법 결정 (Method Determination)** - 주석 방법 식별 (file 또는 inference)
4. **방법 검증 (Method Validation)** - 방법별 요구사항 검증
5. **처리 초기화 (Processing Initialization)** - 메트릭 및 진행 추적 설정
6. **작업 처리 (Task Processing)** - 각 작업에 대한 주석 전략 실행
7. **마무리 (Finalization)** - 최종 메트릭 집계 및 결과 반환

각 단계는 검증되며 실패 시 자동 롤백을 트리거할 수 있습니다.

## 진행 및 메트릭

액션은 다음에 대한 실시간 업데이트를 제공합니다:

- **진행 백분율 (Progress Percentage)**: 전체 완료 백분율
- **성공 카운트 (Success Count)**: 성공적으로 주석이 추가된 작업 수
- **실패 카운트 (Failed Count)**: 주석 추가에 실패한 작업 수
- **대기 카운트 (Standby Count)**: 아직 처리되지 않은 작업 수

## 오류 처리

### 작업 수준 오류

개별 작업 실패는 기록되고 추적되지만 전체 워크플로우를 중지하지 않습니다. 액션은 나머지 작업을 계속 처리합니다.

### 치명적 오류

시스템 수준 오류(예: 잘못된 프로젝트, 네트워크 실패)는 즉시 워크플로우 종료 및 완료된 단계의 롤백을 트리거합니다.

### 자동 롤백

치명적 실패 시 오케스트레이터는 자동으로 다음을 롤백합니다:

- 캐시된 프로젝트 데이터 정리
- 작업 ID 목록 재설정
- 임시 파일 정리
- 메트릭 복원

## 다음 단계

- **사용자 가이드**: 상세한 사용 지침은 [ToTask 개요](./to-task-overview.md)를 참조하세요
- **개발자 가이드**: 아키텍처 세부 정보는 [ToTask 액션 개발](./to-task-action-development.md)을 참조하세요
- **API 레퍼런스**: 전체 API 문서를 살펴보세요

## 관련 문서

- [업로드 플러그인](../upload-plugins/upload-plugin-overview.md) - 파일 업로드 및 데이터 수집
- 플러그인 개발 가이드 - 커스텀 플러그인 생성
- 전처리기 플러그인 - 모델 배포 및 추론
