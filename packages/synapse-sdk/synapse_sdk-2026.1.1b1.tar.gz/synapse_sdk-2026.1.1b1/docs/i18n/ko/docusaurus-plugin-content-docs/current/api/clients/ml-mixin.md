---
id: ml-mixin
title: MLClientMixin
sidebar_position: 16
---

# MLClientMixin

Synapse 백엔드를 위한 머신러닝 모델 관리 및 정답 데이터 작업을 제공합니다.

## 개요

`MLClientMixin`은 머신러닝 모델, 정답 데이터셋, 모델 평가 워크플로와 관련된 모든 작업을 처리합니다. 이 믹스인은 `BackendClient`에 자동으로 포함되며 ML 파이프라인 통합을 위한 메서드를 제공합니다.

## 모델 관리

### `list_models(params=None)`

필터링 옵션과 함께 사용 가능한 머신러닝 모델을 나열합니다.

```python
# 모든 모델 나열
models = client.list_models()
for model in models[0]:
    print(f"모델: {model['name']} (ID: {model['id']})")

# 특정 프로젝트의 모델 나열
project_models = client.list_models(params={'project': 123})

# 유형별 모델 나열
classification_models = client.list_models(params={'model_type': 'classification'})

# 활성 모델만 나열
active_models = client.list_models(params={'is_active': True})
```

**매개변수:**

- `params` (dict, 선택사항): 필터링 매개변수

**일반적인 필터링 params:**

- `project`: 프로젝트 ID로 필터링
- `model_type`: 모델 유형으로 필터링 (`classification`, `detection`, `segmentation`)
- `is_active`: 모델 상태로 필터링
- `created_after`: 생성 날짜로 필터링
- `search`: 모델 이름 및 설명에서 텍스트 검색

**반환값:**

- `tuple`: (models_list, total_count)

### `get_model(pk, params=None, url_conversion=None)`

특정 모델에 대한 상세 정보를 가져옵니다.

```python
# 기본 모델 정보 가져오기
model = client.get_model(456)
print(f"모델: {model['name']}")
print(f"유형: {model['model_type']}")
print(f"정확도: {model['metrics']['accuracy']}")

# 확장된 메트릭과 함께 모델 가져오기
model = client.get_model(456, params={'expand': 'metrics'})

# 파일에 대한 사용자 정의 URL 변환과 함께 모델 가져오기
model = client.get_model(
    456,
    url_conversion={'file': lambda url: f"https://cdn.example.com{url}"}
)
```

**매개변수:**

- `pk` (int): 모델 ID
- `params` (dict, 선택사항): 쿼리 매개변수
- `url_conversion` (dict, 선택사항): 파일 필드에 대한 사용자 정의 URL 변환

**일반적인 params:**

- `expand`: 추가 데이터 포함 (`metrics`, `evaluations`, `versions`)
- `include_file`: 모델 파일 정보 포함 여부

**반환값:**

- `dict`: 메타데이터와 메트릭을 포함한 완전한 모델 정보

**모델 구조:**

- `id`: 모델 ID
- `name`: 모델 이름
- `description`: 모델 설명
- `model_type`: 모델 유형
- `file`: 모델 파일 참조
- `metrics`: 성능 메트릭
- `project`: 연관된 프로젝트 ID
- `is_active`: 모델이 현재 활성 상태인지 여부
- `created_at`: 생성 타임스탬프

### `create_model(data)`

파일 업로드와 함께 새로운 머신러닝 모델을 생성합니다.

```python
# 파일 업로드와 함께 모델 생성
model_data = {
    'name': 'Object Detection Model v2',
    'description': '향상된 정확도를 가진 개선된 객체 탐지 모델',
    'model_type': 'detection',
    'project': 123,
    'metrics': {
        'accuracy': 0.92,
        'precision': 0.89,
        'recall': 0.94,
        'f1_score': 0.91
    },
    'configuration': {
        'input_size': [640, 640],
        'num_classes': 10,
        'framework': 'pytorch'
    },
    'file': '/path/to/model.pkl'  # 청크 업로드를 통해 업로드됨
}

new_model = client.create_model(model_data)
print(f"ID {new_model['id']}로 모델 생성됨")
```

**매개변수:**

- `data` (dict): 모델 구성 및 메타데이터

**모델 데이터 구조:**

- `name` (str, 필수): 모델 이름
- `description` (str): 모델 설명
- `model_type` (str, 필수): 모델 유형
- `project` (int, 필수): 프로젝트 ID
- `file` (str, 필수): 모델 파일 경로
- `metrics` (dict): 성능 메트릭
- `configuration` (dict): 모델 구성
- `is_active` (bool): 모델이 활성 상태여야 하는지 여부

**반환값:**

- `dict`: 생성된 ID가 포함된 생성된 모델

**참고:** 모델 파일은 최적 성능을 위해 청크 업로드를 사용하여 자동으로 업로드됩니다.

## 정답 데이터 작업

### `list_ground_truth_events(params=None, url_conversion=None, list_all=False)`

포괄적인 필터링 옵션과 함께 정답 이벤트를 나열합니다.

```python
# 데이터셋 버전의 정답 이벤트 나열
events = client.list_ground_truth_events(params={
    'ground_truth_dataset_versions': [123]
})

# 모든 이벤트 나열 (페이지네이션 자동 처리)
all_events = client.list_ground_truth_events(list_all=True)

# 날짜 필터링과 함께 이벤트 나열
from datetime import datetime, timedelta
recent_date = (datetime.now() - timedelta(days=30)).isoformat()
recent_events = client.list_ground_truth_events(params={
    'created_after': recent_date,
    'ground_truth_dataset_versions': [123]
})

# 사용자 정의 URL 변환과 함께 이벤트 나열
events = client.list_ground_truth_events(
    params={'ground_truth_dataset_versions': [123]},
    url_conversion={'files': lambda url: f"https://cdn.example.com{url}"}
)
```

**매개변수:**

- `params` (dict, 선택사항): 필터링 매개변수
- `url_conversion` (dict, 선택사항): 파일 필드에 대한 사용자 정의 URL 변환
- `list_all` (bool): True인 경우, 페이지네이션을 자동 처리

**일반적인 필터링 params:**

- `ground_truth_dataset_versions`: 데이터셋 버전 ID 목록
- `project`: 프로젝트 ID로 필터링
- `created_after`: 생성 날짜로 필터링
- `data_type`: 데이터 유형으로 필터링
- `search`: 이벤트 데이터에서 텍스트 검색

**반환값:**

- `tuple`: `list_all=False`인 경우 (events_list, total_count)
- `list`: `list_all=True`인 경우 모든 이벤트

**정답 이벤트 구조:**

- `id`: 이벤트 ID
- `data`: 어노테이션/정답 데이터
- `data_unit`: 연관된 데이터 유닛 정보
- `ground_truth_dataset_version`: 데이터셋 버전 ID
- `created_at`: 생성 타임스탬프
- `metadata`: 추가 이벤트 메타데이터

### `get_ground_truth_version(pk)`

정답 데이터셋 버전에 대한 상세 정보를 가져옵니다.

```python
version = client.get_ground_truth_version(123)
print(f"데이터셋 버전: {version['version']}")
print(f"데이터셋: {version['ground_truth_dataset']['name']}")
print(f"총 이벤트: {version['event_count']}")
print(f"생성됨: {version['created_at']}")
```

**매개변수:**

- `pk` (int): 정답 데이터셋 버전 ID

**반환값:**

- `dict`: 완전한 데이터셋 버전 정보

**데이터셋 버전 구조:**

- `id`: 버전 ID
- `version`: 버전 번호/이름
- `ground_truth_dataset`: 부모 데이터셋 정보
- `event_count`: 이 버전의 이벤트 수
- `description`: 버전 설명
- `is_active`: 버전이 현재 활성 상태인지 여부
- `created_at`: 생성 타임스탬프
- `statistics`: 버전 통계 및 메트릭

## 오류 처리

```python
from synapse_sdk.clients.exceptions import ClientError

def robust_model_operations():
    """오류 처리가 있는 안정적인 모델 작업 예제."""

    try:
        # 모델 가져오기 시도
        model = client.get_model(999)
    except ClientError as e:
        if e.status_code == 404:
            print("모델을 찾을 수 없음")
            return None
        else:
            print(f"모델 가져오기 오류: {e}")
            raise

    try:
        # 모델 생성 시도
        model_data = {
            'name': 'Test Model',
            'model_type': 'classification',
            'project': 123,
            'file': '/path/to/model.pkl'
        }
        new_model = client.create_model(model_data)
    except ClientError as e:
        if e.status_code == 400:
            print(f"잘못된 모델 데이터: {e.response}")
        elif e.status_code == 413:
            print("모델 파일이 너무 큼")
        else:
            print(f"모델 생성 오류: {e}")
        return None

    return new_model
```

## 참고

- [BackendClient](./backend.md) - 메인 백엔드 클라이언트
- [DataCollectionClientMixin](./data-collection-mixin.md) - 데이터 관리 작업
- [IntegrationClientMixin](./integration-mixin.md) - 플러그인 및 작업 관리
