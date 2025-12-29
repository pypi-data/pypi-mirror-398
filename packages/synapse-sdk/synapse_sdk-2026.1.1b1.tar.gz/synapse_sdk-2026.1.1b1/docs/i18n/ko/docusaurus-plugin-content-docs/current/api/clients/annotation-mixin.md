---
id: annotation-mixin
title: AnnotationClientMixin
sidebar_position: 11
---

# AnnotationClientMixin

Synapse 백엔드를 위한 어노테이션 및 태스크 관리 작업을 제공합니다.

## 개요

`AnnotationClientMixin`은 태스크, 어노테이션, 프로젝트, 태스크 태깅과 관련된 모든 작업을 처리합니다. 이 믹스인은 `BackendClient`에 자동으로 포함되며 어노테이션 워크플로를 위한 메서드를 제공합니다.

## 프로젝트 작업

### `get_project(pk)`

특정 프로젝트에 대한 상세 정보를 가져옵니다.

```python
project = client.get_project(123)
print(f"프로젝트: {project['name']}")
print(f"설명: {project['description']}")
```

**매개변수:**

- `pk` (int): 프로젝트 ID

**반환값:**

- `dict`: 구성, 메타데이터, 설정을 포함한 프로젝트 상세정보

## 태스크 작업

### `get_task(pk, params)`

특정 태스크에 대한 상세 정보를 가져옵니다.

```python
# 기본 태스크 상세정보
task = client.get_task(456)

# 확장된 데이터 유닛이 포함된 태스크
task = client.get_task(456, params={'expand': 'data_unit'})

# 여러 확장이 포함된 태스크
task = client.get_task(456, params={
    'expand': ['data_unit', 'assignment', 'annotations']
})
```

**매개변수:**

- `pk` (int): 태스크 ID
- `params` (dict): 필터링 및 확장을 위한 쿼리 매개변수

**일반적인 params:**

- `expand`: 포함할 관련 객체의 목록 또는 문자열
- `include_annotations`: 어노테이션 데이터 포함 여부

### `annotate_task_data(pk, data)`

태스크에 대한 어노테이션 데이터를 제출합니다.

```python
# 바운딩 박스 어노테이션 제출
annotation_data = {
    'annotations': [
        {
            'type': 'bbox',
            'coordinates': [10, 10, 100, 100],
            'label': 'person',
            'confidence': 0.95
        },
        {
            'type': 'polygon',
            'points': [[0, 0], [50, 0], [50, 50], [0, 50]],
            'label': 'vehicle'
        }
    ],
    'metadata': {
        'annotator_id': 'user123',
        'timestamp': '2023-10-01T12:00:00Z'
    }
}

result = client.annotate_task_data(456, annotation_data)
```

**매개변수:**

- `pk` (int): 태스크 ID
- `data` (dict): 어노테이션 데이터 구조

**반환값:**

- `dict`: 제출된 어노테이션이 포함된 업데이트된 태스크

### `list_tasks(params=None, url_conversion=None, list_all=False)`

필터링 및 페이지네이션 지원과 함께 태스크를 나열합니다.

```python
# 특정 프로젝트의 태스크 나열
tasks = client.list_tasks(params={'project': 123})

# 상태 필터가 적용된 태스크 나열
tasks = client.list_tasks(params={
    'project': 123,
    'status': 'pending'
})

# 모든 태스크 가져오기 (페이지네이션 자동 처리)
all_tasks = client.list_tasks(list_all=True)

# 파일에 대한 사용자 정의 URL 변환과 함께 태스크 나열
tasks = client.list_tasks(
    params={'project': 123},
    url_conversion={'files': lambda url: f"https://cdn.example.com{url}"}
)
```

**매개변수:**

- `params` (dict, 선택사항): 필터링 매개변수
- `url_conversion` (dict, 선택사항): 파일 필드에 대한 사용자 정의 URL 변환
- `list_all` (bool): True인 경우, 모든 결과를 가져오기 위해 페이지네이션을 자동 처리

**일반적인 필터링 params:**

- `project`: 프로젝트 ID로 필터링
- `status`: 태스크 상태로 필터링 (`pending`, `in_progress`, `completed`)
- `assignee`: 할당된 사용자 ID로 필터링
- `created_after`: 생성 날짜로 필터링
- `search`: 태스크 내용에서 텍스트 검색

**반환값:**

- `tuple`: `list_all=False`인 경우 (tasks_list, total_count)
- `list`: `list_all=True`인 경우 모든 태스크

### `create_tasks(data)`

하나 이상의 새 태스크를 생성합니다.

```python
# 단일 태스크 생성
new_task = client.create_tasks({
    'project': 123,
    'data_unit': 789,
    'priority': 'high',
    'metadata': {'batch': 'batch_001'}
})

# 여러 태스크 생성
new_tasks = client.create_tasks([
    {'project': 123, 'data_unit': 789},
    {'project': 123, 'data_unit': 790},
    {'project': 123, 'data_unit': 791}
])
```

**매개변수:**

- `data` (dict 또는 list): 태스크 데이터 또는 태스크 데이터 목록

**태스크 데이터 구조:**

- `project` (int, 필수): 프로젝트 ID
- `data_unit` (int, 필수): 데이터 유닛 ID
- `priority` (str, 선택사항): 태스크 우선순위 (`low`, `normal`, `high`)
- `assignee` (int, 선택사항): 태스크를 할당할 사용자 ID
- `metadata` (dict, 선택사항): 추가 태스크 메타데이터

**반환값:**

- `dict` 또는 `list`: 생성된 ID가 포함된 생성된 태스크

### `set_tags_tasks(data, params=None)`

여러 태스크에 일괄적으로 태그를 설정합니다.

```python
# 여러 태스크에 태그 설정
client.set_tags_tasks({
    'task_ids': [456, 457, 458],
    'tag_ids': [1, 2, 3]  # 적용할 태그 ID
})

# 추가 매개변수와 함께 태그 설정
client.set_tags_tasks(
    {
        'task_ids': [456, 457],
        'tag_ids': [1, 2]
    },
    params={'replace': True}  # 기존 태그 교체
)
```

**매개변수:**

- `data` (dict): 일괄 태깅 데이터
- `params` (dict, 선택사항): 추가 매개변수

**데이터 구조:**

- `task_ids` (list): 태그를 설정할 태스크 ID 목록
- `tag_ids` (list): 적용할 태그 ID 목록

**선택적 params:**

- `replace` (bool): True인 경우 기존 태그 교체, False인 경우 기존 태그에 추가

## 태스크 태그 작업

### `get_task_tag(pk)`

특정 태스크 태그에 대한 상세정보를 가져옵니다.

```python
tag = client.get_task_tag(123)
print(f"태그: {tag['name']} - {tag['description']}")
```

**매개변수:**

- `pk` (int): 태그 ID

**반환값:**

- `dict`: 이름, 설명, 메타를 포함한 태그 상세정보

### `list_task_tags(params)`

필터링과 함께 사용 가능한 태스크 태그를 나열합니다.

```python
# 모든 태그 나열
tags = client.list_task_tags({})

# 특정 프로젝트의 태그 나열
project_tags = client.list_task_tags({
    'project': 123
})

# 이름으로 태그 검색
search_tags = client.list_task_tags({
    'search': 'quality'
})
```

**매개변수:**

- `params` (dict): 필터링 매개변수

**일반적인 필터링 params:**

- `project`: 프로젝트 ID로 필터링
- `search`: 태그 이름에서 텍스트 검색
- `color`: 태그 색상으로 필터링

**반환값:**

- `tuple`: (tags_list, total_count)

## 오류 처리

```python
from synapse_sdk.clients.exceptions import ClientError

try:
    task = client.get_task(999999)
except ClientError as e:
    if e.status_code == 404:
        print("태스크를 찾을 수 없음")
    elif e.status_code == 403:
        print("권한이 거부됨")
    else:
        print(f"API 오류: {e}")
```

## 참고

- [BackendClient](./backend.md) - 메인 백엔드 클라이언트
- [HITLClientMixin](./hitl-mixin.md) - Human-in-the-loop 작업
- [DataCollectionClientMixin](./data-collection-mixin.md) - 데이터 관리
