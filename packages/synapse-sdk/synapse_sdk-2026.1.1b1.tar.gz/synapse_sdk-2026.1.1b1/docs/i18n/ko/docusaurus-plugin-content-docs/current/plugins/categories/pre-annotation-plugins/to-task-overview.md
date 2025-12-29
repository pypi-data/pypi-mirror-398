---
id: to-task-overview
title: ToTask 액션 - 사용자 가이드
sidebar_position: 2
---

# ToTask 액션 - 사용자 가이드

`to_task` 액션은 파일 기반 및 AI 추론 기반 주석 방법을 모두 지원하며 포괄적인 검증 및 진행 추적 기능과 함께 자동화된 작업 주석 기능을 제공합니다.

## 개요

ToTask 액션은 다음과 같은 방법으로 Synapse 프로젝트의 작업에 주석을 추가합니다:

- JSON 파일에서 주석 데이터 가져오기 (파일 기반 방법)
- 전처리기를 통한 모델 추론 실행 (추론 기반 방법)
- 자동으로 작업 데이터에 주석 적용
- 실시간으로 진행 및 메트릭 추적
- 자동 롤백으로 오류를 우아하게 처리

## 사전 요구사항

### 공통 요구사항

- 작업이 있는 유효한 Synapse 프로젝트
- 프로젝트에 연결된 데이터 컬렉션
- 적절한 권한이 있는 에이전트
- 필터 기준과 일치하는 작업

### 파일 기반 방법 요구사항

- 데이터 유닛에 `target_specification_name`과 일치하는 파일이 있어야 함
- JSON 파일이 HTTP/HTTPS URL을 통해 접근 가능해야 함
- JSON 구조가 작업 객체 형식과 일치해야 함

### 추론 기반 방법 요구사항

- 배포되고 활성화된 전처리기 플러그인
- 전처리기가 작업의 데이터 타입을 지원해야 함
- 작업에 주 이미지 또는 호환 가능한 입력 데이터가 있어야 함

## 기본 사용법

### 파일 기반 주석

데이터 유닛에 저장된 파일 URL의 JSON 데이터를 사용하여 작업에 주석을 추가합니다.

```python
from synapse_sdk.plugins.categories.pre_annotation.actions.to_task import ToTaskAction

# 구성
params = {
    'name': 'File_Based_Annotation',
    'description': 'Annotate tasks from JSON files',
    'project': 123,
    'agent': 1,
    'task_filters': {
        'status': 'pending',
        'data_collection': 456
    },
    'method': 'file',
    'target_specification_name': 'annotation_data',
    'pre_processor_params': {}
}

# 실행
action = ToTaskAction(run=run_instance, params=params)
result = action.start()

# 결과 확인
if result['status'] == 'SUCCEEDED':
    print(f"성공: {result['message']}")
else:
    print(f"실패: {result['message']}")
```

**작동 방식:**

1. 시스템이 필터와 일치하는 작업을 찾음
2. 각 작업에 대해 데이터 유닛을 가져옴
3. 사양 이름이 `annotation_data`인 파일을 찾음
4. 파일 URL에서 JSON 데이터를 다운로드
5. JSON 데이터를 작업에 적용
6. 각 작업의 성공/실패를 추적

### 추론 기반 주석

전처리기를 통한 AI 모델 추론을 사용하여 작업에 주석을 추가합니다.

```python
params = {
    'name': 'Inference_Based_Annotation',
    'description': 'Auto-annotate using AI model',
    'project': 123,
    'agent': 1,
    'task_filters': {
        'status': 'pending',
        'assignee': None  # 할당되지 않은 작업만
    },
    'method': 'inference',
    'pre_processor': 789,  # 전처리기 플러그인 릴리스 ID
    'pre_processor_params': {
        'confidence_threshold': 0.8,
        'model_config': {
            'batch_size': 16,
            'device': 'cuda'
        }
    }
}

action = ToTaskAction(run=run_instance, params=params)
result = action.start()
```

**작동 방식:**

1. 시스템이 전처리기가 활성화되어 있는지 검증
2. 필터와 일치하는 작업을 찾음
3. 각 작업에 대해 주 이미지 URL을 추출
4. 이미지와 파라미터로 전처리기 API 호출
5. 추론 결과를 작업 객체 형식으로 변환
6. 생성된 주석으로 작업 업데이트

## 파라미터 레퍼런스

### 필수 파라미터

#### `name` (string)

- 액션 이름 식별자
- 공백을 포함해서는 안 됨
- 예: `"File_Annotation_Job"`

#### `project` (integer)

- Synapse 프로젝트 ID
- 유효하고 접근 가능한 프로젝트여야 함
- 예: `123`

#### `agent` (integer)

- 실행을 위한 에이전트 ID
- 에이전트가 프로젝트에 대한 권한이 있어야 함
- 예: `1`

#### `task_filters` (object)

- 작업 선택을 위한 필터 기준 딕셔너리
- 모든 작업 쿼리 파라미터 지원
- 예: `{"status": "pending", "data_collection": 456}`

#### `method` (string)

- 주석 방법 타입
- 값: `"file"` 또는 `"inference"`
- 사용할 주석 전략을 결정

### 방법별 파라미터

#### 파일 기반 방법용

**`target_specification_name`** (string, 파일 방법에 필수)

- 주석 JSON을 포함하는 파일 사양 이름
- 프로젝트의 파일 사양에 존재해야 함
- 예: `"annotation_data"`

#### 추론 기반 방법용

**`pre_processor`** (integer, 추론 방법에 필수)

- 전처리기 플러그인 릴리스 ID
- 전처리기가 배포되고 활성화되어 있어야 함
- 예: `789`

**`pre_processor_params`** (object, 선택사항)

- 전처리기에 전달되는 구성 파라미터
- 구조는 전처리기 구현에 따라 다름
- 예:
  ```python
  {
      'confidence_threshold': 0.8,
      'model_config': {
          'batch_size': 16,
          'device': 'cuda',
          'use_fp16': True
      },
      'post_processing': {
          'nms_threshold': 0.5,
          'min_size': 10
      }
  }
  ```

### 선택적 파라미터

#### `description` (string)

- 액션에 대한 사람이 읽을 수 있는 설명
- 예: `"Annotate all pending tasks with model v2 predictions"`

## 작업 필터링

`task_filters` 파라미터는 다양한 필터링 옵션을 지원합니다:

### 일반적인 필터 예제

```python
# 상태별 필터링
task_filters = {'status': 'pending'}

# 데이터 컬렉션별 필터링
task_filters = {'data_collection': 456}

# 담당자별 필터링
task_filters = {'assignee': 12}  # 특정 사용자
task_filters = {'assignee': None}  # 할당되지 않은 작업

# 다중 필터 (AND 로직)
task_filters = {
    'status': 'pending',
    'data_collection': 456,
    'assignee': None
}

# 생성 날짜별 필터링
task_filters = {
    'created_at__gte': '2025-01-01',
    'created_at__lte': '2025-01-31'
}
```

### 고급 필터링

```python
# 여러 기준 결합
task_filters = {
    'status__in': ['pending', 'in_progress'],
    'data_collection': 456,
    'created_at__gte': '2025-01-01'
}
```

## 진행 및 메트릭

### 실시간 진행 업데이트

액션은 지속적인 진행 업데이트를 제공합니다:

```python
# 실행 중 진행이 자동으로 기록됩니다
# 로그 출력 예:
# [annotate_task_data] 진행: 25.0% (25/100)
# [annotate_task_data] 진행: 50.0% (50/100)
# [annotate_task_data] 진행: 100.0% (100/100)
```

### 메트릭 카테고리

**성공 메트릭:**

- 처리된 총 작업 수
- 성공적으로 주석이 추가된 수
- 주석 추가 실패 수
- 대기 중(아직 처리되지 않음) 수

**상태 메시지:**

```python
# 메트릭 출력 예
{
    'total': 100,
    'success': 95,
    'failed': 5,
    'stand_by': 0
}
```

### 메트릭 접근

메트릭은 실행 로거에 자동으로 기록되며 Synapse 플랫폼 UI 또는 API를 통해 접근할 수 있습니다.

## 파일 기반 주석 세부사항

### 예상 JSON 구조

JSON 파일은 작업 데이터 객체 형식을 따라야 합니다:

```json
{
  "objects": [
    {
      "id": "obj_001",
      "class_id": 1,
      "type": "bbox",
      "coordinates": {
        "x": 100,
        "y": 150,
        "width": 200,
        "height": 180
      },
      "properties": {
        "confidence": 0.95,
        "label": "person"
      }
    }
  ]
}
```

### 파일 사양 설정

1. **파일 사양 정의** - 프로젝트에서 대상 이름으로 파일 사양 정의 (예: `annotation_data`)
2. **주석 JSON 파일 업로드** - 이 사양으로 데이터 유닛에 업로드
3. **파일 접근성 확인** - HTTP/HTTPS URL을 통해 접근 가능한지 확인
4. **ToTask 액션 실행** - 사양과 일치하는 `target_specification_name`으로 실행

### 예제 워크플로우

```python
# 1단계: 데이터 준비
# - 데이터 컬렉션에 이미지 업로드
# - 사양 "annotations"로 주석 JSON 파일 업로드

# 2단계: 구성 및 실행
params = {
    'name': 'Apply_Pregenerated_Annotations',
    'project': 123,
    'agent': 1,
    'task_filters': {'status': 'pending'},
    'method': 'file',
    'target_specification_name': 'annotations'
}

action = ToTaskAction(run=run_instance, params=params)
result = action.start()
```

## 추론 기반 주석 세부사항

### 전처리기 요구사항

전처리기는 다음을 충족해야 합니다:

- 배포되어 `RUNNING` 상태여야 함
- 입력으로 이미지 URL을 받아야 함
- 작업 호환 형식으로 결과를 반환해야 함
- 작업의 데이터 타입을 지원해야 함

### 전처리기 파라미터

`pre_processor_params`를 통해 추론 동작 구성:

```python
pre_processor_params = {
    # 모델 구성
    'model_config': {
        'batch_size': 16,
        'device': 'cuda',
        'use_fp16': True
    },

    # 추론 임계값
    'confidence_threshold': 0.8,
    'nms_threshold': 0.5,

    # 후처리
    'min_object_size': 10,
    'max_objects': 100,

    # 출력 형식
    'include_masks': True,
    'output_format': 'coco'
}
```

### 추론 워크플로우

```python
# 1단계: 전처리기 배포
# (전처리기 플러그인 문서 참조)

# 2단계: 추론 주석 구성
params = {
    'name': 'AI_Auto_Annotation',
    'project': 123,
    'agent': 1,
    'task_filters': {
        'status': 'pending',
        'data_collection': 456
    },
    'method': 'inference',
    'pre_processor': 789,
    'pre_processor_params': {
        'confidence_threshold': 0.85,
        'model_config': {
            'device': 'cuda'
        }
    }
}

# 3단계: 실행
action = ToTaskAction(run=run_instance, params=params)
result = action.start()

# 4단계: 결과 검토
# 메트릭에서 성공/실패 수 확인
# Synapse UI에서 주석이 추가된 작업 검토
```

### 전처리기 관리

시스템은 자동으로:

- 전처리기가 실행 중인지 확인
- 필요시 전처리기 시작
- 전처리기가 준비될 때까지 대기
- 전처리기 오류를 우아하게 처리

## 오류 처리

### 작업 수준 오류

개별 작업 실패는 워크플로우를 중지하지 않습니다:

```python
# 예: 100개의 작업 처리
# - 95개 성공
# - 5개 실패 (예: 잘못된 JSON, 네트워크 오류)
# 결과: 작업 완료, success=95, failed=5
```

실패한 작업은 오류 세부정보와 함께 기록됩니다:

```
[작업 123] 실패: 주석 파일의 JSON 형식이 잘못됨
[작업 456] 실패: 전처리기 추론 시간 초과
```

### 치명적 오류

시스템 수준 오류는 즉시 롤백을 트리거합니다:

```python
# 치명적 오류 예:
# - 프로젝트를 찾을 수 없음
# - 데이터 컬렉션이 연결되지 않음
# - 대상 사양이 존재하지 않음
# - 전처리기가 배포되지 않음

# 치명적 오류 발생 시:
# 1. 워크플로우 즉시 중지
# 2. 완료된 단계 롤백
# 3. 임시 파일 정리
# 4. 상세한 메시지와 함께 오류 발생
```

### 일반적인 오류 및 해결 방법

#### "Project has no data collection"

**해결 방법:** 실행 전 프로젝트에 데이터 컬렉션을 연결하세요.

#### "Target specification not found"

**해결 방법:** `target_specification_name`이 프로젝트 파일 사양에 존재하는지 확인하세요.

#### "Pre-processor not active"

**해결 방법:** 추론 주석을 실행하기 전에 전처리기를 배포하고 시작하세요.

#### "No tasks found matching filters"

**해결 방법:** `task_filters` 기준을 확인하고 작업이 존재하는지 확인하세요.

#### "Failed to download JSON from URL"

**해결 방법:** 주석 파일이 접근 가능하고 URL이 유효한지 확인하세요.

## 모범 사례

### 성능 최적화

1. **추론을 위한 배치 크기**

   ```python
   pre_processor_params = {
       'model_config': {
           'batch_size': 32  # GPU 메모리에 따라 조정
       }
   }
   ```

2. **효과적인 작업 필터링**

   ```python
   # 좋음: 구체적인 필터
   task_filters = {
       'status': 'pending',
       'data_collection': 456,
       'created_at__gte': '2025-01-01'
   }

   # 피할 것: 너무 광범위함
   task_filters = {'status': 'pending'}  # 수천 개 일치 가능
   ```

3. **적절한 신뢰도 임계값 사용**

   ```python
   # 높은 임계값 = 더 적은 거짓 양성
   pre_processor_params = {
       'confidence_threshold': 0.9  # 엄격함
   }

   # 낮은 임계값 = 더 많은 탐지
   pre_processor_params = {
       'confidence_threshold': 0.5  # 허용적
   }
   ```

### 신뢰성

1. **처리 전 데이터 검증**

   - 작업에 필요한 데이터(이미지, 파일)가 있는지 확인
   - 파일 사양이 존재하는지 확인
   - 전처리기가 테스트되고 안정적인지 확인

2. **진행 모니터링**

   - 실행 중 진행 로그 검토
   - 완료 후 메트릭 확인
   - 실패한 작업 조사

3. **부분 실패 처리**
   ```python
   # 실행 후 메트릭 확인
   if result['status'] == 'SUCCEEDED':
       # 모든 작업이 성공했는지 확인
       # 실패 수 검토
       # 필요시 실패한 작업에 대해 재실행
   ```

### 보안

1. **파일 접근 검증**

   - JSON 파일이 신뢰할 수 있는 소스에서 온 것인지 확인
   - 업로드 전 파일 내용 검증
   - 보안 HTTPS URL 사용

2. **입력 검증**
   - 전처리기 파라미터 검증
   - 신뢰도 임계값이 합리적인지 확인
   - 작업 필터가 민감한 데이터를 노출하지 않는지 확인

## 완전한 예제

### 예제 1: 대량 파일 기반 주석

```python
"""
시나리오: 사전 생성된 주석 JSON 파일이 있는 1000개의 이미지가 있습니다.
목표: 모든 주석을 대기 중인 작업에 적용합니다.
"""

from synapse_sdk.plugins.categories.pre_annotation.actions.to_task import ToTaskAction

params = {
    'name': 'Bulk_File_Annotation_Jan2025',
    'description': 'Apply pre-generated annotations from external tool',
    'project': 123,
    'agent': 1,
    'task_filters': {
        'status': 'pending',
        'data_collection': 456,
        'created_at__gte': '2025-01-01'
    },
    'method': 'file',
    'target_specification_name': 'external_annotations',
    'pre_processor_params': {}
}

action = ToTaskAction(run=run_instance, params=params)
result = action.start()

print(f"상태: {result['status']}")
print(f"메시지: {result['message']}")
```

### 예제 2: AI 기반 자동 주석

```python
"""
시나리오: 전처리기로 배포된 학습된 객체 탐지 모델이 있습니다.
목표: 높은 신뢰도 예측으로 할당되지 않은 모든 작업에 자동 주석을 추가합니다.
"""

params = {
    'name': 'AI_Object_Detection_v2',
    'description': 'Auto-detect objects using YOLOv8 model',
    'project': 123,
    'agent': 1,
    'task_filters': {
        'status': 'pending',
        'assignee': None,  # 할당되지 않은 작업만
        'data_collection': 789
    },
    'method': 'inference',
    'pre_processor': 456,
    'pre_processor_params': {
        'confidence_threshold': 0.85,
        'nms_threshold': 0.5,
        'model_config': {
            'batch_size': 16,
            'device': 'cuda',
            'use_fp16': True
        },
        'class_filter': [1, 2, 3],  # 특정 클래스만 탐지
        'min_object_size': 20
    }
}

action = ToTaskAction(run=run_instance, params=params)
result = action.start()

# 결과 확인
if result['status'] == 'SUCCEEDED':
    print("자동 주석 성공적으로 완료")
    # 품질 확인을 위해 Synapse UI에서 작업 검토
else:
    print(f"실패: {result['message']}")
```

### 예제 3: 능동 학습 워크플로우

```python
"""
시나리오: 능동 학습을 통한 반복적 모델 개선.
목표: 모델로 자동 주석 추가, 불확실한 케이스는 수동 검토.
"""

# 1단계: 높은 신뢰도로 자동 주석
params_high_confidence = {
    'name': 'Active_Learning_Round1_High',
    'project': 123,
    'agent': 1,
    'task_filters': {'status': 'pending'},
    'method': 'inference',
    'pre_processor': 789,
    'pre_processor_params': {
        'confidence_threshold': 0.9  # 높은 신뢰도만
    }
}

action = ToTaskAction(run=run_instance, params=params_high_confidence)
result = action.start()

# 2단계: 낮은 신뢰도 케이스는 수동 검토로
# (사람 주석 작업자를 위해 대기 중으로 유지)

# 3단계: 수동 검토 후 모델 재학습 및 반복
```

## 문제 해결

### 실패한 작업 디버깅

1. **특정 오류에 대한 로그 확인**

   ```
   다음과 같은 메시지 찾기:
   [작업 123] 실패: <error_message>
   ```

2. **작업 데이터 구조 확인**

   - 작업에 필요한 필드가 있는지 확인
   - 데이터 유닛이 존재하는지 확인
   - 파일 URL이 접근 가능한지 검증

3. **먼저 소규모 배치로 테스트**
   ```python
   # 먼저 10개 작업으로 테스트
   task_filters = {
       'status': 'pending',
       'limit': 10
   }
   ```

### 성능 문제

1. 시간 초과가 발생하면 **배치 크기 줄이기**
2. 더 작은 그룹을 처리하기 위해 **작업을 더 좁게 필터링**
3. 추론 방법의 경우 **전처리기 리소스 사용량 확인**

### 검증 오류

1. **"No tasks found"** - 필터와 작업 존재 확인
2. **"Invalid project"** - 프로젝트 ID 및 권한 확인
3. **"Target specification not found"** - 파일 사양 이름 확인
4. **"Pre-processor not found"** - 전처리기 ID 및 상태 확인

## 다음 단계

- **아키텍처 세부사항**: 기술 아키텍처는 [ToTask 액션 개발](./to-task-action-development.md)을 읽어보세요
- **커스텀 전략**: 커스텀 검증 및 주석 전략으로 ToTask 액션을 확장하는 방법을 배우세요
- **전처리기 가이드**: 모델 배포는 전처리기 플러그인 문서를 참조하세요

## 관련 문서

- [Pre-annotation 플러그인 개요](./pre-annotation-plugin-overview.md)
- [업로드 플러그인](../upload-plugins/upload-plugin-overview.md)
- 플러그인 개발 가이드
- API 레퍼런스
