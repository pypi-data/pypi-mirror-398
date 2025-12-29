---
id: hitl-mixin
title: HITLClientMixin
sidebar_position: 14
---

# HITLClientMixin

Synapse 백엔드를 위한 Human-in-the-Loop (HITL) 할당 관리 작업을 제공합니다.

## 개요

`HITLClientMixin`은 할당 관리 및 태깅을 포함한 human-in-the-loop 워크플로와 관련된 모든 작업을 처리합니다. 이 믹스인은 `BackendClient`에 자동으로 포함되며 인간 어노테이션 및 검토 워크플로를 관리하기 위한 메서드를 제공합니다.

## 할당 작업

### `get_assignment(pk)`

특정 할당에 대한 상세 정보를 가져옵니다.

```python
assignment = client.get_assignment(789)
print(f"할당: {assignment['id']}")
print(f"프로젝트: {assignment['project']}")
print(f"상태: {assignment['status']}")
print(f"할당자: {assignment['assignee']}")
print(f"데이터: {assignment['data']}")
```

**매개변수:**

- `pk` (int): 할당 ID

**반환값:**

- `dict`: 완전한 할당 정보

**할당 구조:**

- `id`: 할당 ID
- `project`: 연관된 프로젝트 ID
- `status`: 할당 상태 (`pending`, `in_progress`, `completed`, `rejected`)
- `assignee`: 할당된 검토자의 사용자 ID
- `data`: 할당 데이터 및 어노테이션
- `file`: 연관된 파일
- `created_at`: 생성 타임스탬프
- `updated_at`: 마지막 업데이트 타임스탬프
- `metadata`: 추가 할당 메타데이터

### `list_assignments(params=None, url_conversion=None, list_all=False)`

포괄적인 필터링 및 페이지네이션 지원과 함께 할당을 나열합니다.

```python
# 특정 프로젝트의 할당 나열
assignments = client.list_assignments(params={'project': 123})

# 상태별 할당 나열
pending_assignments = client.list_assignments(params={
    'project': 123,
    'status': 'pending'
})

# 특정 할당자의 할당 나열
user_assignments = client.list_assignments(params={
    'assignee': 456
})

# 모든 할당 가져오기 (페이지네이션 자동 처리)
all_assignments = client.list_assignments(list_all=True)

# 파일에 대한 사용자 정의 URL 변환과 함께 할당 나열
assignments = client.list_assignments(
    params={'project': 123},
    url_conversion={'files': lambda url: f"https://cdn.example.com{url}"}
)
```

**매개변수:**

- `params` (dict, 선택사항): 필터링 매개변수
- `url_conversion` (dict, 선택사항): 파일 필드에 대한 사용자 정의 URL 변환
- `list_all` (bool): True인 경우, 페이지네이션을 자동 처리

**일반적인 필터링 params:**

- `project`: 프로젝트 ID로 필터링
- `status`: 할당 상태로 필터링
- `assignee`: 할당된 사용자 ID로 필터링
- `created_after`: 생성 날짜로 필터링
- `updated_after`: 마지막 업데이트 날짜로 필터링
- `priority`: 할당 우선순위로 필터링
- `search`: 할당 내용에서 텍스트 검색

**반환값:**

- `tuple`: `list_all=False`인 경우 (assignments_list, total_count)
- `list`: `list_all=True`인 경우 모든 할당

### `set_tags_assignments(data, params=None)`

일괄 작업으로 여러 할당에 태그를 설정합니다.

```python
# 여러 할당에 태그 설정
client.set_tags_assignments({
    'assignment_ids': [789, 790, 791],
    'tag_ids': [1, 2, 3]  # 적용할 태그 ID
})

# 교체 옵션과 함께 태그 설정
client.set_tags_assignments(
    {
        'assignment_ids': [789, 790],
        'tag_ids': [1, 2]
    },
    params={'replace': True}  # 기존 태그 교체
)

# 우선순위 태그 설정
client.set_tags_assignments({
    'assignment_ids': [789],
    'tag_ids': [5]  # 높은 우선순위 태그
})
```

**매개변수:**

- `data` (dict): 일괄 태깅 데이터
- `params` (dict, 선택사항): 추가 매개변수

**데이터 구조:**

- `assignment_ids` (list): 태그를 설정할 할당 ID 목록
- `tag_ids` (list): 적용할 태그 ID 목록

**선택적 params:**

- `replace` (bool): True인 경우 기존 태그 교체, False인 경우 기존 태그에 추가
- `notify` (bool): True인 경우 태그 변경을 할당자에게 알림

**반환값:**

- `dict`: 태깅 작업 결과

## 오류 처리

```python
from synapse_sdk.clients.exceptions import ClientError

def robust_assignment_operations():
    """오류 처리가 있는 안정적인 할당 작업 예제."""

    try:
        # 할당 가져오기 시도
        assignment = client.get_assignment(999)
    except ClientError as e:
        if e.status_code == 404:
            print("할당을 찾을 수 없음")
            return None
        elif e.status_code == 403:
            print("권한이 거부됨 - 액세스 권한 부족")
            return None
        else:
            print(f"할당 가져오기 오류: {e}")
            raise

    try:
        # 태그 설정 시도
        client.set_tags_assignments({
            'assignment_ids': [999],
            'tag_ids': [1, 2, 3]
        })
    except ClientError as e:
        if e.status_code == 400:
            print(f"잘못된 태깅 데이터: {e.response}")
        elif e.status_code == 404:
            print("할당 또는 태그를 찾을 수 없음")
        else:
            print(f"태그 설정 오류: {e}")

    return assignment

# 안정적인 작업 사용
assignment = robust_assignment_operations()
```

## 참고

- [BackendClient](./backend.md) - 메인 백엔드 클라이언트
- [AnnotationClientMixin](./annotation-mixin.md) - 태스크 및 어노테이션 관리
- [IntegrationClientMixin](./integration-mixin.md) - 플러그인 및 작업 관리
